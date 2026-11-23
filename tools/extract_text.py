#!/usr/bin/env python3
"""Extract stable text + page offsets from stored originals.

Requires pypdf only for PDF extraction (see requirements-tools.txt). The
extracted text and page map are stored in the repository so `make build` and
`make test` never need a PDF library or the network.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from corpuslib import CORPUS_DIR, dump_json, sha256_file


def normalise(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00ad", "")  # soft hyphen
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip() + "\n"


def extract_pdf(path: Path) -> tuple[str, list[dict]]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    chunks: list[str] = []
    pages: list[dict] = []
    cursor = 0
    for idx, page in enumerate(reader.pages, 1):
        raw = page.extract_text() or ""
        chunk = normalise(raw) + "\n"
        start = cursor
        chunks.append(chunk)
        cursor += len(chunk)
        pages.append({"page": idx, "char_start": start, "char_end": cursor - 1})
    body = "".join(chunks)
    # Recompute offsets against the joined body (normalise per page already applied).
    cursor = 0
    for page in pages:
        page["char_start"] = cursor
        cursor += len(chunks[page["page"] - 1])
        page["char_end"] = cursor - 1
    return body, pages


def extract_html(path: Path) -> tuple[str, list[dict]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", raw)
    raw = re.sub(r"(?i)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?i)</(p|div|li|h[1-6]|tr|article)>", "\n", raw)
    text = re.sub(r"(?s)<[^>]+>", "", raw)
    text = html.unescape(text)
    body = normalise(text)
    return body, [{"page": 1, "char_start": 0, "char_end": len(body) - 1}]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("instrument_id")
    parser.add_argument("source", help="path relative to corpus/<id>/")
    parser.add_argument("--out", default="text/en.txt")
    parser.add_argument("--mode", choices=["pdf", "html"], default="pdf")
    args = parser.parse_args()

    base = CORPUS_DIR / args.instrument_id
    src = base / args.source
    if not src.exists():
        raise SystemExit(f"missing source: {src}")
    if args.mode == "pdf":
        body, pages = extract_pdf(src)
    else:
        body, pages = extract_html(src)
    out = base / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    dump_json(base / "pages.json", {"pages": pages, "primary_text": args.out})
    print(f"{out.relative_to(CORPUS_DIR)}: {len(body)} chars, {len(pages)} page(s)")
    print(f"source sha256: {sha256_file(src)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
