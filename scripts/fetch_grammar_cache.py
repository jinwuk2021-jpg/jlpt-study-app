#!/usr/bin/env python3
"""Fetch JLPTsensei grammar list pages and save to scripts/grammar_cache/."""

import ssl
import urllib.request
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

CACHE = Path(__file__).resolve().parent / "grammar_cache"
LEVELS = {
    "n5": {"url": "https://jlptsensei.com/jlpt-n5-grammar-list/", "pages": 3},
    "n4": {"url": "https://jlptsensei.com/jlpt-n4-grammar-list/", "pages": 4},
    "n3": {"url": "https://jlptsensei.com/jlpt-n3-grammar-list/", "pages": 5},
    "n2": {"url": "https://jlptsensei.com/jlpt-n2-grammar-list/", "pages": 5},
    "n1": {"url": "https://jlptsensei.com/jlpt-n1-grammar-list/", "pages": 7},
}


def fetch_page(url: str, page: int = 1) -> str:
    full = url if page == 1 else f"{url.rstrip('/')}/page/{page}/"
    req = urllib.request.Request(full, headers={"User-Agent": "Mozilla/5.0 JLPT-Study-App"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    for level, info in LEVELS.items():
        for page in range(1, info["pages"] + 1):
            html = fetch_page(info["url"], page)
            out = CACHE / f"{level}_p{page}.txt"
            out.write_text(html, encoding="utf-8")
            print(f"Saved {out.name} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
