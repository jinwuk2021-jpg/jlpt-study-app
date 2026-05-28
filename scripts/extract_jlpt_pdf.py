#!/usr/bin/env python3
"""
Render JLPT exam PDF pages to PNG for vision/OCR review.

Usage:
  python scripts/extract_jlpt_pdf.py /path/to/exam.pdf
  python scripts/extract_jlpt_pdf.py /path/to/exam.pdf --out data/exam/n2/_pdf_pages
"""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz  # PyMuPDF


def render_pdf(pdf_path: Path, out_dir: Path, scale: float = 2.0) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    paths: list[Path] = []
    matrix = fitz.Matrix(scale, scale)
    for i in range(doc.page_count):
        pix = doc[i].get_pixmap(matrix=matrix)
        dest = out_dir / f"page_{i + 1:02d}.png"
        pix.save(str(dest))
        paths.append(dest)
    doc.close()
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Render JLPT PDF pages to PNG")
    parser.add_argument("pdf", type=Path, help="Path to 真题.pdf")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: data/exam/<level>/_pdf_<stem>)",
    )
    parser.add_argument("--scale", type=float, default=2.0, help="Render scale")
    args = parser.parse_args()

    pdf_path = args.pdf.expanduser().resolve()
    if not pdf_path.is_file():
        raise SystemExit(f"PDF not found: {pdf_path}")

    if args.out:
        out_dir = args.out
    else:
        repo = Path(__file__).resolve().parents[1]
        out_dir = repo / "data" / "exam" / "_pdf" / pdf_path.stem

    paths = render_pdf(pdf_path, out_dir, scale=args.scale)
    print(f"Rendered {len(paths)} pages → {out_dir}")


if __name__ == "__main__":
    main()
