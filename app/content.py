"""Static content for landing page and helpers."""

LEVEL_COLORS = {"N5": "emerald", "N4": "teal", "N3": "blue", "N2": "indigo", "N1": "purple"}

JLPT_LEVELS = [
    {"level": "N5", "name": "Beginner", "words": 800, "description": "Basic Japanese for everyday situations"},
    {"level": "N4", "name": "Elementary", "words": 1500, "description": "Understanding basic Japanese"},
    {"level": "N3", "name": "Intermediate", "words": 3750, "description": "Everyday Japanese at a basic level"},
    {"level": "N2", "name": "Upper Intermediate", "words": 6000, "description": "Japanese in everyday situations"},
    {"level": "N1", "name": "Advanced", "words": 10000, "description": "Japanese in a variety of circumstances"},
]

PRICING_PLANS = [
    {"name": "Free", "price": 0, "period": "forever", "features": ["N5 & N4 content", "5 mock exams/month", "Basic flashcards", "Daily streak tracking"], "cta": "Get Started", "popular": False},
    {"name": "Pro", "price": 9.99, "period": "month", "features": ["All JLPT levels", "Unlimited mock exams", "AI tutor access", "SRS vocabulary", "Detailed analytics", "Certificate generation"], "cta": "Start Free Trial", "popular": True},
    {"name": "Premium", "price": 19.99, "period": "month", "features": ["Everything in Pro", "AI speaking practice", "Personalized study plans", "Priority support", "Offline mode", "Group leaderboard"], "cta": "Go Premium", "popular": False},
]

TESTIMONIALS = [
    {"name": "Sarah Chen", "level": "N2", "text": "Passed N2 on my first attempt! The mock exams were incredibly realistic.", "avatar": "SC", "rating": 5},
    {"name": "Michael Park", "level": "N3", "text": "The spaced repetition system helped me memorize 2000+ vocabulary words.", "avatar": "MP", "rating": 5},
    {"name": "Emily Rodriguez", "level": "N1", "text": "AI tutor explained complex grammar points better than any textbook.", "avatar": "ER", "rating": 5},
]

FEATURES = [
    {"title": "Mock Exams", "description": "Full JLPT simulations with real exam timing and scoring", "icon": "clipboard-check"},
    {"title": "Smart SRS", "description": "Spaced repetition that adapts to your learning pace", "icon": "brain"},
    {"title": "AI Tutor", "description": "24/7 Japanese tutor powered by advanced AI", "icon": "bot"},
    {"title": "Analytics", "description": "Detailed weakness analysis and progress tracking", "icon": "bar-chart"},
    {"title": "Gamification", "description": "XP, streaks, badges, and leaderboards", "icon": "trophy"},
    {"title": "All Skills", "description": "Vocabulary, kanji, grammar, and listening", "icon": "book-open"},
]

DAILY_MISSIONS = [
    {"id": "m1", "title": "Study 20 vocabulary words", "xp_reward": 50, "progress": 14, "target": 20, "completed": False},
    {"id": "m2", "title": "Complete a grammar lesson", "xp_reward": 75, "progress": 1, "target": 1, "completed": True},
    {"id": "m3", "title": "Practice listening 10 min", "xp_reward": 60, "progress": 6, "target": 10, "completed": False},
]

WEEKLY_PROGRESS = [
    {"day": "Mon", "xp": 120}, {"day": "Tue", "xp": 85}, {"day": "Wed", "xp": 200},
    {"day": "Thu", "xp": 150}, {"day": "Fri", "xp": 90}, {"day": "Sat", "xp": 250}, {"day": "Sun", "xp": 180},
]

AI_RESPONSES = {
    "default": "That's a great question! In Japanese, grammar patterns often depend on context and formality level.",
    "te-form": "The て-form is used for:\n1. Connecting actions\n2. Requests (待ってください)\n3. Ongoing actions (読んでいる)",
    "particles": "Key particles:\n• は — topic\n• が — subject\n• を — object\n• に — direction/time\n• で — location/means",
}
