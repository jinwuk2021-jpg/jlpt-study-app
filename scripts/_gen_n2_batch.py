#!/usr/bin/env python3
"""Generate N2 exam markdown from jpnihon text dumps + answer keys."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from app.exam_loader import parse_exam_file

# Official answer keys (from 答案.pdf / 答案解析)
ANSWERS: dict[str, dict[str, int]] = {
    "2014-07": {f"Q{i}": a for i, a in enumerate([
        1,2,3,1,4, 4,4,1,2,3, 1,3,4,2,4, 3,1,3,2,2,1,4, 2,2,1,3,4, 3,2,1,4,3,
        4,2,3,2,4,1,3,1,1,3,4,2, 1,1,2,3,4, 1,4,2,2,3, 4,3,1,4,1, 4,2,1,3,2,2,2,4,3,
        4,1, 4,2,1, 3,3,
        4,4,3,3,3, 2,3,4,1,3,2, 1,2,1,4,2, 1,2,2,2,3,3,2,1,2,1,3,2, 2,3,1,3,
    ], 1)},
    "2014-12": {f"Q{i}": a for i, a in enumerate([
        3,4,2,1,2, 2,4,3,3,1, 4,1,3,2,3, 1,4,2,1,1,4,3, 4,2,4,1,3, 2,3,1,3,1,
        4,1,3,4,3,1,2,4,1,3,2,4, 2,1,4,3,3, 3,1,2,3,4, 4,3,1,4,1, 2,4,4,3,4,1,1,3,2,
        2,3, 2,3,4, 2,2,
        1,2,4,2,3, 2,2,3,2,4,3, 4,3,3,4,2, 3,1,3,2,1,1,3,2,1,2,2,3, 3,2,4,2,
    ], 1)},
    "2015-07": {f"Q{i}": a for i, a in enumerate([
        4,1,4,3,2, 1,3,3,4,1, 4,2,1,3,2, 4,3,2,3,1,4,2, 3,1,4,3,2, 3,1,4,2,1,
        1,4,2,3,2,4,1,3,3,3,4,2, 1,2,3,4,1, 1,3,1,4,2, 3,4,4,1,2, 4,4,2,1,2,1,3,4,1,
        3,3, 4,3,2, 3,2,
        3,3,2,3,3, 2,4,1,2,3,2, 1,3,2,4,4, 3,1,3,2,2,1,3,1,3,1,2,2, 3,1,1,2,
    ], 1)},
    "2015-12": {f"Q{i}": a for i, a in enumerate([
        3,1,4,2,3, 1,4,1,2,3, 2,4,4,3,1, 1,3,1,2,3,4,2, 4,1,2,4,3, 2,3,2,4,1,
        1,4,3,2,3,2,1,1,3,1,2,4, 4,3,1,3,2, 2,1,3,2,4, 3,3,2,1,3, 2,4,3,3,1,4,2,4,1,
        1,4, 3,2,4, 4,2,
        4,1,2,4,3, 2,3,1,2,3,2, 3,4,2,2,3, 3,2,3,1,2,3,1,3,2,2,2,3, 4,3,4,2,
    ], 1)},
    "2016-07": {f"Q{i}": a for i, a in enumerate([
        4,1,4,3,2, 3,2,1,4,2, 4,1,3,3,2, 2,1,4,1,2,3,4, 4,1,1,3,2, 2,3,3,4,1,
        1,3,2,1,4,2,2,4,4,3,1,3, 1,4,2,1,3, 2,1,4,3,2, 2,3,2,4,1, 4,1,3,4,2,1,1,2,4,
        2,3, 3,1,4, 3,4,
        2,3,3,2,1, 3,3,3,4,3,2, 4,1,2,1,3, 3,2,2,1,2,1,1,2,3,3,2,3, 0,0,0,  # L5 partial on PDF
    ], 1)},
    "2016-12": {f"Q{i}": a for i, a in enumerate([
        2,4,2,3,1, 2,3,2,1,4, 1,3,3,4,1, 2,1,3,2,3,1,4, 1,4,3,4,2, 3,4,1,4,2,
        1,1,2,3,1,4,2,2,3,4,3,4, 3,4,1,2,3, 2,2,4,1,3, 2,3,4,2,1, 1,3,1,4,1,2,2,3,1,
        4,3, 2,4,3, 4,3,
        1,2,2,4,3, 3,2,1,2,4,1, 2,1,3,1,2, 2,3,2,1,3,1,2,2,2,1,1,3, 3,1,3,1,
    ], 1)},
    "2017-07": {f"Q{i}": a for i, a in enumerate([
        3,2,2,1,4, 1,2,3,1,3, 4,2,2,4,3, 4,2,4,1,3,1,3, 4,4,2,1,3, 2,4,1,1,3,
        4,3,1,2,4,1,2,2,4,3,2,1, 1,4,4,3,2, 2,1,3,4,1, 3,2,3,1,1, 4,4,3,4,1,2,2,4,1,
        1,4, 3,2,2, 3,3,
        1,2,2,3,2, 3,3,3,1,2,3, 4,4,3,2,1, 3,1,1,2,3,2,3,2,1,2,2,2, 1,1,2,4,
    ], 1)},
    "2017-12": {f"Q{i}": a for i, a in enumerate([
        1,3,4,2,2, 3,2,4,1,3, 4,4,2,1,3, 1,1,2,3,4,2,4, 3,1,1,2,3, 2,4,4,1,3,
        4,1,2,1,1,3,3,1,4,3,3,2, 1,4,4,2,1, 2,4,2,3,1, 2,4,1,3,2, 2,2,4,1,4,3,4,1,3,
        4,3, 3,1,2, 2,3,
        4,1,3,4,2, 2,1,2,4,1,2, 1,3,4,1,2, 2,2,3,2,1,3,1,2,3,2,3,1, 3,2,2,3,
    ], 1)},
}

# Listening answers L1-L30 mapping from 听解 sections
LISTENING: dict[str, list[int]] = {
    "2014-07": [4,4,3,3,3, 2,3,4,1,3,2, 1,2,1,4,2, 1,2,2,2,3,3,2,1,2,1,3,2, 2,3,1,3],
    "2014-12": [1,2,4,2,3, 2,2,3,2,4,3, 4,3,3,4,2, 3,1,3,2,1,1,3,2,1,2,2,3, 3,2,4,2],
    "2015-07": [3,3,2,3,3, 2,4,1,2,3,2, 1,3,2,4,4, 3,1,3,2,2,1,3,1,3,1,2,2, 3,1,1,2],
    "2015-12": [4,1,2,4,3, 2,3,1,2,3,2, 3,4,2,2,3, 3,2,3,1,2,3,1,3,2,2,2,3, 4,3,4,2],
    "2016-07": [2,3,3,2,1, 3,3,3,4,3,2, 4,1,2,1,3, 3,2,2,1,2,1,1,2,3,3,2,3, 2,4,1,2],
    "2016-12": [1,2,2,4,3, 3,2,1,2,4,1, 2,1,3,1,2, 2,3,2,1,3,1,2,2,2,1,1,3, 3,1,3,1],
    "2017-07": [1,2,2,3,2, 3,3,3,1,2,3, 4,4,3,2,1, 3,1,1,2,3,2,3,2,1,2,2,2, 1,1,2,4],
    "2017-12": [4,1,3,4,2, 2,1,2,4,1,2, 1,3,4,1,2, 2,2,3,2,1,3,1,2,3,2,3,1, 3,2,2,3],
}

EXAMS = [
    ("2014", "07", "N2-2014-07-真题.pdf", "2014年7月N2.mp3", "jpnihon_2014_07.txt"),
    ("2014", "12", "N2-2014-12-真题.pdf", "2014年12月N2.mp3", None),
    ("2015", "07", "N2-2015-07-真题.pdf", "2015年7月N2.mp3", "jpnihon_2015_07.txt"),
    ("2015", "12", "N2-2015-12-真题.pdf", "2015年12月.mp3", None),
    ("2016", "07", "N2-2016-07-真题.pdf", "2016年7月N2.mp3", None),
    ("2016", "12", "N2-2016-12-真题.pdf", "2016年12月N2.mp3", None),
    ("2017", "07", "N2-2017-07-真题.pdf", "2017年7月N2.mp3", None),
    ("2017", "12", "N2-2017-12-真题.pdf", "2017年12月N2.mp3", None),
    ("2020", "12", "2020年12月N2真题+答案.pdf", "N2-2020.12.mp3", "jpnihon_2020_12.txt"),
    ("2021", "07", "2021年7月N2真题.pdf", "2021.7.n2.mp3", None),
]

SECTIONS = [
    ("文字", "文字（読み方）", "1-5", "📖 問題1｜文字（読み方）", "＿＿の言葉の読み方として最もよいものを、１・２・３・４からひとつ選びなさい。"),
    ("文字2", "文字（漢字書き）", "6-10", "📖 問題2｜文字（漢字書き）", "＿＿の言葉を漢字で書くとき、最もよいものを、１・２・３・４からひとつ選びなさい。"),
    ("語彙1", "語彙（文脈規定）", "11-15", "📖 問題3｜語彙（文脈規定）", "（　）に入れるのに最もよいものを、１・２・３・４からひとつ選びなさい。"),
    ("語彙2", "語彙（文脈規定）", "16-22", "📖 問題4｜語彙（文脈規定）", "（　）に入れるのに最もよいものを、１・２・３・４からひとつ選びなさい。"),
    ("語彙3", "語彙（言い換え類義）", "23-27", "📖 問題5｜語彙（言い換え類義）", "＿＿の言葉に意味が最も近いものを、１・２・３・４からひとつ選びなさい。"),
    ("語彙4", "語彙（用法）", "28-32", "📖 問題6｜語彙（用法）", "＿＿の言葉の使い方として最もよいものを、１・２・３・４からひとつ選びなさい。"),
    ("文法1", "文法（文の文法1）", "33-44", "📖 問題7｜文法（文の文法1）", "（　）に入れるのに最もよいものを、１・２・３・４からひとつ選びなさい。"),
    ("文法2", "文法（文の文法2・並べ替え）", "45-49", "📖 問題8｜文法（文の文法2・並べ替え）", "次の文の ★ に入る最もよいものを、１・２・３・４からひとつ選びなさい。"),
    ("読解1", "読解（文章の文法）", "50-54", "📖 問題9｜読解（文章の文法）", "次の文章を読んで、文章全体の内容を考えて、50から54の中に入る最もよいものを、１・２・３・４からひとつ選びなさい。"),
    ("読解2", "読解（短文・中文）", "55-59", "📖 問題10｜読解（短文）", None),
    ("読解3", "読解（中文・長文）", "60-68", "📖 問題11｜読解（中文・長文）", None),
    ("読解4", "読解（比較・統合）", "69-70", "📖 問題12｜読解（比較・統合）", None),
    ("読解5", "読解（長文）", "71-73", "📖 問題13｜読解（長文）", None),
    ("読解6", "読解（情報検索）", "74-75", "📖 問題14｜読解（情報検索）", None),
    ("聴解1", "聴解（課題理解）", "L1-L5", "🔊 問題1｜課題理解", None),
    ("聴解2", "聴解（ポイント理解）", "L6-L11", "🔊 問題2｜ポイント理解", None),
    ("聴解3", "聴解（概要理解）", "L12-L16", "🔊 問題3｜概要理解", None),
    ("聴解4", "聴解（即時応答）", "L17-L28", "🔊 問題4｜即時応答", None),
    ("聴解5", "聴解（統合理解）", "L29-L30", "🔊 問題5｜統合理解", None),
]

SKIP = re.compile(
    r"^(Loading\.\.\.|---|\d+ / \d+ 页|邀请码|网站|NEW |日语能力考|点击听解|回复|发布于|快来|Related|©|/ \d+ 页)$"
)
SECTION_RE = re.compile(r"^### (問題[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭]|聴解[①②③④⑤])")
QNUM_RE = re.compile(r"^(\d+)\.\s*(.*)")
LISTEN_RE = re.compile(r"^(\d+)\.\s*(\d+\s*番|質問\s*\d+)?\s*(.*)")


def parse_jpnihon(text: str) -> dict:
    """Parse jpnihon text dump into sections with questions."""
    lines = [ln.strip() for ln in text.splitlines()]
    data: dict = {"sections": {}, "passages": {}}
    current = None
    qnum = None
    passage_buf: list[str] = []
    in_passage = False

    i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln or SKIP.match(ln) or ln.startswith("- ") or ln.startswith("## ["):
            i += 1
            continue
        if ln.startswith("## ") and not ln.startswith("###"):
            i += 1
            continue

        sm = SECTION_RE.match(ln)
        if sm:
            current = sm.group(1)
            data["sections"].setdefault(current, {"questions": [], "instruction": ""})
            qnum = None
            in_passage = False
            passage_buf = []
            i += 1
            continue

        if current is None:
            i += 1
            continue

        if ln.startswith("> "):
            passage_buf.append(ln[2:])
            in_passage = True
            i += 1
            continue

        qm = QNUM_RE.match(ln)
        if qm and current.startswith("問題"):
            num = int(qm.group(1))
            rest = qm.group(2).strip()
            if in_passage and passage_buf:
                data["passages"][num] = "\n".join(f"> {p}" for p in passage_buf)
                passage_buf = []
                in_passage = False
            if rest:
                data["sections"][current]["questions"].append({
                    "num": num, "stem": rest, "options": [], "passage": data["passages"].get(num, "")
                })
                qnum = num
            elif num >= 50:
                data["sections"][current]["questions"].append({
                    "num": num, "stem": f"（{num}）", "options": [], "passage": ""
                })
                qnum = num
            i += 1
            continue

        if current.startswith("聴解"):
            lm = LISTEN_RE.match(ln)
            if lm:
                num = int(lm.group(1))
                label = (lm.group(2) or "").strip()
                rest = (lm.group(3) or "").strip()
                data["sections"][current]["questions"].append({
                    "num": num, "stem": label or rest, "options": [], "passage": ""
                })
                qnum = num
                i += 1
                continue

        # options or continuation
        if qnum is not None and current in data["sections"]:
            qs = data["sections"][current]["questions"]
            if not qs:
                i += 1
                continue
            q = qs[-1]
            if re.match(r"^[1-4]$", ln):
                q["options"].append(ln)
            elif ln in ("1", "2", "3") and current.startswith("聴解") and int(str(qnum)) >= 92:
                q["options"].append(ln)
            elif len(q["options"]) < 4 and not ln.startswith("(") and current.startswith("問題"):
                if q["stem"] and not q["options"]:
                    q["stem"] += " " + ln
                elif q["options"]:
                    # might be extra option text continuation
                    if len(q["options"]) <= 4:
                        q["options"].append(ln)
            elif current.startswith("聴解") and len(q["options"]) < 4:
                q["options"].append(ln)
        i += 1

    return data


def wrap_stem(stem: str) -> str:
    """Wrap blanks with underscores."""
    stem = re.sub(r"（\s*）", "_＿＿＿_", stem)
    stem = re.sub(r"\(\s*\)", "_＿＿＿_", stem)
    if "★" in stem:
        stem = stem.replace("★", "_★_")
    return stem.strip()


def q_block(qid: str, stem: str, options: list[str], answer: int, passage: str = "") -> str:
    lines = []
    if passage and qid.startswith("Q") and int(qid[1:]) in (50, 55, 60, 69, 71, 74):
        lines.append(passage)
        lines.append("")
    lines.append(f"#### {qid}")
    lines.append("")
    if stem and stem not in ("****", "(音声確認要)"):
        lines.append(f"**{wrap_stem(stem)}**")
        lines.append("")
    for j, opt in enumerate(options[:4], 1):
        mark = " ✅" if j == answer else ""
        lines.append(f"- [ ] {j}. {opt}{mark}")
    if not options and answer:
        n = 3 if qid.startswith("L") and 17 <= int(qid[1:]) <= 28 else 4
        for j in range(1, n + 1):
            mark = " ✅" if j == answer else ""
            lines.append(f"- [ ] {j}. {j}{mark}")
    lines.append("")
    if qid.startswith("L") and "質問" in stem:
        pass
    else:
        lines.append(f"`answer: {answer}`")
    lines.append("")
    lines.append("---")
    return "\n".join(lines)


def meta_yaml(date: str, source: str, audio: str) -> str:
    rows = ["```yaml", "exam: JLPT N2", f"date: {date}", f"source_pdf: {source}", f"audio: {audio}", "sections:"]
    for sid, label, qs, *_ in SECTIONS:
        rows.append(f"  - id: {sid}")
        rows.append(f"    label: {label}")
        rows.append(f"    questions: {qs}")
    rows.append("```")
    return "\n".join(rows)


def listening_map(jp_section: str) -> tuple[int, int]:
    """Map jpnihon 聴解 section to L range."""
    maps = {"聴解①": (1, 5), "聴解②": (6, 11), "聴解③": (12, 16), "聴解④": (17, 28), "聴解⑤": (29, 30)}
    return maps.get(jp_section, (0, 0))


def generate(year: str, month: str, source: str, audio: str, jpnihon_file: str | None) -> str:
    key = f"{year}-{month}"
    ans = ANSWERS.get(key, {})
    lans = LISTENING.get(key, [])
    y_label = f"{year}年{int(month)}月"

    parts = [
        f"# JLPT N2 — {y_label} 真題",
        "",
        f"> **試験**: {y_label} 新日本語能力試験 N2  ",
        "> **構成**: 言語知識（文字・語彙・文法）・読解・聴解  ",
        f"> **出典**: `{source}`（学習用途）／正答表：公式答案",
        "",
        "---",
        "",
        "## 📁 META",
        "",
        meta_yaml(f"{year}-{month}", source, audio),
        "",
        "---",
        "",
        "## 言語知識（文字・語彙・文法）",
        "",
        "---",
    ]

    if not jpnihon_file:
        parts.append(f"\n> ※ 要PDF確認 — jpnihonテキスト未取得。答案のみ登録。\n")
        return "\n".join(parts)

    cache = REPO / "data/exam/n2/_build_cache" / jpnihon_file
    parsed = parse_jpnihon(cache.read_text(encoding="utf-8"))

    sec_map = {
        "問題①": 0, "問題②": 1, "問題③": 2, "問題④": 3, "問題⑤": 4, "問題⑥": 5,
        "問題⑦": 6, "問題⑧": 7, "問題⑨": 8, "問題⑩": 9, "問題⑪": 10,
        "問題⑫": 11, "問題⑬": 12, "問題⑭": 13,
    }

    for jp_sec, idx in sec_map.items():
        if jp_sec not in parsed["sections"]:
            continue
        sec = parsed["sections"][jp_sec]
        sid, label, qrange, title, instr = SECTIONS[idx]
        parts.append(f"### {title}")
        parts.append("")
        if instr:
            parts.append(f"> {instr}")
            parts.append("")
        parts.append("---")
        for q in sec["questions"]:
            qid = f"Q{q['num']}"
            a = ans.get(qid, 1)
            passage = q.get("passage") or parsed["passages"].get(q["num"], "")
            parts.append(q_block(qid, q["stem"], q["options"], a, passage))

    parts.extend(["", "## 読解", "", "---", ""])
    # reading already in 問題⑨-⑭ above

    parts.extend([
        "",
        f"## 聴解（問題用紙のみ・音声: `{audio}`）",
        "",
        "> ⚠️ 聴解は音声が必要です。以下は問題用紙に記載された選択肢と公式参考答案です。",
        "",
        "---",
        "",
    ])

    li = 0
    for jp_sec in ["聴解①", "聴解②", "聴解③", "聴解④", "聴解⑤"]:
        if jp_sec not in parsed["sections"]:
            continue
        lstart, lend = listening_map(jp_sec)
        idx = 14 + ["聴解①", "聴解②", "聴解③", "聴解④", "聴解⑤"].index(jp_sec)
        sid, label, qrange, title, instr = SECTIONS[idx]
        parts.append(f"### {title}")
        parts.append("")
        if jp_sec in ("聴解③", "聴解④"):
            parts.append("> 問題用紙に何も印刷されていません。")
            parts.append("")
            memo = ", ".join(f"L{lstart + k}={lans[li + k]}" for k in range(lend - lstart + 1) if li + k < len(lans))
            parts.append(f"*(参考答案: {memo})*")
            parts.append("")
            li += lend - lstart + 1
        else:
            for q in parsed["sections"][jp_sec]["questions"]:
                li += 1
                lid = f"L{li}"
                a = lans[li - 1] if li - 1 < len(lans) else 1
                opts = q["options"]
                if opts and all(re.match(r"^[1-4]$", o) for o in opts):
                    opts = []
                parts.append(q_block(lid, q["stem"], opts, a))
        parts.append("")

    parts.append(f"*© {year} 日本語能力試験 N2 真題（{y_label}）— 学習用途のみ*")
    return "\n".join(parts)


def main():
    for year, month, source, audio, jpn in EXAMS:
        if jpn is None:
            print(f"SKIP (no jpnihon): {year}-{month}")
            continue
        md = generate(year, month, source, audio, jpn)
        out = REPO / "data/exam/n2" / f"JLPT_N2_{year}_{month}.md"
        out.write_text(md, encoding="utf-8")
        parsed = parse_exam_file(out)
        n = len(parsed["questions"]) if parsed else 0
        print(f"Wrote {out.name}: {n} questions")


if __name__ == "__main__":
    main()
