from flask import Blueprint, redirect, render_template, request, session, url_for

from app.content import LEVEL_COLORS
from app.models import Exam
from app.services import (
    calculate_results,
    exam_to_dict,
    get_exam_by_slug,
    get_exam_history,
    question_to_dict,
    save_exam_attempt,
)
from app.utils import login_required

exams_bp = Blueprint("exams", __name__)


@exams_bp.route("/")
@login_required
def index():
    exams = Exam.query.order_by(Exam.id).all()
    user_id = session["user_id"]
    return render_template(
        "exams/index.html",
        exams=exams,
        exam_history=get_exam_history(user_id),
        level_colors=LEVEL_COLORS,
    )


@exams_bp.route("/<exam_id>")
@login_required
def take(exam_id):
    exam_model = get_exam_by_slug(exam_id)
    if not exam_model:
        return redirect(url_for("exams.index"))

    exam = exam_to_dict(exam_model)
    session["current_exam"] = exam_id
    session.setdefault("exam_answers", {})
    session.setdefault("exam_marked", [])

    q_idx = int(request.args.get("q", 0))
    q_idx = max(0, min(q_idx, len(exam["questions"]) - 1))

    return render_template(
        "exams/take.html",
        exam=exam,
        question=exam["questions"][q_idx],
        q_idx=q_idx,
        total=len(exam["questions"]),
        answers=session.get("exam_answers", {}),
        marked=session.get("exam_marked", []),
        level_colors=LEVEL_COLORS,
    )


@exams_bp.route("/<exam_id>/answer", methods=["POST"])
@login_required
def save_answer(exam_id):
    exam_model = get_exam_by_slug(exam_id)
    if not exam_model:
        return redirect(url_for("exams.index"))

    exam = exam_to_dict(exam_model)
    q_id = request.form.get("question_id")
    answer = request.form.get("answer")

    if q_id and answer is not None:
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

    if action == "prev" and q_idx > 0:
        return redirect(url_for("exams.take", exam_id=exam_id, q=q_idx - 1))
    if action == "next" and q_idx < len(exam["questions"]) - 1:
        return redirect(url_for("exams.take", exam_id=exam_id, q=q_idx + 1))
    if action == "submit":
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

    return render_template(
        "exams/results.html",
        exam=exam,
        results=results_data,
        review=review,
        level_colors=LEVEL_COLORS,
    )
