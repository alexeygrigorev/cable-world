from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "demo_catalog_europe.gd"
STAGING_PATH = ROOT / "examples" / "staging" / "europe_catalog_candidates.json"


EXPECTED_BY_ID = {
    "braga-bom-jesus-funicular": {
        "country": "Португалия",
        "latitude": "41.5547",
        "longitude": "-8.3778",
        "status": "unknown",
    },
    "grenoble-bastille-cable-car": {
        "country": "Франция",
        "latitude": "45.1939",
        "longitude": "5.7265",
        "status": "unknown",
    },
    "como-brunate-funicular": {
        "country": "Италия",
        "latitude": "45.8148",
        "longitude": "9.0835",
        "status": "unknown",
    },
    "prague-petrin-funicular": {
        "country": "Чехия",
        "latitude": "50.0838",
        "longitude": "14.4039",
        "status": "temporarily_closed_planned",
    },
    "stary-smokovec-hrebienok-funicular": {
        "country": "Словакия",
        "latitude": "49.1419",
        "longitude": "20.2224",
        "status": "unknown",
    },
    "zakopane-kasprowy-wierch-cable-car": {
        "country": "Польша",
        "latitude": "49.232",
        "longitude": "19.981",
        "status": "unknown",
    },
}

REQUIRED_FIELDS = [
    "id",
    "name",
    "kind",
    "region",
    "coordinates",
    "description",
    "visited",
    "visit_status_id",
    "notes",
    "transport_type_id",
    "country",
    "city",
    "latitude",
    "longitude",
    "opened_year",
    "operator",
    "manufacturer",
]


class DemoCatalogEuropeContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.script_text = SCRIPT_PATH.read_text(encoding="utf-8")
        self.staging_text = STAGING_PATH.read_text(encoding="utf-8")

    def test_module_declares_standalone_europe_catalog_class(self) -> None:
        for expected in [
            "extends RefCounted",
            "class_name DemoCatalogEurope",
            "static func get_objects() -> Array[Dictionary]:",
            "static func get_operational_status_by_id() -> Dictionary:",
            "const OPERATIONAL_STATUS_BY_ID := {",
        ]:
            self.assertIn(expected, self.script_text)

    def test_promotes_all_six_staging_candidates_with_stable_ascii_ids(self) -> None:
        object_ids = re.findall(r'"id": "([^"]+)"', self.script_text)

        self.assertEqual(sorted(EXPECTED_BY_ID), sorted(object_ids))
        self.assertEqual(len(object_ids), 6)

        for object_id in object_ids:
            self.assertRegex(object_id, r"^[a-z0-9-]+$")
            self.assertIn(f'"id": "{object_id}"', self.staging_text)

    def test_objects_keep_demo_catalog_compatible_fields(self) -> None:
        object_blocks = self._object_blocks()
        self.assertEqual(len(object_blocks), 6)

        for object_id, block in object_blocks.items():
            with self.subTest(object_id=object_id):
                for field in REQUIRED_FIELDS:
                    self.assertIn(f'"{field}":', block)
                self.assertIn('"visited": false', block)
                self.assertIn('"visit_status_id": "not_visited"', block)

    def test_countries_and_coordinates_use_vector2_longitude_latitude(self) -> None:
        object_blocks = self._object_blocks()

        countries = set()
        for object_id, expected in EXPECTED_BY_ID.items():
            block = object_blocks[object_id]
            countries.add(expected["country"])

            self.assertIn(f'"country": "{expected["country"]}"', block)
            self.assertIn(f'"latitude": {expected["latitude"]}', block)
            self.assertIn(f'"longitude": {expected["longitude"]}', block)
            self.assertIn(
                f'Vector2({expected["longitude"]}, {expected["latitude"]})',
                block,
            )

        self.assertEqual(
            countries,
            {"Португалия", "Франция", "Италия", "Чехия", "Словакия", "Польша"},
        )

    def test_user_facing_strings_are_russian(self) -> None:
        object_blocks = self._object_blocks()

        for object_id, block in object_blocks.items():
            with self.subTest(object_id=object_id):
                for field in ["name", "kind", "region", "description", "notes", "country", "city"]:
                    match = re.search(rf'"{field}": "([^"]+)"', block)
                    self.assertIsNotNone(match, f"missing field {field}")
                    self.assertRegex(match.group(1), r"[А-Яа-яЁё]")

    def test_operational_statuses_are_preserved_separately(self) -> None:
        status_block = self.script_text.split("const OPERATIONAL_STATUS_BY_ID := {", 1)[1].split(
            "static func get_operational_status_by_id",
            1,
        )[0]

        for object_id, expected in EXPECTED_BY_ID.items():
            with self.subTest(object_id=object_id):
                self.assertIn(f'"{object_id}": {{', status_block)
                object_status_block = status_block.split(f'"{object_id}": {{', 1)[1].split("\n\t},", 1)[0]
                self.assertIn(f'"operational_status": "{expected["status"]}"', object_status_block)
                self.assertIn('"status_checked_at": "2026-05-30"', object_status_block)
                self.assertIn('"status_source_url": "https://', object_status_block)
                self.assertIn('"status_note": "', object_status_block)

        self.assertIn('"operational_status": "temporarily_closed_planned"', status_block)

    def test_europe_seed_is_connected_to_main_demo_catalog(self) -> None:
        main_catalog_text = (ROOT / "scripts" / "demo_catalog.gd").read_text(encoding="utf-8")
        main_screen_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        self.assertIn('preload("res://scripts/demo_catalog_europe.gd")', main_catalog_text)
        self.assertIn("DemoCatalogEuropeScript.get_objects()", main_catalog_text)
        self.assertIn("DemoCatalogEuropeScript.get_operational_status_by_id()", main_catalog_text)
        self.assertNotIn("DemoCatalogEurope", main_screen_text)
        self.assertNotIn("demo_catalog_europe.gd", scene_text)

    def _object_blocks(self) -> dict[str, str]:
        blocks: dict[str, str] = {}

        for object_id in EXPECTED_BY_ID:
            marker = f'"id": "{object_id}"'
            self.assertIn(marker, self.script_text)
            block_start = self.script_text.rfind("\n\t\t{", 0, self.script_text.index(marker))
            block_end = self.script_text.index("\n\t\t}", self.script_text.index(marker))
            blocks[object_id] = self.script_text[block_start:block_end]

        return blocks


if __name__ == "__main__":
    unittest.main()
