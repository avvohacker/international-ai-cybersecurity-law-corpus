#!/usr/bin/env python3
"""Audit which catalogue records have a stored full text.

The audit is offline by default and reads only ``catalog/instruments/*.json``.
It exists to distinguish four different reasons why a record may have no stored
text:

* the official text is located at the cited source but the record is
  metadata-only;
* the text is a paywalled standard;
* only an official summary is published;
* the record is internal law, not an international instrument.

With ``--probe`` it also performs a real GET on the first official source of
every ``official_text_located`` record and records whether the download
succeeds, is blocked or is broken. The probe is not part of ``make test`` and
the offline classification functions stay network-free.

Usage:
  python3 tools/audit_texts.py
  python3 tools/audit_texts.py --json --output build/text-availability-audit.json
  python3 tools/audit_texts.py --probe --json --output build/text-availability-audit.json
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
from datetime import date
import urllib.error
import urllib.parse
import urllib.request
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

PROBE_TIMEOUT = 40.0
PROBE_MAX_BYTES = 8 * 1024 * 1024
# A 202 response is reported as transient: the resource was accepted, not
# delivered. See classify_download.
PROBE_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
    "InternationalAILawAtlasTextProbe/1.0"
)
PROBE_ACCEPT = (
    "application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.7"
)
PROBE_MARKERS = (
    "just a moment",
    "cf-chl",
    "checking your browser",
    "attention required",
    "captcha",
    "access denied",
    "request blocked",
    "enable javascript and cookies",
    "verify you are human",
)


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


def classify_download(
    status: int | None,
    content_type: str = "",
    body: bytes = b"",
    error: BaseException | None = None,
) -> tuple[str, str]:
    """Classify a download probe without touching the network.

    Returns ``(outcome, reason)``: ``downloaded`` when a 2xx response actually
    carries the resource (a PDF, or a non-challenge HTML page), ``blocked``
    for an anti-bot or authorisation response, ``broken`` for a missing
    resource or a transport failure, ``transient`` for a timeout or a server
    error.
    """
    if error is not None:
        if isinstance(error, urllib.error.HTTPError):
            return classify_download(error.code, content_type, body)
        if isinstance(error, urllib.error.URLError):
            return classify_download(status, content_type, body, error.reason)
        if isinstance(error, ssl.SSLCertVerificationError):
            return "broken", "tls_certificate"
        if isinstance(error, ssl.SSLError):
            return "broken", "tls_handshake"
        if isinstance(error, socket.gaierror):
            return "broken", "dns"
        if isinstance(error, (TimeoutError, socket.timeout)):
            return "transient", "timeout"
        if isinstance(
            error, (ConnectionRefusedError, ConnectionResetError, BrokenPipeError)
        ):
            return "broken", "connection"
        return "transient", type(error).__name__

    if status is None:
        return "transient", "no_status"
    if 200 <= status < 300:
        if body[:5] == b"%PDF-":
            return "downloaded", "pdf"
        if b"%PDF-" in body[:1024]:
            return "downloaded", "pdf"
        if status == 202:
            # 202 Accepted means the server queued the request; it is not a
            # delivered file. The UN Digital Library answers this way to
            # scripted clients and serves the PDF only to a browser session.
            return "transient", "http_202"
        lowered = body[:96 * 1024].decode("utf-8", "replace").lower()
        if any(marker in lowered for marker in PROBE_MARKERS):
            return "blocked", "challenge_on_200"
        if "html" in content_type:
            return "downloaded", "html"
        return ("downloaded", "binary") if body else ("transient", "empty_200")
    if status in (401, 403, 405, 406, 409, 429, 451):
        return "blocked", f"http_{status}"
    if status in (404, 410):
        return "broken", f"http_{status}"
    if 300 <= status < 400 or 500 <= status < 600:
        return "transient", f"http_{status}"
    return "broken", f"http_{status}"


def probe_date() -> str:
    """Return the date of the probe run, never a hard-coded date."""
    return date.today().isoformat()


def probe_download(
    url: str,
    timeout: float = PROBE_TIMEOUT,
    checked_on: str | None = None,
) -> dict[str, Any]:
    """Download one URL (capped) and report whether it really serves a text."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": PROBE_USER_AGENT,
            "Accept": PROBE_ACCEPT,
            "Accept-Language": "en",
        },
    )
    context = ssl.create_default_context()
    result: dict[str, Any] = {
        "checked_on": checked_on or probe_date(),
        "url": url,
    }
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            body = response.read(PROBE_MAX_BYTES)
            status = getattr(response, "status", response.getcode())
            headers = response.headers
            content_type = headers.get_content_type() if headers else ""
            try:
                content_length: int | None = int(headers.get("Content-Length"))
            except (TypeError, ValueError):
                content_length = None
            outcome, reason = classify_download(status, content_type, body)
            result.update(
                {
                    "outcome": outcome,
                    "reason": reason,
                    "http_status": status,
                    "content_type": content_type,
                    "content_length": content_length,
                    "bytes_read": len(body),
                    "final_url": response.geturl(),
                }
            )
    except urllib.error.HTTPError as error:
        body = error.read(96 * 1024)
        outcome, reason = classify_download(error.code, "", body)
        result.update(
            {
                "outcome": outcome,
                "reason": reason,
                "http_status": error.code,
                "content_type": "",
                "content_length": None,
                "bytes_read": len(body),
                "final_url": error.geturl() if hasattr(error, "geturl") else url,
            }
        )
    except BaseException as error:  # noqa: BLE001 - report, never crash the run
        outcome, reason = classify_download(None, error=error)
        result.update(
            {
                "outcome": outcome,
                "reason": reason,
                "http_status": None,
                "content_type": "",
                "content_length": None,
                "bytes_read": 0,
                "final_url": url,
                "error": type(error).__name__,
            }
        )
    return result


def audit(
    probe: bool = False,
    timeout: float = PROBE_TIMEOUT,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify every record, optionally probing and merging earlier results.

    Without ``probe`` a stored download result is copied onto a record only
    when that record is still ``official_text_located`` and its first official
    source is the same URL that was probed. A record that has since been
    acquired, or whose source link has changed, must not inherit a stale
    download block from the previous report.
    """
    records = []
    for path in sorted(CATALOG_DIR.glob("*.json")):
        inst = json.loads(path.read_text(encoding="utf-8"))
        availability, reason = classify(inst)
        source, source_kind = first_official_source(inst)
        row: dict[str, Any] = {
            "id": inst["id"],
            "title": inst["title"].get("short") or inst["title"].get("official"),
            "binding_status": inst.get("binding_status"),
            "category": inst.get("category"),
            "availability": availability,
            "reason": reason,
            "official_source": source,
            "official_source_kind": source_kind,
        }
        if probe and availability == "official_text_located" and source:
            row["download"] = probe_download(source, timeout)
        records.append(row)
    if not probe and previous:
        stored_downloads = {
            old["id"]: old["download"]
            for old in previous.get("records", [])
            if old.get("download")
        }
        for row in records:
            download = stored_downloads.get(row["id"])
            if not download:
                continue
            if row["availability"] != "official_text_located":
                continue
            if download.get("url") != row.get("official_source"):
                continue
            row["download"] = download
    counts = Counter(row["availability"] for row in records)
    summary: dict[str, Any] = {
        "stored": counts["stored"],
        "official_text_located": counts["official_text_located"],
        "paywalled": counts["paywalled"],
        "summary_only": counts["summary_only"],
        "internal_law": counts["internal_law"],
    }
    downloads = [row["download"] for row in records if row.get("download")]
    if downloads:
        outcomes = Counter(download["outcome"] for download in downloads)
        summary["download_probe"] = {
            "checked": len(downloads),
            "downloaded": outcomes["downloaded"],
            "blocked": outcomes["blocked"],
            "broken": outcomes["broken"],
            "transient": outcomes["transient"],
            "checked_on": max(
                (download.get("checked_on", "") for download in downloads),
                default="",
            ),
        }
    return {
        "total": len(records),
        "summary": summary,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON")
    parser.add_argument("--output", type=Path, help="write JSON to this path")
    parser.add_argument(
        "--probe",
        action="store_true",
        help="download the first official source of each located, unstored record",
    )
    parser.add_argument("--timeout", type=float, default=PROBE_TIMEOUT)
    args = parser.parse_args()

    previous = None
    if args.output and args.output.exists() and not args.probe:
        previous = json.loads(args.output.read_text(encoding="utf-8"))
    data = audit(probe=args.probe, timeout=args.timeout, previous=previous)
    if args.output:
        dump_json(args.output, data)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            "total={total} stored={stored} official_text_located={official_text_located} "
            "paywalled={paywalled} summary_only={summary_only} internal_law={internal_law}".format(
                **{key: value for key, value in data["summary"].items() if key != "download_probe"},
                total=data["total"],
            )
        )
        for row in data["records"]:
            if row["availability"] == "official_text_located":
                print(f"located  {row['id']}  {row['official_source']}")
                download = row.get("download")
                if download:
                    print(
                        "         {outcome:10} {http_status} {content_type} "
                        "{bytes_read} bytes ({reason})".format(
                            outcome=download["outcome"],
                            http_status=download["http_status"] or "-",
                            content_type=download["content_type"] or "-",
                            bytes_read=download["bytes_read"],
                            reason=download["reason"],
                        )
                    )
        if "download_probe" in data["summary"]:
            probe = data["summary"]["download_probe"]
            print(
                "Download probe: checked={checked} downloaded={downloaded} blocked={blocked} "
                "broken={broken} transient={transient} on {checked_on}".format(**probe)
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
