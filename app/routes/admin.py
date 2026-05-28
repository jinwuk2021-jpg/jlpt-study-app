from flask import Blueprint, render_template, request, session

from app.content import LEVEL_COLORS
from app.data_loader import JLPT_LEVELS
from app.level_groups import group_items_by_level, resolve_active_level
from app.models import Exam
from app.services import get_admin_stats, get_user_by_id
from app.utils import login_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@login_required
def index():
    user = get_user_by_id(session.get("user_id"))
    default_lv = user.level if user and user.level in JLPT_LEVELS else "N5"
    return render_template(
        "admin/index.html",
        stats=get_admin_stats(),
        exams_by_level=group_items_by_level(Exam.query.order_by(Exam.level, Exam.id).all()),
        tab="overview",
        level_colors=LEVEL_COLORS,
        open_level=resolve_active_level(request, default_lv),
    )
