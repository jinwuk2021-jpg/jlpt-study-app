# AGENTS.md

## Cursor Cloud specific instructions

### Overview

NihongoMaster is a Flask + SQLite JLPT learning platform. See `README.md` for full feature list and project structure.

### Running the dev server

```bash
python3 run.py
```

The server starts on `http://127.0.0.1:5001` in debug mode with hot-reloading enabled. Use `python3` (not `python`) as the system does not alias `python` to `python3`.

### Database

SQLite at `instance/jlpt.db` — auto-created and seeded on first startup. To reset, delete `instance/jlpt.db` and restart the server.

### Demo account

- Email: `hanako@example.com` / Password: `password123`

### Linting / Testing

No dedicated linter or test framework is configured in this project. Use `python3 -m py_compile <file>` for syntax verification.

### Environment variables

All optional with sensible defaults — no secrets are required to run the app locally. See `app/__init__.py` for `SECRET_KEY`, `DATABASE_URL`, and `JLPT_SKIP_EXAM_SYNC`.

### Gotchas

- First startup takes a few extra seconds due to exam markdown sync (loads ~45 exam files from `data/exam/`). Set `JLPT_SKIP_EXAM_SYNC=1` to skip this during development if not working on exam features.
- `deep-translator` and `PyMuPDF` in `requirements.txt` are only used by offline scripts in `scripts/`, not at runtime.
