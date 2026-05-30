from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "examples" / "staging" / "research" / "russia_catalog_candidates.json"
REPORT = ROOT / "docs" / "research" / "russia-transport-report.md"
DEMO_CATALOG_RUSSIA = ROOT / "scripts" / "demo_catalog_russia.gd"

APPROVED_IDS = {
    "nizhny-novgorod-bor-cable-car",
    "moscow-vorobyovy-gory-cable-car",
    "vladivostok-funicular",
    "nizhny-novgorod-kremlin-funicular",
    "pyatigorsk-mashuk-cable-car",
    "svetlogorsk-panorama-elevator",
    "moscow-monorail",
}

REQUIRED_TYPES = {
    "cable_urban",
    "funicular_classic",
    "funicular_modern",
    "cable_aerial_tram",
    "elevator_panoramic",
    "monorail",
}

DEFERRED_RESORT_SYSTEMS = [
    "Эльбрус",
    "Архыз",
    "Домбай",
    "Роза Хутор",
    "Бобровый лог",
]


def _extract_object_ids(source: str) -> set[str]:
    return set(re.findall(r'"id": "([^"]+)"', source))


class RussiaSeedReviewContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report_text = REPORT.read_text(encoding="utf-8")
        cls.demo_source = DEMO_CATALOG_RUSSIA.read_text(encoding="utf-8")
        cls.candidates = json.loads(STAGING.read_text(encoding="utf-8"))["candidates"]
        cls.by_id = {candidate["id"]: candidate for candidate in cls.candidates}

    def test_exact_russia_staging_set_is_approved_for_seed_1_0(self) -> None:
        self.assertEqual(set(self.by_id), APPROVED_IDS)

        for object_id, candidate in self.by_id.items():
            with self.subTest(object_id=object_id):
                review = candidate["review"]
                self.assertEqual(review["state"], "approved")
                self.assertEqual(review["reviewed_by"], "Codex worker #36")
                self.assertEqual(review["reviewed_at"], "2026-05-30")
                self.assertIn("Approved for Russia seed 1.0", review["notes"])
                self.assertIn("Coordinates reviewed", review["notes"])
                self.assertTrue(candidate["source_urls"])
                self.assertTrue(candidate["source_ids"])
                self.assertTrue(candidate["status_checked_at"])
                self.assertTrue(candidate["status_source_url"].startswith("https://"))

    def test_production_seed_contains_all_approved_russia_objects(self) -> None:
        demo_ids = _extract_object_ids(self.demo_source)
        self.assertEqual(APPROVED_IDS, demo_ids)
        self.assertIn('"country": "Россия"', self.demo_source)

        staging_types = {candidate["transport_type_id"] for candidate in self.candidates}
        self.assertTrue(REQUIRED_TYPES.issubset(staging_types))

    def test_moscow_monorail_decision_is_historical(self) -> None:
        monorail = self.by_id["moscow-monorail"]
        self.assertEqual(monorail["transport_type_id"], "monorail")
        self.assertEqual(monorail["operational_status"], "historical")
        self.assertIn("historical", monorail["review"]["notes"])
        self.assertIn("28 июня 2025 года", self.report_text)
        self.assertIn("включить как historical-объект", self.report_text)

    def test_osm_wikidata_absence_has_explicit_source_review(self) -> None:
        for object_id, candidate in self.by_id.items():
            with self.subTest(object_id=object_id):
                source_ids = candidate["source_ids"]
                has_osm_or_wikidata = "osm" in source_ids or "wikidata" in source_ids
                accepted_official = "official" in " ".join(source_ids.keys()) or "official" in candidate["review"]["notes"]
                has_explicit_not_required = "OSM/Wikidata ids not_required" in candidate["review"]["notes"]

                self.assertTrue(
                    has_osm_or_wikidata or (accepted_official and has_explicit_not_required),
                    f"{object_id} должен иметь OSM/Wikidata id или явный official-source review",
                )

    def test_deferred_resort_granularity_is_an_explicit_decision(self) -> None:
        self.assertIn("Для 1.0 Эльбрус, Архыз, Домбай, Роза Хутор и Бобровый лог не входят", self.report_text)
        self.assertIn("должны моделироваться будущими отдельными пакетами", self.report_text)

        for resort_name in DEFERRED_RESORT_SYSTEMS:
            with self.subTest(resort=resort_name):
                self.assertIn(resort_name, self.report_text)

        for candidate in self.candidates:
            title = candidate["localized"]["ru"]["title"]
            for resort_name in DEFERRED_RESORT_SYSTEMS:
                self.assertNotIn(resort_name, title)


if __name__ == "__main__":
    unittest.main()
