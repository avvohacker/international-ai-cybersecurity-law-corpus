#!/usr/bin/env python3
"""Audit the official links used by the atlas instrument panels.

The audit is deliberately separate from ``make test``. It is the only part of
this repository that touches the network; the tests exercise ``classify`` with
synthetic responses and never call ``probe``.

Usage:
    python3 tools/audit_sources.py
    python3 tools/audit_sources.py --json --output build/link-audit.json
    python3 tools/audit_sources.py --only waico-establishment-agreement-2026

Exit status:
    0  no link was classified as broken
    1  at least one link was broken (or an anti-bot block, with
       --fail-on-blocked)
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import build_site  # noqa: E402
import corpuslib  # noqa: E402

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
    "InternationalAILawAtlasLinkAudit/1.0"
)
ACCEPT = (
    "text/html,application/xhtml+xml,application/xml;q=0.9,"
    "application/pdf;q=0.8,*/*;q=0.7"
)
MAX_BODY = 96 * 1024

# These markers are deliberately conservative: a plain 403 is already treated
# as a block, and a challenge marker on a 200 response means the page did not
# return the resource we asked for.
ANTI_BOT_MARKERS = (
    "just a moment",
    "cf-chl",
    "cloudflare",
    "attention required",
    "captcha",
    "datadome",
    "akamai bot manager",
    "access denied",
    "request blocked",
    "enable javascript and cookies",
    "verify you are human",
)
BOT_SERVERS = ("cloudflare", "akamai", "datadome", "imperva", "sucuri")

# A few official hosts serve their block page with a 404 instead of a 403. The
# URL was checked in a browser, so the result is reported as anti_bot rather
# than broken. This is not proof that every path on the host exists: a human
# should still open the link. The key is the exact hostname.
BROWSER_ONLY_HOSTS = {
    "www.state.gov": "State Department serves 404/405 to automated clients",
}


@dataclass(frozen=True)
class Target:
    instrument_id: str
    source_id: str
    label: str
    url: str


@dataclass(frozen=True)
class Result:
    instrument_id: str
    source_id: str
    label: str
    url: str
    status: int | None
    outcome: str
    reason: str
    detail: str = ""


def targets() -> list[Target]:
    """Return the official links used by the seven map panels."""
    instruments = corpuslib.load_instruments()
    found: list[Target] = []
    for instrument_id in build_site.MAP_INSTRUMENT_IDS:
        inst = instruments[instrument_id]
        for source in inst.get("sources") or []:
            if source.get("kind") not in build_site.OFFICIAL_SOURCE_KINDS:
                continue
            url = source.get("url")
            if not url:
                continue
            found.append(
                Target(
                    instrument_id=instrument_id,
                    source_id=source["id"],
                    label=build_site.SOURCE_LABELS.get(
                        source["id"], source.get("publisher") or source["id"]
                    ),
                    url=url,
                )
            )
    return sorted(found, key=lambda target: (target.instrument_id, target.source_id))


def _lower_headers(headers: dict | None) -> dict[str, str]:
    return {str(key).lower(): str(value).lower() for key, value in (headers or {}).items()}


def browser_only_host(url: str) -> str | None:
    """Return the reason a host is known to block non-browser clients."""
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    return BROWSER_ONLY_HOSTS.get(host)


def override_browser_only(
    url: str, status: int | None, outcome: str, reason: str
) -> tuple[str, str]:
    """Reclassify a 404/410 from a known browser-only host as a block."""
    if outcome == "broken" and status in (404, 410) and browser_only_host(url):
        return "anti_bot", "known_browser_only"
    return outcome, reason


def has_anti_bot_marker(
    status: int | None, headers: dict | None, body: str = ""
) -> bool:
    """Whether a response looks like a bot challenge rather than a page."""
    lowered = _lower_headers(headers)
    body_lower = (body or "")[:MAX_BODY].lower()
    if any(marker in body_lower for marker in ANTI_BOT_MARKERS):
        return True
    if lowered.get("cf-mitigated") or lowered.get("x-datadome"):
        return True
    if any(bot in lowered.get("server", "") for bot in BOT_SERVERS) and status in (
        401,
        403,
        405,
        406,
        409,
        429,
        451,
    ):
        return True
    return False


def classify(
    status: int | None,
    headers: dict | None = None,
    body: str = "",
    error: BaseException | None = None,
) -> tuple[str, str]:
    """Classify a response or transport error without touching the network.

    Returns ``(outcome, reason)`` where outcome is one of ``ok``, ``anti_bot``,
    ``broken`` or ``transient``. A 403/405/429 is a block, not a broken URL; a
    404/410, a DNS failure, a refused connection or a TLS failure is broken.
    A 404/410 from a host listed in ``BROWSER_ONLY_HOSTS`` is the known
    exception: ``probe`` reclassifies it as an anti-bot block.
    """
    if error is not None:
        if isinstance(error, urllib.error.HTTPError):
            return classify(error.code, dict(error.headers or {}), body)
        if isinstance(error, urllib.error.URLError):
            return classify(status, headers, body, error.reason)
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
        if has_anti_bot_marker(status, headers, body):
            return "anti_bot", "challenge_on_200"
        return "ok", "http_2xx"
    if status in (401, 403, 405, 406, 409, 429, 451):
        return "anti_bot", f"http_{status}"
    if status in (404, 410):
        return "broken", f"http_{status}"
    if 300 <= status < 400:
        return "transient", f"http_{status}"
    if 500 <= status < 600:
        return "transient", f"http_{status}"
    return "broken", f"http_{status}"


def probe(target: Target, timeout: float) -> Result:
    """Fetch one URL and classify the result. Network access lives here only."""
    request = urllib.request.Request(
        target.url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": ACCEPT,
            "Accept-Language": "en",
        },
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            body = response.read(MAX_BODY).decode("utf-8", "replace")
            status = getattr(response, "status", response.getcode())
            outcome, reason = classify(status, dict(response.headers), body)
            return Result(
                target.instrument_id,
                target.source_id,
                target.label,
                target.url,
                status,
                outcome,
                reason,
            )
    except urllib.error.HTTPError as error:
        body = error.read(MAX_BODY).decode("utf-8", "replace")
        outcome, reason = classify(error.code, dict(error.headers or {}), body)
        outcome, reason = override_browser_only(
            target.url, error.code, outcome, reason
        )
        detail = browser_only_host(target.url) if reason == "known_browser_only" else ""
        return Result(
            target.instrument_id,
            target.source_id,
            target.label,
            target.url,
            error.code,
            outcome,
            reason,
            detail,
        )
    except BaseException as error:  # noqa: BLE001 - report, never crash the run
        outcome, reason = classify(None, error=error)
        return Result(
            target.instrument_id,
            target.source_id,
            target.label,
            target.url,
            None,
            outcome,
            reason,
            type(error).__name__,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    parser.add_argument("--output", type=Path, help="write the JSON report to this path")
    parser.add_argument("--only", help="audit only this instrument id")
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="exit 1 when an anti-bot block is found, not only a broken link",
    )
    args = parser.parse_args(argv)

    selected = targets()
    if args.only:
        selected = [target for target in selected if target.instrument_id == args.only]
        if not selected:
            print(f"no official links found for instrument {args.only!r}", file=sys.stderr)
            return 2

    results = [probe(target, args.timeout) for target in selected]
    summary = Counter(result.outcome for result in results)
    payload = {
        "checked": len(results),
        "instruments": len({result.instrument_id for result in results}),
        "summary": {
            key: summary.get(key, 0)
            for key in ("ok", "anti_bot", "broken", "transient")
        },
        "results": [asdict(result) for result in results],
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(
            f"Link audit: {payload['checked']} official links in "
            f"{payload['instruments']} instrument panels"
        )
        marks = {
            "ok": "OK",
            "anti_bot": "BLOCKED",
            "broken": "BROKEN",
            "transient": "RETRY",
        }
        for result in results:
            print(
                f"  [{marks[result.outcome]:7}] {result.instrument_id}/{result.source_id}  "
                f"{result.status or '-'}  {result.url}"
            )
            if result.outcome != "ok":
                detail = f" ({result.detail})" if result.detail else ""
                print(f"            {result.reason}{detail}")
        print(
            "Summary: "
            + ", ".join(
                f"{key}={payload['summary'][key]}"
                for key in ("ok", "anti_bot", "broken", "transient")
            )
        )
        print(
            "Broken links fail the audit; anti-bot blocks and transient errors "
            "are reported separately."
        )

    if summary.get("broken", 0):
        return 1
    if args.fail_on_blocked and summary.get("anti_bot", 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
