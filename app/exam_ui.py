"""Helpers for JLPT exam take UI."""

from __future__ import annotations

import re

from app.services import _ids_in_range


def question_number(display_id: str) -> str:
    num = int(re.sub(r"\D", "", display_id) or 0)
    return f"{num:02d}"


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _wrap_blank(inner: str) -> str:
    return f'<span class="exam-blank">{inner}</span>'


def _is_reading_section(section_label: str, instruction: str) -> bool:
    blob = f"{section_label} {instruction}"
    return any(k in blob for k in ("読み方", "読み", "文字（読み"))


def highlight_blanks(
    text: str,
    section_label: str = "",
    instruction: str = "",
) -> str:
    """Highlight target word(s): ＿…＿, _…_, or spaced kanji (JLPT 読み方)."""
    if not text:
        return ""
    escaped = _escape_html(text.strip())

    if "＿" in text:
        escaped = re.sub(
            r"＿([^＿]+)＿",
            lambda m: _wrap_blank(m.group(1)),
            escaped,
        )
    if "_" in text:
        escaped = re.sub(
            r"_([^_]+)_",
            lambda m: _wrap_blank(m.group(1)),
            escaped,
        )
    if '<span class="exam-blank">' in escaped:
        return escaped

    if _is_reading_section(section_label, instruction):
        # OCR/PDF imports: space before the kanji whose reading is tested
        escaped, n = re.subn(
            r" ([\u4e00-\u9fff々〆ヵヶー]{1,10})",
            lambda m: " " + _wrap_blank(m.group(1)),
            escaped,
        )
        if n == 0:
            escaped = re.sub(
                r"^([\u4e00-\u9fff々〆ヵヶー]{1,10})",
                lambda m: _wrap_blank(m.group(1)),
                escaped,
                count=1,
            )

    # 漢字（書き）: underscore blanks in stem, or single kanji slot
    if "書き" in section_label or "漢字" in section_label:
        if "＿" not in text and "_" not in text:
            escaped = re.sub(
                r" ([\u4e00-\u9fff々]{1,6})(?=[\u4e00-\u9fffのとはがをにで、。、]|)",
                lambda m: " " + _wrap_blank(m.group(1)),
                escaped,
                count=1,
            )

    return escaped


def build_problem_groups(exam: dict, phase_key: str) -> list[dict]:
    all_qs = exam["questions"]
    section_list = exam.get("sections", {}).get("section_list", [])
    groups: list[dict] = []

    if section_list:
        n = 0
        for sec in section_list:
            ids = set(_ids_in_range(str(sec.get("questions", ""))))
            items = []
            for i, q in enumerate(all_qs):
                if q.get("phase") != phase_key:
                    continue
                if q["display_id"] in ids:
                    items.append({"q": q, "idx": i})
            if not items:
                continue
            n += 1
            groups.append(
                {
                    "number": n,
                    "title": f"問題{n}",
                    "label": sec.get("label", ""),
                    "instruction": sec.get("instruction", ""),
                    "questions": items,
                }
            )

    if not groups:
        items = [
            {"q": q, "idx": i}
            for i, q in enumerate(all_qs)
            if q.get("phase") == phase_key
        ]
        if items:
            groups.append(
                {
                    "number": 1,
                    "title": "問題1",
                    "label": "",
                    "instruction": "",
                    "questions": items,
                }
            )

    return groups


def current_problem_group(groups: list[dict], question_id: str) -> dict | None:
    for group in groups:
        if any(item["q"]["id"] == question_id for item in group["questions"]):
            return group
    return groups[0] if groups else None
