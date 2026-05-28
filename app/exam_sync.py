"""Sync official JLPT exams from data/exam/*.md into the database."""

from __future__ import annotations

import json

from app.exam_loader import load_all_official_exams
from app.extensions import db
from app.models import Exam, Question


def sync_official_exams() -> dict:
    """Upsert all markdown exams. Returns counts."""
    imported = 0
    updated = 0
    for data in load_all_official_exams():
        sections_payload = {
            "kind": data["kind"],
            "date": data.get("date", ""),
            "audio": data.get("audio", ""),
            "source_pdf": data.get("source_pdf", ""),
            "phases": data.get("phases", []),
            "section_list": data.get("sections_meta", []),
        }
        exam = Exam.query.filter_by(slug=data["slug"]).first()
        if exam:
            exam.title = data["title"]
            exam.level = data["level"]
            exam.description = data["description"]
            exam.duration = data["duration"]
            exam.passing_score = data["passing_score"]
            exam.sections = json.dumps(sections_payload, ensure_ascii=False)
            Question.query.filter_by(exam_id=exam.id).delete()
            updated += 1
        else:
            exam = Exam(
                slug=data["slug"],
                title=data["title"],
                level=data["level"],
                description=data["description"],
                duration=data["duration"],
                passing_score=data["passing_score"],
                sections=json.dumps(sections_payload, ensure_ascii=False),
            )
            db.session.add(exam)
            db.session.flush()
            imported += 1

        for i, q in enumerate(data["questions"]):
            db.session.add(
                Question(
                    slug=f"{data['slug']}-{q['id']}",
                    exam_id=exam.id,
                    section=q["section"],
                    type=q["type"],
                    level=q["level"],
                    question=q["question"],
                    question_ja=q.get("question_ja", ""),
                    options=json.dumps(q["options"], ensure_ascii=False),
                    correct_answer=q["correct_answer"],
                    explanation=q.get("explanation", ""),
                    passage=q.get("passage", ""),
                    points=q.get("points", 1),
                    sort_order=i,
                )
            )

    db.session.commit()
    return {"imported": imported, "updated": updated, "total": imported + updated}
