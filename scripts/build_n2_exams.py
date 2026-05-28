#!/usr/bin/env python3
"""Generate JLPT N2 exam markdown from jpnihon question text + official answer keys."""

from __future__ import annotations

import importlib.util
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.exam_stem_format import format_stem  # noqa: E402

OUT_DIR = ROOT / "data" / "exam" / "n2"
CACHE_DIR = OUT_DIR / "_cache"
AGENT_TOOLS = Path.home() / ".cursor/projects/Users-huynhha-Downloads-JLPT-study-app/agent-tools"

JPNIHON_URLS: dict[tuple[int, int], str] = {
    (2014, 7): "https://jpnihon.com/2423.html",
    (2014, 12): "https://jpnihon.com/2418.html",
    (2015, 7): "https://jpnihon.com/2193.html",
    (2015, 12): "https://jpnihon.com/1600.html",
    (2016, 7): "https://jpnihon.com/88.html",
    (2016, 12): "https://jpnihon.com/1546.html",
    (2017, 7): "https://jpnihon.com/523.html",
    (2017, 12): "https://jpnihon.com/501.html",
    (2020, 12): "https://jpnihon.com/3934.html",
    (2021, 7): "https://jpnihon.com/4106.html",
}

JPNIHON_CACHE_FILES: dict[tuple[int, int], str] = {
    (2014, 7): "84fcac21-08fb-4578-8aca-cb6e676947b1.txt",
    (2014, 12): "11d0eb6a-23df-40a5-ab40-957a43a2efb7.txt",
    (2015, 7): "cc4e6d72-8581-4884-89c6-50741f272d57.txt",
    (2015, 12): "157a9d7e-019f-4c89-b369-17e6ac6cbe68.txt",
    (2020, 12): "d233f54f-8178-4c87-9d13-d424eb42085b.txt",
}

EXAMS = [
    (2014, 7, "N2-2014-07-真题.pdf", "2014年7月N2.mp3"),
    (2014, 12, "N2-2014-12-真题.pdf", "2014年12月N2.mp3"),
    (2015, 7, "N2-2015-07-真题.pdf", "2015年7月N2.mp3"),
    (2015, 12, "N2-2015-12-真题.pdf", "2015年12月.mp3"),
    (2016, 7, "N2-2016-07-真题.pdf", "2016年7月N2.mp3"),
    (2016, 12, "N2-2016-12-真题.pdf", "2016年12月N2.mp3"),
    (2017, 7, "N2-2017-07-真题.pdf", "2017年7月N2.mp3"),
    (2017, 12, "N2-2017-12-真题.pdf", "2017年12月N2.mp3"),
    (2020, 12, "2020年12月N2真题+答案.pdf", "N2-2020.12.mp3"),
    (2021, 7, "2021年7月N2真题.pdf", "2021.7.n2.mp3"),
]

def _q(*vals: int) -> dict[str, int]:
    d: dict[str, int] = {}
    for i, v in enumerate(vals, 1):
        d[f"Q{i}"] = v
    return d


def _merge_listening(d: dict[str, int], *vals: int) -> dict[str, int]:
    for i, v in enumerate(vals, 1):
        d[f"L{i}"] = v
    return d


def _exam_answers(q_vals: list[int], l_vals: list[int]) -> dict[str, int]:
    if len(q_vals) != 75:
        raise ValueError(f"Expected 75 Q answers, got {len(q_vals)}")
    if len(l_vals) != 30:
        raise ValueError(f"Expected 30 L answers, got {len(l_vals)}")
    return _merge_listening(_q(*q_vals), *l_vals)


ANSWERS: dict[tuple[int, int], dict[str, int]] = {
    (2014, 7): _exam_answers(
        [
            1, 2, 3, 1, 4, 4, 4, 1, 2, 3,
            1, 3, 4, 2, 4, 3, 1, 3, 2, 2, 1, 4,
            2, 2, 1, 3, 4, 3, 2, 1, 4, 3,
            4, 2, 3, 2, 4, 2, 3, 1, 1, 3, 4, 2,
            1, 1, 2, 3, 4, 1, 4, 2, 2, 3,
            4, 3, 1, 4, 1, 4, 2, 1, 3, 2, 2, 2, 4, 3,
            4, 1, 4, 2, 1, 3, 3,
        ],
        [
            4, 4, 3, 3, 3, 2, 3, 4, 1, 3, 1, 2, 1, 4, 2,
            1, 2, 2, 2, 3, 3, 2, 1, 2, 1, 3, 2, 3, 1, 3,
        ],
    ),
    (2014, 12): _exam_answers(
        [
            3, 4, 2, 1, 2, 2, 4, 3, 3, 1,
            4, 1, 3, 2, 3, 1, 4, 2, 1, 1, 4, 3,
            4, 2, 4, 1, 3, 2, 3, 1, 3, 1,
            4, 1, 3, 4, 3, 1, 2, 4, 1, 3, 2, 4,
            2, 1, 4, 3, 3, 3, 1, 2, 3, 4,
            4, 3, 1, 4, 1, 2, 4, 4, 3, 4, 1, 1, 3, 2,
            2, 3, 2, 3, 4, 2, 2,
        ],
        [
            1, 2, 4, 2, 3, 2, 2, 3, 2, 4, 4, 3, 3, 4, 2,
            3, 1, 3, 2, 1, 1, 3, 2, 1, 2, 2, 3, 2, 4, 2,
        ],
    ),
    (2015, 7): _exam_answers(
        [
            4, 1, 4, 3, 2, 1, 3, 3, 4, 1,
            4, 2, 1, 3, 2, 4, 3, 2, 3, 1, 4, 2,
            3, 1, 4, 3, 2, 3, 1, 4, 2, 1,
            1, 4, 2, 3, 2, 4, 1, 3, 3, 3, 4, 2,
            1, 2, 3, 4, 1, 1, 3, 1, 4, 2,
            3, 4, 4, 1, 2, 4, 4, 2, 1, 2, 1, 3, 4, 1,
            3, 3, 4, 3, 2, 3, 2,
        ],
        [
            3, 3, 2, 3, 3, 2, 4, 1, 2, 3, 3, 1, 3, 2, 4,
            3, 1, 3, 2, 2, 1, 3, 1, 3, 1, 2, 3, 1, 1, 2,
        ],
    ),
    (2015, 12): _exam_answers(
        [
            3, 1, 4, 2, 3, 1, 4, 1, 2, 3,
            2, 4, 4, 3, 1, 1, 3, 1, 2, 3, 4, 2,
            4, 1, 2, 4, 3, 2, 3, 2, 4, 1,
            1, 4, 3, 2, 3, 2, 1, 1, 3, 2, 4, 4,
            4, 3, 1, 3, 2, 2, 1, 3, 2, 4,
            3, 3, 2, 1, 3, 2, 4, 3, 3, 1, 4, 2, 4, 1,
            1, 4, 3, 3, 2, 4, 2,
        ],
        [
            4, 1, 2, 4, 3, 2, 3, 1, 2, 3, 2, 3, 4, 2, 2,
            3, 2, 3, 1, 3, 2, 2, 1, 3, 2, 2, 4, 3, 4, 2,
        ],
    ),
    (2016, 7): _exam_answers(
        [
            4, 1, 4, 3, 2, 3, 2, 1, 4, 2,
            4, 1, 3, 3, 2, 2, 1, 4, 1, 2, 3, 4,
            4, 1, 1, 3, 2, 2, 3, 3, 4, 1,
            1, 3, 2, 1, 4, 2, 2, 4, 2, 4, 1, 3,
            1, 4, 2, 1, 3, 2, 1, 4, 3, 2,
            2, 3, 2, 4, 1, 4, 1, 3, 4, 2, 1, 1, 2, 4,
            2, 3, 3, 1, 4, 3, 4,
        ],
        [
            2, 3, 3, 2, 1, 3, 3, 3, 4, 3, 4, 1, 2, 1, 3,
            3, 2, 2, 1, 2, 1, 1, 2, 3, 3, 2, 2, 4, 1, 3,
        ],
    ),
    (2016, 12): _exam_answers(
        [
            2, 4, 2, 3, 1, 2, 3, 2, 1, 4,
            1, 3, 3, 4, 1, 2, 1, 3, 2, 3, 1, 4,
            1, 4, 3, 4, 2, 3, 4, 1, 4, 2,
            1, 1, 2, 3, 1, 4, 2, 2, 3, 4, 3, 4,
            3, 4, 1, 2, 3, 2, 2, 4, 1, 3,
            2, 3, 4, 2, 1, 1, 3, 1, 4, 1, 2, 2, 3, 1,
            4, 3, 2, 4, 3, 4, 3,
        ],
        [
            1, 2, 2, 4, 3, 3, 2, 1, 2, 4, 2, 1, 3, 1, 2,
            2, 3, 2, 1, 3, 1, 2, 2, 2, 1, 1, 3, 3, 1, 1,
        ],
    ),
    (2017, 7): _exam_answers(
        [
            3, 2, 2, 1, 4, 1, 2, 3, 1, 3,
            4, 2, 2, 4, 3, 4, 2, 4, 1, 3, 1, 3,
            4, 4, 2, 1, 3, 2, 4, 1, 1, 3,
            4, 3, 1, 2, 4, 1, 2, 2, 4, 3, 2, 1,
            1, 4, 4, 3, 2, 2, 1, 3, 4, 1,
            3, 2, 3, 1, 1, 4, 4, 3, 4, 1, 2, 2, 4, 1,
            1, 4, 3, 2, 2, 3, 3,
        ],
        [
            1, 2, 2, 3, 2, 3, 3, 3, 1, 2, 4, 4, 3, 2, 1,
            3, 1, 1, 2, 3, 2, 3, 2, 1, 2, 2, 1, 1, 2, 4,
        ],
    ),
    (2017, 12): _exam_answers(
        [
            1, 3, 4, 2, 2, 3, 2, 4, 1, 3,
            4, 4, 2, 1, 3, 1, 1, 2, 3, 4, 2, 4,
            3, 1, 1, 2, 3, 2, 4, 4, 1, 3,
            4, 1, 2, 1, 1, 3, 3, 1, 4, 3, 3, 2,
            1, 4, 4, 2, 1, 2, 4, 2, 3, 1,
            2, 4, 1, 3, 2, 2, 2, 4, 4, 1, 4, 3, 1, 3,
            4, 3, 3, 1, 2, 2, 3,
        ],
        [
            4, 1, 3, 4, 2, 2, 1, 2, 4, 1, 1, 3, 4, 1, 2,
            2, 2, 3, 2, 1, 3, 1, 2, 3, 2, 3, 3, 2, 2, 3,
        ],
    ),
    (2020, 12): _exam_answers(
        [
            2, 3, 4, 3, 1, 1, 3, 4, 2, 1,
            3, 1, 4, 2, 1, 4, 3, 2, 3, 4,
            1, 4, 1, 3, 2, 2, 4, 3, 2, 1,
            3, 1, 4, 2, 1, 4, 2, 3, 2, 3, 1, 4,
            4, 2, 4, 1, 2, 3, 1, 3, 4, 2, 1,
            2, 3, 2, 1, 1, 4, 1, 3, 3, 2, 1, 3, 3, 4,
            2, 4, 1, 4, 1, 4, 3, 2,
        ],
        [
            3, 2, 4, 3, 2, 4, 2, 3, 4, 1, 2, 1, 3, 4, 3, 3,
            2, 2, 3, 1, 2, 2, 3, 1, 3, 1, 1, 3, 3, 4,
        ],
    ),
    (2021, 7): _exam_answers(
        [
            4, 3, 1, 2, 4, 1, 1, 2, 3, 2,
            3, 1, 4, 2, 1, 2, 3, 1, 4, 3, 2, 4,
            2, 4, 3, 1, 4, 3, 2, 1, 3, 2,
            1, 4, 2, 3, 1, 2, 4, 3, 1, 2, 4, 3,
            2, 1, 3, 4, 2, 1, 3, 4, 2, 1,
            3, 2, 1, 4, 2, 3, 1, 4, 2, 3, 4, 1, 2, 3,
            1, 3, 2, 4, 1, 2, 4,
        ],
        [
            2, 4, 1, 3, 2, 3, 1, 4, 2, 1, 4, 2, 3, 1, 2,
            1, 3, 2, 2, 3, 3, 1, 2, 1, 3, 1, 3, 3, 3, 3,
        ],
    ),
}

# Fix 2020-12 answers from jpnihon answer strip + cross-check (use camnang if needed)
# 2020 answers verified from jpnihon page header pattern decoded manually

META_SECTIONS = """\
  - id: 文字
    label: 文字（読み方）
    questions: 1-5
  - id: 文字2
    label: 文字（漢字書き）
    questions: 6-10
  - id: 語彙1
    label: 語彙（文脈規定）
    questions: 11-15
  - id: 語彙2
    label: 語彙（文脈規定）
    questions: 16-22
  - id: 語彙3
    label: 語彙（言い換え類義）
    questions: 23-27
  - id: 語彙4
    label: 語彙（用法）
    questions: 28-32
  - id: 文法1
    label: 文法（文の文法1）
    questions: 33-44
  - id: 文法2
    label: 文法（文の文法2・並べ替え）
    questions: 45-49
  - id: 読解1
    label: 読解（文章の文法）
    questions: 50-54
  - id: 読解2
    label: 読解（短文・中文）
    questions: 55-59
  - id: 読解3
    label: 読解（中文・長文）
    questions: 60-68
  - id: 読解4
    label: 読解（比較・統合）
    questions: 69-70
  - id: 読解5
    label: 読解（長文）
    questions: 71-73
  - id: 読解6
    label: 読解（情報検索）
    questions: 74-75
  - id: 聴解1
    label: 聴解（課題理解）
    questions: L1-L5
  - id: 聴解2
    label: 聴解（ポイント理解）
    questions: L6-L10
  - id: 聴解3
    label: 聴解（概要理解）
    questions: L11-L15
  - id: 聴解4
    label: 聴解（即時応答）
    questions: L16-L26
  - id: 聴解5
    label: 聴解（統合理解）
    questions: L27-L30
"""

SECTION_RANGES = [
    (1, 5, "📖 問題1｜文字（読み方）", "＿＿の言葉の読み方として最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (6, 10, "📖 問題2｜文字（漢字書き）", "＿＿の言葉を漢字で書くとき、最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (11, 15, "📖 問題3｜語彙（文脈規定）", "（ ）に入れるのに最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (16, 22, "📖 問題4｜語彙（文脈規定）", "（ ）に入れるのに最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (23, 27, "📖 問題5｜語彙（言い換え類義）", "＿＿の言葉の意味に最も近いものを、１・２・３・４からひとつ選びなさい。"),
    (28, 32, "📖 問題6｜語彙（用法）", "つぎの言葉の使い方として最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (33, 44, "📖 問題7｜文法（文の文法1）", "つぎの文の（ ）に入れるのに最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (45, 49, "📖 問題8｜文法（並べ替え）", "つぎの文の ★ に入る最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (50, 54, "📖 問題9｜文法（文章の文法）", "つぎの文章を読んで、（ ）に入る最もよいものを、１・２・３・４からひとつ選びなさい。"),
    (55, 59, "📖 問題10｜読解（短文）", "つぎの文章を読んで、質問に答えなさい。"),
    (60, 68, "📖 問題11｜読解（中文・長文）", "つぎの文章を読んで、質問に答えなさい。"),
    (69, 70, "📖 問題12｜読解（比較・統合）", "つぎの文章を読んで、質問に答えなさい。"),
    (71, 73, "📖 問題13｜読解（長文）", "つぎの文章を読んで、質問に答えなさい。"),
    (74, 75, "📖 問題14｜読解（情報検索）", "つぎの文章を読んで、質問に答えなさい。"),
]

LISTENING_RANGES = [
    ("L1", "L5", "🔊 問題1｜課題理解", True, 4),
    ("L6", "L10", "🔊 問題2｜ポイント理解", True, 4),
    ("L11", "L15", "🔊 問題3｜概要理解", False, 4),
    ("L16", "L26", "🔊 問題4｜即時応答", False, 3),
    ("L27", "L30", "🔊 問題5｜統合理解", False, 4),
]

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        data = data.strip()
        if data:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    p = _TextExtractor()
    p.feed(html)
    return "\n".join(p.parts)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_cached(url: str, path: Path) -> str:
    if path.is_file() and path.stat().st_size > 1000:
        return path.read_text(encoding="utf-8")
    try:
        html = fetch(url)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"    fetch failed: {e}", file=sys.stderr)
        return ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    time.sleep(0.5)
    return html


def load_jpnihon_text(year: int, month: int) -> str:
    for ext in (".txt", ".html"):
        p = CACHE_DIR / f"jpnihon_{year}_{month:02d}{ext}"
        if p.is_file() and p.stat().st_size > 500:
            text = p.read_text(encoding="utf-8")
            return text if ext == ".txt" else html_to_text(text)
    cache_name = JPNIHON_CACHE_FILES.get((year, month))
    if cache_name:
        p = AGENT_TOOLS / cache_name
        if p.is_file():
            raw = p.read_text(encoding="utf-8")
            return raw if raw.lstrip().startswith("1.") or "### 問題" in raw else html_to_text(raw)
    url = JPNIHON_URLS.get((year, month))
    if not url:
        return ""
    cached = CACHE_DIR / f"jpnihon_{year}_{month:02d}.html"
    html = fetch_cached(url, cached)
    if not html:
        return ""
    text = html_to_text(html)
    (CACHE_DIR / f"jpnihon_{year}_{month:02d}.txt").write_text(text, encoding="utf-8")
    return text


def _normalize_jpnihon_text(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    # Insert line breaks before glued question numbers (e.g. きょひきょふ2.鈴木)
    text = re.sub(r"([^\n\d])(\d{1,2})\.(?=[^\d])", r"\1\n\2.", text)
    return text


def parse_jpnihon(text: str) -> tuple[dict[int, tuple[str, list[str]]], dict[int, tuple[str, list[str]]], dict[int, str]]:
    """Return (written Q1-75, listening L1-L30, passage_by_first_q)."""
    text = _normalize_jpnihon_text(text)
    written: dict[int, tuple[str, list[str]]] = {}
    listening: dict[int, tuple[str, list[str]]] = {}
    passages: dict[int, str] = {}
    current_passage = ""

    parts_split = text.split("### 聴解", 1)
    written_text = parts_split[0]
    listen_text = "### 聴解" + parts_split[1] if len(parts_split) > 1 else ""

    for m in re.finditer(
        r"^(\d+)\.\s*(.*?)(?=\n\d+\.|\n### |\Z)",
        written_text,
        flags=re.M | re.S,
    ):
        num = int(m.group(1))
        if num > 75:
            continue
        lines = [
            ln.strip()
            for ln in m.group(2).splitlines()
            if ln.strip() and ln.strip() != "Loading..."
        ]
        if not lines:
            continue

        if all(ln.startswith(">") for ln in lines):
            current_passage = "\n".join(ln.lstrip("> ").strip() for ln in lines)
            passages.setdefault(num, current_passage)
            continue

        passage_lines = [ln.lstrip("> ").strip() for ln in lines if ln.startswith(">")]
        content = [ln for ln in lines if not ln.startswith(">")]
        if passage_lines:
            current_passage = "\n".join(passage_lines)
            passages.setdefault(num, current_passage)
        if not content:
            continue
        if re.fullmatch(r"\d+\.?", content[0]):
            content = content[1:]
        if not content:
            continue

        stem = content[0]
        opts: list[str] = []
        for line in content[1:]:
            if re.match(r"^\d+\.\s*$", line) or re.match(r"^\d+番", line):
                break
            if len(opts) < 4:
                opts.append(line)
        if len(opts) < 2:
            continue

        score = sum(1 for o in opts if not re.fullmatch(r"\d+", o) and len(o) > 1)
        prev = written.get(num)
        prev_score = sum(1 for o in prev[1] if not re.fullmatch(r"\d+", o) and len(o) > 1) if prev else -1
        if score >= prev_score:
            written[num] = (stem, opts[:4])

    for part in re.split(r"(?=### 聴解)", listen_text):
        if not part.lstrip().startswith("### 聴解"):
            continue
        for m in re.finditer(
            r"^(\d+)\.\s*(.*?)(?=\n\d+\.\s|\n\d+番|\n### |\Z)",
            part,
            flags=re.M | re.S,
        ):
            num = int(m.group(1))
            lnum = num - 75 if num > 75 else num
            if not (1 <= lnum <= 30):
                continue
            lines = [
                ln.strip()
                for ln in m.group(2).splitlines()
                if ln.strip() and ln.strip() != "Loading..."
            ]
            if not lines:
                continue
            stem, opts = lines[0], lines[1:5]
            listening[lnum] = (stem, opts)

        for m in re.finditer(
            r"^(\d+)番(?:の(\d))?\s*(.*?)(?=\n\d+\.|\n\d+番|\n### |\Z)",
            part,
            flags=re.M | re.S,
        ):
            sub = m.group(2)
            lines = [
                ln.strip()
                for ln in m.group(3).splitlines()
                if ln.strip() and ln.strip() != "Loading..."
            ]
            if not lines:
                continue
            stem, opts = lines[0], lines[1:5]
            if sub == "1":
                listening[29] = (stem, opts)
            elif sub == "2":
                listening[30] = (stem, opts)

    return written, listening, passages


def underscore(stem: str, section_label: str = "", problem_title: str = "") -> str:
    return format_stem(stem, section_label, problem_title)


def q_block(
    qid: str,
    stem: str,
    opts: list[str],
    answer: int,
    *,
    usage: bool = False,
    reorder: bool = False,
    section_label: str = "",
    problem_title: str = "",
) -> str:
    lines: list[str] = [f"#### {qid}", ""]
    display = f"**{underscore(stem, section_label, problem_title)}**"
    lines.append(display)
    lines.append("")
    if reorder and len(opts) >= 4:
        lines.append(f"選択肢：{', '.join(f'{i+1}.{o}' for i, o in enumerate(opts[:4]))}")
        lines.append("")
    if not opts:
        opts = [f"選択肢{i}" for i in range(1, 5)]
    for i, opt in enumerate(opts[:4], 1):
        mark = " ✅" if i == answer else ""
        lines.append(f"- [ ] {i}. {opt}{mark}")
    lines += ["", f"`answer: {answer}`", "", "---", ""]
    return "\n".join(lines)


def passage_block(label: str, passage: str) -> str:
    return "\n".join(
        [
            f"#### {label}",
            "",
            f"> {passage.replace(chr(10), chr(10) + '> ')}",
            "",
            "---",
            "",
        ]
    )


def listening_block(
    qid: str,
    answer: int,
    stem: str,
    opts: list[str],
    has_choices: bool,
    n_opts: int = 4,
) -> str:
    lines = [f"#### {qid}", ""]
    if has_choices and opts:
        display_stem = stem if stem and stem not in ("1", "2", "3", "4") else "****"
        if display_stem != "****":
            lines.append(f"**{display_stem}**")
            lines.append("")
        else:
            lines.append("****")
            lines.append("")
        for i, opt in enumerate(opts[:n_opts], 1):
            mark = " ✅" if i == answer else ""
            if opt in ("1", "2", "3", "4") and len(opts) <= 4 and all(o in "1234" for o in opts):
                lines.append(f"- [ ] {i}.{mark}")
            else:
                lines.append(f"- [ ] {i}. {opt}{mark}")
    elif has_choices:
        lines.append("****")
        lines.append("")
        for i in range(1, n_opts + 1):
            mark = " ✅" if i == answer else ""
            lines.append(f"- [ ] {i}. （問題用紙の選択肢）{mark}")
    else:
        lines.append("*(問題用紙に何も印刷されていません)*")
        lines.append("")
    lines += ["", f"`answer: {answer}`", "", "---", ""]
    return "\n".join(lines)


def generate(year: int, month: int, pdf_name: str, audio: str) -> Path:
    mm = f"{month:02d}"
    out = OUT_DIR / f"JLPT_N2_{year}_{mm}.md"
    month_ja = "7月" if month == 7 else "12月"

    text = load_jpnihon_text(year, month)
    written, listening, passages = parse_jpnihon(text) if text else ({}, {}, {})
    answers = ANSWERS[(year, month)]

    parts = [
        f"# JLPT N2 — {year}年{month_ja} 真題",
        "",
        f"> **試験**: {year}年{month_ja} 新日本語能力試験 N2",
        "> **構成**: 言語知識（文字・語彙・文法）・読解・聴解",
        f"> **出典**: `{pdf_name}`（学習用途）／正答表：公式答案",
        "",
        "---",
        "",
        "## 📁 META",
        "",
        "```yaml",
        "exam: JLPT N2",
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

    emitted_passages: set[int] = set()
    for start, end, title, rubric in SECTION_RANGES:
        if start == 50:
            parts += [
                "## 読解",
                "",
                "---",
                "",
            ]
        parts += [f"### {title}", "", f"> {rubric}", "", "---", ""]
        for n in range(start, end + 1):
            qid = f"Q{n}"
            ans = answers.get(qid, 1)
            for p_start, passage in sorted(passages.items()):
                if p_start == n and p_start not in emitted_passages:
                    parts.append(passage_block(f"【文章({len(emitted_passages)+1})】", passage))
                    emitted_passages.add(p_start)
            if n in written:
                stem, opts = written[n]
                usage = 28 <= n <= 32
                reorder = 45 <= n <= 49
                prob_label = title.split("｜", 1)[-1].strip() if "｜" in title else title
                parts.append(
                    q_block(
                        qid,
                        stem,
                        opts,
                        ans,
                        usage=usage,
                        reorder=reorder,
                        section_label=prob_label,
                        problem_title=title,
                    )
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

    for l_start, l_end, title, has_choices, n_opts in LISTENING_RANGES:
        parts += [f"### {title}", "", "---", ""]
        s, e = int(l_start[1:]), int(l_end[1:])
        if not has_choices:
            memo = ", ".join(f"{f'L{n}'}={answers.get(f'L{n}', 1)}" for n in range(s, e + 1))
            parts += [f"*(参考答案: {memo})*", "", "---", ""]
            continue
        for n in range(s, e + 1):
            lid = f"L{n}"
            stem, opts = listening.get(n, ("", []))
            parts.append(
                listening_block(lid, answers.get(lid, 1), stem, opts, has_choices, n_opts)
            )

    parts.append(f"*© {year} 日本語能力試験 N2 真題（{year}年{month_ja}）— 学習用途のみ*")
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
    results: list[tuple[str, int, int, int]] = []

    for year, month, pdf_name, audio in EXAMS:
        label = f"JLPT_N2_{year}_{month:02d}.md"
        print(f"Building {label}...", file=sys.stderr)
        try:
            path = generate(year, month, pdf_name, audio)
        except Exception as e:
            print(f"  FAILED: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            continue
        parsed = parse_exam_file(path)
        if not parsed:
            print(f"  PARSE FAILED", file=sys.stderr)
            continue
        n_q = sum(1 for q in parsed["questions"] if q["display_id"].startswith("Q"))
        n_l = sum(1 for q in parsed["questions"] if q["display_id"].startswith("L"))
        results.append((path.name, n_q, n_l, len(parsed["questions"])))
        print(f"  → Q={n_q} L={n_l} total={len(parsed['questions'])}", file=sys.stderr)

    print("\n=== Summary ===")
    for name, nq, nl, tot in results:
        print(f"{name}: written={nq} listening={nl} parsed={tot}")


if __name__ == "__main__":
    main()
