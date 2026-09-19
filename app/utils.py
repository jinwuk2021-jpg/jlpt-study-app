from functools import wraps

from flask import redirect, request, session, url_for


def _ensure_guest_session():
    """Auto-login as the shared guest user; create it if it doesn't exist yet."""
    if session.get("user_id"):
        return
    from app.extensions import db
    from app.models import User

    guest = User.query.filter_by(email="guest@local").first()
    if not guest:
        guest = User(name="Người dùng", email="guest@local", level="N5", xp=0, streak=0)
        guest.set_password("guest-no-login")
        db.session.add(guest)
        db.session.commit()

    session["user_id"] = guest.id
    session["user"] = guest.to_session_dict()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        _ensure_guest_session()
        # Redirect to onboarding if level hasn't been selected yet
        if not session.get("level_selected") and request.endpoint != "dashboard.onboarding":
            return redirect(url_for("dashboard.onboarding"))
        return f(*args, **kwargs)

    return decorated
