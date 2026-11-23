#!/usr/bin/env python3
"""Generate the human-readable static site from the verified catalogue.

The page is deliberately dependency-free: Python standard library only, no
network, no external fonts or scripts. Maps are drawn from Natural Earth 1:110m
boundaries stored in data/natural-earth/; counts and memberships come from
catalog/instruments/*.json.
"""

from __future__ import annotations

import html
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import corpuslib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
GEO = ROOT / "data" / "natural-earth" / "ne_110m_admin_0_countries.geojson"
REPO = "https://github.com/avvohacker/international-ai-law-corpus"

PARIS_ID = "paris-ai-action-summit-statement-2025"
CETS_ID = "coe-cets-225"
CHINA_ID = "china-global-ai-governance-initiative-2023"

CATEGORY_LABELS = {
    "ai_treaty": "AI-specific treaty",
    "agreement_ai_provisions": "Agreement with AI provisions",
    "non_binding_instrument": "Non-binding instrument",
    "preparatory_interpretive": "Implementation / interpretation",
    "technical_standard": "Technical standard",
    "draft_negotiation": "Negotiation in progress",
    "supranational_law": "EU law",
    "general_treaty": "General treaty",
}

BINDING_LABELS = {
    "binding": "Binding",
    "non_binding": "Non-binding",
    "mixed": "Mixed",
    "unknown": "Unknown",
}

STATUS_LABELS = {
    "in_force": "In force",
    "not_in_force": "Not in force",
    "adopted": "Adopted",
    "open_for_signature": "Open for signature",
    "in_negotiation": "In negotiation",
    "withdrawn": "Withdrawn",
    "superseded": "Superseded",
    "unknown": "Unknown",
}

VERIFICATION_LABELS = {
    "full_text_checked": "Full text read",
    "metadata_verified": "Metadata verified",
    "source_located": "Source located",
}

# Natural Earth 1:110m omits several microstates. They are drawn as dots so that
# every party on the two maps is represented.
MICRO = {
    "AD": (1.52, 42.51),
    "LI": (9.55, 47.15),
    "MC": (7.42, 43.74),
    "MT": (14.37, 35.94),
    "SM": (12.46, 43.94),
    "SG": (103.82, 1.35),
}

ISO_OVERRIDES = {
    "Côte d’Ivoire": "CI",
    "Liechtenstein": "LI",
    "Malta": "MT",
    "Monaco": "MC",
    "Singapore": "SG",
    "Andorra": "AD",
    "San Marino": "SM",
}

NAME_ALIASES = {
    "czech republic": "czechia",
    "republic of korea": "south korea",
    "republic of moldova": "moldova",
    "united states": "united states of america",
}

TEAL = "#0e6b62"
RED = "#b23a2b"
BLUE = "#1e3a8a"
LIGHT_BLUE = "#8fb4dd"
LAND = "#e3ddd0"
OCEAN = "#eaf0ef"
INK = "#17150f"
PAPER = "#f7f2e7"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = value.lower().replace("’", "'").replace("–", "-")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def year_of(inst: dict) -> str:
    dates = inst.get("dates") or {}
    for key in ("adopted", "signed", "opened_for_signature", "published", "entered_into_force"):
        value = dates.get(key)
        if isinstance(value, str) and value[:4].isdigit():
            return value[:4]
    # ISO/IEC records verified only the publication month, not the day. Use the
    # year stated in the record note rather than inventing a full date.
    match = re.search(r"\b(19|20)\d{2}\b", str(dates.get("notes", "")))
    return match.group(0) if match else "—"


def sort_date(inst: dict) -> str:
    dates = inst.get("dates") or {}
    for key in ("adopted", "signed", "opened_for_signature", "published", "entered_into_force"):
        value = dates.get(key)
        if isinstance(value, str) and value[:4].isdigit():
            return value
    year = year_of(inst)
    return f"{year}-00-00" if year != "—" else "9999-99-99"


def timeline_date(inst: dict) -> str:
    dates = inst.get("dates") or {}
    if inst.get("id") == CETS_ID and dates.get("opened_for_signature"):
        return dates["opened_for_signature"]
    return dates.get("adopted") or sort_date(inst)


def source_url(inst: dict) -> str:
    sources = inst.get("sources") or []
    for source in sources:
        if source.get("kind") == "official_primary":
            return source.get("url", "")
    return sources[0].get("url", "") if sources else ""


def record_url(inst: dict) -> str:
    return f"{REPO}/blob/main/catalog/instruments/{inst['id']}.json"


def first_note(inst: dict) -> str:
    return (inst.get("title") or {}).get("short") or (inst.get("title") or {}).get("official", "")


def load_geo() -> tuple[list[dict], dict[str, dict], dict[str, dict]]:
    if not GEO.exists():
        raise SystemExit(f"missing map data: {GEO.relative_to(ROOT)}")
    data = json.loads(GEO.read_text(encoding="utf-8"))
    features = [f for f in data["features"] if f["properties"].get("ADMIN") != "Antarctica"]
    by_name: dict[str, dict] = {}
    by_iso: dict[str, dict] = {}
    for feature in features:
        props = feature["properties"]
        for key in (props.get("ADMIN"), props.get("NAME"), props.get("NAME_EN")):
            if key:
                by_name.setdefault(norm(key), feature)
        iso = props.get("ISO_A2_EH")
        if iso in (None, "", "-99"):
            iso = props.get("ISO_A2")
        if iso and iso not in ("-99", ""):
            by_iso.setdefault(iso, feature)
    return features, by_name, by_iso


def iso_for(party: str, by_name: dict[str, dict]) -> str:
    if party in ISO_OVERRIDES:
        return ISO_OVERRIDES[party]
    key = norm(party)
    key = NAME_ALIASES.get(key, key)
    feature = by_name.get(key)
    if feature is None:
        return ""
    props = feature["properties"]
    iso = props.get("ISO_A2_EH")
    if iso in (None, "", "-99"):
        iso = props.get("ISO_A2")
    return iso if iso not in (None, "", "-99") else ""


def project(lon: float, lat: float) -> tuple[float, float]:
    x = (lon + 180.0) / 360.0 * 1000.0
    y = (84.0 - lat) / 140.0 * 420.0
    return x, y


def ring_path(ring: list[list[float]]) -> str:
    """Project one ring, splitting it where it crosses the antimeridian."""
    chunks: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    previous_lon: float | None = None
    for point in ring:
        lon, lat = point[0], point[1]
        if previous_lon is not None and abs(lon - previous_lon) > 180:
            if len(current) >= 3:
                chunks.append(current)
            current = []
        current.append(project(lon, lat))
        previous_lon = lon
    if len(current) >= 3:
        chunks.append(current)
    return " ".join(
        "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in chunk) + " Z" for chunk in chunks
    )


def feature_path(feature: dict) -> str:
    geometry = feature.get("geometry") or {}
    kind = geometry.get("type")
    coordinates = geometry.get("coordinates") or []
    rings: list[list[list[float]]] = []
    if kind == "Polygon":
        rings = coordinates
    elif kind == "MultiPolygon":
        rings = [ring for polygon in coordinates for ring in polygon]
    return " ".join(filter(None, (ring_path(ring) for ring in rings)))


def map_fill_paris(iso: str, members: set[str]) -> tuple[str, str]:
    if iso in members:
        return TEAL, "Paris Statement signatory"
    if iso in {"US", "GB"}:
        return RED, "non-signatory (highlighted)"
    return LAND, "non-signatory"


def map_fill_cets(iso: str, members: set[str], ratified: set[str]) -> tuple[str, str]:
    if iso in ratified:
        return BLUE, "signature and ratification"
    if iso in members:
        return LIGHT_BLUE, "signature, no ratification"
    return LAND, "non-signatory"


def render_map(
    kind: str,
    title: str,
    description: str,
    members: set[str],
    ratified: set[str] | None = None,
    labels: dict[str, str] | None = None,
) -> str:
    features, _, by_iso = load_geo()
    ratified = ratified or set()
    labels = labels or {}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 420" '
        f'class="map-svg" role="img" aria-labelledby="map-{kind}-title map-{kind}-desc">',
        f'<title id="map-{kind}-title">{esc(title)}</title>',
        f'<desc id="map-{kind}-desc">{esc(description)}</desc>',
        f'<rect width="1000" height="420" fill="{OCEAN}"/>',
    ]
    for lat in (60, 30, 0, -30):
        _, y = project(0, lat)
        parts.append(
            f'<line x1="0" y1="{y:.1f}" x2="1000" y2="{y:.1f}" '
            f'stroke="#dbe4e1" stroke-width="1"/>'
        )
    for feature in sorted(features, key=lambda f: f["properties"]["ADMIN"]):
        props = feature["properties"]
        iso = props.get("ISO_A2_EH")
        if iso in (None, "", "-99"):
            iso = props.get("ISO_A2")
        iso = iso if iso not in (None, "-99") else ""
        if kind == "paris":
            fill, status = map_fill_paris(iso, members)
        else:
            fill, status = map_fill_cets(iso, members, ratified)
        path = feature_path(feature)
        if not path:
            continue
        parts.append(
            f'<path d="{path}" fill="{fill}" stroke="{PAPER}" stroke-width="0.7" '
            f'data-iso="{esc(iso)}"><title>{esc(props["ADMIN"])} — {esc(status)}</title></path>'
        )
    for iso, (lon, lat) in sorted(MICRO.items()):
        if iso not in members:
            continue
        if iso in by_iso:
            continue
        fill = BLUE if iso in ratified else (TEAL if kind == "paris" else LIGHT_BLUE)
        x, y = project(lon, lat)
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.8" fill="{fill}" '
            f'stroke="{PAPER}" stroke-width="1"><title>{esc(iso)} — member</title></circle>'
        )
    for iso, label in labels.items():
        feature = by_iso.get(iso)
        if not feature:
            continue
        props = feature["properties"]
        x, y = project(props["LABEL_X"], props["LABEL_Y"])
        parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" class="map-label">{esc(label)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def category_bars(category_counts: Counter) -> str:
    maximum = max(category_counts.values()) if category_counts else 1
    rows = []
    for category, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0])):
        width = count / maximum * 100
        rows.append(
            f'<div class="bar-row"><span class="bar-label">{esc(CATEGORY_LABELS[category])}</span>'
            f'<span class="bar-track"><span class="bar-fill cat-{esc(category)}" '
            f'style="width:{width:.1f}%"></span></span>'
            f'<span class="bar-value">{count}</span></div>'
        )
    return "".join(rows)


def year_chart(instruments: list[dict]) -> tuple[str, str]:
    by_year: dict[str, dict[str, int]] = defaultdict(lambda: {"binding": 0, "non_binding": 0, "other": 0})
    for inst in instruments:
        year = year_of(inst)
        if year == "—":
            continue
        binding = inst.get("binding_status")
        if binding == "binding":
            by_year[year]["binding"] += 1
        elif binding == "non_binding":
            by_year[year]["non_binding"] += 1
        else:
            by_year[year]["other"] += 1
    years = sorted(by_year)
    if not years:
        return "", ""
    maxima = max(sum(by_year[y].values()) for y in years)
    base = 212
    usable = 150
    slot = 920 / len(years)
    bar = min(46.0, slot * 0.56)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 260" class="chart-svg" role="img" aria-labelledby="years-title">',
        '<title id="years-title">Instruments adopted per year, binding and non-binding</title>',
        f'<line x1="36" y1="{base}" x2="976" y2="{base}" stroke="#8b8375" stroke-width="1"/>',
    ]
    for index, year in enumerate(years):
        counts = by_year[year]
        total = sum(counts.values())
        height = total / maxima * usable
        h_binding = counts["binding"] / maxima * usable
        h_non = counts["non_binding"] / maxima * usable
        h_other = counts["other"] / maxima * usable
        x = 40 + index * slot + (slot - bar) / 2
        y = base - height
        parts.append(
            f'<rect x="{x:.1f}" y="{y + h_binding + h_other:.1f}" width="{bar:.1f}" '
            f'height="{h_non:.1f}" fill="{TEAL}"><title>{year}: {counts["non_binding"]} non-binding</title></rect>'
        )
        parts.append(
            f'<rect x="{x:.1f}" y="{y + h_other:.1f}" width="{bar:.1f}" '
            f'height="{h_binding:.1f}" fill="{INK}"><title>{year}: {counts["binding"]} binding</title></rect>'
        )
        if h_other:
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar:.1f}" height="{h_other:.1f}" '
                f'fill="#8b8375"><title>{year}: {counts["other"]} other</title></rect>'
            )
        parts.append(
            f'<text x="{x + bar / 2:.1f}" y="{y - 7:.1f}" class="chart-count">{total}</text>'
        )
        parts.append(
            f'<text x="{x + bar / 2:.1f}" y="{base + 20}" class="chart-year">{year}</text>'
        )
    parts.append("</svg>")
    return "".join(parts), "Years present in the corpus; the scale is not continuous."


def binding_bar(instruments: list[dict]) -> str:
    counts = Counter(inst.get("binding_status") for inst in instruments)
    total = len(instruments)
    segments = []
    for key, css in (("binding", "seg-binding"), ("non_binding", "seg-nonbinding"), ("mixed", "seg-other"), ("unknown", "seg-other")):
        count = counts.get(key, 0)
        if not count:
            continue
        segments.append(
            f'<span class="{css}" style="width:{count / total * 100:.2f}%">'
            f'{count} {esc(BINDING_LABELS[key].lower())}</span>'
        )
    return '<div class="stack" role="img" aria-label="Split between binding and non-binding instruments">' + "".join(segments) + "</div>"


def search_text(inst: dict, title: str) -> str:
    category = inst["category"]
    binding = inst["binding_status"]
    status = inst["status"]
    verification = inst["verification"]["level"]
    parts = [
        inst["id"],
        title,
        category,
        CATEGORY_LABELS[category],
        binding,
        BINDING_LABELS[binding],
        status,
        STATUS_LABELS[status],
        verification,
        VERIFICATION_LABELS[verification],
        year_of(inst),
    ]
    title_l = title.lower()
    if "united nations" in title_l or inst["id"].startswith("un-ga"):
        parts.append("un")
    if "china" in title_l or inst["id"].startswith("china"):
        parts.append("china")
    if "paris" in title_l or inst["id"].startswith("paris"):
        parts.append("paris")
    if "council of europe" in title_l:
        parts.append("coe")
    if "european union" in title_l or inst["id"].startswith("eu-"):
        parts.append("eu")
    if "treaty" in title_l or category in {"ai_treaty", "general_treaty"}:
        parts.append("treaty")
    if "artificial intelligence" in title_l:
        parts.append("ai")
    return " ".join(parts).lower()


def badge(css: str, label: str, title: str = "") -> str:
    title_attr = f' title="{esc(title)}"' if title else ""
    return f'<span class="badge {css}"{title_attr}>{esc(label)}</span>'


def table_rows(instruments: list[dict]) -> str:
    rows = []
    for inst in sorted(instruments, key=lambda i: (sort_date(i), i["id"]), reverse=True):
        url = source_url(inst)
        title = (inst.get("title") or {}).get("official", inst["id"])
        title_html = (
            f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(title)}</a>'
            if url
            else esc(title)
        )
        category = inst["category"]
        binding = inst["binding_status"]
        status = inst["status"]
        verification = inst["verification"]["level"]
        search = search_text(inst, title)
        rows.append(
            f'<tr data-search="{esc(search)}">'
            f'<td class="year">{year_of(inst)}</td>'
            f'<td class="title-cell">{title_html}<span class="record-id">{esc(inst["id"])}</span></td>'
            f'<td>{badge("cat-" + category, CATEGORY_LABELS[category])}</td>'
            f'<td>{badge("bind-" + binding, BINDING_LABELS[binding])}</td>'
            f'<td>{esc(STATUS_LABELS[status])}</td>'
            f'<td>{badge("ver-" + verification, VERIFICATION_LABELS[verification], verification)}</td>'
            f'<td class="json-link"><a href="{esc(record_url(inst))}" target="_blank" rel="noopener">JSON</a></td>'
            "</tr>"
        )
    return "".join(rows)


def milestones(instruments_by_id: dict[str, dict]) -> str:
    notes = {
        "iccpr-1966": "The general framework for civil and political rights.",
        "vclt-1969": "The rules on the law of treaties.",
        "oecd-ai-recommendation-2019": "The first intergovernmental standard dedicated to AI.",
        "unesco-ethics-ai-2021": "AI ethics adopted by 193 States.",
        "political-declaration-military-ai-2023": "US-led political declaration on military AI.",
        "china-global-ai-governance-initiative-2023": "The Chinese proposal: sovereignty, development and a central UN role.",
        "g7-hiroshima-code-2023": "Voluntary code for advanced AI developers.",
        "bletchley-declaration-2023": "28 States and the EU on frontier-model risk.",
        "us-uk-ai-safety-mou-2024": "A bilateral AI-safety MOU between the UK and US institutes.",
        "us-eu-ttc-ai-safety-dialogue-2024": "The US–EU TTC statement commits the European AI Office and the US AI Safety Institute to a technical Dialogue.",
        "un-ga-res-78-265": "First UN resolution on AI adopted by consensus.",
        "coe-cets-225": "The only AI-specific treaty; not yet in force.",
        "un-ga-res-79-1": "Pact for the Future and Global Digital Compact.",
        "paris-ai-action-summit-statement-2025": "The Paris Statement: China and India in, the United States and the UK out.",
        "ccw-gge-laws-2026": "2027–2028 mandate to negotiate an instrument on autonomous weapons.",
    }
    items = []
    for iid, note in notes.items():
        inst = instruments_by_id.get(iid)
        if not inst:
            continue
        date = timeline_date(inst)
        title = first_note(inst)
        items.append((date, iid, title, note, record_url(inst)))
    items.sort()
    rows = []
    for date, iid, title, note, url in items:
        rows.append(
            f'<li><time datetime="{esc(date)}">{esc(date)}</time>'
            f'<div><a href="{esc(url)}" target="_blank" rel="noopener">{esc(title)}</a>'
            f'<p>{esc(note)}</p></div></li>'
        )
    return '<ol class="timeline">' + "".join(rows) + "</ol>"


def main() -> int:
    instruments = list(corpuslib.load_instruments().values())
    by_id = {inst["id"]: inst for inst in instruments}
    total = len(instruments)
    counts = Counter(inst["binding_status"] for inst in instruments)
    category_counts = Counter(inst["category"] for inst in instruments)
    verification_counts = Counter(inst["verification"]["level"] for inst in instruments)
    binding = counts.get("binding", 0)
    non_binding = counts.get("non_binding", 0)
    in_force = sum(1 for inst in instruments if inst["binding_status"] == "binding" and inst["status"] == "in_force")
    not_in_force = binding - in_force
    full_texts = sum(1 for inst in instruments if (inst.get("text") or {}).get("full_text"))
    originals = 0
    for inst in instruments:
        text = inst.get("text") or {}
        if not text:
            continue
        manifest_path = corpuslib.CORPUS_DIR / inst["id"] / text["manifest"]
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if any(entry.get("role") == "original" for entry in manifest.get("files", [])):
            originals += 1
    verified_on = max((inst.get("dates") or {}).get("verified_on", "") for inst in instruments)

    paris = by_id[PARIS_ID]
    cets = by_id[CETS_ID]
    paris_entries = paris["parties"]["entries"]
    paris_orgs = {"European Union", "African Union Commission"}
    paris_states = [entry["party"] for entry in paris_entries if entry["party"] not in paris_orgs]
    cets_entries = cets["parties"]["entries"]
    cets_states = [entry["party"] for entry in cets_entries if entry["party"] != "European Union"]
    cets_ratified = [entry["party"] for entry in cets_entries if entry.get("ratification")]
    cets_ratified_states = [name for name in cets_ratified if name != "European Union"]

    _, by_name, _ = load_geo()
    paris_iso = {iso_for(name, by_name) for name in paris_states}
    cets_iso = {iso_for(name, by_name) for name in cets_states}
    missing = [name for name in paris_states + cets_states if not iso_for(name, by_name)]
    if missing:
        raise SystemExit("map name lookup failed for: " + ", ".join(sorted(set(missing))))
    paris_iso.discard("")
    cets_iso.discard("")
    cets_ratified_iso = {iso_for(name, by_name) for name in cets_ratified_states}
    cets_ratified_iso.discard("")

    labels = {"US": "USA", "GB": "UK", "CN": "China", "IN": "India", "BR": "Brazil"}
    paris_map = render_map(
        "paris",
        "Paris Statement signatories (2025)",
        f"{len(paris_states)} signatory States; the United States and the United Kingdom are highlighted in red; China and India in green.",
        paris_iso,
        labels=labels,
    )
    cets_map = render_map(
        "cets",
        "CETS 225 signatures and ratifications",
        f"{len(cets_states)} signatory States; {len(cets_ratified_states)} State has ratified. The European Union is a party but is not shown.",
        cets_iso,
        ratified=cets_ratified_iso,
        labels=labels,
    )

    # Cross-membership for the matrix.
    paris_set = set(paris_states)
    cets_by_party = {entry["party"]: entry for entry in cets_entries}
    matrix_rows = []
    for label, party in (
        ("China", "China"),
        ("United States", "United States of America"),
        ("United Kingdom", "United Kingdom"),
        ("India", "India"),
        ("France", "France"),
        ("Japan", "Japan"),
        ("Canada", "Canada"),
        ("Brazil", "Brazil"),
    ):
        in_paris = party in paris_set
        entry = cets_by_party.get(party)
        if entry and entry.get("ratification"):
            cets_state = "signature + ratification"
        elif entry:
            cets_state = "signature"
        else:
            cets_state = "no"
        matrix_rows.append(
            f'<tr><th scope="row">{esc(label)}</th>'
            f'<td class="{"yes" if in_paris else "no"}">{"yes" if in_paris else "no"}</td>'
            f'<td class="{"yes" if entry else "no"}">{esc(cets_state)}</td></tr>'
        )
    matrix = "".join(matrix_rows)

    chart, chart_note = year_chart(instruments)

    cards = [
        (
            "Washington",
            "Political declaration",
            "Political Declaration on Responsible Military Use of AI and Autonomy",
            "58 States",
            "endorsers as of December 2024; non-binding; the list is not reproduced country by country.",
            "political-declaration-military-ai-2023",
        ),
        (
            "Beijing",
            "Government proposal",
            "Global AI Governance Initiative",
            "No adherence list",
            "2023 unilateral initiative; non-binding; the 2025 Action Plan is a later document in the same policy line.",
            CHINA_ID,
        ),
        (
            "Brussels / Strasbourg",
            "Council of Europe treaty",
            "Council of Europe Framework Convention on AI (CETS 225)",
            "21 signatures · 2 ratifications",
            "binding treaty, not in force; open to non-European States as well.",
            CETS_ID,
        ),
    ]
    cards_html = "".join(
        f'<article class="pole"><p class="pole-place">{esc(place)}</p>'
        f'<p class="pole-tag">{esc(tag)}</p>'
        f'<h3><a href="{esc(record_url(by_id[iid]))}" target="_blank" rel="noopener">{esc(title)}</a></h3>'
        f'<p class="pole-metric">{esc(metric)}</p><p class="pole-note">{esc(note)}</p></article>'
        for place, tag, title, metric, note, iid in cards
    )

    stat_cards = [
        (str(total), "catalogued instruments", "One record per instrument, with source and verification level."),
        (str(binding), "binding instruments", f"{in_force} in force; {not_in_force} not yet in force."),
        ("1", "AI-specific treaty", "CETS 225: 21 signatures, 2 ratifications, not in force."),
        (str(full_texts), "full texts", f"{originals} originals preserved and SHA-256 hashed."),
    ]
    stats_html = "".join(
        f'<div class="stat"><p class="stat-number">{esc(number)}</p>'
        f'<p class="stat-label">{esc(label)}</p><p class="stat-note">{esc(note)}</p></div>'
        for number, label, note in stat_cards
    )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>International AI Law Atlas</title>
<meta name="description" content="Verified instruments, maps, timeline and catalogue of international AI law.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<header class="masthead">
  <div class="wrap">
    <p class="kicker">Verified corpus · verification {esc(verified_on)}</p>
    <h1>International AI Law Atlas</h1>
    <p class="byline">{total} instruments · {full_texts} full texts · {originals} originals with SHA-256 · {binding} binding</p>
    <nav class="toc" aria-label="Sections">
      <a href="#overview">Overview</a>
      <a href="#binding">Binding or not</a>
      <a href="#poles">Three poles</a>
      <a href="#maps">Maps</a>
      <a href="#timeline">Timeline</a>
      <a href="#catalogue">Catalogue</a>
      <a href="#method">Method</a>
    </nav>
  </div>
</header>

<main id="content">
  <section id="overview" class="section">
    <div class="wrap">
      <div class="stats">{stats_html}</div>
      <div class="intro-grid">
        <div>
          <h2>The shape of the corpus</h2>
          <p class="lede">One AI-specific treaty, five trade agreements with AI provisions, a stack of declarations and resolutions, technical standards, and a negotiation on autonomous weapons. The binding layer is thin; the political layer is dense.</p>
        </div>
        <aside class="callout">
          <p><strong>Key point.</strong> There is no single international AI regime. There are overlapping regimes, with different obligations, different members and different legal force.</p>
          <p><a href="{REPO}/blob/main/README.md" target="_blank" rel="noopener">Read the corpus README</a></p>
        </aside>
      </div>
    </div>
  </section>

  <section id="binding" class="section">
    <div class="wrap">
      <p class="eyebrow">01 · What binds</p>
      <h2>Binding or not</h2>
      <p class="lede">In the corpus, {binding} instruments are binding and {non_binding} are not.</p>
      {binding_bar(instruments)}
      <div class="legend">
        <span><i class="swatch swatch-binding"></i>Binding</span>
        <span><i class="swatch swatch-nonbinding"></i>Non-binding</span>
      </div>
      <div class="two-col">
        <div>
          <h3>What “binding” means here</h3>
          <p>A treaty in force, a trade agreement in force, European Union law and two general framework treaties. It does not mean the obligation is detailed: CETS 225 is a framework treaty and the AfCFTA is not yet in force.</p>
          <p>Declarations, UN resolutions, recommendations, codes of conduct and technical standards are non-binding. They are not irrelevant: they set direction, create expectations and prepare the ground for later rules.</p>
        </div>
        <div>
          <h3>By category · {sum(category_counts.values())} instruments</h3>
          <div class="bars">{category_bars(category_counts)}</div>
        </div>
      </div>
    </div>
  </section>

  <section id="poles" class="section section-dark">
    <div class="wrap">
      <p class="eyebrow">02 · Three poles</p>
      <h2>Three poles</h2>
      <div class="poles">{cards_html}</div>
      <div class="paris-band">
        <div>
          <p class="eyebrow">Cross-cutting</p>
          <h3>Paris 2025: China and India in, the United States and the UK out</h3>
          <p>The Paris Statement is endorsed by {len(paris_states)} States, the European Union and the African Union Commission. It is the broadest instrument of the period and shows a fracture that does not track the China–US axis.</p>
        </div>
        <p class="paris-metric">{len(paris_states)}<span>signatory States</span></p>
      </div>
      <h3 class="matrix-title">Who stands where</h3>
      <table class="matrix">
        <caption>Membership derived from the corpus records. “Signature” means signature without ratification.</caption>
        <thead><tr><th scope="col">Country</th><th scope="col">Paris 2025</th><th scope="col">CETS 225</th></tr></thead>
        <tbody>{matrix}</tbody>
      </table>
      <p class="note">The overlap is the point: the United States and the United Kingdom signed CETS 225 but not the Paris Statement; China endorsed Paris but did not sign CETS 225. Normative alignments do not match military ones.</p>
    </div>
  </section>

  <section id="maps" class="section">
    <div class="wrap">
      <p class="eyebrow">03 · Two maps</p>
      <h2>Who signs what</h2>
      <div class="maps">
        <figure class="map-card">
          <figcaption><span class="map-title">Paris 2025</span><span class="map-sub">{len(paris_states)} signatory States; EU and AU Commission not shown</span></figcaption>
          {paris_map}
          <div class="map-legend">
            <span><i class="swatch" style="background:{TEAL}"></i>Signatory</span>
            <span><i class="swatch" style="background:{RED}"></i>USA / UK: no</span>
            <span><i class="swatch" style="background:{LAND}"></i>Non-signatory</span>
          </div>
          <p class="note">The list is the Élysée page as accessed on {esc(verified_on)}. The official PDF of 19 February 2025 lists 64; the page lists 65. The difference is documented in the record.</p>
        </figure>
        <figure class="map-card">
          <figcaption><span class="map-title">CETS 225</span><span class="map-sub">{len(cets_states)} signatory States; 1 State has ratified; EU party not shown</span></figcaption>
          {cets_map}
          <div class="map-legend">
            <span><i class="swatch" style="background:{BLUE}"></i>Signature + ratification</span>
            <span><i class="swatch" style="background:{LIGHT_BLUE}"></i>Signature</span>
            <span><i class="swatch" style="background:{LAND}"></i>Non-signatory</span>
          </div>
          <p class="note">Bosnia and Herzegovina ratified on 28 October 2026; the European Union on 15 May 2026. The treaty is not in force: five ratifications are required, including three Council of Europe member States.</p>
        </figure>
      </div>
      <p class="source-note">Boundaries: Natural Earth 1:110m Admin 0 Countries, public domain. The maps do not imply recognition of boundaries or sovereignty.</p>
    </div>
  </section>

  <section id="timeline" class="section">
    <div class="wrap">
      <p class="eyebrow">04 · How we got here</p>
      <h2>Timeline</h2>
      <p class="lede">The corpus runs from the general framework of 1966 to the instruments of 2026. The chart counts instruments adopted per year; the timeline selects the turning points.</p>
      {chart}
      <p class="source-note">{esc(chart_note)}</p>
      {milestones(by_id)}
    </div>
  </section>

  <section id="catalogue" class="section">
    <div class="wrap">
      <p class="eyebrow">05 · The catalogue</p>
      <h2>All instruments</h2>
      <p class="lede">Click a title for the official source, “JSON” for the verifiable record. The filter searches the title, identifier, category and status.</p>
      <div class="catalogue-tools">
        <label for="filter">Filter</label>
        <input id="filter" type="search" placeholder="e.g. treaty, UN, China, 2026…" autocomplete="off">
        <span class="shown"><strong id="shown">{total}</strong> / {total} instruments</span>
      </div>
      <div class="table-wrap">
        <table class="catalogue" id="catalogue">
          <caption>Catalogue generated from catalog/instruments/*.json. The year is the verified date of adoption, signature, opening for signature or publication; for standards it is the year stated in the record.</caption>
          <thead><tr><th scope="col">Year</th><th scope="col">Instrument</th><th scope="col">Category</th><th scope="col">Force</th><th scope="col">Status</th><th scope="col">Verification</th><th scope="col"></th></tr></thead>
          <tbody>{table_rows(instruments)}</tbody>
        </table>
      </div>
    </div>
  </section>

  <section id="method" class="section section-dark">
    <div class="wrap">
      <p class="eyebrow">06 · Method and limits</p>
      <h2>How it is verified</h2>
      <div class="method-grid">
        <div>
          <h3>The chain of proof</h3>
          <ul class="checks">
            <li><strong>{total}</strong> records in <code>catalog/instruments/</code>, each with source, access date and verification level.</li>
            <li><strong>{full_texts}</strong> full texts preserved; <strong>{originals}</strong> originals with SHA-256 in <code>catalog/acquisitions.json</code> and in the manifest.</li>
            <li><strong>{verification_counts.get("full_text_checked", 0)}</strong> texts read end-to-end; <strong>{verification_counts.get("metadata_verified", 0)}</strong> records verified at metadata level; <strong>{verification_counts.get("source_located", 0)}</strong> sources located.</li>
            <li>Citable units with character offsets and page numbers; the build is deterministic and offline.</li>
          </ul>
        </div>
        <div>
          <h3>What is missing</h3>
          <ul class="checks">
            <li>CETS 225 is not in force: 21 signatures, 2 ratifications.</li>
            <li>Only one AI-specific treaty: this does not mean no others exist, but that no other has been located and verified.</li>
            <li>No international complaint, sanction or judicial review mechanism is established by these instruments.</li>
            <li>Latin America, the Middle East and Central Asia remain uncovered by verified regional instruments.</li>
            <li>ISO/IEC standards are paywalled: metadata only. English texts only; no translation is presented as authentic.</li>
            <li>No national implementation or compliance data.</li>
          </ul>
        </div>
      </div>
      <div class="license">
        <p><strong>Licence.</strong> Code, metadata and documentation: © 2026 Avvohacker, all rights reserved. Official texts remain the property of their respective owners and are not covered by this licence.</p>
        <p><strong>Not legal advice.</strong> Before citing or relying on an instrument, check the official source and its current status.</p>
        <p><a href="{REPO}" target="_blank" rel="noopener">Repository and reproduction instructions</a> · <a href="{REPO}/blob/main/docs/methodology.md" target="_blank" rel="noopener">Methodology</a> · <a href="{REPO}/blob/main/docs/progress.md" target="_blank" rel="noopener">Remaining work</a></p>
      </div>
    </div>
  </section>
</main>

<footer class="footer">
  <div class="wrap footer-inner">
    <p><strong>International AI Law Atlas</strong><br>Generated by <code>tools/build_site.py</code> from the verified corpus.</p>
    <p>Verification: {esc(verified_on)}<br>{total} instruments · {full_texts} full texts</p>
  </div>
</footer>
<script src="assets/app.js?v=2"></script>
</body>
</html>
"""
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "index.html").write_text(page, encoding="utf-8")
    print(f"site/index.html: {len(page):,} chars, {total} instruments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
