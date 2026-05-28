from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services import get_user_by_email
from app.utils import login_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = get_user_by_email(email)
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user"] = user.to_session_dict()
            return redirect(url_for("dashboard.index"))
        flash("Invalid email or password.", "error")
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        from app.extensions import db
        from app.models import User

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 8:
            flash("Please fill all fields. Password must be at least 8 characters.", "error")
            return render_template("auth/register.html")

        if get_user_by_email(email):
            flash("Email already registered.", "error")
            return render_template("auth/register.html")

        user = User(name=name, email=email, level="N5", xp=0, streak=0)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        session["user"] = user.to_session_dict()
        return redirect(url_for("auth.verify_email"))

    return render_template("auth/register.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    sent = False
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "")
        sent = True
    return render_template("auth/forgot_password.html", sent=sent, email=email)


@auth_bp.route("/verify-email")
@login_required
def verify_email():
    return render_template("auth/verify_email.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))
