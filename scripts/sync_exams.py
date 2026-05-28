#!/usr/bin/env python3
"""Sync official exams from data/exam/*.md into the database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.exam_sync import sync_official_exams


def main():
    app = create_app()
    with app.app_context():
        result = sync_official_exams()
        print(f"Synced official exams: {result}")


if __name__ == "__main__":
    main()
