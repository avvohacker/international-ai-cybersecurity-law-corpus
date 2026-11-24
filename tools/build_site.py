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
UNSEEN = ROOT / "data" / "unseen-events.json"
OFF_RECORD = ROOT / "data" / "off-the-record.json"
REPO = "https://github.com/avvohacker/international-ai-law-corpus"

PARIS_ID = "paris-ai-action-summit-statement-2025"
CETS_ID = "coe-cets-225"
CHINA_ID = "china-global-ai-governance-initiative-2023"
BLETCHLEY_ID = "bletchley-declaration-2023"
SEOUL_ID = "seoul-declaration-2024"
MILITARY_ID = "political-declaration-military-ai-2023"
WAICO_ID = "waico-establishment-agreement-2026"
PAX_ID = "pax-silica-declaration-2025"
NEW_DELHI_ID = "new-delhi-declaration-2026"
BRICS_ID = "brics-ai-statement-2025"
MAP_INSTRUMENT_IDS = (
    PARIS_ID,
    BLETCHLEY_ID,
    SEOUL_ID,
    MILITARY_ID,
    CETS_ID,
    WAICO_ID,
    PAX_ID,
    NEW_DELHI_ID,
    BRICS_ID,
)

# IFAD endorsed the New Delhi Declaration but is a UN specialised agency, not a
# State. It is named outside the map frame, without shading its members.
EXTRA_PARTICIPATING_ORGS = {
    "International Fund for Agricultural Development": "IFAD",
}

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
    "xinhua-npc-decision": "Xinhua report on NPC decision",
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
    "MV": (73.50, 3.20),
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
    "Maldives": "MV",
}

NAME_ALIASES = {
    "czech republic": "czechia",
    "republic of korea": "south korea",
    "republic of moldova": "moldova",
    "russian federation": "russia",
    "united states": "united states of america",
}

TEAL = "#0e6b62"
ACT_BLUE = "#5a7fbd"
CHINA_RED = "#c8102e"
INDIA_BROWN = "#a67c52"
BRICS_ORANGE = "#d97706"
RATIFIED_BLUE = "#172e6e"
ORG_MEMBER_BLUE = "#a9c0e0"
ISSUED_GOLD = "#a67c52"
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
    "issued": ISSUED_GOLD,
    "none": LAND,
}
STATUS_TITLE = {
    "endorsed": "endorsed",
    "signed": "signature only",
    "ratified": "ratified",
    "organisation": "member of a participating international organisation; no individual act",
    "issued": "issuing government; collective statement, no individual signature",
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
    fills: dict[str, str] | None = None,
) -> str:
    features, _, by_iso = load_geo()
    legend = legend or []
    fills = fills or {}
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
        fill = fills.get(status, STATUS_FILL[status])
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
        fill = fills.get(status, STATUS_FILL[status])
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
    return "".join(parts), "Instruments only; events in the timeline are not counted. Years present in the corpus; the scale is not continuous."


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


def display_timeline_date(value: str) -> str:
    """Render a complete date, a month/year or a year without inventing a day."""
    if not value:
        return "—"
    parts = value.split("-")
    if len(parts) == 3 and parts[1] not in ("00", "0") and parts[2] not in ("00", "0"):
        try:
            return format_date(value)
        except (ValueError, IndexError):
            pass
    if len(parts) >= 2 and parts[1].isdigit() and 1 <= int(parts[1]) <= 12:
        return f"{MONTHS[int(parts[1]) - 1]} {parts[0]}"
    return parts[0]


# Curated explanations of why an instrument exists. Every other record falls
# back to the reason and history already stored in its own entry, so no row is
# left without a text slot.
TIMELINE_STORIES = {
    "iccpr-1966": "The baseline. The ICCPR is not an AI instrument, but it supplies the rights vocabulary — privacy, equality, due process, freedom of expression — that later AI texts invoke. It binds the States that ratified it and has a monitoring committee; the AI-specific instruments do not create anything comparable.",
    "vclt-1969": "The grammar of the rest. The Vienna Convention governs how treaties are made, interpreted, amended and terminated. It matters here because the difference between a signature, a ratification, a reservation and an entry into force is a legal technique, not a diplomatic nicety.",
    "oecd-ai-recommendation-2019": "The first intergovernmental AI principles. Adopted by the OECD Council, the recommendation fixed the human-centred and trustworthy-AI vocabulary that later declarations and codes reuse. It is not binding, but its principles travel: the G20, UNESCO and several national frameworks borrow them.",
    "unesco-ethics-ai-2021": "The universal standard-setting text. UNESCO adopted the recommendation by acclamation with 193 member States, the widest endorsement of any AI principles. It has no enforcement mechanism, but it is the reference point for ethics language in national laws and in the Global Digital Compact.",
    "un-ga-res-78-265": "The first UN General Assembly resolution on AI. Adopted on 21 March 2024, it establishes the assembly as a venue for AI governance and frames AI as a development and human-rights question. It is a resolution: it recommends, it does not bind.",
    "un-ga-res-79-1": "The Pact for the Future and its Global Digital Compact. The compact is the widest UN framework for digital cooperation, with commitments on AI governance, data and connectivity. Its obligations are political; its value is the universal membership and the follow-up architecture it creates.",
    "un-ga-res-79-325": "The institutional turn at the UN. The resolution creates the Independent International Scientific Panel on AI and the Global Dialogue on AI Governance. It does not create a regulator: the Dialogue issues recommendations, and the Panel synthesises evidence.",
    "bletchley-declaration-2023": "The summit form arrives. The UK convened the first AI Safety Summit and produced a declaration endorsed by 30 States and the EU, including China and the United States. It put frontier-model risk on the leaders' agenda and created a process — the AI Safety Institute network — without creating an obligation.",
    "coe-cets-225": "The rights treaty. The Council of Europe turned its human-rights grammar into the first binding AI convention: obligations for Parties, a Conference of the Parties, and a private-sector opt-in. It has 21 signatures and two ratifications; five ratifications, including three member States, are required for entry into force.",
    "seoul-declaration-2024": "The summit becomes a series. The Seoul declaration follows Bletchley with a leaders' session of ten States and the EU, and adds a ministerial statement with a wider list. The sequence shows how summit diplomacy builds continuity without building law.",
    "eu-ai-act": "The supranational exception. The EU AI Act is a regulation, directly applicable in the member States, with product rules, prohibitions and enforcement. It is in the corpus to mark the difference between international law and EU law: it is binding, but it is not an international instrument and no State signs it.",
    "depa-2020": "The trade route. The Digital Economy Partnership Agreement puts an AI article inside a digital-trade agreement. Its language is cooperative ('shall endeavour'), but it is treaty text, and it shows how AI governance travels through trade chapters rather than dedicated AI treaties.",
    "afcfta-digital-trade-protocol-2024": "The African continental route. The AfCFTA Digital Trade Protocol and its Annex on Emerging and Advanced Technologies treat AI as part of digital trade: deployment, national treatment, standards and regulatory sandboxes. The annex uses 'shall', but the protocol's entry into force is not confirmed.",
    "china-global-ai-governance-initiative-2023": "The Chinese position before WAICO. The initiative sets out sovereignty, development, capacity building and UN-centred governance. It is a unilateral policy text, not a treaty; it is the policy line that later becomes an organisation.",
    "waico-establishment-agreement-2026": "The organisation. China convened the signing of a constituent treaty for the World Artificial Intelligence Cooperation Organization in Shanghai: a Council, a Secretariat, a depositary and a civilian-only mandate. It reports 38 founding members, identifies 37, and no deposit was verified; entry into force is not confirmed.",
    "brics-ai-statement-2025": "The coalition text. The BRICS leaders issue a statement on AI governance centred on digital sovereignty and the Global South. It has no signature block; the record counts 11 member States rather than 11 signatories, and Saudi participation is contested between the presidency's list and the Saudi news agency.",
    "paris-ai-action-summit-statement-2025": "The widest endorsement. The Paris statement is endorsed by 65 States and organisations on the Élysée page, including China and India and excluding the United States and the United Kingdom. It is political, not legal, and the count itself is disputed between the page and the PDF.",
    "pax-silica-declaration-2025": "The US-led coalition. Pax Silica is built around supply-chain access, trusted technology and national tools, not around a treaty. Its 26 'signatories' endorse a political declaration; the word is the source's, not a legal qualification.",
    "san-francisco-declaration-2026": "The coalition becomes operational. Ten governments sign a declaration on sensitive technologies, critical infrastructure and supply-chain security, and announce five working groups. It is still political: no depositary, no ratification, no enforcement. It is the sharpest contrast with WAICO's treaty form.",
    "new-delhi-declaration-2026": "The summit list grows. The New Delhi Declaration is endorsed by 92 participants — 90 States, the EU and IFAD — making it the widest State-level AI text in the corpus. It remains a declaration, and the endorsement list differs between the PIB annex and the MEA page.",
    "us-uk-ai-safety-mou-2024": "The bilateral institute channel. The UK and US AI Safety Institutes sign a memorandum of understanding to cooperate on testing and evaluation. The full text is unpublished and the MOU is not a treaty; it is a political commitment between two administrations.",
    "us-eu-ttc-ai-safety-dialogue-2024": "The transatlantic commitment. The US–EU Trade and Technology Council records a commitment to launch an AI-safety dialogue inside a broader joint statement. It is not a stand-alone instrument and creates no legal obligation.",
    "g7-hiroshima-code-2023": "The club code. The G7 Hiroshima process produced a voluntary code of conduct for advanced AI developers, later extended by an reporting framework. It is non-binding and addressed to companies as much as to governments.",
    "political-declaration-military-ai-2023": "The military red line. The political declaration on military AI commits endorsing States to human control and to international law in the use of force. It is a declaration, not a treaty, and the CCW negotiations remain the formal venue.",
    "ccw-gge-laws-2026": "The negotiation that has not produced an instrument. The CCW Group of Governmental Experts on lethal autonomous weapons systems continues to discuss a possible instrument. The record is a negotiation, not an adopted text, and it is kept to show where the military AI treaty is not.",
    "un-hrc-res-63-15": "The Human Rights Council enters. Resolution 63/15 addresses AI and human rights and creates a mandate for follow-up. It is a resolution adopted without a vote, not a treaty; its importance is the rights framing inside the UN's human-rights machinery.",
}


def set_chart(instruments: list[dict]) -> tuple[str, int]:
    """Draw an UpSet-style chart of overlapping legal-form sets.

    The catalogue's category field is exclusive; these sets are not. The chart
    shows both the size of each set and the exact intersections.
    """
    definitions = [
        ("binding", "Binding", lambda inst: inst["binding_status"] == "binding"),
        ("in_force", "In force", lambda inst: inst["status"] == "in_force"),
        (
            "treaty",
            "Treaty / agreement",
            lambda inst: inst["instrument_type"] in {"treaty", "protocol", "agreement"},
        ),
        ("ai_treaty", "AI-specific treaty", lambda inst: inst["category"] == "ai_treaty"),
        ("standard", "Technical standard", lambda inst: inst["category"] == "technical_standard"),
        ("eu_law", "EU law", lambda inst: inst["category"] == "supranational_law"),
    ]
    members = []
    for key, label, predicate in definitions:
        members.append((key, label, {inst["id"] for inst in instruments if predicate(inst)}))
    labels = {key: label for key, label, _ in members}
    combinations = Counter(
        tuple(key for key, _, ids in members if inst["id"] in ids) for inst in instruments
    )
    outside = combinations.pop((), 0)
    ordered = sorted(combinations.items(), key=lambda item: (-item[1], item[0]))
    if not ordered:
        return "", outside

    max_set = max(len(ids) for _, _, ids in members)
    set_rows = []
    for key, label, ids in members:
        width = len(ids) / max_set * 100
        set_rows.append(
            f'<div class="up-set"><span class="up-set-name">{esc(label)}</span>'
            f'<span class="up-set-track"><span class="up-set-fill up-{esc(key)}" '
            f'style="width:{width:.1f}%"></span></span>'
            f'<span class="up-set-n">{len(ids)}</span></div>'
        )

    max_combo = max(count for _, count in ordered)
    columns = []
    for combo, count in ordered:
        height = max(4, round(count / max_combo * 118))
        active = set(combo)
        dots = "".join(
            f'<span class="up-dot{" up-dot-on" if key in active else ""}" aria-hidden="true"></span>'
            for key, _, _ in members
        )
        name = ", ".join(labels[key] for key in combo) or "No set"
        columns.append(
            f'<div class="up-column" title="{esc(name)}: {count} instruments">'
            f'<div class="up-top"><span class="up-count">{count}</span>'
            f'<span class="up-bar" style="height:{height}px"></span></div>'
            f'<div class="up-dots">{dots}</div></div>'
        )

    html = (
        '<div class="upset" role="img" aria-label="Overlapping sets: binding, in force, treaty or agreement, AI-specific treaty, technical standard and EU law">'
        '<div class="upset-corner">Set size</div>'
        '<div class="upset-toplabel"><span class="up-long">Instruments per intersection</span><span class="up-short">Intersections</span></div>'
        '<div class="upset-left"><div class="upset-spacer"></div>'
        f'<div class="upset-sets">{"".join(set_rows)}</div></div>'
        f'<div class="upset-right" style="--cols:{len(ordered)}">'
        f'{"".join(columns)}</div></div>'
    )
    return html, outside


def combined_timeline(instruments: list[dict], events: list[dict]) -> str:
    """One chronology: instruments as highlighted boxes, events as plain rows."""
    kind_labels = {
        "market": "Market event",
        "bilateral": "Bilateral channel",
        "summit": "Summit without a text",
        "channel": "Communication channel",
    }
    items: list[tuple[str, int, str, str]] = []
    for inst in instruments:
        date = timeline_date(inst)
        iid = inst["id"]
        title = first_note(inst)
        category = CATEGORY_LABELS[inst["category"]]
        binding = BINDING_LABELS[inst["binding_status"]]
        status = STATUS_LABELS[inst["status"]]
        why = TIMELINE_STORIES.get(iid) or (inst.get("relevance") or {}).get("reason") or ""
        note = (inst.get("dates") or {}).get("notes") or ""
        status_note = inst.get("status_note") or ""
        history = ""
        if note:
            history += f'<p class="tl-history">{esc(note)}</p>'
        if status_note and status_note != note:
            history += f'<p class="tl-history">{esc(status_note)}</p>'
        source = source_url(inst)
        source_html = (
            f'<a href="{esc(source)}" target="_blank" rel="noopener">official source</a>'
            if source
            else ""
        )
        body = (
            f'<li class="tl-item tl-instrument" data-instrument-id="{esc(iid)}">'
            f'<div class="tl-marker"><time datetime="{esc(date)}">{esc(display_timeline_date(date))}</time>'
            f'<span class="tl-dot" aria-hidden="true"></span></div>'
            f'<div class="tl-body tl-card">'
            f'<p class="tl-meta"><span class="tl-kind">Instrument</span> · {esc(category)} · '
            f'{esc(binding)} · {esc(status)}</p>'
            f'<h3><a href="{esc(record_url(inst))}" target="_blank" rel="noopener">{esc(title)}</a></h3>'
            f'<p class="tl-why">{esc(why)}</p>'
            f'{history}'
            f'<p class="tl-links">{source_html}'
            f'{" · " if source_html else ""}'
            f'<a href="{esc(record_url(inst))}" target="_blank" rel="noopener">record</a></p>'
            f'</div></li>'
        )
        items.append((date, 1, iid, body))

    for event in events:
        date = event["date"]
        source = event.get("source") or {}
        body = (
            f'<li class="tl-item tl-event unseen-item" data-kind="{esc(event.get("kind", ""))}">'
            f'<div class="tl-marker"><time datetime="{esc(date)}">{esc(display_timeline_date(date))}</time>'
            f'<span class="tl-dot" aria-hidden="true"></span></div>'
            f'<div class="tl-body">'
            f'<p class="tl-meta"><span class="tl-kind">Event</span> · '
            f'{esc(kind_labels.get(event.get("kind"), event.get("kind", "")))}</p>'
            f'<h3>{esc(event["title"])}</h3>'
            f'<p class="tl-why">{esc(event.get("summary", ""))}</p>'
            f'<p class="tl-history">{esc(event.get("why", ""))}</p>'
            f'<p class="tl-links"><a href="{esc(source.get("url", ""))}" target="_blank" '
            f'rel="noopener">{esc(source.get("label", "source"))}</a></p>'
            f'</div></li>'
        )
        items.append((date, 0, event.get("id", event["title"]), body))

    items.sort(key=lambda item: (item[0], item[1], item[2]))
    return '<ol class="timeline combined">' + "".join(item[3] for item in items) + "</ol>"


def off_record_cards(entries: list[dict], by_id: dict[str, dict]) -> str:
    strand_order = {"Doctrine": 0, "Analysis": 1, "Critique": 2}
    ordered = sorted(
        entries,
        key=lambda entry: (strand_order.get(entry.get("strand"), 9), -int(entry["date"].replace("-", ""))),
    )
    cards = []
    for entry in ordered:
        related = []
        for iid in entry.get("related") or []:
            inst = by_id.get(iid)
            if not inst:
                continue
            related.append(
                f'<a href="{esc(record_url(inst))}" target="_blank" rel="noopener">'
                f'{esc(first_note(inst))} record</a>'
            )
        related_html = " · ".join(related)
        cards.append(
            f'<article class="otr-card">'
            f'<p class="otr-kind">{esc(entry["strand"])} · {esc(display_timeline_date(entry["date"]))}</p>'
            f'<h3><a href="{esc(entry["url"])}" target="_blank" rel="noopener">{esc(entry["title"])}</a></h3>'
            f'<p class="otr-byline">{esc(entry["author"])} · {esc(entry["outlet"])}</p>'
            f'<p class="otr-adds">{esc(entry["adds"])}</p>'
            f'<p class="otr-links"><a href="{esc(entry["url"])}" target="_blank" rel="noopener">'
            f'Read the source</a>{(" · " + related_html) if related_html else ""}</p>'
            f'</article>'
        )
    return "".join(cards)


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
    new_delhi = by_id[NEW_DELHI_ID]
    brics = by_id[BRICS_ID]

    organisations = load_organisations()
    org_names = set(organisations) | set(EXTRA_PARTICIPATING_ORGS)

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
    new_delhi_states = state_names(new_delhi)
    brics_states = state_names(brics)
    cets_entries = cets["parties"]["entries"]

    def entries(inst: dict) -> list[dict]:
        return (inst.get("parties") or {}).get("entries") or []

    def ratified_entries(inst: dict) -> list[dict]:
        return [entry for entry in entries(inst) if entry.get("ratification")]

    def reported_total(inst: dict) -> int:
        counts = (inst.get("parties") or {}).get("counts") or {}
        for key in (
            "endorsements",
            "issuing_states",
            "members",
            "signatures",
            "political_signatures",
            "parties",
        ):
            value = (counts.get(key) or {}).get("total")
            if isinstance(value, int):
                return value
        return len(entries(inst))

    def force_phrase(inst: dict) -> str:
        return {
            "in_force": "in force",
            "unknown": "entry into force not confirmed",
        }.get(inst.get("status"), "not in force")

    def org_short(inst: dict) -> str:
        labels = {
            "European Union": "EU",
            "African Union Commission": "AU Commission",
            **EXTRA_PARTICIPATING_ORGS,
        }
        order = {
            "European Union": 0,
            "African Union Commission": 1,
            "International Fund for Agricultural Development": 2,
        }
        parties = sorted(
            (
                entry["party"]
                for entry in entries(inst)
                if entry["party"] in org_names
            ),
            key=lambda party: (order.get(party, 99), party),
        )
        return " + ".join(labels.get(party, party) for party in parties)

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
    new_delhi_iso = iso_set(new_delhi_states, "New Delhi 2026")
    brics_iso = iso_set(brics_states, "BRICS 2025")

    for map_name, values in (
        ("Paris 2025", paris_iso),
        ("CETS 225", cets_iso),
        ("Bletchley 2023", bletchley_iso),
        ("Seoul 2024", seoul_iso),
        ("Military AI 2023", military_iso),
        ("WAICO 2026", waico_iso),
        ("Pax Silica 2025", pax_iso),
        ("New Delhi 2026", new_delhi_iso),
        ("BRICS 2025", brics_iso),
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
    new_delhi_status = {iso: "endorsed" for iso in new_delhi_iso}
    brics_status = {iso: "issued" for iso in brics_iso}
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
            if name not in organisations:
                continue
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
    new_delhi_org_notes = add_org_members(new_delhi_status, new_delhi, "endorsed")
    brics_org_notes = []

    endorsement_legend = [
        {"color": ACT_BLUE, "label": "State: endorsed"},
        {"color": LAND, "label": "State: not endorsed"},
    ]
    new_delhi_legend = [
        {"color": INDIA_BROWN, "label": "State: endorsed"},
        {"color": LAND, "label": "State: not endorsed"},
    ]
    cets_legend = [
        {"color": RATIFIED_BLUE, "label": "State: ratified"},
        {"color": ACT_BLUE, "label": "State: signed only"},
        {"color": LAND, "label": "State: no signature"},
    ]
    waico_legend = [
        {"color": CHINA_RED, "label": "State: signed only"},
        {"color": LAND, "label": "State: no signature"},
    ]
    brics_legend = [
        {"color": BRICS_ORANGE, "label": "State: member of the group (collective statement)"},
        {"color": LAND, "label": "State: no recorded act"},
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
            elif default == "issued":
                group = "Member States (collective)"
            else:
                group = "Signed"
            groups[group].append(entry)
        blocks = []
        for group in (
            "Ratified",
            "Signed only",
            "Signed",
            "Endorsed",
            "Member States (collective)",
        ):
            items = sorted(groups.get(group, []), key=lambda entry: entry["party"])
            if not items:
                continue
            list_items = []
            for entry in items:
                suffix = ""
                if entry["party"] in org_names:
                    suffix += ' <span class="party-kind">organisation</span>'
                if entry.get("domestic_approval") and not entry.get("ratification"):
                    suffix += (
                        f' <span class="party-kind">domestic approval '
                        f'{esc(format_date(entry["domestic_approval"]))}; no deposit verified</span>'
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
        fills: dict[str, str] | None = None,
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
        default = next(
            (kind for kind in ("endorsed", "issued", "signed") if kind in status.values()),
            "signed",
        )
        party_html = render_party_list(inst, default)
        about_html = render_instrument_about(inst)
        official_title = (inst.get("title") or {}).get("official") or ""
        figure = (
            f'<figure class="map-card">'
            f'<figcaption><span class="map-title">{esc(title)}</span>'
            f'<span class="map-full-title">{esc(official_title)}</span>'
            f'</figcaption>'
            f'<p class="map-participation">{esc(sub)}</p>'
            f"{org_html}"
            f"{render_map(kind, title, description, status, legend=legend, legend_note=legend_note, fills=fills)}"
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
        (
            entry["domestic_approval"]
            for entry in entries(waico)
            if entry.get("domestic_approval")
        ),
        "",
    )
    military_as_of = format_date(military["parties"]["as_of"])
    pax_as_of = format_date(pax["parties"]["as_of"])

    map_entries = [
        map_figure(
            paris,
            "paris",
            "Paris 2025",
            f"{len(paris_states)} States + {org_short(paris)}",
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
            new_delhi,
            "new-delhi",
            "New Delhi 2026",
            f"{len(new_delhi_states)} States + {org_short(new_delhi)}",
            f"World map. Brown: {len(new_delhi_states)} States that endorsed the New Delhi Declaration. Sand: States with no recorded endorsement.",
            new_delhi_status,
            new_delhi_org_notes,
            new_delhi_legend,
            note=(
                f"Endorsement, not signature or ratification. The PIB list of 5 March 2026 "
                f"names {reported_total(new_delhi)} endorsers: {len(new_delhi_states)} States, the EU "
                "and IFAD. The MEA page of 21 February 2026 lists 91 and omits Colombia. "
                "IFAD is a UN specialised agency and is not shown on the State map."
            ),
            legend_note=(
                f"{len(new_delhi_states)} endorsing States + EU + IFAD"
            ),
            fills={"endorsed": INDIA_BROWN},
        ),
        map_figure(
            brics,
            "brics",
            "BRICS 2025",
            f"{len(brics_states)} listed member States",
            f"World map. Orange: {len(brics_states)} States listed as BRICS members when the statement was issued collectively. Sand: States outside the group. The statement has no individual signature block.",
            brics_status,
            brics_org_notes,
            brics_legend,
            fills={"issued": BRICS_ORANGE},
            note=(
                "Collective statement, not a treaty and not an individual signature. "
                f"The 2025 presidency lists {len(brics_states)} BRICS member States; the "
                "statement was issued collectively at the Rio de Janeiro summit and has no "
                "signature block. The record counts the listed member States, not individually "
                "evidenced issuers. Saudi Arabia is on the presidency's list, but the Saudi Press "
                "Agency described the Kingdom on 7 July 2025 as an invited country; the conflict "
                "is recorded in the record and is not resolved by counting ten."
            ),
            legend_note=(
                f"{len(brics_states)} listed member States · collective statement, no individual signature"
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
            f"World map. Red: {len(waico_states)} confirmed States that signed the WAICO Agreement. Sand: States with no recorded signature. China's MFA reports {reported_total(waico)} founding members; {len(waico_states)} are individually identified. China is the depositary.",
            waico_status,
            [],
            waico_legend,
            fills={"signed": CHINA_RED},
            note=(
                f"Treaty signature, not ratification. {len(waico_states)} of the "
                f"{reported_total(waico)} founding members reported by China's MFA are individually "
                f"identified: {waico_first} at the {waico_signed} ceremony and {waico_later} in later "
                f"signing records. China's NPC approved ratification on {format_date(waico_approval)}, "
                "but no deposit was verified and entry into force is not confirmed; the number of "
                "deposited instruments is unknown (Article 15 requires three). Bangladesh announced on 1 August 2026 that it would join "
                "'initially as an observer', not as a founding member, and Article 11 requires Council "
                "approval; no admission is recorded. Singapore has been reported as considering an "
                "invitation and is not a member. The 38th founding member is not named in the primary record."
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
                f"Political declaration, not a treaty. Pax Silica calls them 'signatories', but they "
                f"endorse a political declaration, not a treaty. {reported_total(pax)} signatories "
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
    unseen_events = json.loads(UNSEEN.read_text(encoding="utf-8"))
    off_record = json.loads(OFF_RECORD.read_text(encoding="utf-8"))
    off_record_html = off_record_cards(off_record["entries"], by_id)
    set_html, set_outside = set_chart(instruments)

    ai_treaties = [inst for inst in instruments if inst["category"] == "ai_treaty"]
    ai_count = len(ai_treaties)
    trade_count = category_counts.get("agreement_ai_provisions", 0)
    general_treaty_count = category_counts.get("general_treaty", 0)

    new_delhi_total = reported_total(new_delhi)

    legal_form_rows = f"""
      <tr><th scope="row">AI-specific treaty</th><td>{category_counts.get("ai_treaty", 0)}</td>
        <td>Creates obligations for the States that become parties. WAICO also creates an organisation, a Council, a Secretariat and a depositary.</td>
        <td>Neither AI-specific treaty is confirmed in force. They do not set product rules, testing standards or market-access conditions, and they bind only their parties.</td></tr>
      <tr><th scope="row">Agreement with AI provisions</th><td>{trade_count}</td>
        <td>Treaty text, often with a dedicated AI article or annex. DEPA, SADEA, UKSDEA, KSDPA and the AfCFTA Protocol use trade disciplines; the US–UK MOU uses a bilateral institute channel.</td>
        <td>The AI clauses are mostly cooperative and best-efforts. They do not create an AI regulator, and the MOU is not a treaty.</td></tr>
      <tr><th scope="row">Non-binding instrument</th><td>{category_counts.get("non_binding_instrument", 0)}</td>
        <td>Declarations, resolutions, recommendations, principles, codes and commitments. They set direction, create expectations and name the actors.</td>
        <td>No legal obligation, ratification, depositary or enforcement. A political text can be signed or endorsed; that does not make it a treaty.</td></tr>
      <tr><th scope="row">Technical standard</th><td>{category_counts.get("technical_standard", 0)}</td>
        <td>ISO/IEC vocabulary, governance and management-system standards. They are used in procurement and certification.</td>
        <td>Private standards, not international law. They bind only through contract, regulation or adoption by a public authority.</td></tr>
      <tr><th scope="row">Supranational law</th><td>{category_counts.get("supranational_law", 0)}</td>
        <td>The EU AI Act: a regulation directly applicable in the member States, with prohibitions, product rules and enforcement.</td>
        <td>Not an international instrument. No State signs or ratifies it, and it is not part of the treaty record.</td></tr>
      <tr><th scope="row">General treaty</th><td>{category_counts.get("general_treaty", 0)}</td>
        <td>The ICCPR and the VCLT: rights and treaty-law background that the AI instruments presuppose.</td>
        <td>Not AI-specific. They do not regulate AI systems, but they govern the rights and the legal technique at issue.</td></tr>
      <tr><th scope="row">Implementation and interpretation</th><td>{category_counts.get("preparatory_interpretive", 0)}</td>
        <td>The Council of Europe explanatory report to CETS 225. It explains the treaty's provisions and the drafters' intent.</td>
        <td>Not a source of obligation. It is persuasive, not binding, and it cannot amend the treaty.</td></tr>
      <tr><th scope="row">Negotiation in progress</th><td>{category_counts.get("draft_negotiation", 0)}</td>
        <td>The CCW Group of Governmental Experts on lethal autonomous weapons systems. It is the formal venue for a possible military-AI instrument.</td>
        <td>No adopted text. A negotiation record is not an instrument and creates no obligation.</td></tr>
    """

    vocab_rows = """
      <tr><th scope="row">Member</th><td>WAICO</td><td>A State party to the Agreement, bound once it is in force and for it.</td><td>Not an observer; not a State that has only announced an intention to join.</td></tr>
      <tr><th scope="row">Treaty signatory</th><td>CETS 225; WAICO; DEPA</td><td>A State or organisation that signed the treaty text. Signature may create an obligation not to defeat the object and purpose before ratification.</td><td>Not a ratification, and not a party unless the treaty so provides.</td></tr>
      <tr><th scope="row">Political signatory</th><td>San Francisco Declaration; US–UK MOU</td><td>A government that signed a political text or a memorandum.</td><td>Not a treaty signature, ratification or legal obligation.</td></tr>
      <tr><th scope="row">Endorser</th><td>Paris; Bletchley; Seoul; New Delhi; military declaration</td><td>A State or organisation that associated itself with a political text, often through a list maintained by the host.</td><td>Not a signature or ratification, even where the source calls it a signatory.</td></tr>
      <tr><th scope="row">Issuing State</th><td>BRICS</td><td>A member State of the group whose government issued a collective leaders' statement.</td><td>Not an individual signature, and not proof that each listed State separately co-issued the document.</td></tr>
      <tr><th scope="row">Observer</th><td>WAICO</td><td>A non-member admitted by the Council, without a vote.</td><td>Not a member; not a founding member; not a party.</td></tr>
      <tr><th scope="row">Domestic approval</th><td>WAICO (China, 6 November 2026)</td><td>A decision by a national legislature authorising ratification.</td><td>Not international consent and not a deposit. It does not make the State a party.</td></tr>
      <tr><th scope="row">Ratification</th><td>CETS 225</td><td>The international act by which a State consents to be bound, usually effected by depositing an instrument.</td><td>Not a signature, and not entry into force for the treaty as a whole.</td></tr>
      <tr><th scope="row">Accession</th><td>DEPA (Korea, Costa Rica); WAICO after 31 July 2026</td><td>Joining an agreement after the signature period or after entry into force, on the terms it provides.</td><td>Not a founding signature.</td></tr>
    """

    timeline_note = """
      <p class="source-note"><strong>Reading the sequence.</strong> The chronology is best read as a regime complex rather than a ladder: partially overlapping institutions, no single hierarchy, and forum choice as a political act. See Karen J. Alter and Kal Raustiala, <a href="https://www.annualreviews.org/content/journals/10.1146/annurev-lawsocsci-101317-030830" target="_blank" rel="noopener">“The Rise of International Regime Complexity”</a>, <em>Annual Review of Law and Social Science</em> 14 (2018), 329–349; Robert O. Keohane and David G. Victor, <a href="https://www.cambridge.org/core/journals/perspectives-on-politics/article/abs/regime-complex-for-climate-change/F5C4F620A4723D5DA5E0ACDC48D860C0" target="_blank" rel="noopener">“The Regime Complex for Climate Change”</a>, <em>Perspectives on Politics</em> 9(1) (2011), 7–23; Johannes Geith, Magnus Lundgren and Jonas Tallberg, <a href="https://academic.oup.com/isagsq/article/6/4/ksag145/8993928" target="_blank" rel="noopener">“The Emerging Regime Complex for Artificial Intelligence”</a>, <em>Global Studies Quarterly</em> 6(4) (2026); Hana Kim, <a href="https://link.springer.com/article/10.1007/s11077-026-09632-w" target="_blank" rel="noopener">“Coordinating fragmented global AI governance”</a>, <em>Policy Sciences</em> (2026); Huw Roberts, Emmie Hine, Mariarosaria Taddeo and Luciano Floridi, <a href="https://academic.oup.com/ia/article/100/3/1275/7641064" target="_blank" rel="noopener">“Global AI governance: barriers and pathways forward”</a>, <em>International Affairs</em> 100(3) (2024), 1275–1286; Peter Cihon, Matthijs M. Maas and Luke Kemp, <a href="https://onlinelibrary.wiley.com/doi/10.1111/1758-5899.12890" target="_blank" rel="noopener">“Fragmentation and the Future”</a>, <em>Global Policy</em> 11(5) (2020), 545–556; Sabine Mokry and Julia Gurol, <a href="https://onlinelibrary.wiley.com/doi/10.1111/1758-5899.13444" target="_blank" rel="noopener">“Competing ambitions regarding the global governance of artificial intelligence”</a>, <em>Global Policy</em> 15(5) (2024); Sina Hoch, <a href="https://onlinelibrary.wiley.com/doi/full/10.1111/jcms.70151" target="_blank" rel="noopener">“Shaping Global AI Governance?”</a>, <em>JCMS</em> (2026); Anu Bradford, <em>Digital Empires</em> (Oxford University Press, 2023); Yves Tiberghien, <a href="https://eastasiaforum.org/2026/10/22/three-competing-approaches-to-global-ai-governance" target="_blank" rel="noopener">“Three competing approaches to global AI governance”</a>, <em>East Asia Forum</em> (2026).</p>
    """

    ai_note = (
        f"CETS 225: {len(cets_entries)} signatures, {len(cets_ratifications)} ratifications, "
        f"{force_phrase(cets)}. WAICO: {reported_total(waico)} reported founding members, "
        f"{force_phrase(waico)}."
    )
    stat_cards = [
        (str(total), "catalogued instruments", "One record per instrument, with source and verification level."),
        (str(binding), "binding instruments", f"{in_force} in force; {not_in_force} not confirmed in force."),
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
<link rel="stylesheet" href="assets/style.css?v=16">
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<header class="masthead">
  <div class="wrap">
    <p class="kicker">Verified corpus · verification {esc(verified_on)}</p>
    <h1>International AI Law Atlas</h1>
    <p class="byline">{total} instruments · {full_texts} full texts · {originals} originals with SHA-256 · {binding} binding</p>
    <nav class="toc" aria-label="Sections">
      <a href="#index">Index</a>
      <a href="#form">01 Sets</a>
      <a href="#maps">02 Instruments</a>
      <a href="#timeline">03 Timeline</a>
      <a href="#unseen">04 Off the record</a>
      <a href="#catalogue">05 Catalogue</a>
      <a href="#method">06 Method</a>
    </nav>
  </div>
</header>

<main id="content">
  <section id="index" class="section section-dark">
    <div class="wrap">
      <p class="eyebrow">00 · Index</p>
      <h2>What this atlas contains</h2>
      <div class="stats">{stats_html}</div>
      <div class="index-grid">
        <a class="index-card" href="#form"><span class="index-number">01</span><strong>Overlapping sets</strong><span>Binding, in force, treaty, AI treaty, standard and EU law are not boxes. The chart shows which instruments sit in several sets, and which sit in none.</span></a>
        <a class="index-card" href="#maps"><span class="index-number">02</span><strong>The instruments</strong><span>Nine maps of the State-level acts recorded in the corpus: signatures, ratifications, endorsements and collective issuances.</span></a>
        <a class="index-card" href="#timeline"><span class="index-number">03</span><strong>Timeline</strong><span>{total} instruments and {len(unseen_events)} events in one chronology: highlighted boxes for the texts, plain rows for what left no text.</span></a>
        <a class="index-card" href="#unseen"><span class="index-number">04</span><strong>Off the record</strong><span>Legal doctrine, think-tank analysis and civil-society critique: the argument around the record, never used as evidence for it.</span></a>
        <a class="index-card" href="#catalogue"><span class="index-number">05</span><strong>Catalogue</strong><span>The filterable table of every record, with legal force, status, verification level and a link to the JSON.</span></a>
        <a class="index-card" href="#method"><span class="index-number">06</span><strong>Method</strong><span>Sources, hashes, validation, the difference between a declared and a verified count, and the limits of the corpus.</span></a>
      </div>
    </div>
  </section>

    <section id="form" class="section">
    <div class="wrap">
      <p class="eyebrow">01 · Sets</p>
      <h2>One corpus, overlapping sets</h2>
      <p class="lede">Six sets, read across the same {total} records. A treaty can be in force; a recommendation can carry the status “in force” without binding anyone; a standard is neither a treaty nor law. The chart counts the exact intersections instead of forcing every instrument into one box.</p>
      {set_html}
      <div class="set-readings">
        <div>
          <p class="set-kicker">Reading 1</p>
          <h3>Binding is not a synonym for treaty</h3>
          <p>The EU AI Act is binding and in force, but it is neither a treaty nor an agreement. Six trade and framework treaties are both. The two AI-specific treaties are binding but not in force: CETS 225 still needs five ratifications, and WAICO's entry into force is unconfirmed.</p>
        </div>
        <div>
          <p class="set-kicker">Reading 2</p>
          <h3>“In force” is a status, not a force category</h3>
          <p>The OECD recommendation is recorded as in force and remains non-binding. The AfCFTA Protocol is binding but its status is unknown. WAICO is binding but not confirmed in force. Status and legal force are separate fields, and the chart keeps them separate.</p>
        </div>
        <div>
          <p class="set-kicker">Reading 3</p>
          <h3>Most of the corpus sits outside all six</h3>
          <p><strong>{set_outside}</strong> records belong to none of the sets above: declarations, resolutions, recommendations, codes, strategies and guidance. They bind no one, but they are where much of the norm-making happens. The catalogue keeps them as records, not as noise around the binding core.</p>
        </div>
      </div>
      <p class="source-note">Sets are derived mechanically from <code>binding_status</code>, <code>status</code>, <code>instrument_type</code> and <code>category</code>. They are not a hierarchy and not exclusive: an instrument can be in several sets, or in none.</p>
    </div>
  </section>

<section id="maps" class="section section-dark">
    <div class="wrap">
      <p class="eyebrow">02 · {number_word(len(map_entries)).capitalize()} maps</p>
      <h2>The treaties, declarations and statements</h2>
      <p class="lede">{number_word(len(map_entries)).capitalize()} instruments with a published State-level list. Each map also explains the instrument and links its official sources.</p>
      <div class="maps">
        {maps_html}
      </div>
      <p class="source-note">Boundaries: Natural Earth 1:110m Admin 0 Countries, public domain. The maps do not imply recognition of boundaries or sovereignty. “Endorsed” is used for political declarations, which create no treaty signature or ratification; “member State” is used for the BRICS collective statement, which has no individual signature block.</p>
      <p class="source-note"><strong>Selection.</strong> The {number_word(len(map_entries))} maps cover the instruments in the corpus with a published State-level list and a distinct legal act: {number_word(map_nonbinding_count)} political instruments and {number_word(map_binding_count)} treaties. The {len(brics_states)}-member BRICS statement is mapped as a collective issue by its member States, not as {len(brics_states)} individual signatures. Not mapped: instruments without a published State-level list, or where the act is not a signature, or where a map would add no information — the OECD and UNESCO recommendations, the EU AI Act, strategies, codes and company commitments, the bilateral UK–US MOU and US–EU TTC commitment, the separate Pax Silica deliverables (the June 2026 AI Opportunity Statement and the November 2026 San Francisco Declaration, which is catalogued as a record but not mapped), and the digital trade agreements, whose membership follows trade-partner logic rather than AI-governance alignment.</p>
    </div>
  </section>

  <section id="timeline" class="section">
    <div class="wrap">
      <p class="eyebrow">03 · Timeline</p>
      <h2>The story, with the instruments in it</h2>
      <p class="lede">{total} instruments and {len(unseen_events)} events in one chronology, 1966–2026. The instruments are highlighted boxes; between them sit the bilaterals, hotlines, summits and market shocks that produced no text. The chart counts instruments adopted per year; the events are not counted.</p>
      <div class="timeline-key">
        <span><i class="key-instrument"></i>Instrument</span>
        <span><i class="key-event"></i>Event without a text</span>
      </div>
      {chart}
      <p class="source-note">{esc(chart_note)}</p>
      {combined_timeline(instruments, unseen_events)}
      {timeline_note}
    </div>
  </section>

  <section id="unseen" class="section section-dark">
    <div class="wrap">
      <p class="eyebrow">04 · Off the record</p>
      <h2>Off the record</h2>
      <p class="lede">The argument around the record: official sources establish what was adopted, but rarely explain the negotiation behind it, the reading that will govern it, or the interests it leaves out. This is the non-official layer — legal doctrine, think-tank analysis and civil-society critique. None of it is used to verify a catalogue fact.</p>
      <div class="otr-grid">
        {off_record_html}
      </div>
      <p class="source-note"><strong>Status of these texts.</strong> They are scholarship, analysis and reporting, not primary sources for the instruments. Their claims are attributed to their authors; the catalogue records remain based on the official texts and pages cited in each JSON record. The selection is curated, not exhaustive.</p>
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
            <li><strong>{total}</strong> records in <code>catalog/instruments/</code>, each validated against the published JSON Schema and checked semantically against its sources.</li>
            <li><strong>{full_texts}</strong> full texts preserved; <strong>{originals}</strong> originals with SHA-256 in <code>catalog/acquisitions.json</code> and in the manifest.</li>
            <li><strong>{verification_counts.get("full_text_checked", 0)}</strong> texts read end-to-end; <strong>{verification_counts.get("metadata_verified", 0)}</strong> records verified at metadata level; <strong>{verification_counts.get("source_located", 0)}</strong> sources located.</li>
            <li>Counts are qualified: a total declared by a source, a number of individually verified entries, an unknown total and an act that does not apply are four different things. Zero is used only when a source or the entry list supports it.</li>
            <li>Citable units carry character offsets and page numbers; the build is deterministic and offline.</li>
          </ul>
        </div>
        <div>
          <h3>What is missing</h3>
          <ul class="checks">
            <li>CETS 225 is not in force: {len(cets_entries)} signatures and {len(cets_ratifications)} ratifications; five ratifications, including three member States, are required.</li>
            <li>WAICO: entry into force is not confirmed. {len(waico_states)} founding members are identified of 38 reported; China approved ratification domestically on 6 November 2026 but no deposit was verified, so the number of deposits is unknown.</li>
            <li>{number_word(ai_count).capitalize()} AI-specific treaties: CETS 225 and the WAICO Agreement. This does not mean no others exist, but that no other has been located and verified.</li>
            <li>No international complaint, sanction or judicial review mechanism is established by these instruments.</li>
            <li>Latin America, the Middle East and Central Asia remain uncovered by verified regional instruments.</li>
            <li><strong>Scope of sources.</strong> This is a register of written instruments, not an inventory of international law. Customary international law, general principles, <em>jus cogens</em>, Security Council resolutions (none AI-specific was located), decisions of courts and tribunals, international humanitarian law and general human-rights treaties beyond the ICCPR are outside the corpus. Section 03 interleaves some events that produced no instrument, but it is a selection, not a register. Section 04 lists non-official analysis and is not evidence for any record.</li>
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
