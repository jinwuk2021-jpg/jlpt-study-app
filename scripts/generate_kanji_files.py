#!/usr/bin/env python3
"""Generate full JLPT kanji markdown (N5–N1) from open datasets.

Sources:
  - AnchorI/jlpt-kanji-dictionary (jlpt-kanji.json)
  - Smallsan/jlpt_kanji_json_msgpack (kanji_jlpt_only.json)
  - kanjiapi.dev — compound words
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

from deep_translator import GoogleTranslator

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(__file__).resolve().parent / "kanji_cache"
OUT = ROOT / "data" / "kanji"
JLPT_JSON = CACHE / "jlpt-kanji.json"
KANJI_API_JSON = CACHE / "kanji_jlpt_only.json"
WORDS_CACHE = CACHE / "words"
TRANS_CACHE = CACHE / "translations_vi.json"
SOURCE_NOTE = "AnchorI/jlpt-kanji-dictionary, kanjiapi.dev"
FETCH_WORKERS = 12

LEVELS = ["N5", "N4", "N3", "N2", "N1"]
translator = GoogleTranslator(source="en", target="vi")
_meaning_cache: dict[str, str] = {}


def load_trans_cache() -> None:
    if TRANS_CACHE.exists():
        _meaning_cache.update(json.loads(TRANS_CACHE.read_text(encoding="utf-8")))


def save_trans_cache() -> None:
    TRANS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TRANS_CACHE.write_text(
        json.dumps(_meaning_cache, ensure_ascii=False),
        encoding="utf-8",
    )


def vi_meaning(text: str) -> str:
    text = (text or "").strip()
    if not text or text.startswith("ví dụ "):
        return text
    if text in _meaning_cache:
        return _meaning_cache[text]
    try:
        out = translator.translate(text)
    except Exception:
        out = text
    _meaning_cache[text] = out
    return out


def curl_json(url: str) -> object:
    proc = subprocess.run(
        ["curl", "-fsSL", "-A", "Mozilla/5.0 (JLPT study app)", url],
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def ensure_cache() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    WORDS_CACHE.mkdir(parents=True, exist_ok=True)
    if not JLPT_JSON.exists():
        subprocess.run(
            [
                "curl", "-fsSL", "-o", str(JLPT_JSON),
                "https://raw.githubusercontent.com/AnchorI/jlpt-kanji-dictionary/main/jlpt-kanji.json",
            ],
            check=True,
        )
    if not KANJI_API_JSON.exists():
        subprocess.run(
            [
                "curl", "-fsSL", "-o", str(KANJI_API_JSON),
                "https://raw.githubusercontent.com/Smallsan/jlpt_kanji_json_msgpack/main/kanji_jlpt_only.json",
            ],
            check=True,
        )


def load_jlpt_by_level() -> dict[str, list[dict]]:
    rows = json.loads(JLPT_JSON.read_text(encoding="utf-8"))
    by_level: dict[str, list[dict]] = {lv: [] for lv in LEVELS}
    for row in rows:
        lv = row.get("jlpt")
        if lv in by_level:
            by_level[lv].append(row)
    for lv in LEVELS:
        by_level[lv].sort(key=lambda r: (r.get("frequency") or 9999, r.get("kanji", "")))
    return by_level


def load_readings() -> dict[str, dict]:
    return json.loads(KANJI_API_JSON.read_text(encoding="utf-8"))


def fetch_words(character: str) -> list[dict]:
    cache_path = WORDS_CACHE / f"{ord(character):x}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    url = f"https://kanjiapi.dev/v1/words/{quote(character)}"
    try:
        data = curl_json(url)
    except subprocess.CalledProcessError:
        data = []
    cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def prefetch_words(characters: list[str]) -> None:
    missing = [c for c in characters if not (WORDS_CACHE / f"{ord(c):x}.json").exists()]
    if not missing:
        return
    print(f"  Fetching vocabulary for {len(missing)} kanji ({FETCH_WORKERS} workers)...", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        futures = {pool.submit(fetch_words, ch): ch for ch in missing}
        for fut in as_completed(futures):
            fut.result()
            done += 1
            if done % 50 == 0:
                print(f"    cached {done}/{len(missing)}", flush=True)
            time.sleep(0.02)


def pick_examples(character: str, words: list[dict], limit: int = 10) -> list[tuple[str, str, str]]:
    scored: list[tuple[int, str, str, str]] = []
    for entry in words:
        gloss = ""
        if entry.get("meanings"):
            gloss = entry["meanings"][0].get("glosses", [""])[0]
        for variant in entry.get("variants", []):
            written = variant.get("written") or ""
            if character not in written or len(written) > 10:
                continue
            reading = variant.get("pronounced") or ""
            pri = variant.get("priorities") or []
            score = len(pri) * 2
            if any(p.startswith(("ichi", "news", "spec", "gai")) for p in pri):
                score += 20
            if written == character:
                score -= 3
            scored.append((score, written, reading, gloss))

    seen: set[str] = set()
    result: list[tuple[str, str, str]] = []
    for score, written, reading, gloss in sorted(scored, reverse=True):
        if written in seen:
            continue
        seen.add(written)
        result.append((written, reading, gloss))
        if len(result) >= limit:
            break
    while len(result) < limit:
        n = len(result) + 1
        result.append((character, "", f"ví dụ {n}"))
    return result[:limit]


def format_readings(readings: list[str]) -> str:
    cleaned = []
    for r in readings or []:
        r = r.strip()
        if r:
            cleaned.append(r)
    return "、".join(cleaned) if cleaned else "—"


def kanji_vi_meaning(description: str, api_meanings: list[str]) -> str:
    if api_meanings:
        en = ", ".join(api_meanings[:4])
    else:
        m = re.search(r"means (.+?)\.", description or "")
        en = m.group(1) if m else (description or "")
    return vi_meaning(en)


def render_kanji_section(
    index: int,
    row: dict,
    api: dict | None,
    examples: list[tuple[str, str, str]],
) -> str:
    ch = row["kanji"]
    strokes = row.get("strokes") or (api or {}).get("stroke_count") or 10
    on_list = (api or {}).get("on_readings") or []
    kun_list = (api or {}).get("kun_readings") or []
    meaning_vi = kanji_vi_meaning(row.get("description", ""), (api or {}).get("meanings") or [])

    lines = [
        f"## {index}. {ch}",
        "",
        f"- **Từ kanji:** {ch}",
        f"- **Nghĩa:** {meaning_vi}",
        f"- **Số nét:** {strokes}",
        f"- **Cách đọc âm On:** {format_readings(on_list)}",
        f"- **Cách đọc âm Kun:** {format_readings(kun_list)}",
        "",
        "**10 từ mẫu ghép:**",
        "",
        "| STT | Từ ghép | Cách đọc | Nghĩa |",
        "|-----|---------|----------|-------|",
    ]
    for i, (word, reading, gloss) in enumerate(examples, 1):
        if gloss.startswith("ví dụ"):
            gloss_out = gloss
        elif gloss and len(gloss) < 120:
            gloss_out = vi_meaning(gloss)
        else:
            gloss_out = gloss or "—"
        lines.append(f"| {i} | {word} | {reading or '—'} | {gloss_out} |")
    return "\n".join(lines)


def write_level(level: str, items: list[dict], readings_db: dict[str, dict]) -> int:
    chars = [r["kanji"] for r in items]
    prefetch_words(chars)

    header = [
        f"# Kanji JLPT {level}",
        "",
        f"*Nguồn: {SOURCE_NOTE}*",
        "",
        "---",
        "",
    ]
    path = OUT / f"{level.lower()}.md"
    path.write_text("\n".join(header), encoding="utf-8")

    for i, row in enumerate(items, 1):
        ch = row["kanji"]
        api = readings_db.get(ch)
        words = fetch_words(ch)
        examples = pick_examples(ch, words)
        block = render_kanji_section(i, row, api, examples) + "\n\n---\n\n"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(block)
        if i % 25 == 0:
            save_trans_cache()
            print(f"  {level}: {i}/{len(items)} written", flush=True)

    save_trans_cache()
    return len(items)


def main() -> None:
    ensure_cache()
    load_trans_cache()
    by_level = load_jlpt_by_level()
    readings_db = load_readings()
    counts = {}
    for level in LEVELS:
        items = by_level[level]
        print(f"Generating {level} ({len(items)} kanji)...", flush=True)
        counts[level] = write_level(level, items, readings_db)
    print("Done:", counts)


if __name__ == "__main__":
    main()
