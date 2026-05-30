from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "europe-catalog-research.md"
CANDIDATES = ROOT / "examples" / "staging" / "europe_catalog_candidates.json"
VALIDATOR = ROOT / "scripts" / "validate_staging_candidates.py"


class EuropeCatalogResearchContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = REPORT.read_text(encoding="utf-8")
        cls.payload = json.loads(CANDIDATES.read_text(encoding="utf-8"))
        cls.candidates = cls.payload["candidates"]

    def test_report_exists_and_is_russian(self) -> None:
        self.assertTrue(REPORT.exists())
        cyrillic = sum("а" <= char.lower() <= "я" or char in "Ёё" for char in self.text)
        latin = sum("a" <= char.lower() <= "z" for char in self.text)
        self.assertGreater(cyrillic, latin)

    def test_report_covers_required_countries_and_transport_types(self) -> None:
        for country in ["Португалия", "Франция", "Италия", "Чехия", "Словакия", "Польша"]:
            self.assertIn(country, self.text)

        for transport_type in [
            "cable_gondola",
            "cable_aerial_tram",
            "cable_urban",
            "cable_tourist",
            "funicular_classic",
            "funicular_water",
            "funicular_modern",
            "rail_cog",
            "suspended_train",
            "monorail",
            "special_transport_system",
        ]:
            self.assertIn(f"`{transport_type}`", self.text)

    def test_report_documents_sources_confidence_priorities_and_risks(self) -> None:
        for expected in [
            "Уровни уверенности",
            "высокая",
            "средняя",
            "низкая",
            "Что включать первым",
            "Источники",
            "Риски",
            "Petřín",
            "temporarily_closed_planned",
            "2026-05-30",
        ]:
            self.assertIn(expected, self.text)

    def test_staging_candidates_cover_required_countries(self) -> None:
        self.assertEqual(self.payload["schema_version"], "import-candidates-v1")
        countries = {candidate["country"] for candidate in self.candidates}
        self.assertEqual(
            countries,
            {"Португалия", "Франция", "Италия", "Чехия", "Словакия", "Польша"},
        )

    def test_staging_candidates_are_approved_with_sources(self) -> None:
        for candidate in self.candidates:
            self.assertEqual(candidate["visit_status_id"], "not_visited")
            self.assertEqual(candidate["review"]["state"], "approved")
            self.assertEqual(candidate["review"]["reviewed_by"], "Codex #35 seed-review")
            self.assertEqual(candidate["review"]["reviewed_at"], "2026-05-30")
            self.assertIn("Evidence 2026-05-30", candidate["review"]["notes"])
            self.assertIn("ru", candidate["localized"])
            self.assertTrue(candidate["localized"]["ru"]["title"])
            self.assertTrue(candidate["localized"]["ru"]["description"])
            self.assertTrue(candidate["source_urls"])
            self.assertTrue(candidate["status_source_url"].startswith("https://"))

    def test_staging_candidate_file_passes_local_validator(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(CANDIDATES)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
