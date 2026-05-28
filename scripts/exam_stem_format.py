"""Format JLPT question stems with fullwidth ＿ markers (JLPT_N1_2021_07 style)."""

from __future__ import annotations

import re

FW = "＿"


def _wrap(word: str) -> str:
    w = word.strip()
    if not w or FW in w:
        return word
    return f"{FW}{w}{FW}"


def _mark_spaced_kanji(stem: str, *, limit: int = 1) -> str:
    """JLPT OCR style: space before target word → ＿…＿ (kanji + okurigana)."""

    def repl(m: re.Match) -> str:
        return " " + _wrap(m.group(1))

    return re.sub(
        r" ([\u4e00-\u9fff々〆ヵヶー][\u3040-\u309f\u30a0-\u30ff]{0,12})",
        repl,
        stem,
        count=limit,
    )


def _mark_first_kanji(stem: str) -> str:
    return re.sub(
        r"^([\u4e00-\u9fff々〆ヵヶー]{1,14})",
        lambda m: _wrap(m.group(1)),
        stem,
        count=1,
    )


def _has_fullwidth_marks(stem: str) -> bool:
    return stem.count(FW) >= 2


def _ascii_to_fullwidth_marks(stem: str) -> str:
    return re.sub(r"_([^_]+)_", lambda m: _wrap(m.group(1)), stem)


def _normalize_blank_parens(stem: str) -> str:
    stem = re.sub(r"（\s*）", "（　）", stem)
    stem = re.sub(r"\(\s*\)", "（　）", stem)
    return stem


def format_stem(
    stem: str,
    section_label: str = "",
    problem_title: str = "",
) -> str:
    """Return stem with ＿…＿ (or （　）) matching official JLPT layout."""
    stem = re.sub(r"\s+", " ", stem.strip())
    if not stem or "PDF参照" in stem or re.match(r"^[_（(]?Q\d+", stem):
        return stem

    stem = re.sub(
        r"＿([^＿]{1,3})＿([\u3040-\u309f\u30a0-\u30ff]{1,12})",
        lambda m: _wrap(m.group(1) + m.group(2)),
        stem,
    )
    if _has_fullwidth_marks(stem):
        return stem

    stem = _ascii_to_fullwidth_marks(stem)
    if _has_fullwidth_marks(stem):
        return stem

    ctx = f"{section_label} {problem_title}"

    if "読み方" in ctx or ("文字" in ctx and "書き" not in ctx and "読み" in ctx):
        out = _mark_spaced_kanji(stem)
        return out if _has_fullwidth_marks(out) else _mark_first_kanji(stem)

    if "書き" in ctx or ("漢字" in ctx and "読み" not in ctx):
        stem = _normalize_blank_parens(stem)
        out = _mark_spaced_kanji(stem)
        if _has_fullwidth_marks(out):
            return out
        # hiragana slot: もう少しこい鉛筆 → wrap short kana run after space
        m = re.search(r" ([\u3040-\u309f\u30a0-\u30ff]{1,8})(?=[\u4e00-\u9fff])", stem)
        if m:
            return stem[: m.start(1)] + " " + _wrap(m.group(1)) + stem[m.end(1) :]
        return out

    if "言い換え" in ctx or "類義" in ctx or ("意味" in ctx and "近い" in ctx):
        out = _mark_spaced_kanji(stem)
        if _has_fullwidth_marks(out):
            return out
        m = re.search(r"([\u4e00-\u9fff々]{2,8})", stem)
        if m:
            return stem[: m.start()] + _wrap(m.group(1)) + stem[m.end() :]
        return stem

    if "用法" in ctx:
        if stem.startswith("「") and stem.endswith("」"):
            return stem
        return f"「{stem}」"

    if "並べ替え" in ctx or "★" in stem:
        return _normalize_blank_parens(stem)

    if "（" in stem or "(" in stem:
        return _normalize_blank_parens(stem)

    out = _mark_spaced_kanji(stem)
    return out if _has_fullwidth_marks(out) else stem
