#!/usr/bin/env python3
"""Write corpus/<id>/manifest.json from the files actually present.

The manifest is the integrity contract checked by `make validate`. Source
hashes come from catalog/acquisitions.json so that a manifest cannot silently
bless altered bytes.
"""

from __future__ import annotations

import json
from pathlib import Path

from corpuslib import CATALOG_DIR, CORPUS_DIR, ROOT, dump_json, sha256_file

LOCK = ROOT / "catalog" / "acquisitions.json"


def main() -> int:
    acquisitions = {}
    if LOCK.exists():
        for entry in json.loads(LOCK.read_text(encoding="utf-8")):
            acquisitions.setdefault(entry["instrument_id"], []).append(entry)

    count = 0
    for inst_path in sorted(CATALOG_DIR.glob("*.json")):
        inst = json.loads(inst_path.read_text(encoding="utf-8"))
        iid = inst["id"]
        base = CORPUS_DIR / iid
        if not base.exists():
            continue
        files = []
        for entry in sorted(acquisitions.get(iid, []), key=lambda e: e["dest"]):
            path = base / entry["dest"]
            if not path.exists():
                continue
            digest = sha256_file(path)
            if digest != entry["sha256"]:
                raise SystemExit(f"{path}: hash differs from acquisitions.json")
            files.append(
                {
                    "path": entry["dest"],
                    "role": "original",
                    "sha256": digest,
                    "bytes": path.stat().st_size,
                    "source_url": entry["url"],
                    "accessed": entry["accessed"],
                    "media_type": entry.get("media_type", "application/pdf"),
                    "note": entry.get("note", ""),
                }
            )
        derived = [
            ("text/en.txt", "text", "text/plain; charset=utf-8"),
            ("pages.json", "metadata", "application/json"),
            ("units.jsonl", "units", "application/x-ndjson"),
        ]
        for rel, role, media in derived:
            path = base / rel
            if path.exists():
                files.append(
                    {
                        "path": rel,
                        "role": role,
                        "sha256": sha256_file(path),
                        "bytes": path.stat().st_size,
                        "media_type": media,
                    }
                )
        for path in sorted((base / "status").glob("*")):
            if not path.is_file():
                continue
            media = {
                ".json": "application/json",
                ".html": "text/html; charset=utf-8",
                ".txt": "text/plain; charset=utf-8",
                ".pdf": "application/pdf",
            }.get(path.suffix, "application/octet-stream")
            files.append(
                {
                    "path": path.relative_to(base).as_posix(),
                    "role": "status_snapshot",
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                    "media_type": media,
                }
            )
        if not files:
            continue
        manifest = {
            "instrument_id": iid,
            "primary_text": "text/en.txt" if (base / "text/en.txt").exists() else None,
            "files": files,
        }
        dump_json(base / "manifest.json", manifest)
        count += 1
        print(f"manifest {iid}: {len(files)} file(s)")
    print(f"{count} manifest(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
