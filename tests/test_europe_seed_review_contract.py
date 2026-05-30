from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "examples" / "staging" / "europe_catalog_candidates.json"
REPORT = ROOT / "docs" / "europe-catalog-research.md"

EXPECTED_COUNTRIES = {
    "Португалия",
    "Франция",
    "Италия",
    "Чехия",
    "Словакия",
    "Польша",
}

EXPECTED_STATUS_BY_ID = {
    "braga-bom-jesus-funicular": "unknown",
    "grenoble-bastille-cable-car": "unknown",
    "como-brunate-funicular": "unknown",
    "prague-petrin-funicular": "temporarily_closed_planned",
    "stary-smokovec-hrebienok-funicular": "unknown",
    "zakopane-kasprowy-wierch-cable-car": "unknown",
}

EXPECTED_WIKIDATA_BY_ID = {
    "braga-bom-jesus-funicular": "Q892885",
    "grenoble-bastille-cable-car": "Q1520467",
    "como-brunate-funicular": "Q1055831",
    "prague-petrin-funicular": "Q1502676",
    "stary-smokovec-hrebienok-funicular": "Q7607830",
    "zakopane-kasprowy-wierch-cable-car": "Q637591",
}

class EuropeSeedReviewContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(CANDIDATES.read_text(encoding="utf-8"))
        cls.candidates = cls.payload["candidates"]
        cls.by_id = {candidate["id"]: candidate for candidate in cls.candidates}
        cls.report_text = REPORT.read_text(encoding="utf-8")

    def test_review_approves_exactly_six_required_countries(self) -> None:
        self.assertEqual(len(self.candidates), 6)
        self.assertEqual({candidate["country"] for candidate in self.candidates}, EXPECTED_COUNTRIES)

        for object_id, candidate in self.by_id.items():
            with self.subTest(object_id=object_id):
                self.assertEqual(candidate["review"]["state"], "approved")
                self.assertEqual(candidate["review"]["reviewed_by"], "Codex #35 seed-review")
                self.assertEqual(candidate["review"]["reviewed_at"], "2026-05-30")
                self.assertIn("Approved seed candidate", candidate["review"]["notes"])

    def test_status_and_source_evidence_is_complete(self) -> None:
        for object_id, expected_status in EXPECTED_STATUS_BY_ID.items():
            candidate = self.by_id[object_id]
            notes = candidate["review"]["notes"]
            with self.subTest(object_id=object_id):
                self.assertEqual(candidate["operational_status"], expected_status)
                self.assertEqual(candidate["status_checked_at"], "2026-05-30")
                self.assertTrue(candidate["status_source_url"].startswith("https://"))
                self.assertIn(f"transport_type_id={candidate['transport_type_id']}", notes)
                self.assertIn("coordinates checked", notes)
                self.assertIn(f"operational_status={expected_status}", notes)
                self.assertIn("status_checked_at and status_source_url present", notes)

        self.assertNotEqual(self.by_id["prague-petrin-funicular"]["operational_status"], "active")
        self.assertIn(
            "Petřín нельзя показывать как `active`",
            self.report_text,
        )

    def test_seasonal_and_mountain_unknown_statuses_are_explicit(self) -> None:
        for object_id in [
            "grenoble-bastille-cable-car",
            "como-brunate-funicular",
            "stary-smokovec-hrebienok-funicular",
            "zakopane-kasprowy-wierch-cable-car",
        ]:
            notes = self.by_id[object_id]["review"]["notes"].lower()
            with self.subTest(object_id=object_id):
                self.assertEqual(self.by_id[object_id]["operational_status"], "unknown")
                self.assertTrue(
                    any(marker in notes for marker in ["seasonal", "mountain", "timetable", "weather"]),
                    notes,
                )

    def test_duplicate_audit_covers_slug_osm_wikidata_and_name(self) -> None:
        slugs = set()
        wikidata_ids = set()

        for object_id, candidate in self.by_id.items():
            notes = candidate["review"]["notes"]
            source_ids = candidate["source_ids"]
            with self.subTest(object_id=object_id):
                self.assertNotIn(object_id, slugs)
                slugs.add(object_id)
                self.assertIn("Duplicate audit", notes)
                self.assertIn("slug=unique", notes)
                self.assertIn("OSM id=", notes)
                self.assertIn("line/station name=", notes)

                if "osm" in source_ids:
                    osm_values = source_ids["osm"]
                    if isinstance(osm_values, str):
                        osm_values = [osm_values]
                    for osm_id in osm_values:
                        self.assertIn(osm_id, notes)
                else:
                    self.assertIn("OSM id=not_provided/not_required_for_seed", notes)

                wikidata_id = source_ids["wikidata"]
                self.assertEqual(wikidata_id, EXPECTED_WIKIDATA_BY_ID[object_id])
                self.assertNotIn(wikidata_id, wikidata_ids)
                wikidata_ids.add(wikidata_id)
                self.assertIn(f"Wikidata id={wikidata_id} unique", notes)

    def test_report_records_approved_seed_review(self) -> None:
        for expected in [
            "Seed review 2026-05-30",
            "все 6 staging-кандидатов",
            "`review.state = \"approved\"`",
            "Duplicate audit",
            "`not_provided/not_required_for_seed`",
        ]:
            self.assertIn(expected, self.report_text)

        for object_id in EXPECTED_STATUS_BY_ID:
            self.assertIn(f"`{object_id}`", self.report_text)

    def test_report_declares_review_scope_does_not_change_runtime_or_release_files(self) -> None:
        for expected in [
            "без изменения UI",
            "release-файлов",
            "`VERSION`",
            "SQLite seed",
            "runtime-сцен",
            "`examples/staging/europe_catalog_candidates.json`",
        ]:
            self.assertIn(expected, self.report_text)


if __name__ == "__main__":
    unittest.main()
