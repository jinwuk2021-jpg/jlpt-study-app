"""Parse JLPT exam markdown files under data/exam/."""

from __future__ import annotations

import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "exam"

# Official JLPT section timings (minutes)
JLPT_PHASES = {
    "N1": {"written": 110, "listening": 60, "total": 170, "pass": 100},
    "N2": {"written": 105, "listening": 50, "total": 155, "pass": 90},
    "N3": {"written": 95, "listening": 40, "total": 140, "pass": 95},
    "N4": {"written": 80, "listening": 35, "total": 125, "pass": 90},
    "N5": {"written": 75, "listening": 30, "total": 105, "pass": 80},
}

Q_HEADER = re.compile(r"^#### (Q|L)(\d+)\b", re.MULTILINE)
OPTION_RE = re.compile(r"^- \[ \] (\d+)\.\s*(.+?)(?:\s*✅)?\s*$", re.MULTILINE)
ANSWER_RE = re.compile(r"`answer:\s*(\d+)`")
STEM_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
PASSAGE_HEADER = re.compile(r"^#### 【文章", re.MULTILINE)
MEMO_ANSWERS_RE = re.compile(
    r"\*\(参考答案:\s*([^)]+)\)\*"
)


def _slug_from_path(path: Path) -> str:
    # JLPT_N1_2017_07.md -> n1-2017-07
    name = path.stem  # JLPT_N1_2017_07
    m = re.match(r"JLPT_(N\d)_(.+)", name, re.I)
    if m:
        return f"{m.group(1).lower()}-{m.group(2).replace('_', '-')}"
    return name.lower()


def _level_from_path(path: Path) -> str:
    m = re.search(r"N[1-5]", path.stem, re.I)
    return m.group(0).upper() if m else "N1"


def _parse_meta(text: str) -> dict:
    m = re.search(r"```yaml\n(.*?)```", text, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    meta: dict = {}
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("exam:"):
            meta["exam"] = line.split(":", 1)[1].strip()
        elif line.startswith("date:"):
            meta["date"] = line.split(":", 1)[1].strip()
        elif line.startswith("audio:"):
            meta["audio"] = line.split(":", 1)[1].strip()
        elif line.startswith("source_pdf:"):
            meta["source_pdf"] = line.split(":", 1)[1].strip()
        elif line.startswith("- id:"):
            if "sections" not in meta:
                meta["sections"] = []
            meta["sections"].append({"id": line.split(":", 1)[1].strip()})
        elif line.startswith("label:") and meta.get("sections"):
            meta["sections"][-1]["label"] = line.split(":", 1)[1].strip()
        elif line.startswith("questions:") and meta.get("sections"):
            meta["sections"][-1]["questions"] = line.split(":", 1)[1].strip()
    return meta


def _question_range_to_ids(q_range: str) -> list[str]:
    q_range = str(q_range).strip()
    if "-" not in q_range:
        return [q_range]
    start, end = q_range.split("-", 1)
    start, end = start.strip(), end.strip()
    prefix = "L" if start.upper().startswith("L") else "Q"
    s_num = int(re.sub(r"\D", "", start))
    e_num = int(re.sub(r"\D", "", end))
    return [f"{prefix}{i}" for i in range(s_num, e_num + 1)]


def _enrich_sections_with_instructions(text: str, sections: list) -> list:
    """Attach blockquote instructions from ### 問題N headers to YAML sections (in order)."""
    if not sections:
        return sections
    blocks = list(
        re.finditer(
            r"^### [^\n]*問題(\d+)[｜|][^\n]*\n(.*?)(?=\n### |\n## [^#]|\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
    )
    enriched = []
    for i, sec in enumerate(sections):
        row = dict(sec)
        if i < len(blocks):
            body = blocks[i].group(2)
            lines = [
                ln[1:].strip()
                for ln in body.splitlines()
                if ln.startswith(">") and not ln.startswith(">>")
            ]
            row["instruction"] = " ".join(lines).strip()
        enriched.append(row)
    return enriched


def _build_section_map(meta: dict) -> dict[str, dict]:
    """Map Q1 / L3 -> {id, label, group}."""
    mapping: dict[str, dict] = {}
    for sec in meta.get("sections") or []:
        label = sec.get("label", sec.get("id", ""))
        sec_id = sec.get("id", "")
        group = "listening" if "聴解" in label or str(sec_id).startswith("聴解") else "written"
        if "読解" in label:
            group = "reading"
        elif "語彙" in label or "文法" in label:
            group = "language"
        for qid in _question_range_to_ids(sec.get("questions", "")):
            mapping[qid] = {"section": sec_id, "label": label, "group": group}
    return mapping


def _extract_passages(text: str) -> dict[str, str]:
    """Passages keyed by question id they apply to (next questions until new passage)."""
    passages: dict[str, str] = {}
    parts = PASSAGE_HEADER.split(text)
    if len(parts) <= 1:
        return passages

    current_passage = ""
    for i, part in enumerate(parts[1:], 1):
        block = part
        lines = []
        for line in block.splitlines():
            if line.startswith("#### Q") or line.startswith("#### L"):
                break
            if line.startswith("> "):
                lines.append(line[2:].strip())
            elif line.startswith(">") and not line.startswith(">>"):
                lines.append(line[1:].strip())
        passage_text = "\n\n".join(lines).strip()
        if not passage_text:
            continue
        # First question after this passage header
        qm = re.search(r"^#### (Q|L)(\d+)\b", block, re.MULTILINE)
        if qm:
            current_passage = passage_text
            qid = f"{qm.group(1)}{qm.group(2)}"
            passages[qid] = passage_text
    return passages


def _passage_for_question(qid: str, passage_starts: dict[str, str]) -> str:
    if qid in passage_starts:
        return passage_starts[qid]
    # inherit from nearest previous passage start
    num = int(re.sub(r"\D", "", qid))
    prefix = "L" if qid.startswith("L") else "Q"
    best = ""
    for key, text in passage_starts.items():
        k_num = int(re.sub(r"\D", "", key))
        if key.startswith(prefix) and k_num <= num:
            if k_num == num or k_num < num:
                if not best or k_num > int(re.sub(r"\D", "", best.split("|")[0])):
                    best = f"{k_num}|{text}"
    if best:
        return best.split("|", 1)[1]
    return ""


def _parse_memo_answers(text: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for m in MEMO_ANSWERS_RE.finditer(text):
        chunk = m.group(1)
        for part in chunk.split(","):
            part = part.strip()
            mm = re.match(r"(L?\d+)\s*=\s*(\d+)", part)
            if mm:
                qid = mm.group(1)
                if not qid.startswith(("Q", "L")):
                    qid = "L" + qid
                result[qid] = int(mm.group(2)) - 1
    return result


def _section_type(qid: str, group: str) -> str:
    if qid.startswith("L"):
        return "listening"
    if group == "reading":
        return "reading_comprehension"
    if "文法" in group or group == "language":
        return "grammar" if qid.startswith("Q") and int(re.sub(r"\D", "", qid)) >= 26 else "vocabulary"
    return "multiple_choice"


def parse_exam_file(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    meta = _parse_meta(text)
    level = _level_from_path(path)
    if meta.get("exam"):
        mm = re.search(r"N[1-5]", str(meta["exam"]), re.I)
        if mm:
            level = mm.group(0).upper()

    section_map = _build_section_map(meta)
    passage_starts = _extract_passages(text)
    memo_answers = _parse_memo_answers(text)

    # Running passage for reading sections
    active_passage = ""
    questions: list[dict] = []

    matches = list(Q_HEADER.finditer(text))
    for idx, match in enumerate(matches):
        qid = f"{match.group(1)}{match.group(2)}"
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end]
        q_num = int(match.group(2))

        opts = []
        for om in OPTION_RE.finditer(body):
            opts.append(om.group(2).strip())

        ans_m = ANSWER_RE.search(body)
        correct = None
        if ans_m:
            correct = int(ans_m.group(1)) - 1
        elif qid in memo_answers:
            correct = memo_answers[qid]

        if not opts and correct is not None:
            n_opts = 3 if qid.startswith("L") and 19 <= q_num <= 31 else 4
            opts = [str(j + 1) for j in range(n_opts)]

        if correct is None or not opts:
            continue

        audio_only = not OPTION_RE.search(body) and qid.startswith("L")

        stem_m = STEM_RE.search(body)
        stem = stem_m.group(1).strip() if stem_m else f"Question {qid}"
        stem = re.sub(r"\s+", " ", stem)

        sec_info = section_map.get(qid, {})
        group = sec_info.get("group", "listening" if qid.startswith("L") else "written")

        if qid in passage_starts:
            active_passage = passage_starts[qid]
        passage = active_passage if group in ("reading", "written") and not qid.startswith("L") else ""
        if qid.startswith("L"):
            passage = ""

        questions.append({
            "id": qid.lower(),
            "section": sec_info.get("section", "listening" if qid.startswith("L") else "vocabulary"),
            "section_label": sec_info.get("label", ""),
            "type": _section_type(qid, group),
            "level": level,
            "question": stem,
            "question_ja": stem if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", stem) else "",
            "options": opts,
            "correct_answer": correct,
            "explanation": "",
            "passage": passage,
            "points": 1,
            "display_id": qid,
            "phase": "listening" if qid.startswith("L") else "written",
            "audio_only": audio_only,
        })

    existing_ids = {q["display_id"] for q in questions}
    for qid, correct in memo_answers.items():
        if qid in existing_ids:
            continue
        num = int(re.sub(r"\D", "", qid))
        n_opts = 3 if qid.startswith("L") and 19 <= num <= 31 else 4
        sec_info = section_map.get(qid, {})
        group = sec_info.get("group", "listening")
        questions.append({
            "id": qid.lower(),
            "section": sec_info.get("section", "聴解"),
            "section_label": sec_info.get("label", "聴解"),
            "type": "listening",
            "level": level,
            "question": f"（音声を聞いて選択）{qid}",
            "question_ja": f"問題用紙に選択肢は印刷されていません。{qid}",
            "options": [str(j + 1) for j in range(n_opts)],
            "correct_answer": correct,
            "explanation": "",
            "passage": "",
            "points": 1,
            "display_id": qid,
            "phase": "listening",
            "audio_only": True,
        })

    # L32/L33: answer without options in some papers
    for q in questions:
        if q["display_id"] in ("L32", "L33") and len(q["options"]) < 2:
            q["options"] = ["1", "2", "3", "4"]
            q["audio_only"] = True
            q["question_ja"] = "問題用紙に何も印刷されていません。音声を聞いて選択。"

    def _sort_key(q: dict) -> tuple:
        prefix = 1 if q["display_id"].startswith("L") else 0
        num = int(re.sub(r"\D", "", q["display_id"]))
        return (prefix, num)

    questions.sort(key=_sort_key)

    if not questions:
        return None

    date = meta.get("date", "")
    timing = JLPT_PHASES.get(level, JLPT_PHASES["N1"])
    title_date = path.stem
    if date:
        parts = date.split("-")
        if len(parts) >= 2:
            title_date = f"{parts[0]}年{int(parts[1])}月"

    is_listening_only = all(q["display_id"].startswith("L") for q in questions)
    duration = timing["listening"] if is_listening_only else timing["total"]

    phases = [
        {
            "key": "written",
            "label": "言語知識（文字・語彙・文法）・読解",
            "label_vi": "Từ vựng · Ngữ pháp · Đọc hiểu",
            "minutes": timing["written"],
        },
        {
            "key": "listening",
            "label": "聴解",
            "label_vi": "Nghe hiểu",
            "minutes": timing["listening"],
        },
    ]
    if is_listening_only:
        phases = [phases[1]]

    sections_meta = _enrich_sections_with_instructions(text, meta.get("sections", []))

    return {
        "slug": _slug_from_path(path),
        "title": f"JLPT {level} — {title_date} 真題" + ("（聴解）" if is_listening_only else ""),
        "level": level,
        "description": f"Đề thi thật {level} ({date or 'past paper'}) — thời gian và cấu trúc như kỳ thi JLPT.",
        "duration": duration,
        "passing_score": timing["pass"],
        "kind": "official",
        "date": date,
        "audio": meta.get("audio", ""),
        "source_pdf": meta.get("source_pdf", ""),
        "sections_meta": sections_meta,
        "phases": phases,
        "questions": questions,
    }


def discover_exam_files() -> list[Path]:
    files = []
    for level_dir in sorted(DATA_DIR.iterdir()):
        if not level_dir.is_dir() or level_dir.name.startswith("_"):
            continue
        for path in sorted(level_dir.glob("JLPT_*.md")):
            if "_pdf" in path.name or path.name.startswith("."):
                continue
            files.append(path)
    return files


def load_all_official_exams() -> list[dict]:
    exams = []
    for path in discover_exam_files():
        parsed = parse_exam_file(path)
        if parsed:
            exams.append(parsed)
    return exams
