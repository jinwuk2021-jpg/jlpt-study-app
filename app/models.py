import json
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(2), default="N5")
    xp = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    attempts = db.relationship("ExamAttempt", back_populates="user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_session_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "level": self.level,
            "xp": self.xp,
            "streak": self.streak,
        }


class Vocabulary(db.Model):
    __tablename__ = "vocabulary"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    word = db.Column(db.String(100), nullable=False)
    reading = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(2), nullable=False)
    example = db.Column(db.Text, default="")
    example_meaning = db.Column(db.Text, default="")
    srs_level = db.Column(db.Integer, default=0)


class Kanji(db.Model):
    __tablename__ = "kanji"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    character = db.Column(db.String(10), nullable=False)
    meaning = db.Column(db.String(255), nullable=False)
    onyomi = db.Column(db.Text, default="[]")
    kunyomi = db.Column(db.Text, default="[]")
    strokes = db.Column(db.Integer, default=1)
    level = db.Column(db.String(2), nullable=False)
    examples = db.Column(db.Text, default="[]")

    @property
    def onyomi_list(self):
        return json.loads(self.onyomi)

    @property
    def kunyomi_list(self):
        return json.loads(self.kunyomi)

    @property
    def examples_list(self):
        return json.loads(self.examples)


class Grammar(db.Model):
    __tablename__ = "grammar"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    pattern = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(2), nullable=False)
    explanation = db.Column(db.Text, default="")
    usage = db.Column(db.String(255), default="")
    examples = db.Column(db.Text, default="[]")

    @property
    def examples_list(self):
        return json.loads(self.examples)


class Listening(db.Model):
    __tablename__ = "listening"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(2), nullable=False)
    transcript = db.Column(db.Text, default="")
    transcript_en = db.Column(db.Text, default="")
    duration = db.Column(db.Integer, default=60)


class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(2), nullable=False)
    description = db.Column(db.Text, default="")
    duration = db.Column(db.Integer, default=120)
    sections = db.Column(db.Text, default="{}")
    passing_score = db.Column(db.Integer, default=80)

    questions = db.relationship("Question", back_populates="exam", lazy="dynamic", order_by="Question.sort_order")
    attempts = db.relationship("ExamAttempt", back_populates="exam", lazy="dynamic")

    @property
    def sections_dict(self):
        return json.loads(self.sections)


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    section = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    level = db.Column(db.String(2), nullable=False)
    question = db.Column(db.Text, nullable=False)
    question_ja = db.Column(db.Text, default="")
    options = db.Column(db.Text, default="[]")
    correct_answer = db.Column(db.Integer, nullable=False)
    explanation = db.Column(db.Text, default="")
    passage = db.Column(db.Text, default="")
    points = db.Column(db.Integer, default=1)
    sort_order = db.Column(db.Integer, default=0)

    exam = db.relationship("Exam", back_populates="questions")

    @property
    def options_list(self):
        return json.loads(self.options)


class ExamAttempt(db.Model):
    __tablename__ = "exam_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    score = db.Column(db.Integer, default=0)
    passed = db.Column(db.Boolean, default=False)
    answers = db.Column(db.Text, default="{}")
    section_scores = db.Column(db.Text, default="{}")
    weaknesses = db.Column(db.Text, default="[]")
    completed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="attempts")
    exam = db.relationship("Exam", back_populates="attempts")

    @property
    def answers_dict(self):
        return json.loads(self.answers)


class Achievement(db.Model):
    __tablename__ = "achievements"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    icon = db.Column(db.String(10), default="🏆")
    max_progress = db.Column(db.Integer, default=1)


class UserAchievement(db.Model):
    __tablename__ = "user_achievements"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey("achievements.id"), nullable=False)
    progress = db.Column(db.Integer, default=0)
    unlocked_at = db.Column(db.DateTime, nullable=True)

    achievement = db.relationship("Achievement")
