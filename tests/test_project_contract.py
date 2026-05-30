import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]

MIN_GERMAN_FALLBACK_OBJECTS = 21
EXPECTED_INTEGRATED_DEMO_OBJECTS = 34

REQUIRED_GERMAN_FALLBACK_IDS = {
    "berlin-gaerten-der-welt",
    "thale-hexentanzplatz",
    "thale-rosstrappe",
    "stuttgart-standseilbahn",
    "stuttgart-zahnradbahn",
    "bayerische-zugspitzbahn",
    "seilbahn-zugspitze",
    "zugspitze-gletscherbahn",
    "wuppertaler-schwebebahn",
    "dresden-schwebebahn",
    "dresden-standseilbahn",
    "nerobergbahn",
    "bad-schandau-lift",
    "heidelberg-bergbahn",
    "bad-harzburg-burgbergseilbahn",
    "wurmbergseilbahn",
    "dortmund-h-bahn",
    "duesseldorf-skytrain",
    "baden-baden-merkurbergbahn",
    "koblenz-seilbahn",
    "koeln-seilbahn",
}

REPLACED_LEGACY_RUSSIA_IDS = {
    "vorobyovy-gory",
    "nizhny-novgorod",
    "vladivostok-funicular",
}

REQUIRED_EUROPE_FALLBACK_IDS = {
    "braga-bom-jesus-funicular",
    "grenoble-bastille-cable-car",
    "como-brunate-funicular",
    "prague-petrin-funicular",
    "stary-smokovec-hrebienok-funicular",
    "zakopane-kasprowy-wierch-cable-car",
}

REQUIRED_RUSSIA_FALLBACK_IDS = {
    "nizhny-novgorod-bor-cable-car",
    "moscow-vorobyovy-gory-cable-car",
    "vladivostok-funicular",
    "nizhny-novgorod-kremlin-funicular",
    "pyatigorsk-mashuk-cable-car",
    "svetlogorsk-panorama-elevator",
    "moscow-monorail",
}

REQUIRED_NEW_FALLBACK_COUNTRIES = {
    "Португалия",
    "Франция",
    "Италия",
    "Чехия",
    "Словакия",
    "Польша",
    "Россия",
}


class ProjectContractTest(unittest.TestCase):
    def test_godot_project_points_to_existing_main_scene(self) -> None:
        project_text = (ROOT / "project.godot").read_text(encoding="utf-8")
        match = re.search(r'run/main_scene="res://([^"]+)"', project_text)
        self.assertIsNotNone(match, "В project.godot должна быть главная сцена")
        self.assertTrue((ROOT / match.group(1)).exists(), "Главная сцена должна существовать")

    def test_main_scene_uses_typed_scripts(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")
        scripts = re.findall(r'path="res://(scripts/[^"]+\.gd)"', scene_text)
        self.assertGreaterEqual(len(scripts), 3)
        for script in scripts:
            text = (ROOT / script).read_text(encoding="utf-8")
            self.assertIn("class_name ", text)
            self.assertRegex(text, r"(var|const|func|signal) .+:", f"{script} должен использовать типизацию")

    def test_demo_catalog_contains_mvp_fields(self) -> None:
        text = (ROOT / "scripts" / "demo_catalog.gd").read_text(encoding="utf-8")
        for field in ["id", "name", "kind", "region", "coordinates", "description", "visited", "notes"]:
            self.assertIn(f'"{field}"', text)

    def test_demo_catalog_contains_german_fallback_objects(self) -> None:
        text = (ROOT / "scripts" / "demo_catalog.gd").read_text(encoding="utf-8")
        object_ids = set(re.findall(r'"id": "([^"]+)"', text))
        german_object_count = text.count('"country": "Германия"')

        self.assertGreaterEqual(german_object_count, MIN_GERMAN_FALLBACK_OBJECTS)
        self.assertIn('"transport_type_id": "rail_cog"', text)
        self.assertIn('"transport_type_id": "rail_suspended"', text)
        self.assertIn('"transport_type_id": "funicular_water"', text)

        for object_id in REQUIRED_GERMAN_FALLBACK_IDS:
            with self.subTest(object_id=object_id):
                self.assertIn(object_id, object_ids)

    def test_demo_catalog_integrates_europe_and_russia_seed_modules(self) -> None:
        text = (ROOT / "scripts" / "demo_catalog.gd").read_text(encoding="utf-8")

        for expected in [
            'preload("res://scripts/demo_catalog_europe.gd")',
            'preload("res://scripts/demo_catalog_russia.gd")',
            "DemoCatalogEuropeScript.get_objects()",
            "DemoCatalogRussiaScript.get_objects()",
            "DemoCatalogEuropeScript.get_operational_status_by_id()",
            "DemoCatalogRussiaScript.get_operational_status_by_id()",
            "LEGACY_OBJECT_IDS_REPLACED_BY_STAGING",
            "_without_replaced_legacy_objects(objects)",
            "_append_seed_objects(objects, DemoCatalogEuropeScript.get_objects())",
            "_append_seed_objects(objects, DemoCatalogRussiaScript.get_objects())",
        ]:
            self.assertIn(expected, text)

    def test_integrated_demo_catalog_has_expected_seed_shape_without_russia_duplicates(self) -> None:
        legacy_text = (ROOT / "scripts" / "demo_catalog.gd").read_text(encoding="utf-8")
        europe_text = (ROOT / "scripts" / "demo_catalog_europe.gd").read_text(encoding="utf-8")
        russia_text = (ROOT / "scripts" / "demo_catalog_russia.gd").read_text(encoding="utf-8")

        legacy_ids = _object_ids(legacy_text) - REPLACED_LEGACY_RUSSIA_IDS
        europe_ids = _object_ids(europe_text)
        russia_ids = _object_ids(russia_text)
        integrated_ids = legacy_ids | europe_ids | russia_ids

        self.assertEqual(len(integrated_ids), EXPECTED_INTEGRATED_DEMO_OBJECTS)
        self.assertTrue(REQUIRED_GERMAN_FALLBACK_IDS.issubset(integrated_ids))
        self.assertEqual(europe_ids, REQUIRED_EUROPE_FALLBACK_IDS)
        self.assertEqual(russia_ids, REQUIRED_RUSSIA_FALLBACK_IDS)
        self.assertTrue(REPLACED_LEGACY_RUSSIA_IDS.isdisjoint(integrated_ids - russia_ids))

        integrated_titles = _integrated_demo_titles_without_replaced_legacy()
        duplicate_titles = sorted(
            title
            for title in set(integrated_titles)
            if integrated_titles.count(title) > 1
        )
        self.assertEqual(duplicate_titles, [])

    def test_demo_catalog_preserves_seed_operational_statuses(self) -> None:
        text = (ROOT / "scripts" / "demo_catalog.gd").read_text(encoding="utf-8")
        europe_text = (ROOT / "scripts" / "demo_catalog_europe.gd").read_text(encoding="utf-8")
        russia_text = (ROOT / "scripts" / "demo_catalog_russia.gd").read_text(encoding="utf-8")

        self.assertIn("var status_by_id := OPERATIONAL_STATUS_BY_ID.duplicate(true)", text)
        self.assertIn("status_by_id[object_id] =", text)
        self.assertIn('"operational_status": "temporarily_closed_planned"', europe_text)
        self.assertIn('"operational_status": "historical"', russia_text)

    def test_demo_catalog_countries_cover_new_filters(self) -> None:
        europe_text = (ROOT / "scripts" / "demo_catalog_europe.gd").read_text(encoding="utf-8")
        russia_text = (ROOT / "scripts" / "demo_catalog_russia.gd").read_text(encoding="utf-8")
        countries = set(re.findall(r'"country": "([^"]+)"', europe_text + russia_text))

        self.assertTrue(REQUIRED_NEW_FALLBACK_COUNTRIES.issubset(countries))

    def test_user_facing_docs_are_russian(self) -> None:
        for relative_path in ["README.md", "process.md", "agents.md", "docs/architecture.md"]:
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            cyrillic_letters = len(re.findall(r"[А-Яа-яЁё]", text))
            latin_letters = len(re.findall(r"[A-Za-z]", text))
            self.assertGreater(cyrillic_letters, latin_letters, f"{relative_path} должен быть преимущественно на русском")


def _integrated_demo_titles_without_replaced_legacy() -> list[str]:
    titles: list[str] = []
    for relative_path in [
        "scripts/demo_catalog.gd",
        "scripts/demo_catalog_europe.gd",
        "scripts/demo_catalog_russia.gd",
    ]:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for block in _object_blocks(text):
            object_id_match = re.search(r'"id": "([^"]+)"', block)
            title_match = re.search(r'"name": "([^"]+)"', block)
            if object_id_match is None or title_match is None:
                continue
            if relative_path == "scripts/demo_catalog.gd" and object_id_match.group(1) in REPLACED_LEGACY_RUSSIA_IDS:
                continue
            titles.append(title_match.group(1))
    return titles


def _object_ids(source: str) -> set[str]:
    return {
        match.group(1)
        for block in _object_blocks(source)
        if (match := re.search(r'"id": "([^"]+)"', block)) is not None
    }


def _object_blocks(source: str) -> list[str]:
    return [
        block
        for block in re.findall(r"\n\t\t\{.*?\n\t\t\}", source, flags=re.S)
        if '"name":' in block
    ]


if __name__ == "__main__":
    unittest.main()
