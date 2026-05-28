import time

from flask import Blueprint, redirect, render_template, request, session, url_for

from app.content import LEVEL_COLORS
from app.models import Exam
from app.services import (
    calculate_results,
    exam_to_dict,
    get_exam_by_slug,
    get_exam_history,
    save_exam_attempt,
)
from app.utils import login_required

exams_bp = Blueprint("exams", __name__)


def _phase_questions(exam: dict, phase_key: str) -> list[dict]:
    if phase_key == "all":
        return exam["questions"]
    qs = [q for q in exam["questions"] if q.get("phase") == phase_key]
    return qs if qs else exam["questions"]


def _exam_phases(exam: dict) -> list[dict]:
    phases = exam.get("phases") or []
    if phases:
        return phases
    return [{"key": "all", "label": "試験", "label_vi": "Bài thi", "minutes": exam["duration"]}]


def _current_phase(exam: dict) -> str:
    phases = _exam_phases(exam)
    return session.get("exam_phase") or phases[0]["key"]


def _phase_timer_seconds(exam: dict, phase_key: str) -> int:
    for ph in _exam_phases(exam):
        if ph["key"] == phase_key:
            return int(ph.get("minutes", exam["duration"])) * 60
    return exam["duration"] * 60


def _global_question_index(exam: dict, phase_key: str, local_idx: int) -> int:
    """Map phase-local index to index in full question list."""
    phase_qs = _phase_questions(exam, phase_key)
    if local_idx < 0 or local_idx >= len(phase_qs):
        return 0
    target_id = phase_qs[local_idx]["id"]
    for i, q in enumerate(exam["questions"]):
        if q["id"] == target_id:
            return i
    return local_idx


@exams_bp.route("/")
@login_required
def index():
    all_exams = Exam.query.order_by(Exam.level, Exam.id.desc()).all()
    official = []
    practice = []
    for e in all_exams:
        meta = e.sections_dict
        if meta.get("kind") == "official":
            official.append(e)
        else:
            practice.append(e)
    user_id = session["user_id"]
    return render_template(
        "exams/index.html",
        official_exams=official,
        practice_exams=practice,
        exam_history=get_exam_history(user_id),
        level_colors=LEVEL_COLORS,
    )


@exams_bp.route("/<exam_id>/start", methods=["GET", "POST"])
@login_required
def start(exam_id):
    exam_model = get_exam_by_slug(exam_id)
    if not exam_model:
        return redirect(url_for("exams.index"))

    exam = exam_to_dict(exam_model)
    phases = _exam_phases(exam)

    if request.method == "POST":
        session["current_exam"] = exam_id
        session["exam_answers"] = {}
        session["exam_marked"] = []
        session["exam_phase"] = phases[0]["key"]
        session["exam_phase_started"] = time.time()
        session["exam_started"] = time.time()
        return redirect(url_for("exams.take", exam_id=exam_id, q=0))

    written_n = len(_phase_questions(exam, "written")) if any(
        p["key"] == "written" for p in phases
    ) else len(exam["questions"])
    listening_n = len(_phase_questions(exam, "listening"))

    return render_template(
        "exams/start.html",
        exam=exam,
        phases=phases,
        written_count=written_n,
        listening_count=listening_n,
        level_colors=LEVEL_COLORS,
    )


@exams_bp.route("/<exam_id>/phase/<phase_key>")
@login_required
def begin_phase(exam_id, phase_key):
    exam_model = get_exam_by_slug(exam_id)
    if not exam_model:
        return redirect(url_for("exams.index"))
    exam = exam_to_dict(exam_model)
    valid = {p["key"] for p in _exam_phases(exam)}
    if phase_key not in valid:
        return redirect(url_for("exams.take", exam_id=exam_id, q=0))
    session["exam_phase"] = phase_key
    session["exam_phase_started"] = time.time()
    first = _global_question_index(exam, phase_key, 0)
    return redirect(url_for("exams.take", exam_id=exam_id, q=first))


@exams_bp.route("/<exam_id>")
@login_required
def take(exam_id):
    exam_model = get_exam_by_slug(exam_id)
    if not exam_model:
        return redirect(url_for("exams.index"))

    exam = exam_to_dict(exam_model)
    if session.get("current_exam") != exam_id:
        return redirect(url_for("exams.start", exam_id=exam_id))

    phase_key = _current_phase(exam)
    phase_questions = _phase_questions(exam, phase_key)
    if not phase_questions:
        return redirect(url_for("exams.start", exam_id=exam_id))

    session.setdefault("exam_answers", {})
    session.setdefault("exam_marked", [])

    q_global = int(request.args.get("q", 0))
    q_global = max(0, min(q_global, len(exam["questions"]) - 1))
    current = exam["questions"][q_global]
    if current not in phase_questions:
        q_global = _global_question_index(exam, phase_key, 0)
        current = exam["questions"][q_global]

    local_idx = phase_questions.index(current)
    phase_info = next((p for p in _exam_phases(exam) if p["key"] == phase_key), {})
    timer_sec = _phase_timer_seconds(exam, phase_key)
    phases = _exam_phases(exam)
    phase_order = [p["key"] for p in phases]
    is_last_in_phase = local_idx >= len(phase_questions) - 1
    has_next_phase = (
        is_last_in_phase
        and phase_key == "written"
        and "listening" in phase_order
        and len(_phase_questions(exam, "listening")) > 0
    )

    phase_nav = [
        {"q": q, "idx": i}
        for i, q in enumerate(exam["questions"])
        if q.get("phase") == phase_key
    ]

    return render_template(
        "exams/take.html",
        exam=exam,
        question=current,
        q_idx=q_global,
        local_idx=local_idx,
        phase_total=len(phase_questions),
        phase_nav=phase_nav,
        total=len(exam["questions"]),
        answers=session.get("exam_answers", {}),
        marked=session.get("exam_marked", []),
        level_colors=LEVEL_COLORS,
        phase_key=phase_key,
        phase_info=phase_info,
        timer_seconds=timer_sec,
        has_next_phase=has_next_phase,
        is_official=exam.get("kind") == "official",
    )


@exams_bp.route("/<exam_id>/answer", methods=["POST"])
@login_required
def save_answer(exam_id):
    exam_model = get_exam_by_slug(exam_id)
    if not exam_model:
        return redirect(url_for("exams.index"))

    exam = exam_to_dict(exam_model)
    phase_key = _current_phase(exam)
    phase_questions = _phase_questions(exam, phase_key)

    q_id = request.form.get("question_id")
    answer = request.form.get("answer")

    if q_id and answer is not None and answer != "":
        answers = session.get("exam_answers", {})
        answers[q_id] = int(answer)
        session["exam_answers"] = answers

    action = request.form.get("action", "next")
    q_idx = int(request.form.get("q_idx", 0))

    if request.form.get("mark"):
        marked = session.get("exam_marked", [])
        if q_id in marked:
            marked.remove(q_id)
        else:
            marked.append(q_id)
        session["exam_marked"] = marked

    current = exam["questions"][q_idx] if q_idx < len(exam["questions"]) else None
    local_idx = phase_questions.index(current) if current in phase_questions else 0

    if action == "save":
        return redirect(url_for("exams.take", exam_id=exam_id, q=q_idx))

    if action == "prev" and local_idx > 0:
        prev_global = _global_question_index(exam, phase_key, local_idx - 1)
        return redirect(url_for("exams.take", exam_id=exam_id, q=prev_global))
    if action == "next_phase":
        return redirect(url_for("exams.begin_phase", exam_id=exam_id, phase_key="listening"))
    if action == "next" and local_idx < len(phase_questions) - 1:
        next_global = _global_question_index(exam, phase_key, local_idx + 1)
        return redirect(url_for("exams.take", exam_id=exam_id, q=next_global))
    if action in ("submit", "next") and local_idx >= len(phase_questions) - 1:
        phases = _exam_phases(exam)
        if (
            action == "next"
            and phase_key == "written"
            and any(p["key"] == "listening" for p in phases)
            and _phase_questions(exam, "listening")
        ):
            return redirect(url_for("exams.begin_phase", exam_id=exam_id, phase_key="listening"))
        return redirect(url_for("exams.results", exam_id=exam_id))

    return redirect(url_for("exams.take", exam_id=exam_id, q=q_idx))


@exams_bp.route("/<exam_id>/results")
@login_required
def results(exam_id):
    exam_model = get_exam_by_slug(exam_id)
    if not exam_model:
        return redirect(url_for("exams.index"))

    answers = session.get("exam_answers", {})
    results_data = calculate_results(exam_model, answers)

    save_exam_attempt(session["user_id"], exam_model, answers, results_data)

    from app.services import get_user_by_id

    user_obj = get_user_by_id(session["user_id"])
    session["user"] = user_obj.to_session_dict()

    exam = exam_to_dict(exam_model)
    review = []
    for i, q in enumerate(exam["questions"]):
        user_ans = answers.get(q["id"])
        is_correct = user_ans is not None and int(user_ans) == q["correct_answer"]
        review.append({**q, "user_answer": user_ans, "is_correct": is_correct, "index": i})

    session.pop("exam_answers", None)
    session.pop("exam_marked", None)
    session.pop("exam_phase", None)
    session.pop("exam_phase_started", None)
    session.pop("current_exam", None)

    return render_template(
        "exams/results.html",
        exam=exam,
        results=results_data,
        review=review,
        level_colors=LEVEL_COLORS,
    )
