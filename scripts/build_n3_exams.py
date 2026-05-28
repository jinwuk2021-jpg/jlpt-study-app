#!/usr/bin/env python3
"""Generate JLPT N3 exam markdown: jlpt247/jpnihon questions + camnangnhatban answers."""

from __future__ import annotations

import importlib.util
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.exam_stem_format import format_stem  # noqa: E402

OUT_DIR = ROOT / "data" / "exam" / "n3"
CACHE_DIR = OUT_DIR / "_cache"
AGENT_TOOLS = Path.home() / ".cursor/projects/Users-huynhha-Downloads-JLPT-study-app/agent-tools"

JPNIHON_CACHE: dict[tuple[int, int], str] = {
    (2014, 7): "a08afe2f-d088-4a5e-b098-8d59d237d066.txt",
    (2014, 12): "a08afe2f-d088-4a5e-b098-8d59d237d066.txt",
    (2015, 12): "a08afe2f-d088-4a5e-b098-8d59d237d066.txt",
    (2016, 12): "47cfbec5-f527-4b31-a177-726c92cfa18c.txt",
    (2019, 7): "1db4cc3b-5555-48da-a2e4-1ab666cff81e.txt",
    (2021, 7): "a8045823-3611-4fae-81b7-0041e448ba70.txt",
}

EXAMS = [
    (2014, 7, "n3-07-2014", "dap-an-jlpt-n3-7-2014-nhanh-chuan-nhat",
     "/Users/huynhha/Downloads/N3/N3-2014-07/N3-2014-07-真题.pdf",
     "2014年7月N3.mp3"),
    (2014, 12, "n3-12-2014", "dap-an-jlpt-n3-12-2014-nhanh-chuan-nhat",
     "/Users/huynhha/Downloads/N3/N3-2014-12/N3-2014-12-真题.pdf", "2014年12月N3.mp3"),
    (2015, 12, "n372015", "dap-an-jlpt-n3-12-2015-nhanh-chuan-nhat",
     "/Users/huynhha/Downloads/N3/N3-2015-12/N3-2015-12-真题.pdf", "2015年12月N3.mp3"),
    (2016, 7, "n3-07-2016", "dap-an-jlpt-n3-7-2016-nhanh-chuan-nhat",
     "/Users/huynhha/Downloads/N3/N3-2016-07/N3-2016-07-真题.pdf", "2016年7月N3.mp3"),
    (2016, 12, "n3-12-2016", "dap-an-jlpt-n3-12-2016-nhanh-chuan-nhat",
     "/Users/huynhha/Downloads/N3/N3-2016-12/N3-2016-12-真题.pdf", "2016年12月N3.mp3"),
    (2017, 7, "n3-07-2017", "dap-an-jlpt-n3-7-2017-nhanh-chuan-nhat",
     "/Users/huynhha/Downloads/N3/N3-2017-07/N3-2017-07-真题.pdf", "2017年7月N3.mp3"),
    (2017, 12, "n3-12-2017", "dap-an-jlpt-n3-12-2017-nhanh-chuan-nhat",
     "/Users/huynhha/Downloads/N3/N3-2017-12/N3-2017-12-答案.pdf", "2017年12月N3.mp3"),
    (2018, 7, "n3-07-2018", "dap-an-jlpt-n3-7-2018-nhanh-chuan-nhat",
     "/Users/huynhha/Downloads/N3/N3-2018-07/N3-2018-07-真题.pdf", "2018年7月N3音频.mp3"),
    (2018, 12, "n3-12-2018", "dap-an-jlpt-n3-12-2018-nhanh-chuan-nhat",
     "/Users/huynhha/Downloads/N3/N3-2018-12/N3-2018-12-真题.pdf", "2018年12月N3.mp3"),
    (2019, 7, "n3-07-2019", "dap-an-jlpt-n3-7-2019-nhanh-chuan-nhat",
     "/Users/huynhha/Downloads/N3/N3-2019-07/N3-2019-07-真题.pdf", "2019年7月N3.mp3"),
    (2019, 12, "n3-12-2019", "dap-an-jlpt-n3-12-2019-nhanh-chuan-nhat",
     "/Users/huynhha/Downloads/N3/2019.12/2019年12月N3真题 (2).pdf", "01 N3-2019.12.mp3"),
    (2020, 12, "n3-12-2020", "dap-an-jlpt-n3-12-2020-nhanh-chuan-nhat",
     "/Users/huynhha/Downloads/N3/2020/2020年12月日本語能力試験N3真题.pdf", "N3-2020.12.mp3"),
    (2021, 7, "n3-07-2021", "dap-an-jlpt-n3-7-2021-nhanh-chuan-nhat",
     "/Users/huynhha/Downloads/N3/2021.7/2021年7月N3真题.pdf", "2021年07月JLPT日语N3真题听力.MP3"),
]

# Fix 2017-12 exam pdf path
for i, row in enumerate(EXAMS):
    if row[0] == 2017 and row[1] == 12:
        EXAMS[i] = (
            2017, 12, "n3-12-2017", "dap-an-jlpt-n3-12-2017-nhanh-chuan-nhat",
            "/Users/huynhha/Downloads/N3/N3-2017-12/N3-2017-12-真题.pdf", "2017年12月N3.mp3",
        )

META_SECTIONS = """\
  - id: 文字
    label: 文字（読み方）
    questions: 1-8
  - id: 文字2
    label: 文字（漢字書き）
    questions: 9-14
  - id: 語彙1
    label: 語彙（文脈規定）
    questions: 15-25
  - id: 語彙2
    label: 語彙（言い換え）
    questions: 26-30
  - id: 語彙3
    label: 語彙（用法）
    questions: 31-35
  - id: 文法1
    label: 文法（文の文法1）
    questions: 36-48
  - id: 文法2
    label: 文法（並べ替え）
    questions: 49-53
  - id: 文法3
    label: 文法（文章の文法）
    questions: 54-58
  - id: 読解1
    label: 読解（短文）
    questions: 59-62
  - id: 読解2
    label: 読解（中文）
    questions: 63-68
  - id: 読解3
    label: 読解（長文）
    questions: 69-72
  - id: 読解4
    label: 読解（情報検索）
    questions: 73-74
  - id: 聴解1
    label: 聴解（課題理解）
    questions: L1-L6
  - id: 聴解2
    label: 聴解（ポイント理解）
    questions: L7-L12
  - id: 聴解3
    label: 聴解（概要理解）
    questions: L13-L15
  - id: 聴解4
    label: 聴解（即時応答）
    questions: L16-L19
  - id: 聴解5
    label: 聴解（統合理解）
    questions: L20-L28
"""

SECTION_RANGES = [
    (1, 8, "📖 問題1｜文字（読み方）", "＿＿の言葉の読み方として最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (9, 14, "📖 問題2｜文字（漢字書き）", "＿＿の言葉を漢字で書くとき、最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (15, 25, "📖 問題3｜語彙（文脈規定）", "（ ）に入れるのに最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (26, 30, "📖 問題4｜語彙（言い換え）", "＿＿の言葉の意味に最も近いものを、１・２・３・４からひとつ選びなさい。"),
    (31, 35, "📖 問題5｜語彙（用法）", "つぎのことばの使い方として最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (36, 48, "📖 問題6｜文法（文の文法1）", "つぎの文の（ ）に入れるのに最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (49, 53, "📖 問題7｜文法（並べ替え）", "つぎの文の ★ に入る最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (54, 58, "📖 問題8｜文法（文章の文法）", "つぎの文章を読んで、（ ）に入る最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (59, 62, "📖 問題9｜読解（短文）", "つぎの文章を読んで、質問に答えなさい。"),
    (63, 68, "📖 問題10｜読解（中文）", "つぎの文章を読んで、質問に答えなさい。"),
    (69, 72, "📖 問題11｜読解（長文）", "つぎの文章を読んで、質問に答えなさい。"),
    (73, 74, "📖 問題12｜読解（情報検索）", "右のページを読んで、質問に答えなさい。"),
]

LISTENING_RANGES = [
    ("L1", "L6", "🔊 問題1｜課題理解", True),
    ("L7", "L12", "🔊 問題2｜ポイント理解", True),
    ("L13", "L15", "🔊 問題3｜概要理解", False),
    ("L16", "L19", "🔊 問題4｜即時応答", False),
    ("L20", "L28", "🔊 問題5｜統合理解", False),
]

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_cached(url: str, path: Path) -> str:
    if path.is_file():
        return path.read_text(encoding="utf-8")
    try:
        html = fetch(url)
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"    fetch failed: {e}", file=sys.stderr)
        return ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    time.sleep(0.4)
    return html


def parse_jpnihon(text: str) -> dict[int, tuple[str, list[str]]]:
    out: dict[int, tuple[str, list[str]]] = {}
    parts = re.split(r"(?=### (?:問題|聴解))", text)
    for part in parts:
        if part.lstrip().startswith("### 聴解"):
            continue
        for m in re.finditer(
            r"^(\d+)\.\s*(.*?)(?=\n\d+\.\s|\n### |\Z)",
            part,
            flags=re.M | re.S,
        ):
            num = int(m.group(1))
            if num > 74:
                continue
            lines = [
                ln.strip()
                for ln in m.group(2).splitlines()
                if ln.strip() and ln.strip() != "Loading..."
            ]
            if not lines:
                continue
            stem, opts = lines[0], lines[1:5]
            out[num] = (stem, opts)
    return out


def load_jpnihon_questions(year: int, month: int) -> dict[int, tuple[str, list[str]]]:
    candidates = [
        CACHE_DIR / f"jpnihon_{year}_{month:02d}.txt",
        CACHE_DIR / f"jpnihon_{year}_{month}.txt",
    ]
    rel = JPNIHON_CACHE.get((year, month))
    if rel:
        candidates.append(AGENT_TOOLS / rel)
    for path in candidates:
        if path.is_file() and path.stat().st_size > 500:
            parsed = parse_jpnihon(path.read_text(encoding="utf-8"))
            if len(parsed) >= 10:
                return parsed
    return {}


def parse_jlpt247(html: str) -> dict[int, tuple[str, list[str]]]:
    out: dict[int, tuple[str, list[str]]] = {}
    stems = re.findall(
        r"<div class='question-content'\s*><div>(.*?)</div>",
        html,
        flags=re.S,
    )
    choice_blocks = re.findall(
        r"<div class='question-choices[^']*'>(.*?)</div>\s*<!--",
        html,
        flags=re.S,
    )
    for stem_raw, choices_raw in zip(stems, choice_blocks):
        stem = re.sub(r"<[^>]+>", "", stem_raw).strip()
        stem = re.sub(r"\s+", " ", stem)
        opts = [o.strip() for o in re.findall(r"<span>([^<]*)</span>", choices_raw) if o.strip()]
        m = re.match(r"(\d+)\.", stem)
        if m and len(opts) >= 2:
            out[int(m.group(1))] = (stem, opts[:4])
    return out


def _section_html(html: str, start: str, ends: list[str]) -> str:
    pat = rf"{start}(.*?)(?:{'|'.join(ends)}|$)"
    m = re.search(pat, html, flags=re.S)
    return m.group(1) if m else ""


def _table_rows(section: str) -> list[list[int]]:
    rows: list[list[int]] = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", section, flags=re.S):
        row: list[int] = []
        for cell in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S):
            cell = re.sub(r"<[^>]+>", " ", cell)
            cell = re.sub(r"\s+", " ", cell).strip()
            if not cell or re.fullmatch(r"問題\d+", cell):
                continue
            for p in cell.split():
                if p.isdigit():
                    row.append(int(p))
        if row:
            rows.append(row)
    return rows


def parse_camnang(html: str) -> dict[str, int]:
    ans: dict[str, int] = {}
    vocab = _section_html(html, r"N3\s*文字", [r"N3\s*文法"])
    grammar = _section_html(html, r"N3\s*文法", [r"N3\s*読解"])
    reading = _section_html(html, r"N3\s*読解", [r"N3\s*聴解", r"N3聴解"])
    listening = _section_html(html, r"N3\s*聴解", [r">>XEM", r"tablepress-11"])

    def pair(rows: list[list[int]]):
        i = 0
        while i + 1 < len(rows):
            qrow, arow = rows[i], rows[i + 1]
            if arow and all(1 <= a <= 4 for a in arow):
                for q, a in zip(qrow, arow):
                    yield q, a
                i += 2
            else:
                i += 1

    for q, a in pair(_table_rows(vocab)):
        if 1 <= q <= 35:
            ans[f"Q{q}"] = a
    for q, a in pair(_table_rows(grammar)):
        if 1 <= q <= 23:
            ans[f"Q{q + 35}"] = a
    for q, a in pair(_table_rows(reading)):
        if 24 <= q <= 39:
            ans[f"Q{q + 35}"] = a

    l_idx = 1
    rows = _table_rows(listening)
    i = 0
    while i + 1 < len(rows) and l_idx <= 28:
        arow = rows[i + 1]
        if all(1 <= a <= 4 for a in arow):
            for a in arow:
                if l_idx <= 28:
                    ans[f"L{l_idx}"] = a
                    l_idx += 1
            i += 2
        else:
            i += 1
    return ans


def underscore(stem: str, section_label: str = "", problem_title: str = "") -> str:
    return format_stem(stem, section_label, problem_title)


def q_block(
    qid: str,
    stem: str,
    opts: list[str],
    answer: int,
    *,
    section_label: str = "",
    problem_title: str = "",
) -> str:
    lines = [f"#### {qid}", "", f"**{underscore(stem, section_label, problem_title)}**", ""]
    if not opts:
        opts = [f"選択肢{i}" for i in range(1, 5)]
    for i, opt in enumerate(opts[:4], 1):
        mark = " ✅" if i == answer else ""
        lines.append(f"- [ ] {i}. {opt}{mark}")
    lines += ["", f"`answer: {answer}`", "", "---", ""]
    return "\n".join(lines)


def listening_block(qid: str, answer: int, has_choices: bool, n_opts: int = 4) -> str:
    lines = [f"#### {qid}", ""]
    if has_choices:
        lines += ["****", ""]
        for i in range(1, n_opts + 1):
            mark = " ✅" if i == answer else ""
            lines.append(f"- [ ] {i}. （問題用紙の選択肢）{mark}")
    else:
        lines.append("*(問題用紙に何も印刷されていません)*")
        lines.append("")
    lines += ["", f"`answer: {answer}`", "", "---", ""]
    return "\n".join(lines)


def generate(year: int, month: int, jlpt_slug: str, camnang_slug: str, pdf_name: str, audio: str) -> Path:
    mm = f"{month:02d}"
    out = OUT_DIR / f"JLPT_N3_{year}_{mm}.md"
    month_ja = "7月" if month == 7 else "12月"

    jlpt_html = fetch_cached(
        f"https://jlpt247.com/{jlpt_slug}/",
        CACHE_DIR / f"jlpt247_{jlpt_slug}.html",
    )
    camnang_html = fetch_cached(
        f"https://camnangnhatban.com/dap-an-de-thi-jlpt/{camnang_slug}.html",
        CACHE_DIR / f"camnang_{camnang_slug}.html",
    )
    if not camnang_html:
        raise RuntimeError(f"No camnang HTML for {camnang_slug}")

    qtext = parse_jlpt247(jlpt_html) if jlpt_html else {}
    qtext.update({k: v for k, v in load_jpnihon_questions(year, month).items() if k not in qtext})
    answers = parse_camnang(camnang_html)

    parts = [
        f"# JLPT N3 — {year}年{month_ja} 真題",
        "",
        f"> **試験**: {year}年{month_ja} 日本語能力試験 N3",
        "> **構成**: 言語知識（文字・語彙・文法）・読解・聴解",
        f"> **出典**: `{pdf_name}`（学習用途）",
        "",
        "---",
        "",
        "## 📁 META",
        "",
        "```yaml",
        "exam: JLPT N3",
        f"date: {year}-{mm}",
        f"source_pdf: {pdf_name}",
        f"audio: {audio}",
        "sections:",
        META_SECTIONS.rstrip(),
        "```",
        "",
        "---",
        "",
        "## 言語知識（文字・語彙・文法）",
        "",
        "---",
        "",
    ]

    for start, end, title, rubric in SECTION_RANGES:
        parts += [f"### {title}", "", f"> {rubric}", "", "---", ""]
        for n in range(start, end + 1):
            qid = f"Q{n}"
            ans = answers.get(qid, 1)
            if n in qtext:
                stem, opts = qtext[n]
                prob_label = title.split("｜", 1)[-1].strip() if "｜" in title else title
                parts.append(
                    q_block(qid, stem, opts, ans, section_label=prob_label, problem_title=title)
                )
            else:
                parts.append(q_block(qid, f"（{qid} — 原文はPDF参照）", [], ans))

    parts += [
        "## 聴解",
        "",
        f"> ⚠️ 聴解は音声が必要です（`{audio}`）。",
        "",
        "---",
        "",
    ]

    for l_start, l_end, title, has_choices in LISTENING_RANGES:
        parts += [f"### {title}", "", "---", ""]
        s, e = int(l_start[1:]), int(l_end[1:])
        if l_start == "L13":
            memo = ", ".join(f"L{n}={answers.get(f'L{n}', 1)}" for n in range(s, e + 1))
            parts += [f"*(参考答案: {memo})*", "", "---", ""]
            continue
        n_opts = 3 if l_start in ("L16", "L20") else 4
        for n in range(s, e + 1):
            lid = f"L{n}"
            parts.append(listening_block(lid, answers.get(lid, 1), has_choices, n_opts))

    parts.append(f"*© {year} 日本語能力試験 N3 真題（{year}年{month_ja}）— 学習用途のみ*")
    parts.append("")
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def _parse_exam_file():
    spec = importlib.util.spec_from_file_location("exam_loader", ROOT / "app" / "exam_loader.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_exam_file


def main() -> None:
    parse_exam_file = _parse_exam_file()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, int, int, int, int]] = []

    for year, month, jlpt_slug, camnang_slug, pdf_name, audio in EXAMS:
        label = f"JLPT_N3_{year}_{month:02d}.md"
        print(f"Building {label}...", file=sys.stderr)
        try:
            path = generate(year, month, jlpt_slug, camnang_slug, Path(pdf_name).name, audio)
        except Exception as e:
            print(f"  FAILED: {e}", file=sys.stderr)
            continue
        parsed = parse_exam_file(path)
        n_q = sum(1 for q in parsed["questions"] if q["display_id"].startswith("Q"))
        n_l = sum(1 for q in parsed["questions"] if q["display_id"].startswith("L"))
        n_jlpt = len(parse_jlpt247(
            (CACHE_DIR / f"jlpt247_{jlpt_slug}.html").read_text(encoding="utf-8")
            if (CACHE_DIR / f"jlpt247_{jlpt_slug}.html").is_file() else ""
        ))
        results.append((path.name, n_q, n_l, len(parsed["questions"]), n_jlpt))
        print(f"  → Q={n_q} L={n_l} jlpt247_stems={n_jlpt}", file=sys.stderr)

    print("\n=== Summary ===")
    for name, nq, nl, tot, stems in results:
        print(f"{name}: written={nq} listening={nl} parsed={tot} jlpt247_Q1-53={stems}")


if __name__ == "__main__":
    main()
