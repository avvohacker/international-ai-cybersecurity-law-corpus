"""Tests for corpus integrity, schema rules and deterministic builds."""

from __future__ import annotations

import html
import json
import re
import shutil
import socket
import ssl
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

    def test_domains_are_explicit(self) -> None:
        instruments = corpuslib.load_instruments()
        for iid, inst in instruments.items():
            domains = inst.get("domains")
            self.assertIsInstance(domains, list, iid)
            self.assertTrue(domains, iid)
            self.assertLessEqual(set(domains), {"ai", "cyber"}, iid)
            self.assertEqual(len(domains), len(set(domains)), iid)
        self.assertEqual(sum(1 for inst in instruments.values() if "ai" in inst["domains"]), 46)
        self.assertEqual(sum(1 for inst in instruments.values() if "cyber" in inst["domains"]), 8)

    def test_budapest_record_is_cyber_domain(self) -> None:
        inst = read_instrument("budapest-convention-2001")
        self.assertEqual(inst["domains"], ["cyber"])
        self.assertEqual(inst["category"], "cyber_treaty")
        self.assertEqual(inst["binding_status"], "binding")
        self.assertEqual(inst["status"], "in_force")
        parties = inst["parties"]
        self.assertEqual(parties["as_of"], "2026-11-24")
        self.assertEqual(len(parties["entries"]), 86)
        party_entries = [entry for entry in parties["entries"] if entry.get("role") == "party"]
        signatories = [entry for entry in parties["entries"] if entry.get("role") == "signatory"]
        self.assertEqual(len(party_entries), 84)
        self.assertEqual({entry["party"] for entry in signatories}, {"Ireland", "South Africa"})
        self.assertEqual(parties["counts"]["ratifications"]["total"], 48)
        self.assertEqual(parties["counts"]["ratifications"]["verified"], 48)
        self.assertEqual(parties["counts"]["accessions"]["total"], 36)
        self.assertEqual(parties["counts"]["accessions"]["verified"], 36)
        self.assertEqual(len(parties["reservations"]), 96)
        self.assertEqual(len(parties["declarations"]), 280)
        self.assertIn("84 Parties", parties["summary"])
        self.assertIn("Eleven further States have no recorded signature", parties["summary"])
        self.assertNotIn("ai_provisions", inst["relevance"])
        self.assertIn("coe-declarations", {source["id"] for source in inst["sources"]})

    def test_cyber_protocols_are_catalogued(self) -> None:
        ets = read_instrument("coe-ets-189")
        self.assertEqual(ets["domains"], ["cyber"])
        self.assertEqual(ets["category"], "cyber_treaty")
        self.assertEqual(ets["instrument_type"], "protocol")
        self.assertEqual(ets["status"], "in_force")
        self.assertEqual(len(ets["parties"]["entries"]), 47)
        self.assertEqual(
            sum(1 for entry in ets["parties"]["entries"] if entry.get("role") == "party"),
            38,
        )
        self.assertEqual(ets["parties"]["counts"]["ratifications"]["total"], 33)
        self.assertEqual(ets["parties"]["counts"]["accessions"]["total"], 5)
        self.assertEqual(len(ets["parties"]["reservations"]), 21)
        self.assertEqual(len(ets["parties"]["declarations"]), 11)
        self.assertEqual(len(ets["parties"]["notifications"]), 1)
        self.assertIn("coe-declarations-189", {source["id"] for source in ets["sources"]})
        self.assertTrue(ets["parties"]["reservations"][0].startswith("Croatia — Reservation"))
        self.assertTrue(ets["parties"]["notifications"][0].startswith("Ukraine — Communication"))
        self.assertEqual(ets["related"][0]["id"], "budapest-convention-2001")

        cets = read_instrument("coe-cets-224")
        self.assertEqual(cets["domains"], ["cyber"])
        self.assertEqual(cets["category"], "cyber_treaty")
        self.assertEqual(cets["instrument_type"], "protocol")
        self.assertEqual(cets["status"], "not_in_force")
        self.assertEqual(len(cets["parties"]["entries"]), 52)
        self.assertEqual(cets["parties"]["counts"]["signatures"]["total"], 52)
        self.assertEqual(cets["parties"]["counts"]["ratifications"]["total"], 4)
        self.assertEqual(len(cets["parties"]["reservations"]), 1)
        self.assertEqual(len(cets["parties"]["declarations"]), 21)
        self.assertNotIn("notifications", cets["parties"])
        self.assertIn("coe-declarations-224", {source["id"] for source in cets["sources"]})
        self.assertTrue(cets["parties"]["reservations"][0].startswith("Japan — Reservation"))
        self.assertEqual(
            {entry["party"] for entry in cets["parties"]["entries"] if entry.get("ratification")},
            {"Costa Rica", "Hungary", "Japan", "Serbia"},
        )
        self.assertEqual(cets["related"][0]["id"], "budapest-convention-2001")

    def test_eu_internal_cyber_law_records(self) -> None:
        for iid, instrument_type, entered, adopted in (
            ("eu-nis2-directive-2022", "directive", "2023-01-16", "2022-12-14"),
            ("eu-cyber-resilience-act-2024", "regulation", "2024-12-10", "2024-10-23"),
        ):
            inst = read_instrument(iid)
            self.assertEqual(inst["domains"], ["cyber"])
            self.assertEqual(inst["category"], "supranational_law")
            self.assertEqual(inst["instrument_type"], instrument_type)
            self.assertEqual(inst["binding_status"], "binding")
            self.assertEqual(inst["status"], "in_force")
            self.assertEqual(inst["dates"]["adopted"], adopted)
            self.assertEqual(inst["dates"]["entered_into_force"], entered)
            self.assertEqual(inst["legal_nature"]["qualification"], "supranational_law")
            self.assertNotIn("parties", inst)
            self.assertIn("not as an international", inst["relevance"]["reason"])

    def test_paris_call_record_uses_official_supporter_list(self) -> None:
        inst = read_instrument("paris-call-cyberspace-2018")
        self.assertEqual(inst["domains"], ["cyber"])
        self.assertEqual(inst["category"], "non_binding_instrument")
        self.assertEqual(inst["binding_status"], "non_binding")
        self.assertEqual(inst["status"], "adopted")
        self.assertEqual(inst["parties"]["act"], "endorsement")
        self.assertEqual(inst["parties"]["as_of"], "2026-11-24")
        entries = inst["parties"]["entries"]
        self.assertEqual(len(entries), 82)
        self.assertEqual(len({entry["party"] for entry in entries}), 82)
        states = [entry for entry in entries if entry["party"] != "European Union"]
        self.assertEqual(len(states), 81)
        self.assertIn("European Union", {entry["party"] for entry in entries})
        self.assertEqual(inst["parties"]["counts"]["endorsements"]["total"], 82)
        self.assertEqual(inst["parties"]["counts"]["endorsements"]["verified"], 82)
        self.assertEqual(inst["parties"]["counts"]["ratifications"]["basis"], "not_applicable")
        self.assertIn("paris-call-supporters", inst["parties"]["source_ids"])
        self.assertIn("paris-call-source", inst["parties"]["source_ids"])

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
        self.assertEqual(parties["counts"]["signatures"]["total"], 21)
        self.assertEqual(parties["counts"]["signatures"]["verified"], 21)
        self.assertEqual(parties["counts"]["ratifications"]["total"], 2)
        self.assertEqual(parties["counts"]["ratifications"]["verified"], 2)
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
        self.assertEqual(parties["act"], "endorsement")
        self.assertEqual(parties["counts"]["endorsements"]["total"], 65)
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
        self.assertEqual(parties["act"], "endorsement")
        self.assertEqual(parties["counts"]["endorsements"]["total"], 30)
        self.assertEqual(parties["counts"]["ratifications"]["basis"], "not_applicable")
        self.assertIsNone(parties["counts"]["ratifications"]["total"])
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
        self.assertEqual(parties["act"], "endorsement")
        self.assertEqual(parties["counts"]["endorsements"]["total"], 11)
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
        self.assertEqual(parties["act"], "endorsement")
        self.assertEqual(parties["counts"]["endorsements"]["total"], 58)
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
        self.assertEqual(inst["parties"]["act"], "political_signature")
        self.assertEqual(inst["parties"]["counts"]["political_signatures"]["total"], 2)

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
        self.assertEqual(inst["status"], "unknown")
        self.assertEqual(inst["verification"]["level"], "metadata_verified")
        self.assertNotIn("text", inst)
        parties = inst["parties"]
        self.assertEqual(parties["counts"]["signatures"]["total"], 38)
        self.assertEqual(parties["counts"]["signatures"]["verified"], 37)
        self.assertEqual(parties["counts"]["ratifications"]["basis"], "unknown")
        self.assertIsNone(parties["counts"]["ratifications"]["total"])
        self.assertEqual(parties["counts"]["ratifications"]["verified"], 0)
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
        self.assertNotIn("Bangladesh", names)
        self.assertNotIn("Singapore", names)
        china = next(entry for entry in parties["entries"] if entry["party"] == "China")
        self.assertEqual(china["signature"], "2026-07-16")
        self.assertEqual(china["domestic_approval"], "2026-11-06")
        self.assertNotIn("approval", china)
        self.assertNotIn("ratification", china)
        unknowns = " ".join(parties["unknowns"])
        self.assertIn("38", unknowns)
        self.assertIn("37", unknowns)
        self.assertIn("deposit", unknowns)
        self.assertIn("Bangladesh", unknowns)
        self.assertIn("observer", unknowns)
        self.assertIn("Article 11", inst["status_note"])
        self.assertIn("Singapore", unknowns)
        source_ids = {source["id"] for source in inst["sources"]}
        self.assertIn("bss-bangladesh-observer", source_ids)
        self.assertIn("thestar-singapore-invite", source_ids)

    def test_pax_silica_record(self) -> None:
        inst = read_instrument("pax-silica-declaration-2025")
        self.assertEqual(inst["instrument_type"], "declaration")
        self.assertEqual(inst["category"], "non_binding_instrument")
        self.assertEqual(inst["binding_status"], "non_binding")
        self.assertEqual(inst["status"], "adopted")
        self.assertEqual(inst["verification"]["level"], "metadata_verified")
        self.assertNotIn("text", inst)
        parties = inst["parties"]
        self.assertEqual(parties["act"], "endorsement")
        self.assertEqual(parties["counts"]["endorsements"]["total"], 26)
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
        self.assertIn("word 'signatory'", inst["status_note"])
        gaps = " ".join(inst["gaps"])
        self.assertIn("San Francisco", gaps)
        source_ids = {source["id"] for source in inst["sources"]}
        self.assertIn("state-san-francisco", source_ids)
        self.assertIn("australia-san-francisco", source_ids)

    def test_new_delhi_record(self) -> None:
        inst = read_instrument("new-delhi-declaration-2026")
        self.assertEqual(inst["category"], "non_binding_instrument")
        self.assertEqual(inst["instrument_type"], "declaration")
        self.assertEqual(inst["binding_status"], "non_binding")
        self.assertEqual(inst["status"], "adopted")
        self.assertEqual(inst["verification"]["level"], "metadata_verified")
        self.assertNotIn("text", inst)
        self.assertEqual(inst["dates"]["adopted"], "2026-02-19")
        parties = inst["parties"]
        self.assertEqual(parties["act"], "endorsement")
        self.assertEqual(parties["counts"]["endorsements"]["total"], 92)
        self.assertEqual(parties["counts"]["ratifications"]["basis"], "not_applicable")
        self.assertIsNone(parties["counts"]["ratifications"]["total"])
        self.assertEqual(len(parties["entries"]), 92)
        names = {entry["party"] for entry in parties["entries"]}
        self.assertIn("Colombia", names)
        self.assertIn("European Union", names)
        self.assertIn("International Fund for Agricultural Development", names)
        self.assertEqual(
            len(names - {"European Union", "International Fund for Agricultural Development"}),
            90,
        )
        self.assertNotIn("no itemised", " ".join(parties["unknowns"]).lower())
        source_ids = {source["id"] for source in inst["sources"]}
        self.assertIn("mea-declaration", source_ids)
        self.assertIn("pib-summit", source_ids)

    def test_brics_record(self) -> None:
        inst = read_instrument("brics-ai-statement-2025")
        self.assertEqual(inst["category"], "non_binding_instrument")
        self.assertEqual(inst["binding_status"], "non_binding")
        self.assertEqual(inst["status"], "adopted")
        self.assertEqual(inst["dates"]["adopted"], "2025-07-06")
        self.assertEqual(inst["verification"]["level"], "metadata_verified")
        self.assertNotIn("text", inst)
        self.assertEqual(inst["parties"]["act"], "collective_issue")
        self.assertEqual(inst["parties"]["counts"]["members"]["total"], 11)
        self.assertEqual(inst["parties"]["counts"]["members"]["verified"], 11)
        self.assertEqual(len(inst["parties"]["entries"]), 11)
        self.assertTrue(
            all(entry.get("role") == "member_state" for entry in inst["parties"]["entries"])
        )
        names = {entry["party"] for entry in inst["parties"]["entries"]}
        self.assertIn("Brazil", names)
        self.assertIn("China", names)
        self.assertIn("Iran", names)
        source_ids = {source["id"] for source in inst["sources"]}
        self.assertIn("brics-presidency-pdf", source_ids)
        self.assertIn("brazil-mfa-page", source_ids)
        self.assertIn("brics-members", source_ids)

    def test_depa_costa_rica_is_the_fifth_party(self) -> None:
        inst = read_instrument("depa-2020")
        parties = inst["parties"]
        self.assertEqual(parties["counts"]["parties"]["total"], 5)
        self.assertEqual(parties["counts"]["accessions"]["total"], 2)
        names = {entry["party"] for entry in parties["entries"]}
        self.assertEqual(
            names,
            {"New Zealand", "Singapore", "Chile", "Korea", "Costa Rica"},
        )
        costa = next(entry for entry in parties["entries"] if entry["party"] == "Costa Rica")
        self.assertEqual(costa["accession"], "2026-09-17")
        # The joint release announces the accession, not entry into force.
        self.assertNotIn("entry_into_force", costa)
        self.assertIn("fifth Party", inst["status_note"])
        self.assertIn("does not state an entry-into-force date", inst["status_note"])

    def test_afcfta_protocol_reads_article_2_languages_and_annex(self) -> None:
        inst = read_instrument("afcfta-digital-trade-protocol-2024")
        self.assertEqual(inst["status"], "unknown")
        self.assertEqual(inst["parties"]["counts"]["ratifications"]["basis"], "unknown")
        self.assertIsNone(inst["parties"]["counts"]["ratifications"]["total"])
        self.assertIn("sw", inst["languages"]["authentic"])
        self.assertIn("Kiswahili", inst["languages"]["note"])
        self.assertEqual(inst["languages"]["locator"], "Article 52")
        provisions = " ".join(inst["relevance"]["ai_provisions"])
        self.assertIn("Article 2(2)(f)", provisions)
        self.assertNotIn("Article 3", provisions)
        self.assertIn("Article 4 - State Parties shall", provisions)
        self.assertIn("Article 5 - national treatment", provisions)
        self.assertIn("Article 12 - technical standards", provisions)

    def test_unknown_is_not_zero_and_not_applicable_is_distinct(self) -> None:
        waico = read_instrument("waico-establishment-agreement-2026")["parties"]["counts"]
        afcfta = read_instrument("afcfta-digital-trade-protocol-2024")["parties"]["counts"]
        hrc = read_instrument("un-hrc-res-63-15")["parties"]["counts"]
        for counts in (waico, afcfta):
            ratifications = counts["ratifications"]
            self.assertEqual(ratifications["basis"], "unknown")
            self.assertIsNone(ratifications["total"])
            self.assertEqual(ratifications["verified"], 0)
        self.assertEqual(hrc["ratifications"]["basis"], "not_applicable")
        self.assertIsNone(hrc["ratifications"]["total"])
        self.assertNotEqual(
            hrc["ratifications"]["basis"], waico["ratifications"]["basis"]
        )
        self.assertEqual(waico["signatures"]["total"], 38)
        self.assertEqual(waico["signatures"]["verified"], 37)

    def test_domestic_approval_is_not_an_international_deposit(self) -> None:
        inst = read_instrument("waico-establishment-agreement-2026")
        china = next(
            entry for entry in inst["parties"]["entries"] if entry["party"] == "China"
        )
        self.assertIn("domestic_approval", china)
        self.assertNotIn("ratification", china)
        self.assertNotIn("deposit", china)
        self.assertEqual(inst["parties"]["counts"]["ratifications"]["verified"], 0)

    def test_participation_acts_remain_distinguishable(self) -> None:
        acts: dict[str, list[str]] = {}
        for iid, inst in corpuslib.load_instruments().items():
            act = (inst.get("parties") or {}).get("act")
            if act:
                acts.setdefault(act, []).append(iid)
        for act in (
            "treaty_signature",
            "endorsement",
            "collective_issue",
            "political_signature",
            "resolution",
        ):
            self.assertIn(act, acts)
        sf = read_instrument("san-francisco-declaration-2026")
        self.assertEqual(sf["parties"]["act"], "political_signature")
        self.assertTrue(
            all("political_signature" in entry for entry in sf["parties"]["entries"])
        )
        self.assertEqual(sf["parties"]["counts"]["political_signatures"]["total"], 10)
        brics = read_instrument("brics-ai-statement-2025")
        self.assertTrue(
            all("signature" not in entry for entry in brics["parties"]["entries"])
        )

    def test_provenance_assertions_name_specific_source_locations(self) -> None:
        generic = {
            "status, dates and status_note as recorded",
            "languages.authentic",
            "relevance.ai_provisions and relevance.reason",
            "parties.entries, parties.counts and parties.as_of",
            "Articles 1-18",
            "Full text: no treaty clause",
            "Media note and full text",
            "Text released in English",
            "Full text, paragraphs on sensitive technologies, critical infrastructure, working groups",
            "Signing lists and MFA statement",
        }
        specific = re.compile(
            r"(Article|Annex|paragraph|para\.|section|page|chart|press release|"
            r"media note|statement|list|record|table|title|opening|final clauses)",
            re.I,
        )
        curated = {
            "afcfta-digital-trade-protocol-2024": {"status", "provisions", "languages", "counts"},
            "brics-ai-statement-2025": {"status", "parties", "counts"},
            "depa-2020": {"status", "parties", "counts"},
            "san-francisco-declaration-2026": {"parties"},
            "waico-establishment-agreement-2026": {"status", "parties"},
        }
        for iid, inst in corpuslib.load_instruments().items():
            provenance = inst.get("provenance") or {}
            self.assertTrue(provenance, iid)
            assertions = provenance.get("assertions") or []
            for item in assertions:
                locator = item.get("locator") or ""
                self.assertNotIn(locator, generic, iid)
                self.assertRegex(locator, specific, f"{iid}: {locator!r}")
                self.assertTrue(item.get("source_ids"), iid)
                self.assertEqual(item.get("date"), inst["dates"]["verified_on"], iid)
                self.assertIn(item.get("method"), corpuslib.ASSERTION_METHODS, iid)
            fields = {item.get("field") for item in assertions}
            for field in curated.get(iid, set()):
                self.assertIn(field, fields, iid)

    def test_off_record_reading_list_is_attributed_and_linked(self) -> None:
        data = json.loads((ROOT / "data" / "off-the-record.json").read_text(encoding="utf-8"))
        entries = data.get("entries") or []
        self.assertGreaterEqual(len(entries), 10)
        instrument_ids = set(corpuslib.load_instruments())
        for entry in entries:
            for field in ("id", "strand", "author", "title", "outlet", "date", "url", "adds"):
                self.assertTrue(entry.get(field), entry.get("id"))
            self.assertTrue(entry["url"].startswith("https://"), entry["id"])
            for related in entry.get("related") or []:
                self.assertIn(related, instrument_ids, entry["id"])

    def test_hrc_resolution_record(self) -> None:
        inst = read_instrument("un-hrc-res-63-15")
        self.assertEqual(inst["category"], "non_binding_instrument")
        self.assertEqual(inst["instrument_type"], "resolution")
        self.assertEqual(inst["binding_status"], "non_binding")
        self.assertEqual(inst["status"], "adopted")
        self.assertEqual(inst["dates"]["adopted"], "2026-10-06")
        self.assertEqual(inst["verification"]["level"], "metadata_verified")
        self.assertNotIn("text", inst)
        self.assertEqual(inst["parties"]["act"], "resolution")
        self.assertEqual(inst["parties"]["counts"]["ratifications"]["basis"], "not_applicable")
        self.assertIsNone(inst["parties"]["counts"]["ratifications"]["total"])
        self.assertEqual(inst["parties"]["entries"], [])
        self.assertIn("adopted without a vote", inst["status_note"].lower())
        source_ids = {source["id"] for source in inst["sources"]}
        self.assertIn("hrc-resolution", source_ids)
        self.assertIn("hrc-record", source_ids)

    def test_candidate_register_counts(self) -> None:
        entries = json.loads((ROOT / "catalog" / "candidates.json").read_text(encoding="utf-8"))
        self.assertEqual(len(entries), 31)
        decisions = {"included": 0, "pending": 0, "excluded": 0}
        instruments = corpuslib.load_instruments()
        for entry in entries:
            decisions[entry["decision"]] += 1
            if entry["decision"] == "included":
                self.assertIn(entry["instrument_id"], instruments)
            else:
                self.assertIsNone(entry["instrument_id"])
        self.assertEqual(decisions, {"included": 11, "pending": 11, "excluded": 9})

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

    def test_binding_declaration_requires_sourced_rationale(self) -> None:
        # The name of the instrument is not a rule: a declaration may be argued
        # to be binding, but the qualification must be reasoned and sourced.
        inst = read_instrument("bletchley-declaration-2023")
        inst["binding_status"] = "binding"
        report = corpuslib.Report()
        corpuslib.validate_instrument(inst, report, "test")
        self.assertIn("legal_nature_missing", [i.code for i in report.errors])
        inst["legal_nature"] = {
            "qualification": "political_act",
            "rationale": "Test rationale: qualification must be argued, not inferred from the name.",
            "source_ids": [inst["sources"][0]["id"]],
        }
        report = corpuslib.Report()
        corpuslib.validate_instrument(inst, report, "test")
        self.assertNotIn("legal_nature_missing", [i.code for i in report.errors])
        self.assertEqual(report.errors, [])

    def test_schema_rejects_unknown_fields_modes_and_impossible_dates(self) -> None:
        base = read_instrument("un-ga-res-79-1")
        cases = []
        unknown = json.loads(json.dumps(base))
        unknown["unexpected_property"] = True
        cases.append((unknown, "schema_error"))
        bad_mode = json.loads(json.dumps(base))
        bad_mode["text"]["units_mode"] = "nonexistent_mode"
        cases.append((bad_mode, "schema_error"))
        impossible = json.loads(json.dumps(base))
        impossible["dates"]["signed"] = "2026-02-30"
        cases.append((impossible, "bad_date"))
        for record, expected in cases:
            report = corpuslib.Report()
            corpuslib.validate_instrument(record, report, "test")
            self.assertIn(expected, [i.code for i in report.errors], expected)

    def test_unit_page_and_range_errors_are_reported_not_raised(self) -> None:
        inst = read_instrument("un-ga-res-79-62")
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / "corpus" / inst["id"]
            shutil.copytree(ROOT / "corpus" / inst["id"], dst)
            units = dst / "units.jsonl"
            rows = [json.loads(line) for line in units.read_text(encoding="utf-8").splitlines()]
            rows[0]["page_start"] = 999
            rows[1]["char_end"] = rows[1]["char_start"]
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
        codes = [i.code for i in report.errors]
        self.assertIn("bad_unit_page", codes)
        self.assertIn("bad_unit_anchor", codes)

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
        self.assertEqual(summary["counts"]["by_category"]["supranational_law"], 3)
        self.assertEqual(summary["counts"]["total"], 54)
        self.assertEqual(summary["counts"]["by_domain"], {"ai": 46, "cyber": 8, "joint": 0})
        self.assertEqual(summary["counts"]["by_binding"], {"binding": 17, "non_binding": 37})

    def test_site_maps_are_complete_and_neutral(self) -> None:
        import build_site

        build_site.main()
        page = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(page.count('class="map-frame"'), 15)
        self.assertEqual(page.count('class="map-key"'), 15)
        self.assertEqual(page.count('class="map-participation"'), 15)
        self.assertNotIn('class="map-sub"', page)
        figures = re.findall(r'<figure class="map-card">(.*?)</figure>', page, re.S)
        self.assertEqual(len(figures), 15)
        self.assertNotIn("What it is", page)
        by_title = {
            re.search(r'<span class="map-title">([^<]+)</span>', figure).group(1): figure
            for figure in figures
        }
        self.assertEqual(
            list(by_title),
            [
                "WAICO 2026",
                "CETS 225",
                "UN Cybercrime Convention",
                "Budapest Convention",
                "CETS 224",
                "ETS 189",
                "Malabo Convention",
                "New Delhi 2026",
                "Paris 2025",
                "Military AI 2023",
                "Bletchley 2023",
                "Pax Silica 2025",
                "BRICS 2025",
                "Seoul 2024",
                "Paris Call 2018",
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
        self.assertEqual(page.count('class="map-parties"'), 15)
        self.assertEqual(by_title["Paris Call 2018"].count('fill="#5a7fbd"'), 81)
        self.assertEqual(by_title["Paris Call 2018"].count('<li data-party='), 82)
        self.assertIn("81 States + EU", by_title["Paris Call 2018"])
        self.assertIn("95 States + EU · 3 Parties", by_title["UN Cybercrime Convention"])
        self.assertIn("84 Parties + 2 signatories", by_title["Budapest Convention"])
        self.assertIn("38 Parties + 9 signatories", by_title["ETS 189"])
        self.assertIn("52 signatories · 4 ratifications", by_title["CETS 224"])
        self.assertIn("20 Parties + 11 signatories", by_title["Malabo Convention"])
        self.assertIn('data-status="Party (ratified or acceded)"', by_title["Budapest Convention"])
        self.assertIn("eleven non-party States with no recorded act not mapped", by_title["Budapest Convention"])
        self.assertEqual(by_title["New Delhi 2026"].count('fill="#a9c0e0"'), 0)
        self.assertIn('data-status="Ratified"', page)
        self.assertIn('data-status="Signed only"', page)
        self.assertIn('data-status="Endorsed"', page)
        self.assertIn('data-status="Member States (collective)"', page)
        self.assertIn("State: member of the group (collective statement)", page)
        self.assertEqual(by_title["WAICO 2026"].count('fill="#c8102e"'), 37)
        self.assertEqual(by_title["WAICO 2026"].count('fill="#5a7fbd"'), 0)
        self.assertEqual(by_title["New Delhi 2026"].count('fill="#a67c52"'), 90)
        self.assertEqual(by_title["New Delhi 2026"].count('fill="#5a7fbd"'), 0)
        self.assertEqual(by_title["BRICS 2025"].count('fill="#d97706"'), 11)
        self.assertEqual(by_title["BRICS 2025"].count('fill="#a67c52"'), 0)

    def test_timeline_lists_every_record_and_sections_follow_the_new_order(self) -> None:
        import build_site

        build_site.main()
        page = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        ids = set(re.findall(r'<li[^>]*data-instrument-id="([^"]+)"', page))
        self.assertEqual(ids, set(corpuslib.load_instruments()))
        self.assertEqual(page.count('data-instrument-id='), 54)
        for label in (
            "00 · Index",
            "01 · Sets",
            "02 · 15 maps",
            "03 · Timeline",
            "04 · Reading room",
            "05 · The catalogue",
            "06 · Method and limits",
        ):
            self.assertIn(label, page)
        self.assertIn("The treaties, declarations and statements", page)
        self.assertIn("The argument around the record", page)
        self.assertIn("What this corpus contains", page)
        self.assertIn("<h1>International AI and Cybersecurity Law</h1>", page)
        self.assertIn('class="atlas-subtitle">Atlas</p>', page)
        self.assertNotIn("International AI and Cybersecurity Law Atlas", page)
        index_block = page[page.find('id="index"'):page.find('id="form"')]
        self.assertNotIn("atlas", index_block.lower())
        self.assertIn("Three sets: AI, cyber and international binding", page)
        self.assertIn('class="membership-table"', page)
        self.assertEqual(page.count("data-set-region="), 7)
        self.assertIn('data-set-region="cyber_only"><th scope="row">Cyber only', page)
        self.assertIn('data-set-region="cyber_only"', page)
        self.assertIn("NIS2 Directive", page)
        self.assertIn("Cyber Resilience Act", page)
        self.assertIn("EU Artificial Intelligence Act", page)
        self.assertIn("International binding", page)
        self.assertNotIn('class="cyber-status"', page)
        self.assertEqual(page.count('data-weight="highlight"'), 14)
        self.assertEqual(page.count('data-weight="record"'), 40)
        instruments = corpuslib.load_instruments()
        highlighted = re.findall(
            r'data-weight="highlight" data-instrument-id="([^"]+)"', page
        )
        self.assertEqual(len(highlighted), 14)
        international_binding = {
            iid
            for iid, inst in instruments.items()
            if inst["binding_status"] == "binding"
            and inst["category"] != "supranational_law"
        }
        self.assertEqual(international_binding, set(highlighted))
        for iid in ("eu-ai-act", "eu-nis2-directive-2022", "eu-cyber-resilience-act-2024"):
            self.assertNotIn(f'data-weight="highlight" data-instrument-id="{iid}"', page)
            self.assertIn(f'data-weight="record" data-instrument-id="{iid}"', page)
        self.assertEqual(page.count("EU internal-law record"), 4)
        self.assertNotIn("data-weight=\"highlight\" data-instrument-id=\"new-delhi-declaration-2026\"", page)
        self.assertNotIn("data-weight=\"highlight\" data-instrument-id=\"paris-ai-action-summit-statement-2025\"", page)
        self.assertLess(page.find('id="index"'), page.find('id="form"'))
        self.assertLess(page.find('id="form"'), page.find('id="maps"'))
        self.assertLess(page.find('id="maps"'), page.find('id="timeline"'))
        self.assertLess(page.find('id="timeline"'), page.find('id="unseen"'))
        self.assertLess(page.find('id="unseen"'), page.find('id="catalogue"'))
        self.assertGreaterEqual(page.count('class="tl-item tl-event unseen-item"'), 6)
        self.assertEqual(page.count('class="tl-item tl-instrument"'), 54)
        self.assertIn("Three sets: AI, cyber and international binding", page)
        self.assertIn("The story, with the instruments in it", page)
        self.assertIn("The argument around the record", page)
        self.assertNotIn("The shape of the corpus", page)
        self.assertNotIn("cat-ai_treaty bar-fill", page)

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
                "UN Cybercrime Convention",
                "Budapest Convention",
                "CETS 224",
                "ETS 189",
                "Malabo Convention",
                "New Delhi 2026",
                "Paris 2025",
                "Military AI 2023",
                "Bletchley 2023",
                "Pax Silica 2025",
                "BRICS 2025",
                "Seoul 2024",
                "Paris Call 2018",
            ],
        )
        groups = re.findall(r'data-map-group="([^"]+)">\s*<h3[^>]*>([^<]+)', page)
        self.assertEqual(
            groups,
            [
                ("binding_ai", "Binding AI instruments"),
                ("binding_cyber", "Binding cyber instruments"),
                ("nonbinding_ai", "Non-binding AI instruments"),
                ("nonbinding_cyber", "Non-binding cyber instruments"),
            ],
        )
        instruments = corpuslib.load_instruments()
        for title, iid in (
            ("UN Cybercrime Convention", "un-cybercrime-convention-2024"),
            ("Budapest Convention", "budapest-convention-2001"),
            ("CETS 224", "coe-cets-224"),
            ("ETS 189", "coe-ets-189"),
            ("Malabo Convention", "au-malabo-convention-2014"),
            ("New Delhi 2026", "new-delhi-declaration-2026"),
            ("Paris 2025", "paris-ai-action-summit-statement-2025"),
            ("Bletchley 2023", "bletchley-declaration-2023"),
            ("Seoul 2024", "seoul-declaration-2024"),
            ("Military AI 2023", "political-declaration-military-ai-2023"),
            ("CETS 225", "coe-cets-225"),
            ("WAICO 2026", "waico-establishment-agreement-2026"),
            ("Pax Silica 2025", "pax-silica-declaration-2025"),
            ("BRICS 2025", "brics-ai-statement-2025"),
            ("Paris Call 2018", "paris-call-cyberspace-2018"),
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
            ("UN Cybercrime Convention", "un-cybercrime-convention-2024", "Ratified"),
            ("Budapest Convention", "budapest-convention-2001", "Party (ratified or acceded)"),
            ("CETS 224", "coe-cets-224", "Ratified"),
            ("ETS 189", "coe-ets-189", "Party (ratified or acceded)"),
            ("Malabo Convention", "au-malabo-convention-2014", "Ratified"),
            ("New Delhi 2026", "new-delhi-declaration-2026", "Endorsed"),
            ("Paris 2025", "paris-ai-action-summit-statement-2025", "Endorsed"),
            ("Bletchley 2023", "bletchley-declaration-2023", "Endorsed"),
            ("Seoul 2024", "seoul-declaration-2024", "Endorsed"),
            ("Military AI 2023", "political-declaration-military-ai-2023", "Endorsed"),
            ("CETS 225", "coe-cets-225", "Ratified"),
            ("WAICO 2026", "waico-establishment-agreement-2026", "Signed"),
            ("Pax Silica 2025", "pax-silica-declaration-2025", "Endorsed"),
            ("Paris Call 2018", "paris-call-cyberspace-2018", "Endorsed"),
        ]
        for title, iid, expected_group in cases:
            record = read_instrument(iid)
            entries = record["parties"]["entries"]
            figure = figures[title]
            body_text = figure.split('<div class="map-parties"', 1)[1].split(
                '<div class="map-about">', 1
            )[0]
            self.assertTrue(body_text, title)
            groups: dict[str, set[str]] = {}
            for status, block in re.findall(
                r'<div class="party-group" data-status="([^"]+)">(.*?)</div>',
                body_text,
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
            party_group = (
                "Party (ratified or acceded)"
                if any(entry.get("accession") for entry in entries)
                else "Ratified"
            )
            parties = {
                entry["party"]
                for entry in entries
                if entry.get("ratification") or entry.get("accession")
            }
            if parties:
                expected = {
                    party_group: parties,
                    "Signed only": {entry["party"] for entry in entries} - parties,
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
            "domestic approval 6 November 2026; no deposit verified",
            figures["WAICO 2026"],
        )

    def test_map_about_sections_cite_records(self) -> None:
        import build_site

        build_site.main()
        page = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(page.count('class="map-about"'), 15)
        figures = {
            re.search(r'<span class="map-title">([^<]+)</span>', figure).group(1): figure
            for figure in re.findall(
                r'<figure class="map-card">(.*?)</figure>', page, re.S
            )
        }
        cases = [
            ("UN Cybercrime Convention", "un-cybercrime-convention-2024"),
            ("Budapest Convention", "budapest-convention-2001"),
            ("CETS 224", "coe-cets-224"),
            ("ETS 189", "coe-ets-189"),
            ("Malabo Convention", "au-malabo-convention-2014"),
            ("New Delhi 2026", "new-delhi-declaration-2026"),
            ("Paris 2025", "paris-ai-action-summit-statement-2025"),
            ("Bletchley 2023", "bletchley-declaration-2023"),
            ("Seoul 2024", "seoul-declaration-2024"),
            ("Military AI 2023", "political-declaration-military-ai-2023"),
            ("CETS 225", "coe-cets-225"),
            ("WAICO 2026", "waico-establishment-agreement-2026"),
            ("Pax Silica 2025", "pax-silica-declaration-2025"),
            ("BRICS 2025", "brics-ai-statement-2025"),
            ("Paris Call 2018", "paris-call-cyberspace-2018"),
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

    def test_cyber_declaration_texts_are_rendered(self) -> None:
        import build_site

        build_site.main()
        page = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        figures = {
            re.search(r'<span class="map-title">([^<]+)</span>', figure).group(1): figure
            for figure in re.findall(
                r'<figure class="map-card">(.*?)</figure>', page, re.S
            )
        }
        cases = [
            ("Budapest Convention", "budapest-convention-2001", 376),
            ("ETS 189", "coe-ets-189", 33),
            ("CETS 224", "coe-cets-224", 22),
            ("UN Cybercrime Convention", "un-cybercrime-convention-2024", 15),
        ]
        for title, iid, total in cases:
            record = read_instrument(iid)
            figure = figures[title]
            details = re.search(
                r'<details class="map-declarations">(.*?)</details>', figure, re.S
            )
            self.assertIsNotNone(details, title)
            self.assertIn(
                f"{total} {'entry' if total == 1 else 'entries'}", details.group(1), title
            )
            for key, label in (
                ("reservations", "Reservations"),
                ("declarations", "Declarations"),
                ("notifications", "Communications"),
            ):
                items = record["parties"].get(key) or []
                if not items:
                    continue
                self.assertIn(f"<h4>{label} <span>{len(items)}</span></h4>", figure)
                self.assertIn(html.escape(items[0], quote=True), page, title)

    def test_un_cybercrime_record_uses_official_depositary_table(self) -> None:
        record = read_instrument("un-cybercrime-convention-2024")
        self.assertEqual(record["category"], "cyber_treaty")
        self.assertEqual(record["domains"], ["cyber"])
        self.assertEqual(record["status"], "not_in_force")
        self.assertIsNone(record["dates"]["entered_into_force"])
        self.assertEqual(record["dates"]["adopted"], "2024-12-24")
        self.assertEqual(len(record["parties"]["entries"]), 96)
        states = [
            entry
            for entry in record["parties"]["entries"]
            if entry["party"] != "European Union"
        ]
        self.assertEqual(len(states), 95)
        parties = {
            entry["party"]
            for entry in record["parties"]["entries"]
            if entry.get("ratification")
        }
        self.assertEqual(parties, {"Azerbaijan", "Qatar", "Viet Nam"})
        self.assertEqual(record["parties"]["counts"]["signatures"]["total"], 96)
        self.assertEqual(record["parties"]["counts"]["ratifications"]["total"], 3)
        source_ids = {source["id"] for source in record["sources"]}
        self.assertIn("untc-status", source_ids)
        status_source = next(
            source for source in record["sources"] if source["id"] == "untc-status"
        )
        self.assertEqual(
            status_source["url"],
            "https://treaties.un.org/Pages/ViewDetails.aspx?src=TREATY&mtdsg_no=XVIII-16&chapter=18&clang=_en",
        )
        self.assertIn("96 signatories", record["parties"]["summary"])
        self.assertIn("leaving 37", record["status_note"])
        self.assertEqual(len(record["parties"]["reservations"]), 11)
        self.assertEqual(len(record["parties"]["declarations"]), 4)
        self.assertIn("untc-declarations", source_ids)
        self.assertIn("Azerbaijan — Reservation made upon signature", record["parties"]["reservations"][0])
        self.assertIn("The Socialist Republic of Viet Nam", record["parties"]["declarations"][1])
        self.assertIn("stable", record["provenance"]["notes"])

    def test_malabo_record_uses_au_status_list(self) -> None:
        record = read_instrument("au-malabo-convention-2014")
        self.assertEqual(record["category"], "cyber_treaty")
        self.assertEqual(record["domains"], ["cyber"])
        self.assertEqual(record["status"], "in_force")
        self.assertEqual(record["dates"]["adopted"], "2014-06-27")
        self.assertEqual(record["dates"]["entered_into_force"], "2023-06-08")
        self.assertEqual(len(record["parties"]["entries"]), 31)
        parties = {
            entry["party"]
            for entry in record["parties"]["entries"]
            if entry.get("ratification")
        }
        self.assertEqual(len(parties), 20)
        self.assertEqual(
            record["parties"]["counts"]["signatures"]["total"], 21
        )
        self.assertEqual(
            record["parties"]["counts"]["ratifications"]["total"], 20
        )
        self.assertIn("Côte d’Ivoire", parties)
        self.assertIn("Cabo Verde", parties)
        source_ids = {source["id"] for source in record["sources"]}
        self.assertIn("au-status-list", source_ids)
        self.assertIn("2 February 2026", record["status_note"])
        self.assertIn("24", record["gaps"][4])
        self.assertIn("unknown", record["parties"]["unknowns"][2])

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
        waico_reported = waico["parties"]["counts"]["signatures"]["total"]
        self.assertIn(f"{waico_reported} reported founding members", page)
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
            f"{waico_reported} reported",
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
        self.assertIn("report to the 2028 Meeting of High Contracting Parties", page)
        self.assertIn("2028 Meeting of High Contracting Parties", ccw["status_note"])
        self.assertIn(
            "five ratifications, including three member States, are required",
            page,
        )
        self.assertIn(
            "five ratifications including at least three Council of Europe member States",
            cets["status_note"],
        )
        self.assertIn("Article 15 requires three instruments of ratification", page)
        self.assertIn("three instruments of ratification", waico["status_note"])
        self.assertIn("54 endorsers as of September 2026", page)
        self.assertIn("54 endorsers as of September 2026", pax["parties"]["unknowns"][-1])


class TestLinkAudit(unittest.TestCase):
    """Offline tests for the link classifier; probe() is never called here."""

    def setUp(self) -> None:
        import audit_sources

        self.audit = audit_sources

    def test_classification_without_network(self) -> None:
        classify = self.audit.classify
        self.assertEqual(classify(200, {"Server": "nginx"}, "<html>ok</html>"), ("ok", "http_2xx"))
        self.assertEqual(classify(301, {}, ""), ("transient", "http_301"))
        self.assertEqual(classify(403, {}, ""), ("anti_bot", "http_403"))
        self.assertEqual(classify(405, {"Server": "nginx"}, ""), ("anti_bot", "http_405"))
        self.assertEqual(classify(429, {}, ""), ("anti_bot", "http_429"))
        self.assertEqual(classify(451, {}, ""), ("anti_bot", "http_451"))
        self.assertEqual(classify(404, {}, ""), ("broken", "http_404"))
        self.assertEqual(classify(410, {}, ""), ("broken", "http_410"))
        self.assertEqual(classify(500, {}, ""), ("transient", "http_500"))
        self.assertEqual(classify(200, {"Server": "cloudflare"}, "Just a moment..."), ("anti_bot", "challenge_on_200"))
        self.assertEqual(classify(200, {"cf-mitigated": "challenge"}, ""), ("anti_bot", "challenge_on_200"))
        self.assertEqual(classify(None, error=TimeoutError("timeout")), ("transient", "timeout"))
        self.assertEqual(classify(None, error=socket.gaierror("dns")), ("broken", "dns"))
        self.assertEqual(classify(None, error=ConnectionRefusedError()), ("broken", "connection"))
        self.assertEqual(classify(None, error=ssl.SSLCertVerificationError("cert")), ("broken", "tls_certificate"))
        self.assertEqual(classify(None, error=ssl.SSLError("handshake")), ("broken", "tls_handshake"))
        wrapped = __import__("urllib.error", fromlist=["URLError"]).URLError(socket.gaierror("dns"))
        self.assertEqual(classify(None, error=wrapped), ("broken", "dns"))

    def test_known_browser_only_host(self) -> None:
        self.assertIn(
            "State Department",
            self.audit.browser_only_host(
                "https://www.state.gov/political-declaration-on-responsible-military-use-of-artificial-intelligence-and-autonomy/"
            ),
        )
        self.assertIsNone(self.audit.browser_only_host("https://www.state.gov.example/x"))
        self.assertEqual(
            self.audit.override_browser_only("https://www.state.gov/x", 404, "broken", "http_404"),
            ("anti_bot", "known_browser_only"),
        )
        self.assertEqual(
            self.audit.override_browser_only("https://example.com/x", 404, "broken", "http_404"),
            ("broken", "http_404"),
        )

    def test_catalog_targets_cover_all_official_sources(self) -> None:
        targets = self.audit.catalog_targets()
        self.assertEqual(len(targets), 143)
        self.assertEqual(len({target.instrument_id for target in targets}), 54)
        self.assertTrue(
            all(target.url.startswith(("https://", "http://")) for target in targets)
        )
        self.assertEqual(
            targets,
            sorted(targets, key=lambda target: (target.instrument_id, target.source_id)),
        )

    def test_targets_cover_all_panels(self) -> None:
        import build_site

        targets = self.audit.targets()
        self.assertEqual(len(build_site.MAP_INSTRUMENT_IDS), 15)
        self.assertEqual(
            {target.instrument_id for target in targets},
            set(build_site.MAP_INSTRUMENT_IDS),
        )
        self.assertTrue(
            all(target.url.startswith(("https://", "http://")) for target in targets)
        )
        self.assertEqual(
            targets,
            sorted(targets, key=lambda target: (target.instrument_id, target.source_id)),
        )


if __name__ == "__main__":
    unittest.main()
