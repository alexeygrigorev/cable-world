from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "demo_catalog_russia.gd"
LEGACY_MODULE = ROOT / "scripts" / "demo_catalog.gd"
STAGING = ROOT / "examples" / "staging" / "research" / "russia_catalog_candidates.json"

REQUIRED_FIELDS = {
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
}

REQUIRED_IDS = {
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


def _extract_object_blocks(source: str) -> list[str]:
    start_marker = "var objects: Array[Dictionary] = ["
    start = source.index(start_marker) + len(start_marker)
    end = source.index("\n\t]\n\treturn objects", start)
    body = source[start:end]
    return re.findall(r"\n\t\t\{.*?\n\t\t\}", body, flags=re.S)


def _extract_string(block: str, key: str) -> str:
    match = re.search(rf'"{key}": "([^"]*)"', block)
    if not match:
        return ""
    return match.group(1)


def _extract_float(block: str, key: str) -> float:
    match = re.search(rf'"{key}": ([0-9]+\.[0-9]+)', block)
    if not match:
        raise AssertionError(f"Не найдено числовое поле {key}")
    return float(match.group(1))


def _extract_vector2(block: str) -> tuple[float, float]:
    match = re.search(r'"coordinates": Vector2\(([0-9]+\.[0-9]+), ([0-9]+\.[0-9]+)\)', block)
    if not match:
        raise AssertionError("coordinates должны быть Vector2(longitude, latitude)")
    return float(match.group(1)), float(match.group(2))


def _has_cyrillic(value: str) -> bool:
    return any("а" <= char.lower() <= "я" or char in "Ёё" for char in value)


class DemoCatalogRussiaContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = MODULE.read_text(encoding="utf-8")
        cls.legacy_source = LEGACY_MODULE.read_text(encoding="utf-8")
        cls.staging = json.loads(STAGING.read_text(encoding="utf-8"))["candidates"]
        cls.blocks = _extract_object_blocks(cls.source)
        cls.ids = [_extract_string(block, "id") for block in cls.blocks]

    def test_module_is_standalone_and_connected_through_demo_catalog(self) -> None:
        self.assertIn("class_name DemoCatalogRussia", self.source)
        self.assertIn("static func get_objects() -> Array[Dictionary]", self.source)
        self.assertIn("static func get_operational_status_by_id() -> Dictionary", self.source)
        self.assertNotIn("DemoCatalog.", self.source)
        self.assertNotIn('preload("res://scripts/demo_catalog.gd")', self.source)
        self.assertIn('preload("res://scripts/demo_catalog_russia.gd")', self.legacy_source)
        self.assertIn("DemoCatalogRussiaScript.get_objects()", self.legacy_source)
        self.assertIn("DemoCatalogRussiaScript.get_operational_status_by_id()", self.legacy_source)

    def test_promotes_all_russia_staging_candidates_with_staging_ids(self) -> None:
        staging_ids = {candidate["id"] for candidate in self.staging}
        self.assertGreaterEqual(len(self.blocks), 6)
        self.assertEqual(set(self.ids), REQUIRED_IDS)
        self.assertEqual(set(self.ids), staging_ids)

        legacy_ids = {
            "vorobyovy-gory",
            "nizhny-novgorod",
        }
        self.assertTrue(legacy_ids.isdisjoint(self.ids))

    def test_objects_have_demo_catalog_compatible_fields_and_russian_strings(self) -> None:
        for block in self.blocks:
            with self.subTest(object_id=_extract_string(block, "id")):
                for field in REQUIRED_FIELDS:
                    self.assertIn(f'"{field}"', block)

                self.assertRegex(_extract_string(block, "id"), r"^[a-z][a-z0-9-]*$")
                self.assertEqual(_extract_string(block, "country"), "Россия")
                self.assertEqual(_extract_string(block, "visit_status_id"), "not_visited")
                self.assertIn('"visited": false', block)

                for key in ["name", "kind", "region", "description", "notes", "city"]:
                    self.assertTrue(_has_cyrillic(_extract_string(block, key)), key)

    def test_types_and_operational_statuses_are_preserved(self) -> None:
        types = {_extract_string(block, "transport_type_id") for block in self.blocks}
        self.assertTrue(REQUIRED_TYPES.issubset(types))

        for candidate in self.staging:
            object_id = candidate["id"]
            with self.subTest(object_id=object_id):
                self.assertIn(f'"{object_id}": {{', self.source)
                self.assertIn(f'"operational_status": "{candidate["operational_status"]}"', self.source)
                self.assertIn(f'"status_checked_at": "{candidate["status_checked_at"]}"', self.source)
                self.assertIn(f'"status_source_url": "{candidate["status_source_url"]}"', self.source)
                self.assertIn('"status_note": "', self.source)

        self.assertIn('"operational_status": "historical"', self.source)

    def test_coordinates_use_vector2_longitude_latitude_order(self) -> None:
        staging_by_id = {candidate["id"]: candidate for candidate in self.staging}

        for block in self.blocks:
            object_id = _extract_string(block, "id")
            candidate = staging_by_id[object_id]
            longitude, latitude = _extract_vector2(block)

            self.assertAlmostEqual(longitude, candidate["longitude"], places=4)
            self.assertAlmostEqual(latitude, candidate["latitude"], places=4)
            self.assertAlmostEqual(_extract_float(block, "longitude"), longitude, places=4)
            self.assertAlmostEqual(_extract_float(block, "latitude"), latitude, places=4)


if __name__ == "__main__":
    unittest.main()
