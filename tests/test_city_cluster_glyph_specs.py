import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPECS_PATH = ROOT / "map_pipeline" / "data" / "city_cluster_glyph_specs.json"
MAP_PANEL_PATH = ROOT / "scripts" / "map_panel.gd"


def _map_panel_city_labels() -> dict[str, str]:
    script_text = MAP_PANEL_PATH.read_text(encoding="utf-8")
    block = script_text.split("const CITY_LABELS := [", 1)[1].split("]", 1)[0]
    labels: dict[str, str] = {}
    for entry in re.findall(r'\{"name": "[^"]+"[^}]+\}', block):
        name = re.search(r'"name": "([^"]+)"', entry).group(1)
        icon_match = re.search(r'"icon": "([^"]*)"', entry)
        labels[name] = icon_match.group(1) if icon_match else ""
    return labels


def _asset_cluster_ids() -> set[str]:
    cluster_dir = ROOT / "assets" / "sprites" / "city_landmark_clusters_hi_res"
    return {path.stem.removeprefix("city_") for path in cluster_dir.glob("city_*.png")}


class CityClusterGlyphSpecsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs = json.loads(SPECS_PATH.read_text(encoding="utf-8"))

    def test_specs_cover_every_current_map_panel_city_label(self) -> None:
        labels = _map_panel_city_labels()
        spec_names = {city["map_panel_name"] for city in self.specs["cities"] if city["map_panel_name"]}

        self.assertGreaterEqual(len(labels), 20)
        self.assertLessEqual(set(labels), spec_names)

    def test_specs_are_exactly_runtime_cluster_assets(self) -> None:
        labels = _map_panel_city_labels()
        asset_ids = _asset_cluster_ids()
        planned = {city["id"] for city in self.specs["cities"] if city["status"] == "planned_cluster"}
        existing = {city["id"] for city in self.specs["cities"] if city["status"] == "existing_cluster"}

        self.assertEqual(asset_ids, existing)
        self.assertLessEqual(set(labels.values()), existing)
        self.assertEqual(set(), planned & asset_ids)
        for icon_id in existing:
            with self.subTest(icon_id=icon_id):
                self.assertTrue((ROOT / "assets" / "sprites" / "city_landmark_clusters_hi_res" / f"city_{icon_id}.png").exists())
                self.assertTrue((ROOT / "assets" / "sprites" / "city_landmark_clusters_hi_res" / "outlined" / f"city_{icon_id}.png").exists())

    def test_each_cluster_has_reviewable_prompt_spec(self) -> None:
        for city in self.specs["cities"]:
            with self.subTest(city=city["id"]):
                self.assertIn(city["status"], {"existing_cluster", "planned_cluster"})
                self.assertGreaterEqual(len(city["cluster_elements"]), 2)
                self.assertLessEqual(len(city["cluster_elements"]), 4)
                self.assertIn("cluster", city["prompt_spec"].lower())
                self.assertNotIn("one-symbol-only", city["prompt_spec"].lower())

    def test_pipeline_commands_support_specs_file_for_expansion_review(self) -> None:
        slicer_text = (ROOT / "map_pipeline" / "slice_city_cluster_landmarks_hi_res.py").read_text(encoding="utf-8")
        review_text = (ROOT / "map_pipeline" / "build_city_cluster_hi_res_review.py").read_text(encoding="utf-8")
        docs_text = (ROOT / "docs" / "pipelines" / "city-glyphs.md").read_text(encoding="utf-8")

        for expected in [
            "--specs-file",
            "--status",
            "planned_cluster",
            "city_ids(load_specs",
        ]:
            self.assertIn(expected, slicer_text)
            self.assertIn(expected, review_text)

        for expected in [
            "assets/sprites/city_landmark_clusters_hi_res",
            "--ids hannover,bremen,kiel",
            "Removed Legacy Process",
            "Do not use or reintroduce",
        ]:
            self.assertIn(expected, docs_text)


if __name__ == "__main__":
    unittest.main()
