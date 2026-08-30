"""Create and seed the production database once before deployment."""

import os

from app import create_app
from app.exam_sync import sync_official_exams
from app.extensions import db
from app.seed import seed_database


def main() -> None:
    if not os.environ.get("DATABASE_URL"):
        raise SystemExit("DATABASE_URL is required")

    # Prevent create_app() from doing the same work before this script controls
    # the order explicitly.
    os.environ["VERCEL"] = "1"
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_database()
        result = sync_official_exams()
        print(f"Production database initialized: {result}")


if __name__ == "__main__":
    main()
