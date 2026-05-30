from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "research" / "russia-transport-report.md"
CANDIDATES = ROOT / "examples" / "staging" / "research" / "russia_catalog_candidates.json"
VALIDATOR = ROOT / "scripts" / "validate_staging_candidates.py"


class RussiaResearchContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report_text = REPORT.read_text(encoding="utf-8")
        cls.payload = json.loads(CANDIDATES.read_text(encoding="utf-8"))
        cls.candidates = cls.payload["candidates"]

    def test_report_covers_russia_and_transport_families(self) -> None:
        required_terms = [
            "Россия",
            "канатная дорога",
            "фуникулер",
            "зубчатых железных дорог",
            "монорельс",
            "панорамный лифт",
            "future seed",
        ]
        for term in required_terms:
            self.assertIn(term, self.report_text)

    def test_report_declares_no_production_seed_change(self) -> None:
        self.assertIn("не меняет UI, release-процесс или `VERSION`", self.report_text)
        self.assertIn("Production seed уже содержит утвержденный первый российский набор", self.report_text)
        self.assertIn("Staging JSON", self.report_text)

    def test_candidates_are_russian_and_cover_core_types(self) -> None:
        self.assertGreaterEqual(len(self.candidates), 6)
        self.assertTrue(all(candidate["country"] == "Россия" for candidate in self.candidates))

        transport_types = {candidate["transport_type_id"] for candidate in self.candidates}
        for transport_type in [
            "cable_urban",
            "funicular_classic",
            "funicular_modern",
            "cable_aerial_tram",
            "elevator_panoramic",
            "monorail",
        ]:
            self.assertIn(transport_type, transport_types)

    def test_candidates_are_approved_with_review_evidence(self) -> None:
        for candidate in self.candidates:
            with self.subTest(candidate=candidate["id"]):
                self.assertEqual(candidate["review"]["state"], "approved")
                self.assertEqual(candidate["review"]["reviewed_by"], "Codex worker #36")
                self.assertEqual(candidate["review"]["reviewed_at"], "2026-05-30")
                self.assertIn("Approved for Russia seed 1.0", candidate["review"]["notes"])
                self.assertRegex(candidate["review"]["notes"], r"OSM/Wikidata ids (not_required|не обязательны)")
                self.assertIn("source_urls", candidate)
                self.assertTrue(candidate["source_urls"])
                self.assertTrue(candidate["source_ids"])
                self.assertTrue(candidate["localized"]["ru"]["title"])
                self.assertRegex(candidate["id"], r"^[a-z][a-z0-9-]*$")

    def test_report_records_monorail_and_granularity_decisions(self) -> None:
        self.assertIn("Московский монорельс утвержден как historical-кейс", self.report_text)
        self.assertIn('operational_status = "historical"', self.report_text)
        self.assertIn("Для 1.0 Эльбрус, Архыз, Домбай, Роза Хутор и Бобровый лог не входят", self.report_text)
        for resort in ["Эльбрус", "Архыз", "Домбай", "Роза Хутор", "Бобровый лог"]:
            self.assertIn(resort, self.report_text)
        self.assertIn("resort-system", self.report_text)
        self.assertIn("line-level", self.report_text)

    def test_candidates_pass_staging_validator(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(CANDIDATES)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("прошли проверку", result.stdout)


if __name__ == "__main__":
    unittest.main()
