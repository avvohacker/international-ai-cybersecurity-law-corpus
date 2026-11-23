"""Core library for the international AI law corpus.

Standard library only. The build is deterministic: no timestamps, sorted keys,
stable ordering. Network access is confined to tools/acquire.py.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
CATALOG_DIR = ROOT / "catalog" / "instruments"
CORPUS_DIR = ROOT / "corpus"
BUILD_DIR = ROOT / "build"
SCHEMA_DIR = ROOT / "schema"

CATEGORIES = {
    "ai_treaty": "Treaty specifically dedicated to artificial intelligence",
    "agreement_ai_provisions": "Other international agreement with express, substantive AI provisions",
    "non_binding_instrument": "Non-binding instrument (declaration, resolution, recommendation, principles, code)",
    "preparatory_interpretive": "Official preparatory, interpretive or implementation material",
    "technical_standard": "International technical standard",
    "draft_negotiation": "Draft or negotiation in progress",
    "supranational_law": "Supranational legislation, collected separately",
    "general_treaty": "General treaty applicable to AI (reasoned selection)",
}

BINDING = {"binding", "non_binding", "mixed", "unknown"}
STATUSES = {
    "in_force",
    "not_in_force",
    "adopted",
    "open_for_signature",
    "in_negotiation",
    "withdrawn",
    "superseded",
    "unknown",
}
VERIFICATION_LEVELS = {
    "full_text_checked",
    "metadata_verified",
    "source_located",
}
SOURCE_KINDS = {
    "official_primary",
    "official_secondary",
    "registry",
    "official_journal",
    "secondary",
}
DECISIONS = {"included", "excluded", "pending"}

REQUIRED_INSTRUMENT_FIELDS = [
    "id",
    "title",
    "category",
    "instrument_type",
    "binding_status",
    "status",
    "issuer",
    "relevance",
    "dates",
    "languages",
    "sources",
    "rights",
    "verification",
    "gaps",
]

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,80}$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")


def is_iso_date(value: Any) -> bool:
    if not isinstance(value, str) or not DATE_RE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


@dataclass
class Issue:
    level: str  # error | warning
    code: str
    where: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "level": self.level,
            "code": self.code,
            "where": self.where,
            "message": self.message,
        }


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)

    def error(self, code: str, where: str, message: str) -> None:
        self.issues.append(Issue("error", code, where, message))

    def warn(self, code: str, where: str, message: str) -> None:
        self.issues.append(Issue("warning", code, where, message))

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "warning"]

    def ok(self) -> bool:
        return not self.errors


def load_instruments() -> dict[str, dict[str, Any]]:
    instruments: dict[str, dict[str, Any]] = {}
    for path in sorted(CATALOG_DIR.glob("*.json")):
        data = load_json(path)
        instruments[data.get("id", path.stem)] = data
    return instruments


def validate_instrument(
    inst: dict[str, Any], report: Report, path_label: str
) -> None:
    for key in REQUIRED_INSTRUMENT_FIELDS:
        if key not in inst:
            report.error("missing_field", path_label, f"missing required field: {key}")
    iid = inst.get("id")
    if not isinstance(iid, str) or not ID_RE.match(iid):
        report.error("bad_id", path_label, f"invalid id: {iid!r}")
    if inst.get("category") not in CATEGORIES:
        report.error("bad_category", path_label, f"unknown category: {inst.get('category')!r}")
    if inst.get("binding_status") not in BINDING:
        report.error(
            "bad_binding", path_label, f"unknown binding_status: {inst.get('binding_status')!r}"
        )
    if inst.get("status") not in STATUSES:
        report.error("bad_status", path_label, f"unknown status: {inst.get('status')!r}")

    title = inst.get("title") or {}
    if not isinstance(title, dict) or not title.get("official"):
        report.error("missing_title", path_label, "title.official is required")

    issuer = inst.get("issuer")
    if not isinstance(issuer, list) or not issuer:
        report.error("missing_issuer", path_label, "issuer must be a non-empty list")
    else:
        for idx, item in enumerate(issuer):
            if not isinstance(item, dict) or not item.get("name"):
                report.error("bad_issuer", path_label, f"issuer[{idx}] needs a name")

    relevance = inst.get("relevance") or {}
    if not relevance.get("reason") or not relevance.get("ai_provisions"):
        report.error(
            "missing_relevance",
            path_label,
            "relevance.reason and relevance.ai_provisions are required",
        )

    dates = inst.get("dates") or {}
    for key in ("adopted", "verified_on"):
        if key in dates and dates[key] is not None and not is_iso_date(dates[key]):
            report.error("bad_date", path_label, f"dates.{key} is not ISO YYYY-MM-DD")
    if not dates.get("verified_on"):
        report.error("missing_verified_on", path_label, "dates.verified_on is required")

    languages = inst.get("languages") or {}
    if not languages.get("authentic"):
        report.error("missing_languages", path_label, "languages.authentic is required")

    sources = inst.get("sources")
    source_ids: set[str] = set()
    if not isinstance(sources, list) or not sources:
        report.error("missing_sources", path_label, "at least one source is required")
    else:
        for idx, src in enumerate(sources):
            if not isinstance(src, dict):
                report.error("bad_source", path_label, f"sources[{idx}] is not an object")
                continue
            sid = src.get("id")
            if not sid:
                report.error("bad_source", path_label, f"sources[{idx}] lacks id")
            elif sid in source_ids:
                report.error("duplicate_source_id", path_label, f"duplicate source id {sid}")
            else:
                source_ids.add(sid)
            url = src.get("url", "")
            if not (isinstance(url, str) and url.startswith("https://")):
                report.error("bad_source_url", path_label, f"sources[{idx}] needs https URL")
            if not is_iso_date(src.get("accessed")):
                report.error(
                    "bad_source_access_date",
                    path_label,
                    f"sources[{idx}].accessed must be ISO YYYY-MM-DD",
                )
            if src.get("kind") not in SOURCE_KINDS:
                report.error("bad_source_kind", path_label, f"sources[{idx}] has unknown kind")

    rights = inst.get("rights") or {}
    if not rights.get("status"):
        report.error("missing_rights", path_label, "rights.status is required")

    verification = inst.get("verification") or {}
    if verification.get("level") not in VERIFICATION_LEVELS:
        report.error(
            "bad_verification_level",
            path_label,
            f"unknown verification.level: {verification.get('level')!r}",
        )
    checks = verification.get("checks")
    if not isinstance(checks, list) or not checks:
        report.error("missing_checks", path_label, "verification.checks must be non-empty")

    gaps = inst.get("gaps")
    if not isinstance(gaps, list) or not gaps:
        report.error("missing_gaps", path_label, "gaps must be a non-empty list")

    # Legal-nature consistency: declarations/resolutions cannot be binding.
    itype = inst.get("instrument_type")
    if itype in {"declaration", "resolution", "recommendation", "principles", "code_of_conduct", "strategy", "report", "guidance"} and inst.get("binding_status") == "binding":
        report.error(
            "category_mismatch",
            path_label,
            f"{itype} cannot be marked binding",
        )

    parties = inst.get("parties")
    if parties:
        as_of = parties.get("as_of")
        if not is_iso_date(as_of):
            report.error("bad_parties_date", path_label, "parties.as_of must be ISO date")
        for idx, entry in enumerate(parties.get("entries", [])):
            for key in ("signature", "ratification", "accession", "entry_into_force"):
                value = entry.get(key)
                if value is not None and not is_iso_date(value):
                    report.error(
                        "bad_party_date",
                        path_label,
                        f"parties.entries[{idx}].{key} is not ISO date",
                    )
        if source_ids and parties.get("source_ids"):
            for sid in parties["source_ids"]:
                if sid not in source_ids:
                    report.error(
                        "unknown_source_ref",
                        path_label,
                        f"parties references unknown source {sid}",
                    )

    for rel in inst.get("related", []):
        if not rel.get("id") or not rel.get("relation"):
            report.error("bad_related", path_label, "related entries need id and relation")

    text = inst.get("text")
    if text:
        if not (CORPUS_DIR / iid).exists():
            report.error("missing_corpus_dir", path_label, f"corpus/{iid} does not exist")
        if not text.get("manifest"):
            report.error("missing_text_manifest", path_label, "text.manifest is required")


def validate_corpus_text(inst: dict[str, Any], report: Report) -> None:
    """Verify stored files against the instrument's corpus manifest."""
    iid = inst["id"]
    text = inst.get("text")
    if not text:
        return
    manifest_path = CORPUS_DIR / iid / text["manifest"]
    if not manifest_path.exists():
        report.error("missing_manifest", iid, f"{manifest_path} not found")
        return
    manifest = load_json(manifest_path)
    if manifest.get("instrument_id") != iid:
        report.error("manifest_id_mismatch", iid, "manifest instrument_id mismatch")
    files = manifest.get("files", [])
    if not files:
        report.error("empty_manifest", iid, "manifest has no files")
    seen_hashes: dict[str, str] = {}
    for entry in files:
        rel = entry.get("path")
        if not rel:
            report.error("bad_manifest_entry", iid, "file entry without path")
            continue
        path = CORPUS_DIR / iid / rel
        if not path.exists():
            report.error("missing_file", iid, f"missing file {rel}")
            continue
        digest = sha256_file(path)
        if digest != entry.get("sha256"):
            report.error("hash_mismatch", iid, f"sha256 mismatch for {rel}")
        if path.stat().st_size != entry.get("bytes"):
            report.error("size_mismatch", iid, f"size mismatch for {rel}")
        if digest in seen_hashes:
            report.error(
                "duplicate_content",
                iid,
                f"{rel} duplicates {seen_hashes[digest]} (deduplicate instead)",
            )
        else:
            seen_hashes[digest] = rel
        role = entry.get("role")
        if role not in {"original", "text", "units", "metadata"}:
            report.error("bad_file_role", iid, f"unknown role {role!r} for {rel}")

    pages_path = CORPUS_DIR / iid / "pages.json"
    pages = load_json(pages_path) if pages_path.exists() else None
    units_path = CORPUS_DIR / iid / "units.jsonl"
    if units_path.exists():
        text_path = CORPUS_DIR / iid / manifest.get("primary_text", "text/en.txt")
        if not text_path.exists():
            report.error("missing_primary_text", iid, f"{text_path} missing")
            return
        body = text_path.read_text(encoding="utf-8")
        seen_units: set[str] = set()
        for lineno, line in enumerate(units_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                unit = json.loads(line)
            except json.JSONDecodeError:
                report.error("bad_unit_json", iid, f"units.jsonl line {lineno} is not JSON")
                continue
            uid = unit.get("unit_id")
            if not uid or uid in seen_units:
                report.error("bad_unit_id", iid, f"missing/duplicate unit id at line {lineno}")
            seen_units.add(uid or "")
            if unit.get("instrument_id") != iid:
                report.error("unit_instrument_mismatch", iid, f"unit {uid} has wrong instrument_id")
            start, end = unit.get("char_start"), unit.get("char_end")
            if not isinstance(start, int) or not isinstance(end, int) or not (0 <= start < end <= len(body)):
                report.error("bad_unit_anchor", iid, f"unit {uid} has invalid char range")
                continue
            if body[start:end] != unit.get("text"):
                report.error("unit_text_mismatch", iid, f"unit {uid} text does not match stored anchor")
            if pages:
                for key in ("page_start", "page_end"):
                    p = unit.get(key)
                    if not isinstance(p, int) or p < 1 or p > len(pages.get("pages", [])):
                        report.error("bad_unit_page", iid, f"unit {uid} has invalid {key}")
                if unit.get("page_start") and unit.get("page_end"):
                    page = pages["pages"][unit["page_start"] - 1]
                    if not (page["char_start"] <= start < page["char_end"] + 1):
                        report.error(
                            "unit_page_offset_mismatch",
                            iid,
                            f"unit {uid} start not inside page {unit['page_start']}",
                        )


def validate_candidates(instruments: dict[str, dict[str, Any]], report: Report) -> None:
    path = ROOT / "catalog" / "candidates.json"
    if not path.exists():
        report.error("missing_candidates", "catalog/candidates.json", "file not found")
        return
    data = load_json(path)
    if not isinstance(data, list):
        report.error("bad_candidates", "candidates", "candidates.json must be a list")
        return
    seen: set[str] = set()
    for idx, cand in enumerate(data):
        cid = cand.get("id")
        where = f"candidates[{idx}]"
        if not cid or cid in seen:
            report.error("bad_candidate_id", where, "missing or duplicate candidate id")
        seen.add(cid or "")
        if cand.get("decision") not in DECISIONS:
            report.error("bad_decision", where, f"unknown decision {cand.get('decision')!r}")
        if not cand.get("title"):
            report.error("missing_candidate_title", where, "title required")
        if not cand.get("reason"):
            report.error("missing_candidate_reason", where, "reason required")
        if cand.get("decision") == "included":
            if cand.get("instrument_id") not in instruments:
                report.error(
                    "included_without_instrument",
                    where,
                    f"included candidate points to missing instrument {cand.get('instrument_id')!r}",
                )
        if cand.get("decision") in {"excluded", "pending"} and cand.get("instrument_id") in instruments:
            report.error(
                "candidate_instrument_conflict",
                where,
                "excluded/pending candidate must not point to a catalogued instrument",
            )


def load_units(iid: str) -> list[dict[str, Any]]:
    path = CORPUS_DIR / iid / "units.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate(report: Report | None = None) -> Report:
    report = report or Report()
    instruments = load_instruments()
    for path in sorted(CATALOG_DIR.glob("*.json")):
        inst = load_json(path)
        if path.stem != inst.get("id"):
            report.error("filename_id_mismatch", path.name, "filename must equal instrument id")
        validate_instrument(inst, report, path.name)
        validate_corpus_text(inst, report)
    validate_candidates(instruments, report)

    # Cross-instrument references must resolve.
    for iid, inst in instruments.items():
        for rel in inst.get("related", []):
            if rel.get("id") not in instruments:
                report.warn(
                    "unresolved_related",
                    iid,
                    f"related instrument {rel.get('id')!r} is not in the catalogue",
                )

    # Duplicate title + adoption date is a signal of an accidental copy. Recurring
    # resolution titles (for example successive LAWS resolutions) are legitimate.
    fingerprints: dict[tuple[str, str], str] = {}
    for iid, inst in instruments.items():
        title = (inst.get("title") or {}).get("official", "").strip().lower()
        adopted = (inst.get("dates") or {}).get("adopted") or ""
        key = (title, adopted)
        if key in fingerprints:
            report.warn(
                "duplicate_title_and_date",
                iid,
                f"same official title and adoption date as {fingerprints[key]}",
            )
        else:
            fingerprints[key] = iid
    return report


def build() -> dict[str, Any]:
    """Validate, then write deterministic build artefacts."""
    report = validate()
    if not report.ok():
        raise SystemExit(
            "validation failed:\n"
            + "\n".join(f"- {i.where}: {i.message}" for i in report.errors)
        )

    instruments = load_instruments()
    ordered = [instruments[k] for k in sorted(instruments)]
    by_category: dict[str, int] = {k: 0 for k in sorted(CATEGORIES)}
    by_binding: dict[str, int] = {}
    by_verification: dict[str, int] = {}
    for inst in ordered:
        by_category[inst["category"]] += 1
        by_binding[inst["binding_status"]] = by_binding.get(inst["binding_status"], 0) + 1
        level = inst["verification"]["level"]
        by_verification[level] = by_verification.get(level, 0) + 1

    full_texts = sorted(
        inst["id"] for inst in ordered if inst.get("text", {}).get("full_text")
    )
    summary = {
        "schema_version": 1,
        "instruments": ordered,
        "counts": {
            "total": len(ordered),
            "by_category": by_category,
            "by_binding": dict(sorted(by_binding.items())),
            "by_verification": dict(sorted(by_verification.items())),
            "full_texts": len(full_texts),
            "with_local_original": sum(
                1
                for inst in ordered
                if inst.get("text")
                and any(
                    f.get("role") == "original"
                    for f in load_json(
                        CORPUS_DIR / inst["id"] / inst["text"]["manifest"]
                    ).get("files", [])
                )
            ),
        },
        "full_text_ids": full_texts,
    }
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    dump_json(BUILD_DIR / "catalog.json", summary)

    lines = [
        "# Catalogue",
        "",
        "Generated by `make build` from `catalog/instruments/*.json`. Do not edit by hand.",
        "",
        f"Total instruments: **{len(ordered)}**. Full texts preserved: **{len(full_texts)}**.",
        "",
        "| ID | Official title | Category | Binding | Status | Verification |",
        "|---|---|---|---|---|---|",
    ]
    for inst in ordered:
        title = inst["title"]["official"].replace("|", "\\|")
        lines.append(
            "| `{id}` | {title} | {cat} | {bind} | {status} | {ver} |".format(
                id=inst["id"],
                title=title,
                cat=inst["category"],
                bind=inst["binding_status"],
                status=inst["status"],
                ver=inst["verification"]["level"],
            )
        )
    lines += ["", "## Counts by category", ""]
    for cat, count in sorted(by_category.items()):
        lines.append(f"- `{cat}`: {count} — {CATEGORIES[cat]}")
    lines += ["", "## Counts by verification level", ""]
    for level, count in sorted(by_verification.items()):
        lines.append(f"- `{level}`: {count}")
    (BUILD_DIR / "CATALOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    checksums: list[tuple[str, str]] = []
    for path in sorted(CORPUS_DIR.rglob("*")):
        if path.is_file() and ".gitkeep" not in path.name:
            checksums.append((sha256_file(path), path.relative_to(ROOT).as_posix()))
    (BUILD_DIR / "checksums.sha256").write_text(
        "".join(f"{digest}  {rel}\n" for digest, rel in sorted(checksums)), encoding="utf-8"
    )
    dump_json(BUILD_DIR / "verification-report.json", {"issues": [i.as_dict() for i in report.issues]})
    return summary
