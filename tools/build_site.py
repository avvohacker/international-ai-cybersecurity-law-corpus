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
ORGANISATIONS = ROOT / "data" / "organisations.json"
REPO = "https://github.com/avvohacker/international-ai-law-corpus"

PARIS_ID = "paris-ai-action-summit-statement-2025"
CETS_ID = "coe-cets-225"
CHINA_ID = "china-global-ai-governance-initiative-2023"
BLETCHLEY_ID = "bletchley-declaration-2023"
SEOUL_ID = "seoul-declaration-2024"
MILITARY_ID = "political-declaration-military-ai-2023"
WAICO_ID = "waico-establishment-agreement-2026"
PAX_ID = "pax-silica-declaration-2025"

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

OFFICIAL_SOURCE_KINDS = {"official_primary", "registry", "official_journal"}
SOURCE_LABELS = {
    "elysee-page": "Élysée page",
    "elysee-pdf": "Élysée PDF",
    "elysee-fr": "Élysée French text",
    "govuk-declaration": "GOV.UK declaration",
    "govuk-seoul": "GOV.UK Seoul declaration",
    "state-page": "State Department page",
    "coe-text": "CETS 225 text",
    "coe-status": "CETS 225 status chart",
    "eu-oj-2026-1081": "EU Official Journal",
    "eu-decision-2026-1080": "EU Council Decision",
    "coe-declarations": "CETS 225 declarations",
    "mfa-signing": "MFA signing account",
    "mfa-ratification": "MFA ratification statement",
    "npc-decision": "NPC decision",
    "mfa-progress-report": "MFA progress report",
    "mfa-31-july": "MFA 31 July account",
    "indonesia-founding-list": "Indonesia founding list",
    "state-pax-silica": "State Department Pax Silica page",
    "state-second-summit": "State Department second-summit fact sheet",
    "state-paraguay": "State Department Paraguay release",
    "australia-declaration": "Australian Government declaration",
    "australia-pdf": "Australian Government signed PDF",
    "state-taiwan-joint-statement": "State Department Taiwan statement",
    "state-ai-opportunity": "State Department AI Opportunity page",
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

MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
NUMBER_WORDS = {
    0: "no",
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
}


def format_date(value: str) -> str:
    """Render an ISO date from a record as a human-readable date."""
    try:
        year, month, day = (int(part) for part in value.split("-"))
        return f"{day} {MONTHS[month - 1]} {year}"
    except (AttributeError, ValueError, IndexError):
        return value


def number_word(value: int) -> str:
    return NUMBER_WORDS.get(value, str(value))


def join_with_and(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]

# Natural Earth 1:110m omits several microstates. They are drawn as dots so that
# every party on the maps is represented.
MICRO = {
    "AD": (1.52, 42.51),
    "AG": (-61.80, 17.10),
    "BH": (50.55, 26.07),
    "DM": (-61.37, 15.41),
    "LI": (9.55, 47.15),
    "MC": (7.42, 43.74),
    "MT": (14.37, 35.94),
    "SM": (12.46, 43.94),
    "SG": (103.82, 1.35),
    "CV": (-23.60, 15.10),
    "KM": (43.30, -11.70),
    "MU": (57.60, -20.30),
    "ST": (6.60, 0.30),
    "SC": (55.50, -4.60),
}

ISO_OVERRIDES = {
    "Antigua and Barbuda": "AG",
    "Bahrain": "BH",
    "Côte d’Ivoire": "CI",
    "Dominica": "DM",
    "Kingdom of Saudi Arabia": "SA",
    "Liechtenstein": "LI",
    "Malta": "MT",
    "Monaco": "MC",
    "Singapore": "SG",
    "Andorra": "AD",
    "San Marino": "SM",
    "Türkiye": "TR",
    "Cabo Verde": "CV",
    "Comoros": "KM",
    "Mauritius": "MU",
    "Sahrawi Arab Democratic Republic": "EH",
    "São Tomé and Príncipe": "ST",
    "Seychelles": "SC",
}

NAME_ALIASES = {
    "czech republic": "czechia",
    "republic of korea": "south korea",
    "republic of moldova": "moldova",
    "united states": "united states of america",
}

TEAL = "#0e6b62"
ACT_BLUE = "#5a7fbd"
RATIFIED_BLUE = "#172e6e"
ORG_MEMBER_BLUE = "#a9c0e0"
LAND = "#e3ddd0"
OCEAN = "#eaf0ef"
INK = "#17150f"
PAPER = "#f7f2e7"

# The maps encode the legal act, not the degree of political alignment.
STATUS_FILL = {
    "endorsed": ACT_BLUE,
    "signed": ACT_BLUE,
    "ratified": RATIFIED_BLUE,
    "organisation": ORG_MEMBER_BLUE,
    "none": LAND,
}
STATUS_TITLE = {
    "endorsed": "endorsed",
    "signed": "signature only",
    "ratified": "ratified",
    "organisation": "member of a participating international organisation; no individual act",
    "none": "no recorded act",
}


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


def load_organisations() -> dict[str, dict]:
    if not ORGANISATIONS.exists():
        raise SystemExit(f"missing organisation data: {ORGANISATIONS.relative_to(ROOT)}")
    data = json.loads(ORGANISATIONS.read_text(encoding="utf-8"))
    return {org["name"]: org for org in data["organisations"]}


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


def render_map(
    kind: str,
    title: str,
    description: str,
    state_status: dict[str, str],
    legend: list[dict] | None = None,
    legend_note: str = "",
) -> str:
    features, _, by_iso = load_geo()
    legend = legend or []
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
        status = state_status.get(iso, "none")
        fill = STATUS_FILL[status]
        path = feature_path(feature)
        if not path:
            continue
        parts.append(
            f'<path d="{path}" fill="{fill}" stroke="{PAPER}" stroke-width="0.7" '
            f'data-iso="{esc(iso)}"><title>{esc(props["ADMIN"])} — {esc(STATUS_TITLE[status])}</title></path>'
        )
    for iso, (lon, lat) in sorted(MICRO.items()):
        if iso not in state_status:
            continue
        if iso in by_iso:
            continue
        status = state_status[iso]
        fill = STATUS_FILL[status]
        x, y = project(lon, lat)
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.8" fill="{fill}" '
            f'stroke="{PAPER}" stroke-width="1"><title>{esc(iso)} — {esc(STATUS_TITLE[status])}</title></circle>'
        )
    parts.append("</svg>")

    key_rows = []
    for item in legend:
        key_rows.append(
            f'<span class="key-row"><i class="swatch" style="background:{item["color"]}"></i>'
            f'{esc(item["label"])}</span>'
        )
    note = f'<p class="key-note">{esc(legend_note)}</p>' if legend_note else ""
    key = f'<div class="map-key" aria-label="Map legend">{"".join(key_rows)}{note}</div>'
    return f'<div class="map-frame">{"".join(parts)}{key}</div>'


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
        "unesco-ethics-ai-2021": "AI ethics adopted by UNESCO's Member States.",
        "political-declaration-military-ai-2023": "US-led political declaration on military AI.",
        "china-global-ai-governance-initiative-2023": "The Chinese proposal: sovereignty, development and a central UN role.",
        "g7-hiroshima-code-2023": "Voluntary code for advanced AI developers.",
        "bletchley-declaration-2023": "Signatories including the EU on frontier-model risk.",
        "us-uk-ai-safety-mou-2024": "A bilateral AI-safety MOU between the UK and US institutes.",
        "us-eu-ttc-ai-safety-dialogue-2024": "The US–EU TTC statement commits the European AI Office and the US AI Safety Institute to a technical Dialogue.",
        "un-ga-res-78-265": "First UN resolution on AI adopted by consensus.",
        "coe-cets-225": "The first AI-specific treaty; not yet in force.",
        "un-ga-res-79-1": "Pact for the Future and Global Digital Compact.",
        "paris-ai-action-summit-statement-2025": "The Paris Statement: China and India endorsed; the United States and the UK did not.",
        "ccw-gge-laws-2026": "Mandate to negotiate an instrument on autonomous weapons; report due 2028.",
    }
    items = []
    for iid, note in notes.items():
        inst = instruments_by_id.get(iid)
        if not inst:
            continue
        if iid == "bletchley-declaration-2023":
            note = (
                f"{len((inst.get('parties') or {}).get('entries') or [])} signatories, "
                "including the EU, on frontier-model risk."
            )
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
    bletchley = by_id[BLETCHLEY_ID]
    seoul = by_id[SEOUL_ID]
    military = by_id[MILITARY_ID]
    waico = by_id[WAICO_ID]
    pax = by_id[PAX_ID]

    organisations = load_organisations()
    org_names = set(organisations)

    def state_names(inst: dict) -> list[str]:
        return [
            entry["party"]
            for entry in inst["parties"]["entries"]
            if entry["party"] not in org_names
        ]

    paris_states = state_names(paris)
    cets_states = state_names(cets)
    bletchley_states = state_names(bletchley)
    seoul_states = state_names(seoul)
    military_states = state_names(military)
    waico_states = state_names(waico)
    pax_states = state_names(pax)
    cets_entries = cets["parties"]["entries"]

    def entries(inst: dict) -> list[dict]:
        return (inst.get("parties") or {}).get("entries") or []

    def ratified_entries(inst: dict) -> list[dict]:
        return [entry for entry in entries(inst) if entry.get("ratification")]

    def reported_total(inst: dict) -> int:
        return int(
            (inst.get("parties") or {}).get("signatories_total") or len(entries(inst))
        )

    def force_phrase(inst: dict) -> str:
        return "in force" if inst.get("status") == "in_force" else "not in force"

    def org_short(inst: dict) -> str:
        labels = {"European Union": "EU", "African Union Commission": "AU Commission"}
        return " + ".join(
            labels.get(entry["party"], entry["party"])
            for entry in entries(inst)
            if entry["party"] in org_names
        )

    _, by_name, by_iso = load_geo()

    def iso_set(names: list[str], map_name: str) -> set[str]:
        values: set[str] = set()
        missing: list[str] = []
        for name in names:
            iso = iso_for(name, by_name)
            if not iso:
                missing.append(name)
            else:
                values.add(iso)
        if missing:
            raise SystemExit(
                f"map {map_name}: name lookup failed for: " + ", ".join(sorted(set(missing)))
            )
        return values

    paris_iso = iso_set(paris_states, "Paris 2025")
    cets_iso = iso_set(cets_states, "CETS 225")
    bletchley_iso = iso_set(bletchley_states, "Bletchley 2023")
    seoul_iso = iso_set(seoul_states, "Seoul 2024")
    military_iso = iso_set(military_states, "Military AI 2023")
    waico_iso = iso_set(waico_states, "WAICO 2026")
    pax_iso = iso_set(pax_states, "Pax Silica 2025")

    for map_name, values in (
        ("Paris 2025", paris_iso),
        ("CETS 225", cets_iso),
        ("Bletchley 2023", bletchley_iso),
        ("Seoul 2024", seoul_iso),
        ("Military AI 2023", military_iso),
        ("WAICO 2026", waico_iso),
        ("Pax Silica 2025", pax_iso),
    ):
        absent = sorted(iso for iso in values if iso not in by_iso and iso not in MICRO)
        if absent:
            raise SystemExit(
                f"map {map_name}: no polygon or micro dot for: " + ", ".join(absent)
            )

    paris_status = {iso: "endorsed" for iso in paris_iso}
    bletchley_status = {iso: "endorsed" for iso in bletchley_iso}
    seoul_status = {iso: "endorsed" for iso in seoul_iso}
    military_status = {iso: "endorsed" for iso in military_iso}
    waico_status = {iso: "signed" for iso in waico_iso}
    pax_status = {iso: "endorsed" for iso in pax_iso}
    cets_status = {iso: "signed" for iso in cets_iso}
    for entry in cets_entries:
        if entry.get("ratification") and entry["party"] not in org_names:
            cets_status[iso_for(entry["party"], by_name)] = "ratified"

    def add_org_members(status: dict[str, str], inst: dict, default: str) -> list[str]:
        """Mark member States of a party organisation that did not act themselves.

        A member State that signed, ratified or endorsed in its own right keeps
        its own colour; the organisation is named outside the map frame. When
        every member State acted individually, nothing is shown at all.
        """
        notes: list[str] = []
        parties = {entry["party"] for entry in inst["parties"]["entries"]}
        for name in sorted(parties & org_names):
            org = organisations[name]
            covered = 0
            for member in org["members"]:
                iso = iso_for(member, by_name)
                if not iso:
                    raise SystemExit(
                        f"map {name}: membership name lookup failed for {member}"
                    )
                if iso not in by_iso and iso not in MICRO:
                    raise SystemExit(
                        f"map {name}: no polygon or micro dot for {member} ({iso})"
                    )
                if iso not in status:
                    status[iso] = "organisation"
                    covered += 1
            if not covered:
                continue
            entry = next(
                entry for entry in inst["parties"]["entries"] if entry["party"] == name
            )
            if entry.get("ratification"):
                action, noun = "ratified", "signature"
            elif default == "endorsed":
                action, noun = "endorsed", "endorsement"
            else:
                action, noun = "signed", "signature"
            notes.append(
                f"{name}: {action}. {covered} {org['member_label']} member States "
                f"without an individual {noun} are shown in the lighter tone."
            )
        return notes

    paris_org_notes = add_org_members(paris_status, paris, "endorsed")
    bletchley_org_notes = add_org_members(bletchley_status, bletchley, "endorsed")
    seoul_org_notes = add_org_members(seoul_status, seoul, "endorsed")
    cets_org_notes = add_org_members(cets_status, cets, "signed")
    pax_org_notes = add_org_members(pax_status, pax, "endorsed")

    endorsement_legend = [
        {"color": ACT_BLUE, "label": "State: endorsed"},
        {"color": LAND, "label": "State: not endorsed"},
    ]
    cets_legend = [
        {"color": RATIFIED_BLUE, "label": "State: ratified"},
        {"color": ACT_BLUE, "label": "State: signed only"},
        {"color": LAND, "label": "State: no signature"},
    ]
    waico_legend = [
        {"color": ACT_BLUE, "label": "State: signed only"},
        {"color": LAND, "label": "State: no signature"},
    ]

    def render_party_list(inst: dict, default: str) -> str:
        """List the recorded parties under a map, grouped by recorded act."""
        has_ratifications = bool(ratified_entries(inst))
        groups: dict[str, list[dict]] = defaultdict(list)
        for entry in entries(inst):
            if entry.get("ratification"):
                group = "Ratified"
            elif has_ratifications:
                group = "Signed only"
            elif default == "endorsed":
                group = "Endorsed"
            else:
                group = "Signed"
            groups[group].append(entry)
        blocks = []
        for group in ("Ratified", "Signed only", "Signed", "Endorsed"):
            items = sorted(groups.get(group, []), key=lambda entry: entry["party"])
            if not items:
                continue
            list_items = []
            for entry in items:
                suffix = ""
                if entry["party"] in org_names:
                    suffix += ' <span class="party-kind">organisation</span>'
                if entry.get("approval") and not entry.get("ratification"):
                    suffix += (
                        f' <span class="party-kind">ratification approved '
                        f'{esc(format_date(entry["approval"]))}; no deposit verified</span>'
                    )
                list_items.append(
                    f'<li data-party="{esc(entry["party"])}">{esc(entry["party"])}{suffix}</li>'
                )
            blocks.append(
                f'<div class="party-group" data-status="{esc(group)}">'
                f'<p class="party-label"><strong>{esc(group)}</strong> <span>{len(items)}</span></p>'
                f'<ul class="party-names">{"".join(list_items)}</ul></div>'
            )
        return (
            f'<div class="map-parties" aria-label="Recorded parties">'
            f'{"".join(blocks)}</div>'
        )

    def render_instrument_about(inst: dict) -> str:
        """Explain the instrument and cite the record's official sources."""
        dates = inst.get("dates") or {}
        date_parts = [
            f"{label} {format_date(dates[key])}"
            for key, label in (
                ("adopted", "Adopted"),
                ("signed", "Signed"),
                ("opened_for_signature", "Opened for signature"),
                ("closed_for_signature", "Closed for signature"),
                ("entered_into_force", "In force since"),
                ("published", "Published"),
            )
            if dates.get(key)
        ]
        if inst["status"] != "adopted":
            date_parts.append(
                f"Status: {STATUS_LABELS.get(inst['status'], inst['status'])}"
            )
        official = [
            source
            for source in inst.get("sources") or []
            if source.get("kind") in OFFICIAL_SOURCE_KINDS and source.get("url")
        ]
        source_links = "; ".join(
            f'<a href="{esc(source["url"])}" target="_blank" rel="noopener">'
            f'{esc(SOURCE_LABELS.get(source["id"], source.get("publisher") or source["id"]))}</a>'
            for source in official
        )
        checked = dates.get("verified_on")
        checked_text = f" · record checked {format_date(checked)}" if checked else ""
        reason = (inst.get("relevance") or {}).get("reason") or ""
        history = dates.get("notes") or ""
        history_html = (
            f'<p class="map-about-history"><strong>History:</strong> {esc(history)}</p>'
            if history
            else ""
        )
        reason_html = f"<p>{esc(reason)}</p>" if reason else ""
        dates_html = (
            f'<p class="map-about-dates"><strong>Dates and status:</strong> '
            f'{esc(" · ".join(date_parts))}.</p>'
            if date_parts
            else ""
        )
        return (
            f'<div class="map-about">'
            f'<p class="map-about-meta">{esc(inst["instrument_type"].replace("_", " ").capitalize())} · '
            f'{esc(BINDING_LABELS[inst["binding_status"]])}</p>'
            f'<h3 class="map-about-title">What it is</h3>'
            f"{reason_html}{dates_html}{history_html}"
            f'<p class="map-sources"><strong>Sources:</strong> {source_links}'
            f'{checked_text} · <a href="{esc(record_url(inst))}" target="_blank" rel="noopener">'
            f"record and full citation</a></p></div>"
        )

    def map_figure(
        inst: dict,
        kind: str,
        title: str,
        sub: str,
        description: str,
        status: dict[str, str],
        org_notes: list[str],
        legend: list[dict],
        note: str = "",
        legend_note: str = "",
    ) -> dict:
        if org_notes:
            legend = (
                legend[:-1]
                + [
                    {
                        "color": ORG_MEMBER_BLUE,
                        "label": "State: member of a participating organisation",
                    }
                ]
                + [legend[-1]]
            )
            description += (
                " Pale blue: member States of a participating organisation without an individual act."
            )
        org_html = "".join(
            f'<p class="map-org-note">{esc(text)}</p>' for text in org_notes
        )
        default = "endorsed" if "endorsed" in status.values() else "signed"
        party_html = render_party_list(inst, default)
        about_html = render_instrument_about(inst)
        figure = (
            f'<figure class="map-card">'
            f'<figcaption><span class="map-title">{esc(title)}</span>'
            f'<span class="map-sub">{esc(sub)}</span></figcaption>'
            f"{org_html}"
            f"{render_map(kind, title, description, status, legend=legend, legend_note=legend_note)}"
            f"{party_html}"
            f"{about_html}"
            f'<p class="note">{esc(note)}</p></figure>'
        )
        return {
            "title": title,
            "binding": inst["binding_status"] == "binding",
            "adopters": len(entries(inst)),
            "html": figure,
        }

    cets_ratifications = ratified_entries(cets)
    cets_ratification_text = join_with_and(
        [
            f"{'the ' if entry['party'] in org_names else ''}{entry['party']} "
            f"({format_date(entry['ratification'])})"
            for entry in cets_ratifications
        ]
    )
    cets_ratification_verb = "has" if len(cets_ratifications) == 1 else "have"
    waico_signed = format_date(waico["dates"]["signed"])
    waico_first = sum(
        1
        for entry in entries(waico)
        if entry.get("signature") == waico["dates"]["signed"]
    )
    waico_later = len(entries(waico)) - waico_first
    waico_approval = next(
        (entry["approval"] for entry in entries(waico) if entry.get("approval")), ""
    )
    military_as_of = format_date(military["parties"]["as_of"])
    pax_as_of = format_date(pax["parties"]["as_of"])

    map_entries = [
        map_figure(
            paris,
            "paris",
            "Paris 2025",
            f"{len(paris_states)} States",
            f"World map. Medium blue: {len(paris_states)} States that endorsed the Paris Statement. Sand: States with no recorded endorsement.",
            paris_status,
            paris_org_notes,
            endorsement_legend,
            note=(
                f"Endorsement, not signature or ratification. The Élysée page lists "
                f"{reported_total(paris)} endorsers ({len(paris_states)} States, the EU and the AU Commission); "
                "the 19 February 2025 PDF lists 64. The difference is documented in the record."
            ),
        ),
        map_figure(
            bletchley,
            "bletchley",
            "Bletchley 2023",
            f"{len(bletchley_states)} States + {org_short(bletchley)}",
            f"World map. Medium blue: {len(bletchley_states)} States that endorsed the Bletchley Declaration. Sand: States with no recorded endorsement.",
            bletchley_status,
            bletchley_org_notes,
            endorsement_legend,
            note=(
                f"Political endorsement, not a treaty signature. New Zealand joined on "
                f"23 October 2024; the record lists {len(bletchley_states)} States and the EU."
            ),
        ),
        map_figure(
            seoul,
            "seoul",
            "Seoul 2024",
            f"{len(seoul_states)} States + {org_short(seoul)}",
            f"World map. Medium blue: {len(seoul_states)} States that adopted the Seoul Declaration. Sand: States with no recorded endorsement.",
            seoul_status,
            seoul_org_notes,
            endorsement_legend,
            note=(
                "Leaders' declaration, not a treaty signature. The Seoul Ministerial "
                "Statement of 22 May 2024 is a separate document and is not mapped here."
            ),
        ),
        map_figure(
            military,
            "military",
            "Military AI 2023",
            f"{len(military_states)} States",
            f"World map. Medium blue: {len(military_states)} States that endorsed the Political Declaration on military AI. Sand: States with no recorded endorsement.",
            military_status,
            [],
            endorsement_legend,
            note=(
                f"Political endorsement, not a signature or ratification. "
                f"{len(military_states)} States as of {military_as_of}; later accessions are not reflected."
            ),
            legend_note=f"{len(military_states)} endorsing States as of {military_as_of}.",
        ),
        map_figure(
            cets,
            "cets",
            "CETS 225",
            f"{len(cets_states)} States + {org_short(cets)} · {len(cets_ratifications)} ratifications",
            "World map. Dark blue: States that ratified CETS 225. Medium blue: States that signed only. Sand: States with no recorded signature.",
            cets_status,
            cets_org_notes,
            cets_legend,
            note=(
                f"Treaty signature and ratification. {cets_ratification_text} "
                f"{cets_ratification_verb} ratified; the treaty is not in force. "
                "Five ratifications are required, including three Council of Europe member States. "
                "France and Germany are EU member States but are not recorded as individual "
                "signatories on the Treaty Office chart."
            ),
        ),
        map_figure(
            waico,
            "waico",
            "WAICO 2026",
            f"{len(waico_states)} confirmed of {reported_total(waico)} reported",
            f"World map. Medium blue: {len(waico_states)} confirmed States that signed the WAICO Agreement. Sand: States with no recorded signature. China's MFA reports {reported_total(waico)} founding members; {len(waico_states)} are individually identified. China is the depositary.",
            waico_status,
            [],
            waico_legend,
            note=(
                f"Treaty signature, not ratification. {len(waico_states)} of the "
                f"{reported_total(waico)} founding members reported by China's MFA are individually "
                f"identified: {waico_first} at the {waico_signed} ceremony and {waico_later} in later "
                f"signing records. China's NPC approved ratification on {format_date(waico_approval)}, "
                "but no deposit was verified; the Agreement is not in force (three ratifications "
                "required, Article 15). The remaining reported member is not named in the primary record."
            ),
            legend_note=(
                f"States only · {len(waico_states)} confirmed of {reported_total(waico)} "
                "reported founding members"
            ),
        ),
        map_figure(
            pax,
            "pax",
            "Pax Silica 2025",
            f"{len(pax_states)} States + {org_short(pax)}",
            f"World map. Medium blue: {len(pax_states)} States that endorsed the Pax Silica Declaration. Sand: States with no recorded endorsement.",
            pax_status,
            pax_org_notes,
            endorsement_legend,
            note=(
                f"Political declaration, not a treaty. {reported_total(pax)} signatories "
                f"({len(pax_states)} States and the European Union) as of {pax_as_of}; the United "
                "States is a signatory. Taiwan endorsed the principles through a separate joint "
                "statement but is not a signatory. The separate AI Opportunity Statement "
                "(54 endorsers as of September 2026) is not mapped here."
            ),
        ),
    ]
    # Binding instruments first, then non-binding; within each group, the
    # instrument with the most recorded adopters comes first.
    map_entries.sort(
        key=lambda item: (
            0 if item["binding"] else 1,
            -item["adopters"],
            item["title"],
        )
    )
    maps_html = "".join(item["html"] for item in map_entries)
    map_binding_count = sum(1 for item in map_entries if item["binding"])
    map_nonbinding_count = len(map_entries) - map_binding_count

    chart, chart_note = year_chart(instruments)

    ai_treaties = [inst for inst in instruments if inst["category"] == "ai_treaty"]
    ai_count = len(ai_treaties)
    trade_count = category_counts.get("agreement_ai_provisions", 0)
    general_treaty_count = category_counts.get("general_treaty", 0)

    cards = [
        (
            "Washington",
            "Market-led model · political coalition",
            "Pax Silica Declaration",
            f"{reported_total(pax)} signatories · {len(pax_states)} States + {org_short(pax)}",
            f"The 2025 US-led declaration on secure AI and technology supply chains. It is non-binding and creates no treaty obligation. The United States also convened the 2023 military declaration ({len(military_states)} endorsers) and signed CETS 225, Bletchley and Seoul, but did not endorse Paris.",
            PAX_ID,
        ),
        (
            "Beijing",
            "State-led model · constituent treaty",
            "WAICO Establishment Agreement",
            f"{reported_total(waico)} reported founding members · {force_phrase(waico)}",
            "The 2026 treaty establishing the World AI Cooperation Organization, headquartered in Shanghai. It is one of the corpus's AI-specific treaties and is limited to the civilian domain. China's 2023 Global AI Governance Initiative remains the policy line; China endorsed Bletchley and Paris but did not sign CETS 225 or the military declaration.",
            WAICO_ID,
        ),
        (
            "Brussels / Strasbourg",
            "Rights-based model · treaty and regulation",
            "Council of Europe Framework Convention on AI (CETS 225)",
            f"{len(cets_entries)} signatures · {len(cets_ratifications)} ratifications",
            f"One of {number_word(ai_count)} AI-specific treaties, binding once in force. The EU has signed and ratified; not all EU member States are individual signatories. The EU AI Act is the separate supranational layer.",
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

    ai_note = (
        f"CETS 225: {len(cets_entries)} signatures, {len(cets_ratifications)} ratifications, "
        f"{force_phrase(cets)}. WAICO: {reported_total(waico)} reported founding members, "
        f"{force_phrase(waico)}."
    )
    stat_cards = [
        (str(total), "catalogued instruments", "One record per instrument, with source and verification level."),
        (str(binding), "binding instruments", f"{in_force} in force; {not_in_force} not yet in force."),
        (str(ai_count), "AI-specific treaties", ai_note),
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
<link rel="stylesheet" href="assets/style.css?v=8">
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
      <a href="#poles">Three poles?</a>
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
          <p class="lede">{number_word(ai_count).capitalize()} AI-specific treaties, {number_word(trade_count)} trade agreements with AI provisions, declarations and resolutions, technical standards, and a negotiation on autonomous weapons.</p>
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
          <p>A treaty in force, a trade agreement in force, European Union law and {number_word(general_treaty_count)} general framework treaties. It does not mean the obligation is detailed: CETS 225 and the WAICO Agreement are not in force, and the AfCFTA is not yet in force.</p>
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
      <p class="eyebrow">02 · Three poles?</p>
      <h2>Three poles?</h2>
      <p class="lede">The three-pole image is a shorthand from policy analysis, not a finding of this corpus. It was a working hypothesis, and the legal record does not support reading it as three blocs. International law classifies the act and the party; it does not classify States into poles.</p>
      <div class="poles">{cards_html}</div>
      <div class="frame-note">
        <h3>The frame, not a legal category</h3>
        <p>“Poles” and “blocs” are terms of political analysis. International law asks which act — treaty, political commitment, resolution, recommendation — and which party — State or international organisation. The literature does not converge on a fixed number:</p>
        <ul>
          <li><strong>Regime complexity.</strong> The AI governance landscape has no focal institution and low hierarchy: the United States, China and the EU pursue competing preferences through overlapping institutions, producing fragmentation rather than a tripolar legal order (<a href="https://academic.oup.com/isagsq/article/6/4/ksag145/8993928" target="_blank" rel="noopener">Geith, Lundgren &amp; Tallberg, <em>Global Studies Quarterly</em>, 2026</a>).</li>
          <li><strong>Three models, not three alliances.</strong> Comparative policy analysis describes an American market-driven model, a Chinese state-driven model and a European rights-driven model, but treats them as ideal types, not legal blocs (<a href="https://onlinelibrary.wiley.com/doi/10.1111/1758-5899.13444" target="_blank" rel="noopener">Mokry, <em>Global Policy</em>, 2024</a>; Bradford, <em>Digital Empires</em>, 2023).</li>
          <li><strong>The number depends on the axis.</strong> Policy analysis in 2026 describes two consolidating architectures (<a href="{record_url(by_id[PAX_ID])}" target="_blank" rel="noopener">US-led Pax Silica</a>, <a href="{record_url(by_id[WAICO_ID])}" target="_blank" rel="noopener">China-led WAICO</a>) plus a UN track without capacity, and notes that many States join multiple frameworks (<a href="https://www.csis.org/analysis/state-ai-global-governance-and-its-implications-us-china-summit" target="_blank" rel="noopener">CSIS, 2026</a>). On a forum axis, the triad is UN commons / US club / China–Global South diffusion (<a href="https://eastasiaforum.org/2026/10/22/three-competing-approaches-to-global-ai-governance" target="_blank" rel="noopener">Tiberghien, <em>East Asia Forum</em>, 2026</a>).</li>
        </ul>
        <p class="note">The number of poles therefore depends on the axis chosen: regulatory model, institutional vehicle or diplomatic coalition. The record below tests the metaphor against the legal acts.</p>
      </div>
      <div class="paris-band">
        <div>
          <p class="eyebrow">Cross-cutting</p>
          <h3>Paris 2025: China and India endorsed; the United States and the United Kingdom did not</h3>
          <p>The Paris Statement is endorsed by {len(paris_states)} States, the European Union and the African Union Commission. It is the broadest instrument in the corpus. Its list cuts across the US–China axis: China and India are in, the United States and the United Kingdom are out. That is a political alignment, not a legal bloc.</p>
        </div>
        <p class="paris-metric">{len(paris_states)}<span>endorsing States</span></p>
      </div>
      <p class="note">Participation differs by instrument. The United States and the United Kingdom signed CETS 225 without ratifying it, but did not endorse Paris. China and India endorsed Paris and Bletchley, but did not sign CETS 225 or the military declaration. France and Germany endorsed Paris and the military declaration, but are not recorded as individual signatories of CETS 225. Kazakhstan endorsed Paris and signed both Pax Silica and the WAICO Agreement; Brazil and South Africa signed WAICO but not Pax Silica; India and Japan signed Pax Silica but not WAICO. Political alignment does not map onto treaty participation.</p>
      <p class="note">Note on Paris: the Élysée page lists {reported_total(paris)} endorsers; the 19 February 2025 PDF lists 64; a contemporaneous Canadian release listed 60, including South Africa, the United Arab Emirates and the Holy See. The map follows the current Élysée list, which does not include South Africa; the discrepancy is recorded in the Paris record.</p>
      <p class="takeaway"><strong>What follows legally.</strong> There is no single legal order to join or leave. A State can endorse a political declaration, sign a treaty, ratify it or join a military declaration independently, and the same State can sit in different camps on different instruments: Kazakhstan endorsed Paris and signed both Pax Silica and the WAICO Agreement. The three-pole image describes regulatory competition; it does not describe legal blocs.</p>
    </div>
  </section>

  <section id="maps" class="section">
    <div class="wrap">
      <p class="eyebrow">03 · {number_word(len(map_entries)).capitalize()} maps</p>
      <h2>Who signs what</h2>
      <p class="lede">{number_word(len(map_entries)).capitalize()} instruments with a published State-level list.</p>
      <div class="maps">
        {maps_html}
      </div>
      <p class="source-note">Boundaries: Natural Earth 1:110m Admin 0 Countries, public domain. The maps do not imply recognition of boundaries or sovereignty. “Endorsed” is used for political declarations, which create no treaty signature or ratification.</p>
      <p class="source-note"><strong>Selection.</strong> The {number_word(len(map_entries))} maps cover the instruments in the corpus with a published State-level list and a distinct legal act: {number_word(map_nonbinding_count)} political instruments and {number_word(map_binding_count)} treaties. Not mapped: instruments without a published State-level list, or where the act is not a signature, or where a map would add no information — the OECD and UNESCO recommendations, the EU AI Act, strategies, codes and company commitments, the bilateral UK–US MOU and US–EU TTC commitment, the separate Pax Silica deliverables (the June 2026 AI Opportunity Statement and the November 2026 San Francisco Declaration), and the digital trade agreements, whose membership follows trade-partner logic rather than AI-governance alignment.</p>
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
            <li>CETS 225 is not in force: {len(cets_entries)} signatures, {len(cets_ratifications)} ratifications.</li>
            <li>WAICO is not in force: {reported_total(waico)} reported founding members; no deposited ratification was verified.</li>
            <li>{number_word(ai_count).capitalize()} AI-specific treaties: CETS 225 and the WAICO Agreement. This does not mean no others exist, but that no other has been located and verified.</li>
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
