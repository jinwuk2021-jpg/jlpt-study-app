from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy import func

from app.content import AI_RESPONSES, DAILY_MISSIONS, LEVEL_COLORS, WEEKLY_PROGRESS
from app.data_loader import JLPT_LEVELS
from app.extensions import db
from app.models import Grammar, Kanji, Listening, Vocabulary
from app.services import get_exam_history, get_leaderboard, get_user_achievements, get_user_by_id
from app.utils import login_required

dashboard_bp = Blueprint("dashboard", __name__)


def _current_user():
    return get_user_by_id(session["user_id"])


def _user_level() -> str:
    user = _current_user()
    level = user.level if user and user.level in JLPT_LEVELS else "N5"
    return level


def _grammar_counts() -> list[dict]:
    rows = (
        db.session.query(Grammar.level, func.count(Grammar.id))
        .group_by(Grammar.level)
        .all()
    )
    counts = {level: count for level, count in rows}
    return [{"level": level, "count": counts.get(level, 0)} for level in JLPT_LEVELS]


@dashboard_bp.route("/")
@login_required
def index():
    user = _current_user()
    session["user"] = user.to_session_dict()
    return render_template(
        "dashboard/index.html",
        user=user.to_session_dict(),
        achievements=get_user_achievements(user.id),
        missions=DAILY_MISSIONS,
        exam_history=get_exam_history(user.id),
        weekly=WEEKLY_PROGRESS,
        level_colors=LEVEL_COLORS,
    )


@dashboard_bp.route("/vocabulary")
@login_required
def vocabulary():
    level = _user_level()
    items = Vocabulary.query.filter_by(level=level).order_by(Vocabulary.id).all()
    idx = int(request.args.get("i", 0)) % max(len(items), 1)
    vocab = items[idx] if items else None
    return render_template(
        "dashboard/vocabulary.html",
        vocab=vocab,
        current_idx=idx,
        all_vocab=items,
        user_level=level,
        level_colors=LEVEL_COLORS,
    )


@dashboard_bp.route("/kanji")
@login_required
def kanji():
    level = _user_level()
    items = Kanji.query.filter_by(level=level).order_by(Kanji.id).all()
    idx = int(request.args.get("i", 0)) % max(len(items), 1)
    return render_template(
        "dashboard/kanji.html",
        kanji=items[idx] if items else None,
        kanji_list=items,
        selected=idx,
        user_level=level,
        level_colors=LEVEL_COLORS,
    )


@dashboard_bp.route("/grammar")
@login_required
def grammar():
    level = _user_level()
    items = Grammar.query.filter_by(level=level).order_by(Grammar.id).all()
    idx = int(request.args.get("i", 0)) % max(len(items), 1)
    return render_template(
        "dashboard/grammar.html",
        grammar=items[idx] if items else None,
        grammar_list=items,
        selected=idx,
        grammar_counts=_grammar_counts(),
        user_level=level,
        level_colors=LEVEL_COLORS,
    )


@dashboard_bp.route("/listening")
@login_required
def listening():
    level = _user_level()
    items = Listening.query.filter_by(level=level).order_by(Listening.id).all()
    idx = int(request.args.get("i", 0)) % max(len(items), 1)
    return render_template(
        "dashboard/listening.html",
        item=items[idx] if items else None,
        listening_list=items,
        selected=idx,
        user_level=level,
        level_colors=LEVEL_COLORS,
    )


@dashboard_bp.route("/ai-tutor", methods=["GET", "POST"])
@login_required
def ai_tutor():
    messages = session.get("chat_messages", [
        {"role": "assistant", "content": "こんにちは！I'm your AI Japanese tutor. Ask me anything about grammar, vocabulary, or JLPT preparation!"}
    ])
    if request.method == "POST":
        user_msg = request.form.get("message", "").strip()
        if user_msg:
            messages.append({"role": "user", "content": user_msg})
            lower = user_msg.lower()
            if "te-form" in lower or "て" in user_msg:
                resp = AI_RESPONSES["te-form"]
            elif "particle" in lower or "は" in user_msg or "が" in user_msg:
                resp = AI_RESPONSES["particles"]
            else:
                resp = AI_RESPONSES["default"]
            messages.append({"role": "assistant", "content": resp})
            session["chat_messages"] = messages
    return render_template("dashboard/ai_tutor.html", messages=messages)


@dashboard_bp.route("/leaderboard")
@login_required
def leaderboard():
    user = _current_user()
    return render_template(
        "dashboard/leaderboard.html",
        leaderboard=get_leaderboard(),
        user=user.to_session_dict(),
        level_colors=LEVEL_COLORS,
    )


@dashboard_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = _current_user()
    if request.method == "POST":
        user.name = request.form.get("name", user.name)
        user.email = request.form.get("email", user.email)
        user.level = request.form.get("level", user.level)
        db.session.commit()
        session["user"] = user.to_session_dict()
        return redirect(url_for("dashboard.settings"))
    return render_template(
        "dashboard/settings.html",
        user=user.to_session_dict(),
        levels=JLPT_LEVELS,
        level_colors=LEVEL_COLORS,
    )
