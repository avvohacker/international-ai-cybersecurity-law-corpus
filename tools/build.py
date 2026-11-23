#!/usr/bin/env python3
"""Validate the corpus and write deterministic build artefacts."""

import argparse
import json
import sys

from corpuslib import build, validate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate only")
    args = parser.parse_args()
    if args.check:
        report = validate()
        for issue in report.issues:
            print(f"{issue.level.upper()} {issue.where}: {issue.message}")
        print(
            f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)",
            file=sys.stderr,
        )
        return 0 if report.ok() else 1
    summary = build()
    print(json.dumps(summary["counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
