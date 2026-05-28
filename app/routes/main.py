from flask import Blueprint, render_template

from app.content import FEATURES, JLPT_LEVELS, LEVEL_COLORS, PRICING_PLANS, TESTIMONIALS

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template(
        "landing.html",
        levels=JLPT_LEVELS,
        plans=PRICING_PLANS,
        testimonials=TESTIMONIALS,
        features=FEATURES,
        level_colors=LEVEL_COLORS,
    )
