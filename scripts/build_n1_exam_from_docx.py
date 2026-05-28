#!/usr/bin/env python3
"""Build JLPT N1 exam markdown from docx text (with embedded answer key)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.extract_docx_text import extract_docx  # noqa: E402

META_TEMPLATE = """# JLPT N1 — {year}年{month}月 真題

> **試験**: {year}年{month}月 新日本語能力試験 N1
> **構成**: 言語知識（文字・語彙・文法）・読解・聴解
> **出典**: `{source}`（学習用途）
> **正答**: {year}年{month}月 N1 参考答案

---

## 📁 META

```yaml
exam: JLPT N1
date: {date}
source_pdf: {source}
audio: {audio}
sections:
  - id: 語彙1
    label: 語彙（読み方）
    questions: 1-6
  - id: 語彙2
    label: 語彙（文脈規定）
    questions: 7-13
  - id: 語彙3
    label: 語彙（言い換え類義）
    questions: 14-19
  - id: 語彙4
    label: 語彙（用法）
    questions: 20-25
  - id: 文法1
    label: 文法（文の文法1）
    questions: 26-35
  - id: 文法2
    label: 文法（並べ替え）
    questions: 36-40
  - id: 文法3
    label: 文法（文章の文法）
    questions: 41-45
  - id: 読解1
    label: 読解（短文）
    questions: 46-49
  - id: 読解2
    label: 読解（中文）
    questions: 50-58
  - id: 読解3
    label: 読解（長文）
    questions: 59-62
  - id: 読解4
    label: 読解（比較）
    questions: 63-64
  - id: 読解5
    label: 読解（長文）
    questions: 65-68
  - id: 読解6
    label: 読解（情報検索）
    questions: 69-70
  - id: 聴解1
    label: 聴解（課題理解）
    questions: L1-L6
  - id: 聴解2
    label: 聴解（ポイント理解）
    questions: L7-L13
  - id: 聴解3
    label: 聴解（概要理解）
    questions: L14-L19
  - id: 聴解4
    label: 聴解（即時応答）
    questions: L20-L33
  - id: 聴解5
    label: 聴解（統合理解）
    questions: L34-L37
```

---

## 言語知識（文字・語彙・文法）

---

"""

ANSWER_START = re.compile(
    r"(N1词汇答案|N1语法答案|N1读解答案|N1听力答案|"
    r"20\d{2}\s*年\s*\d{1,2}\s*月.*参考答案|"
    r"参考答案\s*$)",
    re.I | re.M,
)
Q_STEM = re.compile(r"^(\d+)[、](.+)$")
OPT_SPLIT = re.compile(r"[1-4１-４]\s*[\.．、]\s*")
LISTEN_NUM = re.compile(r"^(\d+)番\s*$")
LISTEN_OPT = re.compile(r"^(\d+)\s*[\.．、]?\s*(.+)$")


WRITTEN_PROBLEM_SIZE = {
    1: 6, 2: 7, 3: 6, 4: 6, 5: 5, 6: 5, 7: 5, 8: 4,
    91: 3, 92: 3, 93: 3, 10: 4, 11: 2, 12: 4, 13: 2,
}
LISTENING_PROBLEM_SIZE = {1: 6, 2: 7, 3: 6, 4: 14, 5: 4}


def _normalize_answer_lines(text: str) -> list[str]:
    """Join broken headers like '問題\\n10' and drop sub-markers."""
    raw = [ln.strip() for ln in text.splitlines()]
    lines: list[str] = []
    i = 0
    while i < len(raw):
        ln = raw[i]
        if ln == "問題" and i + 1 < len(raw) and raw[i + 1].isdigit():
            lines.append(f"問題{raw[i + 1]}")
            i += 2
            continue
        if m9 := re.match(r"問題\s*9[（(](\d)[）)]", ln):
            lines.append(f"問題9{m9.group(1)}")
            i += 1
            continue
        if re.search(r"問題\d+[（(]", ln):
            i += 1
            continue
        if ln:
            lines.append(ln)
        i += 1
    return lines


def _parse_answer_block(text: str) -> tuple[dict[str, int], dict[str, int]]:
    """Parse trailing answer key into Q and L dicts."""
    q_ans: dict[str, int] = {}
    l_ans: dict[str, int] = {}
    lines = _normalize_answer_lines(text)
    section = "written"
    problem_num = 0
    digit_buf: list[int] = []

    def flush_written():
        nonlocal digit_buf, problem_num
        while digit_buf and problem_num:
            n = WRITTEN_PROBLEM_SIZE.get(problem_num, len(digit_buf) // 2)
            need = n * 2
            if len(digit_buf) < need:
                break
            data = digit_buf[:need]
            digit_buf = digit_buf[need:]
            for qn, a in zip(data[:n], data[n:]):
                if 1 <= a <= 4:
                    q_ans[f"Q{qn}"] = a

    def flush_listening():
        nonlocal digit_buf, problem_num
        while digit_buf and problem_num:
            n = LISTENING_PROBLEM_SIZE.get(problem_num, len(digit_buf) // 2)
            need = n * 2
            if len(digit_buf) < need:
                break
            data = digit_buf[:need]
            digit_buf = digit_buf[need:]
            for i, a in enumerate(data[n:]):
                key = _listening_global(problem_num, i + 1)
                if key and 1 <= a <= 4:
                    l_ans[key] = a

    for ln in lines:
        if re.search(r"听力|聴解|听解", ln, re.I):
            flush_written()
            digit_buf = []
            section = "listening"
            problem_num = 0
            continue
        if re.search(r"N1(词汇|语法|读解)|文字词汇|文法", ln, re.I) and "听" not in ln:
            if section == "written":
                flush_written()
            else:
                flush_listening()
            digit_buf = []
            problem_num = 0
            section = "written"
            continue

        m = re.match(r"問題\s*(\d+)\s*$", ln) or re.match(r"問題(9[123]|\d+)$", ln)
        if m:
            if section == "listening":
                flush_listening()
            else:
                flush_written()
            problem_num = int(m.group(1))
            continue

        if ln.isdigit():
            digit_buf.append(int(ln))

    if section == "listening":
        flush_listening()
    else:
        flush_written()

    return q_ans, l_ans


def _listening_global(problem: int, idx: int) -> str | None:
    """Map 問題N + index within problem to L number (2012+ N1 layout)."""
    offsets = {1: 0, 2: 6, 3: 13, 4: 19, 5: 33}
    if problem not in offsets:
        return None
    counts = {1: 6, 2: 7, 3: 6, 4: 14, 5: 4}
    if idx > counts.get(problem, 0):
        return None
    return f"L{offsets[problem] + idx}"


def _split_body_answers(text: str) -> tuple[str, str]:
    m = ANSWER_START.search(text)
    if not m:
        raise ValueError("No answer key section found in docx text")
    return text[: m.start()], text[m.start() :]


def _parse_written_questions(body: str, q_ans: dict[str, int]) -> str:
    """Parse Q1–Q70 from docx body (2015-style numbering)."""
    lines = body.splitlines()
    out: list[str] = []
    i = 0
    current_q: int | None = None
    stem_parts: list[str] = []
    opts: list[tuple[int, str]] = []
    in_passage = False
    passage_buf: list[str] = []

    def flush_q():
        nonlocal current_q, stem_parts, opts, in_passage, passage_buf
        if current_q is None:
            return
        if in_passage and passage_buf:
            out.append("#### 【文章】\n\n")
            out.append("> " + "\n> ".join(passage_buf) + "\n\n")
            passage_buf = []
            in_passage = False
        stem = " ".join(stem_parts).strip()
        if stem:
            out.append(f"#### Q{current_q}\n\n")
            out.append(f"**{stem}**\n\n")
            ans = q_ans.get(f"Q{current_q}", 0)
            for n, txt in opts:
                mark = " ✅" if n == ans else ""
                out.append(f"- [ ] {n}. {txt}{mark}\n")
            out.append(f"\n`answer: {ans}`\n\n---\n")
        current_q = None
        stem_parts = []
        opts = []

    while i < len(lines):
        ln = lines[i].strip()
        if not ln:
            i += 1
            continue
        if ln.startswith("聴解") or "听力原文" in ln:
            break
        if re.match(r"^問題\s*[1-9１-９]", ln) and "次の" in ln:
            i += 1
            continue

        sm = Q_STEM.match(ln)
        if sm:
            n = int(sm.group(1))
            if 1 <= n <= 70:
                if current_q is not None and 20 <= current_q <= 25 and 1 <= n <= 4:
                    stem_parts.append(ln)
                    i += 1
                    continue
                flush_q()
                current_q = n
                stem_parts = [sm.group(2).strip()]
                opts = []
                i += 1
                continue

        if current_q is not None and re.search(r"[1-4１-４]\s*[\.．、]", ln):
            parts = [p.strip() for p in OPT_SPLIT.split(ln) if p.strip()]
            start = 1
            for part in parts:
                if start <= 4:
                    opts.append((start, part))
                    start += 1
            i += 1
            continue

        if current_q is not None and 26 <= current_q <= 40 and not opts:
            # reorder: collect numbered fragments
            if re.match(r"^\d+\.", ln):
                opts.append((int(re.match(r"^(\d+)", ln).group(1)), ln.split(".", 1)[-1].strip()))
                i += 1
                continue

        if current_q == 41 or (current_q and 41 <= current_q <= 45):
            if re.match(r"^41、", ln) or (current_q == 41 and not stem_parts):
                in_passage = True
            if in_passage and not re.match(r"^4[1-5]、", ln):
                passage_buf.append(ln)
                i += 1
                continue
            if re.match(r"^4[1-5]、", ln):
                flush_q()
                sub = int(ln[0:2])
                current_q = sub
                stem_parts = [ln.split("、", 1)[-1].strip()]
                opts = []
                i += 1
                continue

        if current_q is not None and not opts and not in_passage:
            stem_parts.append(ln)

        i += 1

    flush_q()
    return "\n".join(out)


def _parse_listening(body: str, l_ans: dict[str, int]) -> str:
    """Parse 聴解 section with printed options (L1–L13)."""
    if "聴解" not in body:
        idx = body.find("問題１では")
        if idx < 0:
            return ""
        listen_text = body[idx:]
    else:
        listen_text = body.split("聴解", 1)[-1]

    lines = [ln.strip() for ln in listen_text.splitlines()]
    out: list[str] = []
    out.append("## 聴解\n\n")
    out.append("> ⚠️ 聴解は音声が必要です。\n\n---\n\n")
    out.append("### 🔊 問題1｜課題理解（L1–L6）\n\n")

    i = 0
    l_num = 0
    opts: list[tuple[int, str]] = []

    def flush_l():
        nonlocal l_num, opts
        if l_num < 1:
            return
        key = f"L{l_num}"
        ans = l_ans.get(key, 0)
        out.append(f"#### {key}\n\n")
        out.append(f"**（問題1・{l_num}番）**\n\n")
        for n, txt in opts:
            mark = " ✅" if n == ans else ""
            out.append(f"- [ ] {n}. {txt}{mark}\n")
        out.append(f"\n`answer: {ans}`\n\n---\n")
        opts = []

    while i < len(lines):
        ln = lines[i]
        if re.match(r"問題\s*2", ln):
            flush_l()
            out.append("\n### 🔊 問題2｜ポイント理解（L7–L13）\n\n")
            l_num = 6
        if re.match(r"問題\s*3", ln):
            flush_l()
            l_num = 13
            out.append("\n### 🔊 問題3｜概要理解（L14–L19）\n\n")
            out.append("> 問題用紙に何も印刷されていません。\n\n")
            memo = ", ".join(f"L{n}={l_ans.get(f'L{n}', '?')}" for n in range(14, 20))
            out.append(f"*(参考答案: {memo})*\n\n---\n")
            break
        if LISTEN_NUM.match(ln) or re.match(r"^[１２３４５６]番", ln):
            flush_l()
            l_num += 1
            i += 1
            continue
        om = LISTEN_OPT.match(ln)
        if om and l_num > 0 and int(om.group(1)) <= 4:
            opts.append((int(om.group(1)), om.group(2).strip()))
        i += 1

    flush_l()

    # L14–L37 memos
    if l_num <= 13:
        out.append("\n### 🔊 問題3｜概要理解（L14–L19）\n\n")
        out.append("> 問題用紙に何も印刷されていません。\n\n")
        memo = ", ".join(f"L{n}={l_ans.get(f'L{n}', '?')}" for n in range(14, 20))
        out.append(f"*(参考答案: {memo})*\n\n---\n")

    out.append("\n### 🔊 問題4｜即時応答（L20–L33）\n\n")
    out.append("> 問題用紙に何も印刷されていません。\n\n")
    memo = ", ".join(f"L{n}={l_ans.get(f'L{n}', '?')}" for n in range(20, 34))
    out.append(f"*(参考答案: {memo})*\n\n---\n")

    out.append("\n### 🔊 問題5｜統合理解（L34–L37）\n\n")
    for n in range(34, 38):
        ans = l_ans.get(f"L{n}", 0)
        out.append(f"#### L{n}\n\n")
        out.append(f"**（問題5・{n - 33}番）問題用紙に何も印刷されていません。**\n\n")
        out.append(f"`answer: {ans}`\n\n---\n")

    return "\n".join(out)


def build(
    docx_path: Path,
    year: int,
    month: int,
    out_path: Path,
    listening_override: dict[str, int] | None = None,
) -> None:
    text = extract_docx(docx_path)
    body, ans_text = _split_body_answers(text)
    q_ans, l_ans = _parse_answer_block(ans_text)
    if listening_override:
        l_ans = {**l_ans, **listening_override}

    mm = f"{month:02d}"
    source = docx_path.name
    header = META_TEMPLATE.format(
        year=year,
        month=month,
        date=f"{year}-{mm}",
        source=source,
        audio=f"{year}.{mm}.N1.mp3",
    )
    written = _parse_written_questions(body, q_ans)
    listening = _parse_listening(body, l_ans)
    footer = f"\n\n*© {year} 日本語能力試験 N1 真題（{year}年{month}月）— 学習用途のみ*\n"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + written + listening + footer, encoding="utf-8")
    print(f"Wrote {out_path} (Q: {len(q_ans)}, L: {len(l_ans)})")


# 2015-12 listening (docx key layout for 問題5 differs)
N1_2015_12_LISTENING = {
    **{f"L{i}": a for i, a in enumerate([2, 3, 3, 2, 1, 2], start=1)},
    **{f"L{i}": a for i, a in enumerate([2, 2, 3, 4, 3, 1, 4], start=7)},
    **{f"L{i}": a for i, a in enumerate([4, 1, 4, 3, 2, 1], start=14)},
    **{f"L{i}": a for i, a in enumerate(
        [3, 1, 3, 2, 2, 1, 1, 3, 3, 1, 2, 3, 1, 1], start=20
    )},
    **{f"L{i}": a for i, a in enumerate([1, 2, 1, 4], start=34)},
}

# 2014-12 listening answers (from 沪江解析 PDF; docx lacks key)
N1_2014_12_LISTENING = {
    **{f"L{i}": a for i, a in enumerate([2, 1, 2, 3, 1, 4], start=1)},
    **{f"L{i}": a for i, a in enumerate([3, 1, 4, 2, 2, 4, 2], start=7)},
    **{f"L{i}": a for i, a in enumerate([1, 3, 2, 1, 2, 4], start=14)},
    **{f"L{i}": a for i, a in enumerate(
        [1, 2, 3, 1, 3, 1, 1, 2, 3, 2, 2, 3, 1, 3], start=20
    )},
    **{f"L{i}": a for i, a in enumerate([2, 4, 4, 1], start=34)},
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("docx", type=Path)
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--month", type=int, choices=[7, 12], required=True)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    mm = f"{args.month:02d}"
    out = args.out or Path(__file__).resolve().parents[1] / f"data/exam/n1/JLPT_N1_{args.year}_{mm}.md"
    override = None
    if args.year == 2015 and args.month == 12:
        override = N1_2015_12_LISTENING
    elif args.year == 2014 and args.month == 12:
        override = N1_2014_12_LISTENING
    build(args.docx, args.year, args.month, out, override)


if __name__ == "__main__":
    main()
