from flask import Blueprint, render_template

from app.content import LEVEL_COLORS
from app.models import Exam
from app.services import get_admin_stats
from app.utils import login_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@login_required
def index():
    return render_template(
        "admin/index.html",
        stats=get_admin_stats(),
        exams=Exam.query.order_by(Exam.id).all(),
        tab="overview",
        level_colors=LEVEL_COLORS,
    )
