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


if __name__ == "__main__":
    unittest.main()
