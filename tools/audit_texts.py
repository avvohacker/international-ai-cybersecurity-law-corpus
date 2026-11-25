#!/usr/bin/env python3
"""Audit which catalogue records have a stored full text.

The audit is offline and reads only ``catalog/instruments/*.json``. It exists to
distinguish four different reasons why a record may have no stored text:

* the official text is located at the cited source but the record is
  metadata-only;
* the text is a paywalled standard;
* only an official summary is published;
* the record is internal law, not an international instrument.

Usage:
  python3 tools/audit_texts.py
  python3 tools/audit_texts.py --json --output build/text-availability-audit.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from corpuslib import CATALOG_DIR, dump_json

PAYWALLED = {
    "iso-iec-22989-2022",
    "iso-iec-23053-2022",
    "iso-iec-23894-2023",
    "iso-iec-42001-2023",
    "iso-iec-42006-2025",
}
SUMMARY_ONLY = {
    "nato-ai-strategy-2024",
    "us-uk-ai-safety-mou-2024",
}
INTERNAL_LAW = {
    "eu-ai-act",
    "eu-cyber-resilience-act-2024",
    "eu-nis2-directive-2022",
}


def classify(inst: dict[str, Any]) -> tuple[str, str]:
    """Return the availability class and a short reason for one record."""
    iid = inst["id"]
    if (inst.get("text") or {}).get("full_text"):
        return "stored", "Full text stored and segmented."
    if iid in PAYWALLED:
        return "paywalled", "ISO/IEC standard sold by the standards body; not stored."
    if iid in SUMMARY_ONLY:
        return "summary_only", "Only an official summary is public; no full instrument text."
    if iid in INTERNAL_LAW:
        return (
            "internal_law",
            "Official text on EUR-Lex; record is internal law, not an international instrument.",
        )
    return "official_text_located", "Official text located at the cited source; record is metadata-only."


def first_official_source(inst: dict[str, Any]) -> tuple[str | None, str | None]:
    for kind in ("official_primary", "official_journal", "official_secondary", "registry"):
        for source in inst.get("sources", []):
            if source.get("kind") == kind:
                return source.get("url"), kind
    return None, None


def audit() -> dict[str, Any]:
    records = []
    for path in sorted(CATALOG_DIR.glob("*.json")):
        inst = json.loads(path.read_text(encoding="utf-8"))
        availability, reason = classify(inst)
        source, source_kind = first_official_source(inst)
        records.append(
            {
                "id": inst["id"],
                "title": inst["title"].get("short") or inst["title"].get("official"),
                "binding_status": inst.get("binding_status"),
                "category": inst.get("category"),
                "availability": availability,
                "reason": reason,
                "official_source": source,
                "official_source_kind": source_kind,
            }
        )
    counts = Counter(row["availability"] for row in records)
    return {
        "total": len(records),
        "summary": {
            "stored": counts["stored"],
            "official_text_located": counts["official_text_located"],
            "paywalled": counts["paywalled"],
            "summary_only": counts["summary_only"],
            "internal_law": counts["internal_law"],
        },
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON")
    parser.add_argument("--output", type=Path, help="write JSON to this path")
    args = parser.parse_args()

    data = audit()
    if args.output:
        dump_json(args.output, data)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            "total={total} stored={stored} official_text_located={official_text_located} "
            "paywalled={paywalled} summary_only={summary_only} internal_law={internal_law}".format(
                **data["summary"], total=data["total"]
            )
        )
        for row in data["records"]:
            if row["availability"] == "official_text_located":
                print(f"located  {row['id']}  {row['official_source']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
