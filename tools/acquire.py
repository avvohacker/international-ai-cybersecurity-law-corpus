#!/usr/bin/env python3
"""Acquire sources listed in catalog/acquisitions.json.

Network step, deliberately separate from the build. It never overwrites an
existing source file: if the bytes differ from the registered hash, the new
bytes are saved under an access-date name and the command fails so that a human
can record the version change.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
LOCK = ROOT / "catalog" / "acquisitions.json"
UA = "international-ai-cybersecurity-law-corpus/0.1 (research corpus; contact: repository owner)"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify stored files only")
    parser.add_argument("--only", help="acquire a single instrument id")
    args = parser.parse_args()
    entries = json.loads(LOCK.read_text(encoding="utf-8"))
    failures = 0
    for entry in entries:
        if args.only and entry["instrument_id"] != args.only:
            continue
        dest = CORPUS / entry["instrument_id"] / entry["dest"]
        if dest.exists():
            actual = digest(dest.read_bytes())
            if actual != entry["sha256"]:
                print(f"HASH MISMATCH {dest}: stored {actual}, registered {entry['sha256']}")
                failures += 1
            else:
                print(f"ok {dest.relative_to(ROOT)}")
            continue
        if args.check:
            print(f"MISSING {dest}")
            failures += 1
            continue
        try:
            data = fetch(entry["url"])
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"FETCH FAILED {entry['url']}: {exc}")
            failures += 1
            continue
        actual = digest(data)
        if actual != entry["sha256"]:
            drift = dest.with_name(f"{entry.get('accessed', 'unknown')}_{dest.name}")
            drift.parent.mkdir(parents=True, exist_ok=True)
            drift.write_bytes(data)
            print(
                f"DRIFT {entry['url']}: got {actual}, expected {entry['sha256']}; "
                f"saved {drift.relative_to(ROOT)} (not overwriting registered version)"
            )
            failures += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        print(f"acquired {dest.relative_to(ROOT)} ({len(data)} bytes)")
    if failures:
        print(f"{failures} problem(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
