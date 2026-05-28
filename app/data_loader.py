"""Load JLPT content from data/grammar and data/kanji files."""

from __future__ import annotations

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
JLPT_LEVELS = ["N5", "N4", "N3", "N2", "N1"]

KANJI_MEANINGS: dict[str, str] = {
    "日": "ngày, mặt trời",
    "人": "người",
    "水": "nước",
    "火": "lửa",
    "木": "cây, gỗ",
    "金": "vàng, tiền",
    "土": "đất",
    "学": "học",
    "食": "ăn, thức ăn",
    "見": "nhìn, xem",
    "語": "ngôn ngữ, từ",
    "試": "thử, thi",
    "運": "vận, vận chuyển",
    "映": "chiếu, phản chiếu",
    "音": "âm thanh",
    "料": "phí, liệu",
    "世": "đời, thế giới",
    "界": "giới, ranh giới",
    "発": "phát, bắn",
    "表": "biểu, bề mặt",
    "影": "bóng",
    "響": "vang, ảnh hưởng",
    "努": "nỗ lực",
    "力": "sức, lực",
    "環": "vòng, môi trường",
    "境": "cảnh, ranh giới",
    "政": "chính trị",
    "治": "trị, cai trị",
    "経": "kinh, trải qua",
    "済": "xong, cứu trợ",
    "議": "nghị, bàn luận",
    "論": "luận, lý thuyết",
    "構": "cấu trúc",
    "造": "tạo, chế tạo",
    "権": "quyền",
    "利": "lợi, lợi ích",
    "責": "trách nhiệm",
    "任": "nhiệm, giao phó",
    "策": "sách lược",
    "略": "lược, chiến lược",
    "憲": "hiến pháp",
    "法": "pháp luật",
    "倫": "luân lý",
    "理": "lý, lý do",
    "覇": "bá, thống trị",
    "妥": "thỏa, ổn",
    "協": "hiệp, hợp tác",
    "賛": "tán thành",
    "否": "phủ nhận",
}

KANJI_STROKES: dict[str, int] = {
    "日": 4, "人": 2, "水": 4, "火": 4, "木": 4, "金": 8, "土": 3, "学": 8, "食": 9, "見": 7,
    "語": 14, "試": 13, "運": 12, "映": 9, "音": 9, "料": 10, "世": 5, "界": 9, "発": 9, "表": 8,
    "影": 15, "響": 20, "努": 7, "力": 2, "環": 17, "境": 14, "政": 9, "治": 8, "経": 11, "済": 11,
    "議": 20, "論": 15, "構": 14, "造": 10, "権": 15, "利": 7, "責": 11, "任": 6, "策": 12, "略": 11,
    "憲": 16, "法": 8, "倫": 10, "理": 11, "覇": 19, "妥": 7, "協": 8, "賛": 15, "否": 7,
}


def load_grammar_from_json(level: str) -> list[dict]:
    path = DATA_DIR / "grammar" / f"{level.lower()}.json"
    if not path.exists():
        return []
    items = json.loads(path.read_text(encoding="utf-8"))
    result = []
    for item in items:
        num = item.get("num", len(result) + 1)
        result.append({
            "slug": f"g-{level.lower()}-{num}",
            "pattern": item["japanese"],
            "meaning": item.get("meaning_en", ""),
            "level": level,
            "explanation": item.get("romaji", ""),
            "usage": item["japanese"],
            "examples": [],
        })
    return result


def parse_grammar_md(level: str) -> list[dict]:
    path = DATA_DIR / "grammar" / f"{level.lower()}.md"
    if not path.exists():
        return load_grammar_from_json(level)

    text = path.read_text(encoding="utf-8")
    sections = re.split(r"\n---\n", text)
    result = []

    for section in sections:
        header = re.search(r"^## (\d+)\. (.+)$", section, re.MULTILINE)
        if not header:
            continue
        num = int(header.group(1))
        fields = {}
        for key, pattern in [
            ("pattern", r"\*\*Mẫu \(JP\):\*\* (.+)"),
            ("romaji", r"\*\*Romaji:\*\* (.+)"),
            ("meaning", r"\*\*Nghĩa:\*\* (.+)"),
            ("meaning_en", r"\*\*Nghĩa \(EN\):\*\* (.+)"),
            ("explanation", r"\*\*Cách dùng:\*\* (.+)"),
        ]:
            match = re.search(pattern, section)
            if match:
                fields[key] = match.group(1).strip()

        examples = []
        for ja, vi in re.findall(
            r"^\d+\. (.+?)  \s*\n\s*→ (.+)$", section, re.MULTILINE
        ):
            examples.append({"japanese": ja.strip(), "english": vi.strip()})

        result.append({
            "slug": f"g-{level.lower()}-{num}",
            "pattern": fields.get("pattern", header.group(2)),
            "meaning": fields.get("meaning") or fields.get("meaning_en", ""),
            "level": level,
            "explanation": fields.get("explanation", fields.get("romaji", "")),
            "usage": fields.get("pattern", ""),
            "examples": examples,
        })

    return result if result else load_grammar_from_json(level)


def parse_kanji_md(level: str) -> list[dict]:
    path = DATA_DIR / "kanji" / f"{level.lower()}.md"
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    sections = re.split(r"\n---\n", text)
    result = []

    for section in sections:
        header = re.search(r"^## (\d+)\. (.+)$", section, re.MULTILINE)
        if not header:
            continue
        num = int(header.group(1))
        character = re.sub(r"（.+?）", "", header.group(2)).strip()

        meaning_match = re.search(r"\*\*Nghĩa:\*\* (.+)", section)
        strokes_match = re.search(r"\*\*Số nét:\*\* (\d+)", section)
        on_match = re.search(r"\*\*Cách đọc âm On:\*\* (.+)", section)
        kun_match = re.search(r"\*\*Cách đọc âm Kun:\*\* (.+)", section)
        onyomi = [p.strip() for p in re.split(r"[、,]", on_match.group(1))] if on_match else []
        kunyomi = [p.strip() for p in re.split(r"[、,]", kun_match.group(1))] if kun_match else []
        if on_match and on_match.group(1).strip() == "—":
            onyomi = []
        if kun_match and kun_match.group(1).strip() == "—":
            kunyomi = []

        examples = []
        for row in re.finditer(
            r"^\| \d+ \| (.+?) \| (.+?) \| (.+?) \|$", section, re.MULTILINE
        ):
            examples.append({
                "word": row.group(1).strip(),
                "reading": row.group(2).strip(),
                "meaning": row.group(3).strip(),
            })

        meaning = (
            meaning_match.group(1).strip()
            if meaning_match
            else KANJI_MEANINGS.get(character, character)
        )
        strokes = (
            int(strokes_match.group(1))
            if strokes_match
            else KANJI_STROKES.get(character, 10)
        )
        result.append({
            "slug": f"k-{level.lower()}-{num}",
            "character": character,
            "meaning": meaning,
            "onyomi": onyomi,
            "kunyomi": kunyomi,
            "strokes": strokes,
            "level": level,
            "examples": examples,
        })

    return result


def vocabulary_from_kanji(kanji_items: list[dict]) -> list[dict]:
    """Build vocabulary flashcards from kanji compound words."""
    vocab = []
    seen: set[str] = set()
    for k in kanji_items:
        for ex in k["examples"]:
            word = ex["word"]
            if word in seen:
                continue
            seen.add(word)
            slug = f"v-{k['level'].lower()}-{word}"
            vocab.append({
                "slug": slug,
                "word": word,
                "reading": ex["reading"],
                "meaning": ex["meaning"],
                "level": k["level"],
                "example": f"{word}（{ex['reading']}）— {ex['meaning']}",
                "example_meaning": ex["meaning"],
                "srs_level": 0,
            })
    return vocab


def load_level_content(level: str) -> dict:
    grammar = parse_grammar_md(level)
    kanji = parse_kanji_md(level)
    vocabulary = vocabulary_from_kanji(kanji)
    return {"grammar": grammar, "kanji": kanji, "vocabulary": vocabulary}


def load_all_content() -> dict:
    all_grammar, all_kanji, all_vocab = [], [], []
    counts = {}
    for level in JLPT_LEVELS:
        data = load_level_content(level)
        all_grammar.extend(data["grammar"])
        all_kanji.extend(data["kanji"])
        all_vocab.extend(data["vocabulary"])
        counts[level] = {
            "grammar": len(data["grammar"]),
            "kanji": len(data["kanji"]),
            "vocabulary": len(data["vocabulary"]),
        }
    return {
        "grammar": all_grammar,
        "kanji": all_kanji,
        "vocabulary": all_vocab,
        "counts": counts,
    }


def import_to_database(force: bool = False) -> dict:
    """Import grammar, kanji, and vocabulary from data files into the DB."""
    import json as json_mod

    from app.extensions import db
    from app.models import Grammar, Kanji, Vocabulary

    if not force and Grammar.query.first():
        return {"skipped": True}

    if force:
        Vocabulary.query.delete()
        Kanji.query.delete()
        Grammar.query.delete()
        db.session.commit()

    content = load_all_content()

    for g in content["grammar"]:
        db.session.add(Grammar(
            slug=g["slug"],
            pattern=g["pattern"],
            meaning=g["meaning"],
            level=g["level"],
            explanation=g["explanation"],
            usage=g["usage"],
            examples=json_mod.dumps(g["examples"], ensure_ascii=False),
        ))

    for k in content["kanji"]:
        db.session.add(Kanji(
            slug=k["slug"],
            character=k["character"],
            meaning=k["meaning"],
            onyomi=json_mod.dumps(k["onyomi"], ensure_ascii=False),
            kunyomi=json_mod.dumps(k["kunyomi"], ensure_ascii=False),
            strokes=k["strokes"],
            level=k["level"],
            examples=json_mod.dumps(k["examples"], ensure_ascii=False),
        ))

    for v in content["vocabulary"]:
        db.session.add(Vocabulary(
            slug=v["slug"],
            word=v["word"],
            reading=v["reading"],
            meaning=v["meaning"],
            level=v["level"],
            example=v["example"],
            example_meaning=v["example_meaning"],
            srs_level=v["srs_level"],
        ))

    db.session.commit()
    return {"skipped": False, "counts": content["counts"]}
