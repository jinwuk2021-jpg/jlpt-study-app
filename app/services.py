import json
import re
from datetime import datetime, timezone

from app.extensions import db
from app.models import Achievement, Exam, ExamAttempt, Question, User, UserAchievement


def get_user_by_id(user_id: int) -> User | None:
    return db.session.get(User, user_id)


def get_user_by_email(email: str) -> User | None:
    return User.query.filter_by(email=email).first()


def get_leaderboard(limit: int = 10) -> list[dict]:
    users = User.query.order_by(User.xp.desc()).limit(limit).all()
    return [
        {"rank": i + 1, "user_id": u.id, "name": u.name, "xp": u.xp, "level": u.level, "streak": u.streak}
        for i, u in enumerate(users)
    ]


def get_user_achievements(user_id: int) -> list[dict]:
    rows = UserAchievement.query.filter_by(user_id=user_id).all()
    result = []
    for row in rows:
        result.append({
            "id": row.achievement.slug,
            "title": row.achievement.title,
            "description": row.achievement.description,
            "icon": row.achievement.icon,
            "unlocked": row.unlocked_at is not None,
            "progress": row.progress,
            "max_progress": row.achievement.max_progress,
        })
    return result


def get_exam_by_slug(slug: str) -> Exam | None:
    return Exam.query.filter_by(slug=slug).first()


def exam_to_dict(exam: Exam) -> dict:
    questions = exam.questions.order_by(Question.sort_order).all()
    sections = exam.sections_dict
    question_dicts = [question_to_dict(q, sections) for q in questions]
    listening_number = 0
    written_number = 0
    for question in question_dicts:
        if question["phase"] == "listening":
            listening_number += 1
            question["display_id"] = f"L{listening_number}"
        else:
            written_number += 1
            question["display_id"] = f"Q{written_number}"
    return {
        "id": exam.slug,
        "db_id": exam.id,
        "title": exam.title,
        "level": exam.level,
        "description": exam.description,
        "duration": exam.duration,
        "sections": sections,
        "passing_score": exam.passing_score,
        "kind": sections.get("kind", "practice"),
        "date": sections.get("date", ""),
        "audio": sections.get("audio", ""),
        "phases": sections.get("phases", []),
        "questions": question_dicts,
    }


def question_to_dict(q: Question, exam_sections: dict | None = None) -> dict:
    tail = q.slug.split("-")[-1]
    display_id = tail[0].upper() + tail[1:] if tail else q.slug

    section_label = q.section
    phase = "listening" if display_id.startswith("L") or q.section.startswith("聴解") else "written"
    if exam_sections:
        for sec in exam_sections.get("section_list", []):
            if sec.get("id") == q.section:
                section_label = sec.get("label", q.section)
                break
            q_range = str(sec.get("questions", ""))
            ids = _ids_in_range(q_range)
            if display_id in ids:
                section_label = sec.get("label", q.section)
                break
        for ph in exam_sections.get("phases", []):
            if ph.get("key") == phase:
                pass

    return {
        "id": q.slug,
        "db_id": q.id,
        "section": q.section,
        "section_label": section_label,
        "type": q.type,
        "level": q.level,
        "question": q.question,
        "question_ja": q.question_ja or "",
        "options": q.options_list,
        "correct_answer": q.correct_answer,
        "explanation": q.explanation,
        "passage": q.passage or "",
        "points": q.points,
        "display_id": display_id,
        "phase": phase,
        "audio_only": "audio_only" in (q.question_ja or "") or "印刷されていません" in (q.question_ja or ""),
    }


def _ids_in_range(q_range: str) -> list[str]:
    q_range = str(q_range).strip()
    if not q_range or "-" not in q_range:
        return [q_range] if q_range else []
    start, end = q_range.split("-", 1)
    prefix = "L" if start.strip().upper().startswith("L") else "Q"
    s_num = int(re.sub(r"\D", "", start))
    e_num = int(re.sub(r"\D", "", end))
    return [f"{prefix}{i}" for i in range(s_num, e_num + 1)]




def calculate_results(exam: Exam, answers: dict) -> dict:
    questions = exam.questions.order_by(Question.sort_order).all()
    correct = 0
    section_scores: dict = {}
    weaknesses = []

    for q in questions:
        sec = q.section
        if sec not in section_scores:
            section_scores[sec] = {"correct": 0, "total": 0}
        section_scores[sec]["total"] += 1

        user_ans = answers.get(q.slug)
        if user_ans is not None and int(user_ans) == q.correct_answer:
            correct += 1
            section_scores[sec]["correct"] += 1
        elif user_ans is not None:
            weaknesses.append(f"{sec}: {q.question[:50]}...")

    total = len(questions)
    score = round((correct / total) * 100) if total else 0
    passed = score >= exam.passing_score

    return {
        "correct": correct,
        "total": total,
        "score": score,
        "passed": passed,
        "section_scores": section_scores,
        "weaknesses": weaknesses,
    }


def save_exam_attempt(user_id: int, exam: Exam, answers: dict, results: dict) -> ExamAttempt:
    attempt = ExamAttempt(
        user_id=user_id,
        exam_id=exam.id,
        score=results["score"],
        passed=results["passed"],
        answers=json.dumps(answers),
        section_scores=json.dumps(results["section_scores"]),
        weaknesses=json.dumps(results["weaknesses"]),
        completed_at=datetime.now(timezone.utc),
    )
    db.session.add(attempt)

    user = db.session.get(User, user_id)
    if user:
        user.xp += results["correct"] * 10

    db.session.commit()
    return attempt


def get_exam_history(user_id: int, limit: int = 10) -> list[dict]:
    attempts = (
        ExamAttempt.query.filter_by(user_id=user_id)
        .order_by(ExamAttempt.completed_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": a.id,
            "exam_title": a.exam.title,
            "date": a.completed_at.strftime("%Y-%m-%d") if a.completed_at else "",
            "score": a.score,
            "passed": a.passed,
            "level": a.exam.level,
        }
        for a in attempts
    ]


def get_admin_stats() -> dict:
    total_students = User.query.count()
    active_exams = Exam.query.count()
    total_questions = Question.query.count()
    attempts = ExamAttempt.query.all()
    avg_pass = round(sum(1 for a in attempts if a.passed) / len(attempts) * 100) if attempts else 0

    recent = (
        ExamAttempt.query.order_by(ExamAttempt.completed_at.desc())
        .limit(5)
        .all()
    )
    return {
        "total_students": total_students,
        "active_exams": active_exams,
        "total_questions": total_questions,
        "avg_pass_rate": avg_pass,
        "recent_results": [
            {
                "student": a.user.name,
                "exam": a.exam.title,
                "score": a.score,
                "date": a.completed_at.strftime("%Y-%m-%d") if a.completed_at else "",
            }
            for a in recent
        ],
    }
