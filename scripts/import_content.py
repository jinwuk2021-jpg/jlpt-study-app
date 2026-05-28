#!/usr/bin/env python3
"""Import grammar, kanji, and vocabulary from data/ into the database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.data_loader import import_to_database


def main():
    force = "--force" in sys.argv
    app = create_app()
    with app.app_context():
        result = import_to_database(force=force)
        if result.get("skipped"):
            print("Content already imported. Use --force to re-import.")
            return
        print("Imported content:")
        for level, counts in result["counts"].items():
            print(f"  {level}: {counts['grammar']} grammar, {counts['kanji']} kanji, {counts['vocabulary']} vocab")


if __name__ == "__main__":
    main()
