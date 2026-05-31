from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "europe-expansion-plan.md"
BACKLOG = ROOT / "docs" / "active-map-backlog.md"
DIRECTION = ROOT / "docs" / "map-production-direction.md"


class EuropeExpansionPlanContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = PLAN.read_text(encoding="utf-8")
        cls.backlog = BACKLOG.read_text(encoding="utf-8")
        cls.direction = DIRECTION.read_text(encoding="utf-8")

    def test_document_exists_and_is_russian_contract(self) -> None:
        self.assertTrue(PLAN.is_file())
        cyrillic_letters = len(re.findall(r"[А-Яа-яЁё]", self.text))
        self.assertGreater(cyrillic_letters, 200)

    def test_required_sub_blocks_are_named(self) -> None:
        for expected in [
            "Switzerland",
            "Austria",
            "Northern Italy",
            "Alpine Relief Source And Elevation Validation",
            "City Landmark Coverage",
            "Cableway And Funicular Object Candidate Data",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.text)

    def test_required_city_landmarks_are_covered(self) -> None:
        for city in [
            "Zürich",
            "Bern",
            "Geneva",
            "Vienna",
            "Innsbruck",
            "Salzburg",
            "Milan",
            "Turin",
            "Venice",
            "Verona",
            "Bolzano",
        ]:
            with self.subTest(city=city):
                self.assertIn(city, self.text)

    def test_real_elevation_source_strategy_is_explicit(self) -> None:
        for expected in [
            "Copernicus DEM GLO-30",
            "EU-DEM",
            "NASA SRTM 1 arc-second",
            "Natural Earth terrain",
            "random decorative",
            "Po Valley",
            "Vienna Basin",
            "German Alpine edge",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.text)

    def test_candidate_transport_contract_is_explicit(self) -> None:
        for expected in [
            "Zürich Polybahn",
            "Innsbruck Hungerburgbahn",
            "Salzburg Festungsbahn",
            "Bergamo funiculars",
            "Como-Brunate funicular",
            "Bolzano/Renon",
            "`cable_gondola`",
            "`funicular_classic`",
            "`rail_cog`",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.text)

    def test_acceptance_and_reviewer_evidence_are_defined(self) -> None:
        for expected in [
            "Acceptance Checks",
            "Reviewer Evidence",
            "contract test",
            "No render assets are changed",
            "Source notes",
            "screenshots",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.text)

    def test_plan_is_linked_from_backlog_and_direction(self) -> None:
        for document in [self.backlog, self.direction]:
            with self.subTest(document=document[:40]):
                self.assertIn("docs/europe-expansion-plan.md", document)
                self.assertIn("#75", document)


if __name__ == "__main__":
    unittest.main()
