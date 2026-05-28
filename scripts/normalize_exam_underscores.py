#!/usr/bin/env python3
"""Add ＿target＿ markers to exam markdown stems (2016+), JLPT_N1_2021_07 style."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.exam_stem_format import format_stem  # noqa: E402

Q_HEADER = re.compile(r"^(#### (Q|L)(\d+)\b.*)$", re.M)
STEM_RE = re.compile(r"^\*\*(.+?)\*\*\s*$", re.M)
META_SECTIONS = re.compile(
    r"```yaml\n(.*?)```",
    re.DOTALL,
)
SECTION_LINE = re.compile(
    r"^\s+-\s+id:\s*.+\n\s+label:\s*(.+)\n\s+questions:\s*(.+)$",
    re.M,
)
PROBLEM_HEADER = re.compile(r"^### [^\n]*問題(\d+)[｜|]([^\n]+)", re.M)


def _ids_in_range(q_range: str) -> list[str]:
    q_range = str(q_range).strip()
    if not q_range or "-" not in q_range:
        return [q_range.upper().replace("Q", "Q").replace("L", "L")] if q_range else []
    start, end = q_range.split("-", 1)
    start, end = start.strip(), end.strip()
    prefix = "L" if start.upper().startswith("L") else "Q"
    s_num = int(re.sub(r"\D", "", start))
    e_num = int(re.sub(r"\D", "", end))
    return [f"{prefix}{i}" for i in range(s_num, e_num + 1)]


def _parse_meta_sections(text: str) -> list[dict]:
    m = META_SECTIONS.search(text)
    if not m:
        return []
    block = m.group(1)
    sections = []
    for sm in SECTION_LINE.finditer(block):
        sections.append({"label": sm.group(1).strip(), "questions": sm.group(2).strip()})
    return sections


def _parse_problem_titles(text: str) -> list[tuple[int, int, str]]:
    """Ranges of Q numbers → problem section title (問題N｜label)."""
    blocks = []
    for m in PROBLEM_HEADER.finditer(text):
        num = int(m.group(1))
        title = m.group(2).strip()
        blocks.append((m.start(), num, title))
    ranges: list[tuple[int, int, str]] = []
    for i, (pos, pnum, title) in enumerate(blocks):
        end = blocks[i + 1][0] if i + 1 < len(blocks) else len(text)
        chunk = text[pos:end]
        qids = [int(x.group(1)) for x in re.finditer(r"^#### Q(\d+)", chunk, re.M)]
        if qids:
            ranges.append((min(qids), max(qids), title))
    return ranges


def _label_for_q(
    qid: str,
    sections: list[dict],
    problem_ranges: list[tuple[int, int, str]],
) -> tuple[str, str]:
    display = qid.upper().replace("#### ", "").strip()
    if display.startswith("L"):
        for sec in sections:
            ids = _ids_in_range(sec["questions"])
            if display in ids:
                return sec["label"], sec["label"]
        return "聴解", ""
    qn = int(re.sub(r"\D", "", display) or 0)
    for sec in sections:
        ids = _ids_in_range(sec["questions"])
        if display in ids:
            prob = ""
            for lo, hi, title in problem_ranges:
                if lo <= qn <= hi:
                    prob = title
                    break
            return sec["label"], prob
    for lo, hi, title in problem_ranges:
        if lo <= qn <= hi:
            return title, title
    return "", ""


def normalize_file(path: Path, min_year: int = 2016) -> tuple[int, int]:
    year = int(path.stem.split("_")[2])
    if year < min_year:
        return 0, 0

    text = path.read_text(encoding="utf-8")
    sections = _parse_meta_sections(text)
    problem_ranges = _parse_problem_titles(text)
    changed = 0
    total = 0

    def replace_stem(m: re.Match) -> str:
        nonlocal changed, total
        stem = m.group(1).strip()
        total += 1
        # find preceding #### Q/L
        before = text[: m.start()]
        qm = list(Q_HEADER.finditer(before))
        qid = qm[-1].group(0) if qm else "Q0"
        label, prob = _label_for_q(qid, sections, problem_ranges)
        new = format_stem(stem, label, prob)
        if new != stem:
            changed += 1
        return f"**{new}**"

    new_text = STEM_RE.sub(replace_stem, text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
    return changed, total


def main() -> None:
    min_year = 2016
    if len(sys.argv) > 1:
        min_year = int(sys.argv[1])

    total_changed = 0
    total_stems = 0
    for level_dir in sorted((ROOT / "data" / "exam").iterdir()):
        if not level_dir.is_dir() or level_dir.name.startswith("_"):
            continue
        for path in sorted(level_dir.glob("JLPT_*.md")):
            c, t = normalize_file(path, min_year)
            if c:
                print(f"  {path.name}: {c}/{t} stems updated")
            total_changed += c
            total_stems += t

    print(f"\nDone: {total_changed} stems updated ({total_stems} checked, year>={min_year})")


if __name__ == "__main__":
    main()
