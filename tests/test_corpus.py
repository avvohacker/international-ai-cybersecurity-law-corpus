"""Tests for corpus integrity, schema rules and deterministic builds."""

from __future__ import annotations

import json
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

    def test_candidate_register_counts(self) -> None:
        entries = json.loads((ROOT / "catalog" / "candidates.json").read_text(encoding="utf-8"))
        self.assertEqual(len(entries), 20)
        decisions = {"included": 0, "pending": 0, "excluded": 0}
        instruments = corpuslib.load_instruments()
        for entry in entries:
            decisions[entry["decision"]] += 1
            if entry["decision"] == "included":
                self.assertIn(entry["instrument_id"], instruments)
            else:
                self.assertIsNone(entry["instrument_id"])
        self.assertEqual(decisions, {"included": 6, "pending": 7, "excluded": 7})

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

    def test_site_maps_are_complete_and_neutral(self) -> None:
        import build_site

        build_site.main()
        page = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(page.count('class="map-frame"'), 5)
        self.assertEqual(page.count('class="map-key"'), 5)
        for title in (
            "Paris 2025",
            "Bletchley 2023",
            "Seoul 2024",
            "Military AI 2023",
            "CETS 225",
        ):
            self.assertIn(title, page)
        self.assertNotIn("USA / UK: no", page)
        self.assertNotIn("Non-signatory", page)
        self.assertIn("EU European Union", page)
        self.assertIn("AU African Union Commission", page)
        self.assertIn("Supranational: endorsed", page)
        self.assertIn("Signed + ratified", page)


if __name__ == "__main__":
    unittest.main()
