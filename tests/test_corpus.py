"""Tests for corpus integrity, schema rules and deterministic builds."""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import corpuslib  # noqa: E402


def read_instrument(iid: str) -> dict:
    return json.loads((ROOT / "catalog" / "instruments" / f"{iid}.json").read_text(encoding="utf-8"))


class TestCatalogue(unittest.TestCase):
    def test_repository_validates(self) -> None:
        report = corpuslib.validate()
        self.assertTrue(report.ok(), [i.as_dict() for i in report.errors])

    def test_ids_unique_and_match_filenames(self) -> None:
        instruments = corpuslib.load_instruments()
        self.assertEqual(len(instruments), len(list((ROOT / "catalog" / "instruments").glob("*.json"))))
        for iid, inst in instruments.items():
            self.assertEqual(iid, inst["id"])

    def test_key_text_passages(self) -> None:
        expectations = {
            "coe-cets-225": [
                "Article 30 – Signature and entry into force",
                "five signatories, including at least three member States",
                "both texts being equally authentic",
            ],
            "un-ga-res-78-265": ["78/265.", "21 March 2024"],
            "depa-2020": ["Article 8.2: Artificial Intelligence"],
            "sadea-2020": ["ARTICLE 31", "Artificial Intelligence"],
            "g7-hiroshima-code-2023": ["voluntary guidance"],
            "oecd-ai-recommendation-2019": ["1.5. Accountability"],
        }
        for iid, needles in expectations.items():
            body = (ROOT / "corpus" / iid / "text" / "en.txt").read_text(encoding="utf-8")
            for needle in needles:
                self.assertIn(needle, body, f"{iid} is missing {needle!r}")

    def test_cets_has_36_article_units(self) -> None:
        units = corpuslib.load_units("coe-cets-225")
        articles = [u for u in units if u["kind"] == "article"]
        self.assertEqual(len(articles), 36)
        self.assertEqual(articles[0]["label"], "Article 1 — Object and purpose")
        self.assertEqual(articles[-1]["label"], "Article 36 — Notification")

    def test_cets_party_data_complete(self) -> None:
        inst = read_instrument("coe-cets-225")
        parties = inst["parties"]
        self.assertEqual(parties["signatories_total"], 21)
        self.assertEqual(parties["ratifications_total"], 2)
        self.assertEqual(len(parties["entries"]), 21)
        by_party = {entry["party"]: entry for entry in parties["entries"]}
        self.assertEqual(by_party["Bosnia and Herzegovina"]["ratification"], "2026-10-28")
        self.assertEqual(by_party["European Union"]["ratification"], "2026-05-15")
        self.assertEqual(len(parties["declarations"]), 5)
        self.assertIn("None recorded", parties["reservations"][0])
        snapshot = ROOT / "corpus" / "coe-cets-225" / "status" / "coe-cets-225-status-2026-11-23.json"
        self.assertTrue(snapshot.exists())
        manifest = json.loads(
            (ROOT / "corpus" / "coe-cets-225" / "manifest.json").read_text(encoding="utf-8")
        )
        status_files = [f for f in manifest["files"] if f["role"] == "status_snapshot"]
        self.assertEqual(len(status_files), 1)
        self.assertEqual(status_files[0]["sha256"], corpuslib.sha256_file(snapshot))
        snapshot_data = json.loads(snapshot.read_text(encoding="utf-8"))
        self.assertEqual(snapshot_data["status_date"], "2026-11-23")
        self.assertFalse(snapshot_data["official_static_export_found"])

    def test_paris_statement_record(self) -> None:
        inst = read_instrument("paris-ai-action-summit-statement-2025")
        self.assertEqual(inst["binding_status"], "non_binding")
        self.assertEqual(inst["verification"]["level"], "full_text_checked")
        parties = inst["parties"]
        self.assertEqual(parties["signatories_total"], 65)
        self.assertEqual(len(parties["entries"]), 65)
        names = {entry["party"] for entry in parties["entries"]}
        for name in ("China", "India", "Brazil", "France", "Zimbabwe", "European Union", "African Union Commission"):
            self.assertIn(name, names)
        self.assertNotIn("United States of America", names)
        self.assertNotIn("United Kingdom", names)
        body = (ROOT / "corpus" / inst["id"] / "text" / "en.txt").read_text(encoding="utf-8")
        self.assertIn("civil applications", body)
        self.assertIn("Global Dialogue on AI governance", body)
        # The stored PDF has 64 entries; Zimbabwe appears only on the later official page.
        self.assertIn("64. European Union", body)
        self.assertNotIn("Zimbabwe", body)

    def test_bletchley_party_list(self) -> None:
        inst = read_instrument("bletchley-declaration-2023")
        parties = inst["parties"]
        self.assertEqual(parties["signatories_total"], 30)
        self.assertEqual(parties["ratifications_total"], 0)
        self.assertEqual(len(parties["entries"]), 30)
        names = {entry["party"] for entry in parties["entries"]}
        for name in (
            "China",
            "United States of America",
            "United Kingdom",
            "New Zealand",
            "European Union",
        ):
            self.assertIn(name, names)
        self.assertNotIn("Russia", names)

    def test_seoul_party_list(self) -> None:
        inst = read_instrument("seoul-declaration-2024")
        parties = inst["parties"]
        self.assertEqual(parties["signatories_total"], 11)
        self.assertEqual(len(parties["entries"]), 11)
        names = {entry["party"] for entry in parties["entries"]}
        for name in (
            "United States of America",
            "United Kingdom",
            "France",
            "Germany",
            "European Union",
        ):
            self.assertIn(name, names)
        for name in ("China", "India", "Brazil", "South Africa"):
            self.assertNotIn(name, names)

    def test_military_declaration_party_list(self) -> None:
        inst = read_instrument("political-declaration-military-ai-2023")
        parties = inst["parties"]
        self.assertEqual(parties["as_of"], "2024-11-27")
        self.assertEqual(parties["signatories_total"], 58)
        self.assertEqual(len(parties["entries"]), 58)
        names = {entry["party"] for entry in parties["entries"]}
        for name in (
            "United States of America",
            "United Kingdom",
            "France",
            "Germany",
            "Japan",
        ):
            self.assertIn(name, names)
        for name in ("China", "India", "Brazil", "South Africa", "Russia"):
            self.assertNotIn(name, names)

    def test_china_initiative_record(self) -> None:
        inst = read_instrument("china-global-ai-governance-initiative-2023")
        self.assertEqual(inst["binding_status"], "non_binding")
        self.assertEqual(inst["verification"]["level"], "full_text_checked")
        body = (ROOT / "corpus" / inst["id"] / "text" / "en.txt").read_text(encoding="utf-8")
        self.assertIn("exclusive groups", body)
        self.assertIn("international institution to govern AI", body)
        self.assertIn("prudent and responsible attitude", body)

    def test_us_uk_ai_safety_mou_record(self) -> None:
        inst = read_instrument("us-uk-ai-safety-mou-2024")
        self.assertEqual(inst["instrument_type"], "mou")
        self.assertEqual(inst["binding_status"], "non_binding")
        self.assertEqual(inst["dates"]["signed"], "2024-04-01")
        self.assertEqual(inst["verification"]["level"], "metadata_verified")
        self.assertNotIn("text", inst)
        self.assertIn("not a treaty", inst["status_note"])
        source_ids = {source["id"] for source in inst["sources"]}
        self.assertIn("govuk-mou-summary", source_ids)
        self.assertIn("govuk-press-release", source_ids)
        self.assertEqual(inst["parties"]["signatories_total"], 2)

    def test_us_eu_ttc_ai_safety_dialogue_record(self) -> None:
        inst = read_instrument("us-eu-ttc-ai-safety-dialogue-2024")
        self.assertEqual(inst["instrument_type"], "joint_statement")
        self.assertEqual(inst["binding_status"], "non_binding")
        self.assertEqual(inst["dates"]["adopted"], "2024-04-05")
        self.assertEqual(inst["verification"]["level"], "metadata_verified")
        self.assertNotIn("text", inst)
        self.assertIn("not a treaty", inst["status_note"])
        self.assertIn("No standalone", inst["status_note"])
        provisions = " ".join(inst["relevance"]["ai_provisions"])
        self.assertIn("committed to establishing a Dialogue", provisions)
        source_ids = {source["id"] for source in inst["sources"]}
        self.assertIn("ec-ttc-joint-statement", source_ids)
        self.assertIn("ustr-ttc-joint-statement", source_ids)

    def test_waico_record(self) -> None:
        inst = read_instrument("waico-establishment-agreement-2026")
        self.assertEqual(inst["instrument_type"], "treaty")
        self.assertEqual(inst["category"], "ai_treaty")
        self.assertEqual(inst["binding_status"], "binding")
        self.assertEqual(inst["status"], "not_in_force")
        self.assertEqual(inst["verification"]["level"], "metadata_verified")
        self.assertNotIn("text", inst)
        parties = inst["parties"]
        self.assertEqual(parties["signatories_total"], 38)
        self.assertEqual(parties["ratifications_total"], 0)
        self.assertEqual(len(parties["entries"]), 37)
        names = {entry["party"] for entry in parties["entries"]}
        for name in (
            "China",
            "Russia",
            "Brazil",
            "South Africa",
            "Kazakhstan",
            "Brunei",
            "Dominica",
        ):
            self.assertIn(name, names)
        self.assertNotIn("United States of America", names)
        self.assertNotIn("India", names)
        china = next(entry for entry in parties["entries"] if entry["party"] == "China")
        self.assertEqual(china["signature"], "2026-07-16")
        self.assertEqual(china["approval"], "2026-11-06")
        self.assertNotIn("ratification", china)
        unknowns = " ".join(parties["unknowns"])
        self.assertIn("38", unknowns)
        self.assertIn("37", unknowns)
        self.assertIn("deposit", unknowns)

    def test_pax_silica_record(self) -> None:
        inst = read_instrument("pax-silica-declaration-2025")
        self.assertEqual(inst["instrument_type"], "declaration")
        self.assertEqual(inst["category"], "non_binding_instrument")
        self.assertEqual(inst["binding_status"], "non_binding")
        self.assertEqual(inst["status"], "adopted")
        self.assertEqual(inst["verification"]["level"], "metadata_verified")
        self.assertNotIn("text", inst)
        parties = inst["parties"]
        self.assertEqual(parties["signatories_total"], 26)
        self.assertEqual(len(parties["entries"]), 26)
        names = {entry["party"] for entry in parties["entries"]}
        for name in (
            "United States of America",
            "United Kingdom",
            "European Union",
            "Kazakhstan",
            "India",
            "Paraguay",
        ):
            self.assertIn(name, names)
        for name in ("China", "Russia", "Brazil", "South Africa", "Taiwan"):
            self.assertNotIn(name, names)
        self.assertIn("not a treaty", inst["status_note"])
        self.assertIn("26", inst["status_note"])

    def test_candidate_register_counts(self) -> None:
        entries = json.loads((ROOT / "catalog" / "candidates.json").read_text(encoding="utf-8"))
        self.assertEqual(len(entries), 22)
        decisions = {"included": 0, "pending": 0, "excluded": 0}
        instruments = corpuslib.load_instruments()
        for entry in entries:
            decisions[entry["decision"]] += 1
            if entry["decision"] == "included":
                self.assertIn(entry["instrument_id"], instruments)
            else:
                self.assertIsNone(entry["instrument_id"])
        self.assertEqual(decisions, {"included": 8, "pending": 7, "excluded": 7})

    def test_pact_units_are_citable(self) -> None:
        units = corpuslib.load_units("un-ga-res-79-1")
        self.assertEqual(len(units), 248)
        labels = [unit["label"] for unit in units]
        self.assertEqual(len(labels), len(set(labels)))
        self.assertIn("Pact for the Future — Preamble, para. 1", labels)
        self.assertIn("Global Digital Compact — Annex I, para. 49", labels)
        self.assertIn("Declaration on Future Generations — Annex II, para. 32", labels)
        self.assertIn("Pact for the Future — Section II: International peace and security, Action 13", labels)
        self.assertIn("Pact for the Future — Section V: Transforming global governance, Action 56", labels)

    def test_acquisitions_hashes_match_stored_files(self) -> None:
        entries = json.loads((ROOT / "catalog" / "acquisitions.json").read_text(encoding="utf-8"))
        self.assertGreater(len(entries), 0)
        for entry in entries:
            path = ROOT / "corpus" / entry["instrument_id"] / entry["dest"]
            self.assertTrue(path.exists(), path)
            self.assertEqual(corpuslib.sha256_file(path), entry["sha256"], path)

    def test_declaration_cannot_be_binding(self) -> None:
        inst = read_instrument("bletchley-declaration-2023")
        inst["binding_status"] = "binding"
        report = corpuslib.Report()
        corpuslib.validate_instrument(inst, report, "test")
        self.assertIn("category_mismatch", [i.code for i in report.errors])

    def test_hash_mismatch_is_detected(self) -> None:
        inst = read_instrument("un-ga-res-79-62")
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / "corpus" / inst["id"]
            shutil.copytree(ROOT / "corpus" / inst["id"], dst)
            (dst / "text" / "en.txt").write_text("tampered text\n", encoding="utf-8")
            original = corpuslib.CORPUS_DIR
            corpuslib.CORPUS_DIR = Path(tmp) / "corpus"
            try:
                report = corpuslib.Report()
                corpuslib.validate_corpus_text(inst, report)
            finally:
                corpuslib.CORPUS_DIR = original
        self.assertIn("hash_mismatch", [i.code for i in report.errors])

    def test_unit_text_divergence_is_detected(self) -> None:
        inst = read_instrument("un-ga-res-79-62")
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / "corpus" / inst["id"]
            shutil.copytree(ROOT / "corpus" / inst["id"], dst)
            units = dst / "units.jsonl"
            rows = [json.loads(line) for line in units.read_text(encoding="utf-8").splitlines()]
            rows[0]["text"] = "altered unit"
            units.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            original = corpuslib.CORPUS_DIR
            corpuslib.CORPUS_DIR = Path(tmp) / "corpus"
            try:
                report = corpuslib.Report()
                corpuslib.validate_corpus_text(inst, report)
            finally:
                corpuslib.CORPUS_DIR = original
        codes = {i.code for i in report.errors}
        self.assertIn("unit_text_mismatch", codes)
        self.assertIn("hash_mismatch", codes)


class TestBuild(unittest.TestCase):
    def test_build_is_deterministic(self) -> None:
        corpuslib.build()
        names = ["catalog.json", "CATALOG.md", "checksums.sha256", "verification-report.json"]
        first = {name: (corpuslib.BUILD_DIR / name).read_bytes() for name in names}
        corpuslib.build()
        second = {name: (corpuslib.BUILD_DIR / name).read_bytes() for name in names}
        self.assertEqual(first, second)

    def test_build_counts_match_catalogue(self) -> None:
        summary = corpuslib.build()
        self.assertEqual(summary["counts"]["total"], len(corpuslib.load_instruments()))
        self.assertEqual(
            sum(summary["counts"]["by_category"].values()), summary["counts"]["total"]
        )
        self.assertGreaterEqual(summary["counts"]["full_texts"], 6)
        self.assertEqual(summary["counts"]["by_category"]["draft_negotiation"], 1)
        self.assertEqual(summary["counts"]["by_category"]["ai_treaty"], 2)

    def test_site_maps_are_complete_and_neutral(self) -> None:
        import build_site

        build_site.main()
        page = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(page.count('class="map-frame"'), 7)
        self.assertEqual(page.count('class="map-key"'), 7)
        figures = re.findall(r'<figure class="map-card">(.*?)</figure>', page, re.S)
        self.assertEqual(len(figures), 7)
        by_title = {
            re.search(r'<span class="map-title">([^<]+)</span>', figure).group(1): figure
            for figure in figures
        }
        self.assertEqual(
            list(by_title),
            [
                "WAICO 2026",
                "CETS 225",
                "Paris 2025",
                "Military AI 2023",
                "Bletchley 2023",
                "Pax Silica 2025",
                "Seoul 2024",
            ],
        )
        for figure in figures:
            self.assertNotIn("<text", figure)
            self.assertNotIn("map-label", figure)
            self.assertNotIn("map-org-label", figure)
            self.assertNotIn("map-org-leader", figure)
        self.assertEqual(page.count('class="map-org-note"'), 5)
        self.assertIn(
            "European Union: ratified. 27 EU member States without an individual signature",
            by_title["CETS 225"],
        )
        self.assertIn(
            "European Union: endorsed. 21 EU member States without an individual endorsement",
            by_title["Bletchley 2023"],
        )
        self.assertIn(
            "European Union: endorsed. 24 EU member States without an individual endorsement",
            by_title["Seoul 2024"],
        )
        self.assertIn(
            "European Union: endorsed. 21 EU member States without an individual endorsement",
            by_title["Pax Silica 2025"],
        )
        self.assertIn(
            "African Union Commission: endorsed. 46 African Union member States",
            by_title["Paris 2025"],
        )
        # All 27 EU member States endorsed Paris individually, so the EU is not
        # indicated on that map at all.
        self.assertNotIn("European Union: endorsed", by_title["Paris 2025"])
        self.assertEqual(by_title["CETS 225"].count('fill="#a9c0e0"'), 27)
        self.assertEqual(by_title["Paris 2025"].count('fill="#a9c0e0"'), 46)
        self.assertEqual(by_title["WAICO 2026"].count('fill="#a9c0e0"'), 0)
        self.assertNotIn("USA / UK: no", page)
        self.assertNotIn("Non-signatory", page)
        self.assertNotIn("International organisation", page)
        self.assertNotIn("Supranational:", page)
        self.assertIn("State: member of a participating organisation", page)
        self.assertIn("State: ratified", page)
        self.assertIn("State: signed only", page)
        self.assertIn("States only", page)
        self.assertIn("37 confirmed of 38 reported", page)
        self.assertEqual(page.count('class="map-parties"'), 7)
        self.assertIn('data-status="Ratified"', page)
        self.assertIn('data-status="Signed only"', page)
        self.assertIn('data-status="Endorsed"', page)

    def test_map_order_follows_binding_then_adopters(self) -> None:
        import build_site

        build_site.main()
        page = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        titles = re.findall(r'<span class="map-title">([^<]+)</span>', page)
        self.assertEqual(
            titles,
            [
                "WAICO 2026",
                "CETS 225",
                "Paris 2025",
                "Military AI 2023",
                "Bletchley 2023",
                "Pax Silica 2025",
                "Seoul 2024",
            ],
        )
        instruments = corpuslib.load_instruments()
        for title, iid in (
            ("Paris 2025", "paris-ai-action-summit-statement-2025"),
            ("Bletchley 2023", "bletchley-declaration-2023"),
            ("Seoul 2024", "seoul-declaration-2024"),
            ("Military AI 2023", "political-declaration-military-ai-2023"),
            ("CETS 225", "coe-cets-225"),
            ("WAICO 2026", "waico-establishment-agreement-2026"),
            ("Pax Silica 2025", "pax-silica-declaration-2025"),
        ):
            official = html.escape(instruments[iid]["title"]["official"])
            self.assertIn(
                f'<span class="map-full-title">{official}</span>', page, title
            )

    def test_organisation_membership_is_complete_and_resolves(self) -> None:
        import build_site

        data = json.loads(
            (ROOT / "data" / "organisations.json").read_text(encoding="utf-8")
        )
        organisations = {org["name"]: org for org in data["organisations"]}
        self.assertEqual(
            set(organisations), {"European Union", "African Union Commission"}
        )
        self.assertEqual(len(organisations["European Union"]["members"]), 27)
        self.assertEqual(
            len(organisations["African Union Commission"]["members"]), 55
        )
        _, by_name, by_iso = build_site.load_geo()
        for org in organisations.values():
            self.assertTrue(org["sources"])
            self.assertEqual(len(org["members"]), len(set(org["members"])))
            for member in org["members"]:
                iso = build_site.iso_for(member, by_name)
                self.assertTrue(iso, member)
                self.assertTrue(iso in by_iso or iso in build_site.MICRO, member)

    def test_map_party_lists_match_records(self) -> None:
        import build_site

        build_site.main()
        page = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('class="matrix"', page)
        self.assertNotIn("Who stands where", page)
        figures = {
            re.search(r'<span class="map-title">([^<]+)</span>', figure).group(1): figure
            for figure in re.findall(
                r'<figure class="map-card">(.*?)</figure>', page, re.S
            )
        }
        cases = [
            ("Paris 2025", "paris-ai-action-summit-statement-2025", "Endorsed"),
            ("Bletchley 2023", "bletchley-declaration-2023", "Endorsed"),
            ("Seoul 2024", "seoul-declaration-2024", "Endorsed"),
            ("Military AI 2023", "political-declaration-military-ai-2023", "Endorsed"),
            ("CETS 225", "coe-cets-225", "Ratified"),
            ("WAICO 2026", "waico-establishment-agreement-2026", "Signed"),
            ("Pax Silica 2025", "pax-silica-declaration-2025", "Endorsed"),
        ]
        for title, iid, expected_group in cases:
            record = read_instrument(iid)
            entries = record["parties"]["entries"]
            figure = figures[title]
            body = re.search(
                r'<div class="map-parties"[^>]*>(.*?)</div>\s*<div class="map-about">',
                figure,
                re.S,
            )
            self.assertIsNotNone(body, title)
            groups: dict[str, set[str]] = {}
            for status, block in re.findall(
                r'<div class="party-group" data-status="([^"]+)">(.*?)</div>',
                body.group(1),
                re.S,
            ):
                count = int(re.search(r"<span>(\d+)</span>", block).group(1))
                listed = [
                    html.unescape(name)
                    for name in re.findall(r'<li data-party="([^"]+)">', block)
                ]
                self.assertEqual(count, len(listed), title)
                self.assertEqual(len(listed), len(set(listed)), title)
                groups[status] = set(listed)
            ratified = {
                entry["party"] for entry in entries if entry.get("ratification")
            }
            if ratified:
                expected = {
                    "Ratified": ratified,
                    "Signed only": {entry["party"] for entry in entries} - ratified,
                }
            else:
                expected = {expected_group: {entry["party"] for entry in entries}}
            self.assertEqual(groups, expected, title)
        self.assertIn(
            "Bosnia and Herzegovina (28 October 2026) and the European Union "
            "(15 May 2026) have ratified",
            page,
        )
        self.assertIn(
            "ratification approved 6 November 2026; no deposit verified",
            figures["WAICO 2026"],
        )

    def test_map_about_sections_cite_records(self) -> None:
        import build_site

        build_site.main()
        page = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(page.count('class="map-about"'), 7)
        figures = {
            re.search(r'<span class="map-title">([^<]+)</span>', figure).group(1): figure
            for figure in re.findall(
                r'<figure class="map-card">(.*?)</figure>', page, re.S
            )
        }
        cases = [
            ("Paris 2025", "paris-ai-action-summit-statement-2025"),
            ("Bletchley 2023", "bletchley-declaration-2023"),
            ("Seoul 2024", "seoul-declaration-2024"),
            ("Military AI 2023", "political-declaration-military-ai-2023"),
            ("CETS 225", "coe-cets-225"),
            ("WAICO 2026", "waico-establishment-agreement-2026"),
            ("Pax Silica 2025", "pax-silica-declaration-2025"),
        ]
        for title, iid in cases:
            record = read_instrument(iid)
            figure = html.unescape(figures[title])
            about = re.search(
                r'<div class="map-about">(.*?)</div>', figures[title], re.S
            )
            self.assertIsNotNone(about, title)
            text = re.sub(
                r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", about.group(1)))
            )
            meta = (
                record["instrument_type"].replace("_", " ").capitalize()
                + " · "
                + build_site.BINDING_LABELS[record["binding_status"]]
            )
            self.assertIn(meta, text, title)
            self.assertIn(record["relevance"]["reason"], text, title)
            self.assertIn(record["dates"]["notes"], text, title)
            for key, label in (
                ("adopted", "Adopted"),
                ("signed", "Signed"),
                ("opened_for_signature", "Opened for signature"),
                ("closed_for_signature", "Closed for signature"),
                ("entered_into_force", "In force since"),
                ("published", "Published"),
            ):
                if record["dates"].get(key):
                    self.assertIn(
                        f"{label} {build_site.format_date(record['dates'][key])}",
                        text,
                        title,
                    )
            if record["status"] != "adopted":
                self.assertIn(
                    f"Status: {build_site.STATUS_LABELS[record['status']]}", text, title
                )
            for source in record["sources"]:
                if source["kind"] in build_site.OFFICIAL_SOURCE_KINDS:
                    self.assertIn(source["url"], figure, title)
                else:
                    self.assertNotIn(source["url"], figure, title)
            self.assertIn(f"/catalog/instruments/{iid}.json", figure, title)

    def test_site_numeric_claims_match_records(self) -> None:
        import build_site

        build_site.main()
        page = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        instruments = list(corpuslib.load_instruments().values())
        by_id = {inst["id"]: inst for inst in instruments}
        cets = by_id["coe-cets-225"]
        waico = by_id["waico-establishment-agreement-2026"]
        pax = by_id["pax-silica-declaration-2025"]
        paris = by_id["paris-ai-action-summit-statement-2025"]
        bletchley = by_id["bletchley-declaration-2023"]
        cets_entries = cets["parties"]["entries"]
        ratifications = sum(1 for entry in cets_entries if entry.get("ratification"))
        ai_count = sum(1 for inst in instruments if inst["category"] == "ai_treaty")
        self.assertIn(f"{len(instruments)} instruments", page)
        self.assertIn(
            f"CETS 225: {len(cets_entries)} signatures, {ratifications} ratifications",
            page,
        )
        self.assertIn(
            f"{waico['parties']['signatories_total']} reported founding members", page
        )
        self.assertIn(f"{len(pax['parties']['entries'])} signatories", page)
        self.assertIn(f"{len(paris['parties']['entries'])} endorsers", page)
        paris_states = [
            entry
            for entry in paris["parties"]["entries"]
            if entry["party"] not in {"European Union", "African Union Commission"}
        ]
        self.assertIn(
            f"{len(paris_states)} States + EU + AU Commission", page
        )
        bletchley_states = [
            entry
            for entry in bletchley["parties"]["entries"]
            if entry["party"] != "European Union"
        ]
        self.assertIn(f"{len(bletchley_states)} States + EU", page)
        cets_states = [
            entry for entry in cets_entries if entry["party"] != "European Union"
        ]
        self.assertIn(
            f"{len(cets_states)} States + EU · {ratifications} ratifications", page
        )
        self.assertIn(
            f"{len(waico['parties']['entries'])} confirmed of "
            f"{waico['parties']['signatories_total']} reported",
            page,
        )
        self.assertIn(
            f"{build_site.number_word(ai_count).capitalize()} AI-specific treaties", page
        )
        self.assertIn(
            f'<p class="stat-number">{ai_count}</p><p class="stat-label">AI-specific treaties</p>',
            page,
        )
        self.assertNotIn("193 States", page)
        self.assertNotIn("28 States and the EU", page)

    def test_historical_notes_match_records(self) -> None:
        import build_site

        build_site.main()
        page = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        paris = read_instrument("paris-ai-action-summit-statement-2025")
        bletchley = read_instrument("bletchley-declaration-2023")
        cets = read_instrument("coe-cets-225")
        waico = read_instrument("waico-establishment-agreement-2026")
        pax = read_instrument("pax-silica-declaration-2025")
        seoul = read_instrument("seoul-declaration-2024")
        ccw = read_instrument("ccw-gge-laws-2026")
        self.assertIn("the 19 February 2025 PDF lists 64", page)
        self.assertIn("PDF lists 64", paris["status_note"])
        self.assertIn("listed 60", page)
        self.assertIn("listed 60", paris["status_note"])
        self.assertIn("New Zealand joined on 23 October 2024", page)
        self.assertIn("New Zealand joined on 23 October 2024", bletchley["status_note"])
        self.assertIn("Seoul Ministerial Statement of 22 May 2024", page)
        self.assertIn("22 May 2024", seoul["status_note"])
        self.assertIn("report due 2028", page)
        self.assertIn("2028 Meeting of High Contracting Parties", ccw["status_note"])
        self.assertIn(
            "Five ratifications are required, including three Council of Europe member States",
            page,
        )
        self.assertIn(
            "five ratifications including at least three Council of Europe member States",
            cets["status_note"],
        )
        self.assertIn("three ratifications required, Article 15", page)
        self.assertIn("three instruments of ratification", waico["status_note"])
        self.assertIn("54 endorsers as of September 2026", page)
        self.assertIn("54 endorsers as of September 2026", pax["parties"]["unknowns"][-1])


if __name__ == "__main__":
    unittest.main()
