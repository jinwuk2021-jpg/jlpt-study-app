from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy import func

from app.content import AI_RESPONSES, DAILY_MISSIONS, LEVEL_COLORS, LEVEL_ORDER, WEEKLY_PROGRESS
from app.data_loader import JLPT_LEVELS
from app.extensions import db
from app.level_groups import group_items_by_level, group_leaderboard, resolve_active_level
from app.models import Grammar, Kanji, Listening, Vocabulary
from app.services import get_exam_history, get_leaderboard, get_user_achievements, get_user_by_id
from app.utils import login_required

dashboard_bp = Blueprint("dashboard", __name__)

STUDY_LINKS = (
    ("dashboard.vocabulary", "Từ vựng", "📖"),
    ("dashboard.kanji", "Kanji", "漢"),
    ("dashboard.grammar", "Ngữ pháp", "✏️"),
    ("dashboard.listening", "Nghe", "🎧"),
    ("exams.index", "Thi thử", "📋"),
)


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
    return [{"level": level, "count": counts.get(level, 0)} for level in LEVEL_ORDER]


def _active_level() -> str:
    return resolve_active_level(request, _user_level())


def _item_at_index(items: list, idx: int):
    if not items:
        return None, 0
    i = int(idx) % len(items)
    return items[i], i


@dashboard_bp.route("/")
@login_required
def index():
    user = _current_user()
    session["user"] = user.to_session_dict()
    study_by_level = [
        {
            "level": lv,
            "links": [
                {"url": url_for(endpoint, level=lv), "label": label, "icon": icon}
                for endpoint, label, icon in STUDY_LINKS
            ],
        }
        for lv in LEVEL_ORDER
    ]
    return render_template(
        "dashboard/index.html",
        user=user.to_session_dict(),
        achievements=get_user_achievements(user.id),
        missions=DAILY_MISSIONS,
        exam_history=get_exam_history(user.id),
        weekly=WEEKLY_PROGRESS,
        level_colors=LEVEL_COLORS,
        study_by_level=study_by_level,
        open_level=_active_level(),
    )


@dashboard_bp.route("/vocabulary")
@login_required
def vocabulary():
    groups = group_items_by_level(
        Vocabulary.query.order_by(Vocabulary.level, Vocabulary.id).all()
    )
    active_level = _active_level()
    active_group = next((g for g in groups if g["level"] == active_level), None)
    items = active_group["entries"] if active_group else []
    idx = int(request.args.get("i", 0))
    vocab, current_idx = _item_at_index(items, idx)
    return render_template(
        "dashboard/vocabulary.html",
        groups=groups,
        vocab=vocab,
        current_idx=current_idx,
        active_level=active_level,
        level_colors=LEVEL_COLORS,
    )


@dashboard_bp.route("/kanji")
@login_required
def kanji():
    groups = group_items_by_level(Kanji.query.order_by(Kanji.level, Kanji.id).all())
    active_level = _active_level()
    active_group = next((g for g in groups if g["level"] == active_level), None)
    items = active_group["entries"] if active_group else []
    idx = int(request.args.get("i", 0))
    item, selected = _item_at_index(items, idx)
    return render_template(
        "dashboard/kanji.html",
        groups=groups,
        kanji=item,
        selected=selected,
        active_level=active_level,
        level_colors=LEVEL_COLORS,
    )


@dashboard_bp.route("/grammar")
@login_required
def grammar():
    groups = group_items_by_level(Grammar.query.order_by(Grammar.level, Grammar.id).all())
    active_level = _active_level()
    active_group = next((g for g in groups if g["level"] == active_level), None)
    items = active_group["entries"] if active_group else []
    idx = int(request.args.get("i", 0))
    item, selected = _item_at_index(items, idx)
    return render_template(
        "dashboard/grammar.html",
        groups=groups,
        grammar=item,
        selected=selected,
        grammar_counts=_grammar_counts(),
        active_level=active_level,
        level_colors=LEVEL_COLORS,
    )


@dashboard_bp.route("/listening")
@login_required
def listening():
    groups = group_items_by_level(Listening.query.order_by(Listening.level, Listening.id).all())
    active_level = _active_level()
    active_group = next((g for g in groups if g["level"] == active_level), None)
    items = active_group["entries"] if active_group else []
    idx = int(request.args.get("i", 0))
    item, selected = _item_at_index(items, idx)
    return render_template(
        "dashboard/listening.html",
        groups=groups,
        item=item,
        selected=selected,
        active_level=active_level,
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
    return render_template(
        "dashboard/ai_tutor.html",
        messages=messages,
        tutor_by_level=[
            {
                "level": lv,
                "prompts": [
                    f"Giải thích ngữ pháp {lv} cho tôi",
                    f"Từ vựng thường gặp ở {lv}",
                    f"Mẹo thi JLPT {lv}",
                ],
            }
            for lv in LEVEL_ORDER
        ],
        open_level=_active_level(),
    )


@dashboard_bp.route("/leaderboard")
@login_required
def leaderboard():
    user = _current_user()
    return render_template(
        "dashboard/leaderboard.html",
        leaderboard_by_level=group_leaderboard(get_leaderboard(50)),
        user=user.to_session_dict(),
        level_colors=LEVEL_COLORS,
        open_level=_active_level(),
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
