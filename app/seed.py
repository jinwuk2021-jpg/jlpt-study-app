import json

from app.extensions import db
from app.models import (
    Achievement,
    Exam,
    Listening,
    Question,
    User,
    UserAchievement,
)

N5_QUESTIONS = [
    {"id": "n5-q1", "section": "vocabulary", "type": "multiple_choice", "level": "N5", "question": "Choose the correct reading for: 学校", "question_ja": "「学校」の読み方は？", "options": ["がっこう", "がくこう", "がっこ", "がくしょう"], "correct_answer": 0, "explanation": "学校 (gakkou) means school.", "points": 1},
    {"id": "n5-q2", "section": "vocabulary", "type": "kanji_recognition", "level": "N5", "question": "What does 食 mean?", "options": ["to eat / food", "to drink", "to cook", "to buy"], "correct_answer": 0, "explanation": "食 relates to eating and food.", "points": 1},
    {"id": "n5-q3", "section": "grammar", "type": "fill_blank", "level": "N5", "question": "私は毎日日本語___勉強しています。", "options": ["を", "が", "に", "で"], "correct_answer": 0, "explanation": "を marks the direct object.", "points": 1},
    {"id": "n5-q4", "section": "grammar", "type": "multiple_choice", "level": "N5", "question": "Which sentence is correct?", "options": ["私は学生です。", "私が学生あります。", "私を学生います。", "私に学生です。"], "correct_answer": 0, "explanation": "私は学生です uses the correct copula.", "points": 1},
    {"id": "n5-q5", "section": "reading", "type": "reading_comprehension", "level": "N5", "question": "Where does Tanaka-san go on Sunday?", "passage": "田中さんは日曜日に公園へ行きます。公園で友達とサッカーをします。", "options": ["School", "Park", "Library", "Store"], "correct_answer": 1, "explanation": "公園 means park.", "points": 2},
    {"id": "n5-q6", "section": "listening", "type": "listening_comprehension", "level": "N5", "question": "What time does the train depart?", "options": ["9:00", "9:15", "9:30", "10:00"], "correct_answer": 2, "explanation": "The announcement says 9:30.", "points": 2},
]

N3_QUESTIONS = [
    {"id": "n3-q1", "section": "vocabulary", "type": "multiple_choice", "level": "N3", "question": "Choose the correct meaning of: 影響", "options": ["influence/effect", "result", "reason", "method"], "correct_answer": 0, "explanation": "影響 (eikyou) means influence.", "points": 1},
    {"id": "n3-q2", "section": "vocabulary", "type": "fill_blank", "level": "N3", "question": "彼の___は多くの人に感動を与えた。", "options": ["努力", "努力する", "努力した", "努力して"], "correct_answer": 0, "explanation": "努力 as a noun fits.", "points": 1},
    {"id": "n3-q3", "section": "grammar", "type": "multiple_choice", "level": "N3", "question": "雨が降っている___、出かけました。", "options": ["のに", "ので", "から", "が"], "correct_answer": 0, "explanation": "のに expresses contrast.", "points": 1},
    {"id": "n3-q4", "section": "grammar", "type": "matching", "level": "N3", "question": "Match the grammar pattern with its meaning:", "options": ["〜てしまう → completion/regret", "〜ておく → preparation", "〜てみる → try doing", "All correct"], "correct_answer": 3, "explanation": "All patterns are correctly matched.", "points": 2},
    {"id": "n3-q5", "section": "reading", "type": "reading_comprehension", "level": "N3", "question": "What is the main topic?", "passage": "近年、日本ではリモートワークが普及してきた。", "options": ["Remote work trends", "Company culture", "Transportation", "Technology"], "correct_answer": 0, "explanation": "The passage discusses remote work.", "points": 3},
    {"id": "n3-q6", "section": "listening", "type": "listening_comprehension", "level": "N3", "question": "What does the speaker recommend?", "options": ["Taking a vacation", "Visiting a doctor", "Changing jobs", "Moving"], "correct_answer": 1, "explanation": "The speaker recommends visiting a doctor.", "points": 2},
]


def seed_database():
    if User.query.first():
        return

    demo = User(name="田中 花子", email="hanako@example.com", level="N3", xp=4250, streak=12)
    demo.set_password("password123")
    db.session.add(demo)

    for u in [
        ("Kenji Yamamoto", "kenji@example.com", "N1", 12500, 45),
        ("Sarah Chen", "sarah@example.com", "N2", 9800, 30),
        ("Michael Park", "michael@example.com", "N2", 8750, 22),
        ("Emily Rodriguez", "emily@example.com", "N3", 3900, 18),
    ]:
        user = User(name=u[0], email=u[1], level=u[2], xp=u[3], streak=u[4])
        user.set_password("password123")
        db.session.add(user)

    db.session.commit()

    from app.data_loader import import_to_database
    import_to_database()

    for l in [
        ("l1", "At the Restaurant", "N5", "いらっしゃいませ。何名様ですか。", "Welcome. How many people?", 45),
        ("l2", "Train Announcement", "N4", "次は東京駅です。お出口は右側です。", "Next stop is Tokyo Station.", 30),
        ("l3", "News Report", "N2", "本日、政府は新しい経済政策を発表しました。", "Today, the government announced new policies.", 90),
    ]:
        db.session.add(Listening(slug=l[0], title=l[1], level=l[2], transcript=l[3], transcript_en=l[4], duration=l[5]))

    exams_data = [
        ("exam-n5-1", "JLPT N5 Mock Exam #1", "N5", "Full N5 practice exam", 105, {"vocabulary": 2, "grammar": 2, "reading": 1, "listening": 1}, 80, N5_QUESTIONS),
        ("exam-n3-1", "JLPT N3 Mock Exam #1", "N3", "Comprehensive N3 practice test", 140, {"vocabulary": 2, "grammar": 2, "reading": 1, "listening": 1}, 95, N3_QUESTIONS),
        ("exam-n2-1", "JLPT N2 Mock Exam #1", "N2", "Advanced N2 simulation", 155, {"vocabulary": 3, "grammar": 3, "reading": 2, "listening": 2}, 90, [{**q, "id": q["id"].replace("n3", "n2"), "level": "N2"} for q in N3_QUESTIONS]),
        ("exam-n1-1", "JLPT N1 Mock Exam #1", "N1", "Expert-level N1 exam", 170, {"vocabulary": 4, "grammar": 4, "reading": 3, "listening": 3}, 100, [{**q, "id": q["id"].replace("n3", "n1"), "level": "N1"} for q in N3_QUESTIONS]),
    ]

    for slug, title, level, desc, duration, sections, passing, questions in exams_data:
        exam = Exam(slug=slug, title=title, level=level, description=desc, duration=duration, sections=json.dumps(sections), passing_score=passing)
        db.session.add(exam)
        db.session.flush()
        for i, q in enumerate(questions):
            db.session.add(Question(
                slug=q["id"], exam_id=exam.id, section=q["section"], type=q["type"], level=q["level"],
                question=q["question"], question_ja=q.get("question_ja", ""), options=json.dumps(q["options"]),
                correct_answer=q["correct_answer"], explanation=q["explanation"], passage=q.get("passage", ""),
                points=q.get("points", 1), sort_order=i,
            ))

    achievements = [
        ("a1", "First Steps", "Complete your first lesson", "🎯", 1),
        ("a2", "Week Warrior", "Maintain a 7-day streak", "🔥", 7),
        ("a3", "Exam Master", "Pass 5 mock exams", "📋", 5),
        ("a4", "Kanji King", "Learn 100 kanji", "漢", 100),
    ]
    for slug, title, desc, icon, max_p in achievements:
        ach = Achievement(slug=slug, title=title, description=desc, icon=icon, max_progress=max_p)
        db.session.add(ach)
        db.session.flush()
        progress = max_p if slug in ("a1", "a2") else (3 if slug == "a3" else 67)
        unlocked = slug in ("a1", "a2")
        from datetime import datetime, timezone
        db.session.add(UserAchievement(
            user_id=demo.id, achievement_id=ach.id, progress=progress,
            unlocked_at=datetime.now(timezone.utc) if unlocked else None,
        ))

    db.session.commit()
