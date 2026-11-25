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
    r"(?m)^\s*(?:Article|ARTICLE)\s+(\d+(?:\.\d+)?(?:er)?)\s*(?:[–\-—:]\s*(.*?))?\s*$"
)
SECTION_RE = re.compile(r"(?m)^\s*(\d{1,2})\.\s+([A-Z][^\n]{3,90})$")
RES_PARA_RE = re.compile(r"(?m)^\s*(\d{1,3})\.\s+(?=\S)")
NUMBERED_RE = re.compile(r"(?m)^(\d{1,2}(?:\.\d{1,2})?)\.\s+(?=\S)")
ROMAN_SECTION_RE = re.compile(r"(?m)^(?:I|II|III|IV|V|VI|VII|VIII)\.\s*$")
PACT_TITLE_RE = re.compile(r"(?m)^  The Pact for the Future$")
PACT_SECTION_RE = re.compile(r"(?m)^  (I|II|III|IV|V)\. (.+)$")
PACT_PARA_RE = re.compile(r"(?m)^(\d{1,3})\.\s+(?=\S)")
PACT_ACTION_RE = re.compile(r"(?m)^Action (\d+)\s*\.\s+(?=\S)")


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


def _pact_units(
    body: str, start: int, end: int, prefix: str, kind: str
) -> list[dict]:
    """Split one Pact section/annex range at numbered paragraphs and actions."""
    anchors: list[tuple[int, str, str]] = []
    anchors += [
        (m.start(), "paragraph", m.group(1))
        for m in PACT_PARA_RE.finditer(body, start, end)
    ]
    anchors += [
        (m.start(), "action", m.group(1))
        for m in PACT_ACTION_RE.finditer(body, start, end)
    ]
    anchors.sort(key=lambda item: item[0])
    boundaries = [start] + [item[0] for item in anchors if item[0] > start]
    # A heading/title immediately before the first paragraph belongs to that
    # paragraph, not to a separate heading-only unit.
    if len(boundaries) > 1 and anchors and boundaries[1] == anchors[0][0] and anchors[0][0] > start:
        boundaries = [start] + [item[0] for item in anchors[1:]]
    units: list[dict] = []
    for idx, unit_start in enumerate(boundaries):
        unit_end = boundaries[idx + 1] if idx + 1 < len(boundaries) else end
        raw = body[unit_start:unit_end]
        text = raw.strip("\n")
        if not text:
            continue
        offset = unit_start + len(raw) - len(raw.lstrip("\n"))
        if idx == 0:
            first = next((item for item in anchors if item[0] >= unit_start), None)
        else:
            first = next((item for item in anchors if item[0] == unit_start), None)
        if first is None:
            label = prefix
            unit_kind = kind
        elif first[1] == "action":
            label = f"{prefix}, Action {first[2]}"
            unit_kind = "action"
        else:
            label = f"{prefix}, para. {first[2]}"
            unit_kind = kind if idx == 0 else "paragraph"
        units.append(
            {
                "unit_id": "",
                "instrument_id": "",
                "kind": unit_kind,
                "label": label,
                "text": text,
                "char_start": offset,
                "char_end": offset + len(text),
            }
        )
    return units


def segment_pact(body: str) -> list[dict]:
    """Segment A/RES/79/1 by Pact section, annex, paragraph and action."""
    title = PACT_TITLE_RE.search(body)
    annex_i = body.find("  Annex I\n  Global Digital Compact")
    annex_ii = body.find("  Annex II\n  Declaration on Future Generations")
    if title is None or annex_i < 0 or annex_ii < 0:
        raise SystemExit("Pact structure not found (title, Annex I or Annex II)")
    sections = list(PACT_SECTION_RE.finditer(body, title.end(), annex_i))
    if not sections:
        raise SystemExit("Pact sections not found")

    units: list[dict] = []
    units += _pact_units(
        body, 0, title.start(), "Resolution front matter (A/RES/79/1)", "front_matter"
    )
    units += _pact_units(
        body, title.start(), sections[0].start(), "Pact for the Future — Preamble", "preamble"
    )
    for idx, section in enumerate(sections):
        section_end = sections[idx + 1].start() if idx + 1 < len(sections) else annex_i
        prefix = f"Pact for the Future — Section {section.group(1)}: {section.group(2).strip()}"
        units += _pact_units(body, section.start(), section_end, prefix, "section")

    units += _pact_units(body, annex_i, annex_ii, "Global Digital Compact — Annex I", "annex")
    declaration_first = PACT_PARA_RE.search(body, annex_ii)
    if declaration_first is None:
        raise SystemExit("Declaration on Future Generations paragraphs not found")
    units += _pact_units(
        body,
        annex_ii,
        declaration_first.start(),
        "Declaration on Future Generations — Annex II, Preamble",
        "preamble",
    )
    units += _pact_units(
        body,
        declaration_first.start(),
        len(body),
        "Declaration on Future Generations — Annex II",
        "annex",
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
        first_section = ROMAN_SECTION_RE.search(body)

        def numbered_label(match: re.Match) -> str:
            # Numbered clauses before the first Roman-numbered section are the
            # adopting act's operative clauses, not the instrument's paragraphs.
            if first_section is not None and match.start() < first_section.start():
                return f"Adoption clause {match.group(1)}"
            return f"Paragraph {match.group(1)}"

        return units_from_matches(
            body, matches, numbered_label, "numbered_paragraph"
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
    if mode == "pact":
        return segment_pact(body)
    raise SystemExit(f"unknown mode {mode}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("instrument_id")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["treaty", "resolution", "sections", "numbered", "whole", "pact"],
    )
    parser.add_argument("--text", default="text/en.txt")
    parser.add_argument("--pages", default="pages.json")
    parser.add_argument("--output", default="units.jsonl")
    args = parser.parse_args()

    base = CORPUS_DIR / args.instrument_id
    body = (base / args.text).read_text(encoding="utf-8")
    pages = json.loads((base / args.pages).read_text(encoding="utf-8"))["pages"]
    units = segment(body, args.mode)
    with (base / args.output).open("w", encoding="utf-8") as fh:
        for idx, unit in enumerate(units, 1):
            unit["unit_id"] = f"{args.instrument_id}-u{idx:04d}"
            unit["instrument_id"] = args.instrument_id
            unit["page_start"] = page_for(pages, unit["char_start"])
            unit["page_end"] = page_for(pages, max(unit["char_start"], unit["char_end"] - 1))
            fh.write(json.dumps(unit, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"{len(units)} unit(s) written to corpus/{args.instrument_id}/{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
