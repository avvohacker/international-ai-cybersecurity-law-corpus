#!/usr/bin/env python3
"""Audit the external links cited by the long-form international AI law account.

The account is documentation, not a catalogue record, so its citations are not
covered by ``audit_sources.py --scope catalog``. This small runner extracts the
unique HTTP(S) URLs from the Markdown, reuses the same classifier and probe as
the catalogue audits, and writes a dated report.

Usage:
    python3 tools/audit_doc_links.py
    python3 tools/audit_doc_links.py --workers 8 --output build/doc-link-audit.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import audit_sources  # noqa: E402

DEFAULT_DOC = ROOT / "docs" / "international-ai-law.md"
DEFAULT_OUTPUT = ROOT / "build" / "doc-link-audit.json"
DOC_ID = "doc-international-ai-law"
URL_RE = re.compile(r"https?://[^\s<>)\]]+")
TRAILING_PUNCTUATION = ".,;:"


def extract_urls(text: str) -> list[str]:
    """Return the unique external URLs in a Markdown document, sorted."""
    found = {
        match.group(0).rstrip(TRAILING_PUNCTUATION).strip()
        for match in URL_RE.finditer(text)
    }
    return sorted(url for url in found if url)


def targets(doc: Path) -> list[audit_sources.Target]:
    urls = extract_urls(doc.read_text(encoding="utf-8"))
    return [
        audit_sources.Target(
            instrument_id=DOC_ID,
            source_id=f"url-{index:02d}",
            label=urlsplit(url).hostname or url,
            url=url,
        )
        for index, url in enumerate(urls, start=1)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--workers", type=int, default=8, help="parallel probes (default 8)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="exit 1 when an anti-bot block is found, not only a broken link",
    )
    args = parser.parse_args(argv)

    selected = targets(args.doc)
    if args.workers > 1:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(lambda target: audit_sources.probe(target, args.timeout), selected))
    else:
        results = [audit_sources.probe(target, args.timeout) for target in selected]

    summary = Counter(result.outcome for result in results)
    entries = [audit_sources.annotate_result(result) for result in results]
    payload = {
        "checked": len(results),
        "audited_on": date.today().isoformat(),
        "scope": "doc",
        "document": str(args.doc.relative_to(ROOT)) if args.doc.is_relative_to(ROOT) else str(args.doc),
        "summary": {
            key: summary.get(key, 0)
            for key in ("ok", "anti_bot", "broken", "transient")
        },
        "results": entries,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Document link audit: {payload['checked']} external links in {payload['document']}")
        marks = {"ok": "OK", "anti_bot": "BLOCKED", "broken": "BROKEN", "transient": "RETRY"}
        for result in results:
            print(f"  [{marks[result.outcome]:7}] {result.status or '-'}  {result.url}")
            if result.outcome != "ok":
                print(f"            {result.reason}")
        print("Summary: " + ", ".join(f"{key}={value}" for key, value in payload["summary"].items()))

    if summary.get("broken", 0):
        return 1
    if args.fail_on_blocked and summary.get("anti_bot", 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
