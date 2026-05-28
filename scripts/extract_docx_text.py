#!/usr/bin/env python3
"""Extract plain text from .docx to stdout or file."""
from __future__ import annotations

import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    lines = []
    for para in root.iter(f"{NS}p"):
        texts = [t.text for t in para.iter(f"{NS}t") if t.text]
        if texts:
            lines.append("".join(texts))
    return "\n".join(lines)


if __name__ == "__main__":
    p = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    text = extract_docx(p)
    if out:
        out.write_text(text, encoding="utf-8")
        print(f"Wrote {out} ({len(text)} chars)")
    else:
        print(text)
