# NihongoMaster — JLPT Learning Platform (Python/Flask + SQLite)

Nền tảng học tiếng Nhật JLPT với mock exam, AI tutor và gamification — **Python Flask + SQLite**.

## Tính năng

- Landing page, auth (login/register), dashboard
- Vocabulary, Kanji, Grammar, Listening
- **Mock Exam System** — timer, chấm điểm, lưu kết quả vào database
- AI Tutor, Leaderboard, Admin panel
- **SQLite database** — users, exams, questions, exam attempts

## Tech Stack

- Python 3, Flask 3, Flask-SQLAlchemy
- SQLite (`instance/jlpt.db`)
- Jinja2, Tailwind CSS, Alpine.js

## Cài đặt & Chạy

```bash
cd "/Users/huynhha/Downloads/JLPT study app"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

Mở **http://localhost:5000**

### Tài khoản demo

| Email | Password |
|-------|----------|
| `hanako@example.com` | `password123` |

Database tự tạo và seed dữ liệu mẫu khi chạy lần đầu.

## Cấu trúc

```
app/
├── models.py       # SQLAlchemy models
├── seed.py         # Seed database
├── services.py     # Business logic
├── content.py      # Static landing content
├── routes/         # Blueprints
├── templates/
└── static/
instance/
└── jlpt.db         # SQLite database (auto-created)
```

## Database Models

- `User` — auth, XP, streak, JLPT level
- `Vocabulary`, `Kanji`, `Grammar`, `Listening`
- `Exam`, `Question` — mock exam content
- `ExamAttempt` — lưu kết quả thi
- `Achievement`, `UserAchievement`

## Reset database

```bash
rm instance/jlpt.db
python run.py
```

## License

MIT
