#!/usr/bin/env python3
"""Segment an extracted text into citable units with page and character anchors.

Usage:
  python tools/segment.py <instrument-id> --mode treaty|resolution|sections|whole
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from corpuslib import CORPUS_DIR, dump_json

ARTICLE_RE = re.compile(
    r"(?m)^\s*(?:Article|ARTICLE)\s+(\d+(?:\.\d+)?)\s*(?:[–\-—:]\s*(.*?))?\s*$"
)
SECTION_RE = re.compile(r"(?m)^\s*(\d{1,2})\.\s+([A-Z][^\n]{3,90})$")
RES_PARA_RE = re.compile(r"(?m)^\s*(\d{1,3})\.\s+(?=\S)")
NUMBERED_RE = re.compile(r"(?m)^\s*(\d{1,2}(?:\.\d{1,2})?)\.\s+(?=\S)")


def page_for(pages: list[dict], offset: int) -> int:
    for page in pages:
        if page["char_start"] <= offset <= page["char_end"]:
            return page["page"]
    return len(pages) if pages else 1


def units_from_matches(body: str, matches: list[re.Match], label_fn, kind: str) -> list[dict]:
    units = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        text = body[start:end].strip("\n")
        if not text:
            continue
        offset = body.index(text, start)
        label = label_fn(match)
        units.append(
            {
                "unit_id": "",
                "instrument_id": "",
                "kind": kind,
                "label": label,
                "text": text,
                "char_start": offset,
                "char_end": offset + len(text),
            }
        )
    return units


def segment(body: str, mode: str) -> list[dict]:
    if mode == "whole":
        return [
            {
                "unit_id": "",
                "instrument_id": "",
                "kind": "document",
                "label": "Full text",
                "text": body.strip("\n"),
                "char_start": body.index(body.strip("\n")),
                "char_end": body.index(body.strip("\n")) + len(body.strip("\n")),
            }
        ]
    if mode == "treaty":
        matches = list(ARTICLE_RE.finditer(body))
        return units_from_matches(
            body,
            matches,
            lambda m: (
                f"Article {m.group(1)} — {m.group(2)}"
                if m.group(2)
                else f"Article {m.group(1)}"
            ),
            "article",
        )
    if mode == "numbered":
        matches = list(NUMBERED_RE.finditer(body))
        return units_from_matches(
            body, matches, lambda m: f"Paragraph {m.group(1)}", "numbered_paragraph"
        )
    if mode == "resolution":
        matches = list(RES_PARA_RE.finditer(body))
        # Keep a preamble unit before the first operative paragraph.
        units: list[dict] = []
        if matches:
            preamble_end = matches[0].start()
            preamble = body[:preamble_end].strip("\n")
            if preamble:
                start = body.index(preamble)
                units.append(
                    {
                        "unit_id": "",
                        "instrument_id": "",
                        "kind": "preamble",
                        "label": "Preamble",
                        "text": preamble,
                        "char_start": start,
                        "char_end": start + len(preamble),
                    }
                )
        units += units_from_matches(
            body, matches, lambda m: f"Paragraph {m.group(1)}", "operative_paragraph"
        )
        return units
    if mode == "sections":
        matches = list(SECTION_RE.finditer(body))
        return units_from_matches(
            body, matches, lambda m: f"Section {m.group(1)} — {m.group(2)}", "section"
        )
    raise SystemExit(f"unknown mode {mode}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("instrument_id")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["treaty", "resolution", "sections", "numbered", "whole"],
    )
    parser.add_argument("--text", default="text/en.txt")
    args = parser.parse_args()

    base = CORPUS_DIR / args.instrument_id
    body = (base / args.text).read_text(encoding="utf-8")
    pages = json.loads((base / "pages.json").read_text(encoding="utf-8"))["pages"]
    units = segment(body, args.mode)
    with (base / "units.jsonl").open("w", encoding="utf-8") as fh:
        for idx, unit in enumerate(units, 1):
            unit["unit_id"] = f"{args.instrument_id}-u{idx:04d}"
            unit["instrument_id"] = args.instrument_id
            unit["page_start"] = page_for(pages, unit["char_start"])
            unit["page_end"] = page_for(pages, max(unit["char_start"], unit["char_end"] - 1))
            fh.write(json.dumps(unit, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"{len(units)} unit(s) written to corpus/{args.instrument_id}/units.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
