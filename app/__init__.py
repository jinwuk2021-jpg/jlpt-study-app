import os
from datetime import timedelta

from flask import Flask

from app.extensions import db


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    if not os.environ.get("VERCEL"):
        os.makedirs(app.instance_path, exist_ok=True)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config.update(
        PERMANENT_SESSION_LIFETIME=timedelta(days=100),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL")),
    )
    database_url = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(app.instance_path, 'jlpt.db')}",
    )
    # Some providers still expose the legacy postgres:// scheme. SQLAlchemy 2
    # expects postgresql://, so normalize it before initializing the engine.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if database_url.startswith("postgresql"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }

    db.init_app(app)

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.exams import exams_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(exams_bp, url_prefix="/dashboard/exams")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.before_request
    def keep_authenticated_sessions():
        """Upgrade active logins to a rolling 100-day persistent session."""
        from flask import session

        if session.get("user_id"):
            session.permanent = True

    # Vercel imports the app on every cold start. Schema creation and the large
    # exam sync are deployment tasks, not request-startup work. Keep the current
    # convenient behavior for local development only.
    if not os.environ.get("VERCEL"):
        with app.app_context():
            db.create_all()
            from app.seed import seed_database
            seed_database()
            if not os.environ.get("JLPT_SKIP_EXAM_SYNC"):
                from app.exam_sync import sync_official_exams
                sync_official_exams()

    return app
