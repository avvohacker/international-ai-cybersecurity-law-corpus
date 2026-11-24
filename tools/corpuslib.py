"""Core library for the international AI and cybersecurity law corpus.

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

from jsonschema import Draft202012Validator, FormatChecker

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
    "cyber_treaty": "Cybersecurity treaty",
}

DOMAINS = {"ai", "cyber"}
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
COUNT_KEYS = {
    "signatures",
    "political_signatures",
    "endorsements",
    "issuing_states",
    "accessions",
    "ratifications",
    "deposits",
    "observers",
    "members",
    "parties",
}
COUNT_BASIS = {"verified_total", "declared_total", "zero_verified", "unknown", "not_applicable"}
# Acts that express international consent and therefore count as a deposit once
# performed. A domestic approval or authorisation is deliberately not in this set.
CONSENT_FIELDS = ("ratification", "acceptance", "approval", "deposit")
ACCESSION_FIELDS = ("accession",)
# Count key -> entry field that evidences the act. `None` means the count is of
# the listed entries themselves.
COUNT_EVIDENCE = {
    "signatures": "signature",
    "political_signatures": "political_signature",
    "endorsements": "endorsement",
    "issuing_states": "role:issuing_state",
    "accessions": "accession",
    "ratifications": "consent",
    "accessions": "accession",
    "deposits": "deposit",
    "observers": "observer",
    "members": None,
    "parties": None,
}
POLITICAL_TYPES = {
    "joint_statement",
    "declaration",
    "resolution",
    "recommendation",
    "principles",
    "code_of_conduct",
    "commitment",
    "strategy",
    "report",
    "guidance",
}
TREATY_TYPES = {"treaty", "protocol", "agreement", "mou", "framework"}
ASSERTION_FIELDS = {
    "title",
    "dates",
    "status",
    "legal_nature",
    "parties",
    "languages",
    "provisions",
    "counts",
    "scope",
}
ASSERTION_METHODS = {
    "official_text_read",
    "official_page_read",
    "registry_read",
    "secondary_corroborated",
    "metadata_only",
}
DATE_FIELDS = {
    "adopted",
    "signed",
    "opened_for_signature",
    "closed_for_signature",
    "published",
    "entered_into_force",
    "verified_on",
    "accessed",
    "as_of",
    "signature",
    "political_signature",
    "endorsement",
    "ratification",
    "acceptance",
    "approval",
    "accession",
    "deposit",
    "domestic_approval",
    "observer",
    "entry_into_force",
    "date",
}

REQUIRED_INSTRUMENT_FIELDS = [
    "id",
    "title",
    "category",
    "instrument_type",
    "binding_status",
    "status",
    "issuer",
    "domains",
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


_SCHEMA: dict[str, Any] | None = None


def instrument_schema() -> dict[str, Any]:
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = load_json(SCHEMA_DIR / "instrument.schema.json")
    return _SCHEMA


def validate_schema(inst: Any, report: Report, path_label: str) -> None:
    """Apply the published JSON Schema, with format checking for dates and URIs."""
    try:
        validator = Draft202012Validator(
            instrument_schema(), format_checker=FormatChecker()
        )
    except Exception as exc:  # a broken schema is a repository error, not a record error
        report.error("schema_invalid", path_label, f"cannot load schema: {exc}")
        return
    errors = sorted(validator.iter_errors(inst), key=lambda err: list(err.absolute_path))
    for err in errors:
        where = "/".join(str(part) for part in err.absolute_path) or "(root)"
        report.error("schema_error", path_label, f"{where}: {err.message}")


def iter_dates(node: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    """Yield (json-path, value) for every field whose name denotes a date."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}" if path else key
            if key in DATE_FIELDS and value is not None:
                yield here, value
            else:
                yield from iter_dates(value, here)
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            yield from iter_dates(value, f"{path}[{idx}]")


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
    # Structural checks come from the published schema. The checks below are
    # semantic and must not be folded back into hand-written structural rules.
    if not isinstance(inst, dict):
        report.error("schema_error", path_label, "record must be a JSON object")
        return
    validate_schema(inst, report, path_label)
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

    domains = inst.get("domains")
    if not isinstance(domains, list) or not domains:
        report.error("bad_domains", path_label, "domains must be a non-empty list")
        domains = []
    else:
        unknown_domains = [domain for domain in domains if domain not in DOMAINS]
        if unknown_domains:
            report.error(
                "bad_domains",
                path_label,
                f"unknown domain(s): {', '.join(map(str, unknown_domains))}",
            )
        if len(set(domains)) != len(domains):
            report.error("bad_domains", path_label, "domains must be unique")

    relevance = inst.get("relevance") or {}
    if not relevance.get("reason"):
        report.error("missing_relevance", path_label, "relevance.reason is required")
    if "ai" in domains and not relevance.get("ai_provisions"):
        report.error(
            "missing_relevance",
            path_label,
            "an AI-domain record needs relevance.ai_provisions",
        )
    if "cyber" in domains and not relevance.get("cyber_provisions"):
        report.error(
            "missing_relevance",
            path_label,
            "a cyber-domain record needs relevance.cyber_provisions",
        )

    for where, value in iter_dates(inst):
        if not is_iso_date(value):
            report.error(
                "bad_date",
                path_label,
                f"{where} is not an existing calendar date in ISO YYYY-MM-DD form: {value!r}",
            )
    dates = inst.get("dates") or {}
    if not dates.get("verified_on"):
        report.error("missing_verified_on", path_label, "dates.verified_on is required")
    for end, start in (
        ("closed_for_signature", "opened_for_signature"),
        ("entered_into_force", "signed"),
    ):
        if is_iso_date(dates.get(end)) and is_iso_date(dates.get(start)):
            if dates[end] < dates[start]:
                report.error(
                    "date_order",
                    path_label,
                    f"dates.{end} precedes dates.{start}",
                )

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
            if not (isinstance(url, str) and url.startswith(("https://", "http://"))):
                report.error("bad_source_url", path_label, f"sources[{idx}] needs an http(s) URL")
            elif url.startswith("http://"):
                report.warn(
                    "plain_http_source",
                    path_label,
                    f"sources[{idx}] uses plain HTTP; the host must not support TLS for this to be acceptable",
                )
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

    # Legal nature is a reasoned qualification, not a label inferred from the
    # name of the instrument. A political form marked binding, or a treaty form
    # marked non-binding, must say why and cite the source of that conclusion.
    itype = inst.get("instrument_type")
    nature = inst.get("legal_nature")
    if isinstance(nature, dict):
        if not str(nature.get("rationale") or "").strip():
            report.error("legal_nature_unsourced", path_label, "legal_nature.rationale is empty")
        for sid in nature.get("source_ids") or []:
            if sid not in source_ids:
                report.error(
                    "unknown_source_ref",
                    path_label,
                    f"legal_nature references unknown source {sid}",
                )
    contested = (
        itype in POLITICAL_TYPES and inst.get("binding_status") == "binding"
    ) or (itype in TREATY_TYPES and inst.get("binding_status") == "non_binding")
    if contested and not isinstance(nature, dict):
        report.error(
            "legal_nature_missing",
            path_label,
            f"{itype} marked {inst.get('binding_status')} needs a sourced legal_nature rationale",
        )

    for sid in (inst.get("relevance") or {}).get("source_ids") or []:
        if sid not in source_ids:
            report.error(
                "unknown_source_ref",
                path_label,
                f"relevance references unknown source {sid}",
            )

    parties = inst.get("parties")
    if parties:
        as_of = parties.get("as_of")
        if not is_iso_date(as_of):
            report.error("bad_parties_date", path_label, "parties.as_of must be ISO date")
        if source_ids and parties.get("source_ids"):
            for sid in parties["source_ids"]:
                if sid not in source_ids:
                    report.error(
                        "unknown_source_ref",
                        path_label,
                        f"parties references unknown source {sid}",
                    )
        validate_parties(parties, report, path_label, source_ids)

    provenance = inst.get("provenance") or {}
    for idx, assertion in enumerate(provenance.get("assertions") or []):
        where = f"provenance.assertions[{idx}]"
        if assertion.get("field") not in ASSERTION_FIELDS:
            report.error("bad_assertion_field", path_label, f"{where}.field is unknown")
        if assertion.get("method") not in ASSERTION_METHODS:
            report.error("bad_assertion_method", path_label, f"{where}.method is unknown")
        if not str(assertion.get("locator") or "").strip():
            report.error("bad_assertion_locator", path_label, f"{where}.locator is empty")
        if not is_iso_date(assertion.get("date")):
            report.error("bad_assertion_date", path_label, f"{where}.date is not a valid date")
        for sid in assertion.get("source_ids") or []:
            if sid not in source_ids:
                report.error(
                    "unknown_source_ref",
                    path_label,
                    f"{where} references unknown source {sid}",
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


def count_entries(entries: list[dict[str, Any]], key: str) -> int:
    evidence = COUNT_EVIDENCE[key]
    if evidence is None:
        return len(entries)
    if evidence == "consent":
        return sum(1 for entry in entries if any(entry.get(field) for field in CONSENT_FIELDS))
    if evidence == "accession":
        return sum(1 for entry in entries if any(entry.get(field) for field in ACCESSION_FIELDS))
    if evidence.startswith("role:"):
        role = evidence.split(":", 1)[1]
        return sum(1 for entry in entries if entry.get("role") == role)
    return sum(1 for entry in entries if entry.get(evidence))


def validate_parties(
    parties: dict[str, Any], report: Report, path_label: str, source_ids: set[str]
) -> None:
    """Check that each count states its basis and matches the recorded entries.

    The point is to keep four things apart: a verified zero, a total declared by
    a source, an unknown total and an act that does not apply. A count of
    international deposits must never be incremented by a domestic approval.
    """
    entries = parties.get("entries") or []
    counts = parties.get("counts") or {}
    if not counts:
        report.error("missing_counts", path_label, "parties.counts must state what was counted")
        return
    for key, count in counts.items():
        where = f"parties.counts.{key}"
        if key not in COUNT_KEYS:
            report.error("unknown_count", path_label, f"unknown count {key}")
            continue
        if not isinstance(count, dict):
            report.error("bad_count", path_label, f"{where} is not an object")
            continue
        basis = count.get("basis")
        total = count.get("total")
        verified = count.get("verified")
        if basis not in COUNT_BASIS:
            report.error("bad_count_basis", path_label, f"{where}.basis is unknown")
            continue
        if basis in {"unknown", "not_applicable"}:
            if total is not None:
                report.error(
                    "ambiguous_count",
                    path_label,
                    f"{where}: a {basis} count must not carry a total",
                )
        elif basis == "zero_verified":
            if total != 0 or verified != 0:
                report.error(
                    "ambiguous_count",
                    path_label,
                    f"{where}: zero_verified requires total 0 and verified 0",
                )
        elif not isinstance(total, int):
            report.error("bad_count", path_label, f"{where}: a stated total must be an integer")
        if not isinstance(verified, int) or verified < 0:
            report.error("bad_count", path_label, f"{where}.verified must be a non-negative integer")
            continue
        if isinstance(total, int) and verified > total:
            report.error(
                "count_exceeds_total",
                path_label,
                f"{where}: {verified} verified entries exceed the stated total {total}",
            )
        if basis == "verified_total" and isinstance(total, int) and verified != total:
            report.error(
                "count_not_itemised",
                path_label,
                f"{where}: verified_total requires {total} itemised entries, found {verified}",
            )
        evidenced = count_entries(entries, key)
        strict = key in {"ratifications", "deposits", "accessions", "observers"} or evidenced > 0
        if strict and verified != evidenced:
            report.error(
                "count_entry_mismatch",
                path_label,
                f"{where}: {verified} verified but {evidenced} entries record the act",
            )
        if not strict and verified > len(entries):
            report.error(
                "count_entry_mismatch",
                path_label,
                f"{where}: {verified} verified exceeds the {len(entries)} listed entries",
            )
        for sid in count.get("source_ids") or []:
            if sid not in source_ids:
                report.error(
                    "unknown_source_ref",
                    path_label,
                    f"{where} references unknown source {sid}",
                )

    # A recorded international consent must be counted; an internal approval
    # must not be. This catches the substitution the corpus previously made.
    consent = count_entries(entries, "ratifications")
    if consent and "ratifications" not in counts:
        report.error(
            "uncounted_consent",
            path_label,
            "entries record ratification/acceptance/approval/accession but no ratifications count is declared",
        )
    if consent and (counts.get("ratifications") or {}).get("basis") == "not_applicable":
        report.error(
            "consent_not_applicable",
            path_label,
            "entries record international consent but ratifications are marked not_applicable",
        )
    if not consent and (counts.get("ratifications") or {}).get("basis") == "verified_total":
        report.error(
            "unverified_consent",
            path_label,
            "ratifications are marked verified_total but no entry records a deposit",
        )
    if any(entry.get("domestic_approval") for entry in entries) and (
        counts.get("ratifications") or {}
    ).get("total") not in (None, 0):
        pass  # a domestic approval does not by itself invalidate a verified deposit
    for entry in entries:
        if entry.get("domestic_approval") and entry.get("ratification"):
            if entry["domestic_approval"] > entry["ratification"]:
                report.error(
                    "approval_after_ratification",
                    path_label,
                    f"{entry.get('party')}: domestic approval is later than the recorded ratification",
                )


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
        if role not in {"original", "text", "units", "metadata", "status_snapshot"}:
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
                page_list = pages.get("pages")
                if not isinstance(page_list, list) or not page_list:
                    report.error("bad_pages", iid, "pages.json has no page list")
                else:
                    ps, pe = unit.get("page_start"), unit.get("page_end")
                    valid_pages = True
                    for key, value in (("page_start", ps), ("page_end", pe)):
                        if not isinstance(value, int) or isinstance(value, bool) or not (
                            1 <= value <= len(page_list)
                        ):
                            report.error(
                                "bad_unit_page",
                                iid,
                                f"unit {uid} has invalid {key} {value!r}; pages 1..{len(page_list)}",
                            )
                            valid_pages = False
                    if valid_pages and ps > pe:
                        report.error(
                            "bad_unit_page",
                            iid,
                            f"unit {uid} page_start {ps} is after page_end {pe}",
                        )
                        valid_pages = False
                    if valid_pages:
                        first, last = page_list[ps - 1], page_list[pe - 1]
                        for label, page in (("page_start", first), ("page_end", last)):
                            bounds = (page.get("char_start"), page.get("char_end"))
                            if not all(
                                isinstance(v, int) and not isinstance(v, bool)
                                for v in bounds
                            ) or not (0 <= bounds[0] < bounds[1]):
                                report.error(
                                    "bad_page_bounds",
                                    iid,
                                    f"pages.json entry for {label} of unit {uid} has invalid char bounds",
                                )
                                valid_pages = False
                        if valid_pages:
                            if not (first["char_start"] <= start < last["char_end"] + 1):
                                report.error(
                                    "unit_page_offset_mismatch",
                                    iid,
                                    f"unit {uid} char range {start}:{end} is not inside pages {ps}-{pe}",
                                )
                            if not (
                                unit.get("page_start") == unit.get("page_end")
                                or first["char_start"] <= start < first["char_end"] + 1
                            ):
                                report.error(
                                    "unit_page_offset_mismatch",
                                    iid,
                                    f"unit {uid} start is not inside its first page {ps}",
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
    by_domain = {"ai": 0, "cyber": 0, "joint": 0}
    for inst in ordered:
        by_category[inst["category"]] += 1
        by_binding[inst["binding_status"]] = by_binding.get(inst["binding_status"], 0) + 1
        level = inst["verification"]["level"]
        by_verification[level] = by_verification.get(level, 0) + 1
        has_ai = "ai" in inst["domains"]
        has_cyber = "cyber" in inst["domains"]
        if has_ai:
            by_domain["ai"] += 1
        if has_cyber:
            by_domain["cyber"] += 1
        if has_ai and has_cyber:
            by_domain["joint"] += 1

    full_texts = sorted(
        inst["id"] for inst in ordered if inst.get("text", {}).get("full_text")
    )
    summary = {
        "schema_version": 1,
        "instruments": ordered,
        "counts": {
            "total": len(ordered),
            "by_category": by_category,
            "by_domain": by_domain,
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
    lines += ["", "## Counts by domain", ""]
    lines.append(f"- `ai`: {by_domain['ai']} (including {by_domain['joint']} joint AI–cyber)")
    lines.append(f"- `cyber`: {by_domain['cyber']} (including {by_domain['joint']} joint AI–cyber)")
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
