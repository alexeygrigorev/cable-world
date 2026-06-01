from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "map_pipeline" / "data" / "france_spain_map_block.json"


class FranceSpainMapBlockContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.region_by_id = {region["id"]: region for region in cls.contract["regions"]}
        cls.relief_by_id = {layer["id"]: layer for layer in cls.contract["relief_layers"]}
        cls.city_by_id = {city["id"]: city for city in cls.contract["city_landmarks"]}

    def test_contract_is_non_render_scope_for_issue_76(self) -> None:
        self.assertEqual(self.contract["schema"], "cable-world.france-spain-map-block.v1")
        self.assertEqual(self.contract["issue"], "#76")
        self.assertEqual(self.contract["parent_issue"], "#63")
        self.assertEqual(self.contract["scope"], "non_render_france_spain_metadata")
        self.assertEqual(self.contract["review_status"], "planning_contract")
        for forbidden in [
            "map images/assets",
            "rendered underlay changes",
            "terrain glyph art",
            "runtime UI",
            "release files",
        ]:
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, self.contract["acceptance_contract"]["forbidden_outputs"])

    def test_regions_cover_france_spain_and_required_context(self) -> None:
        self.assertIn("france_mainland", self.region_by_id)
        self.assertIn("spain_mainland_balearic_context", self.region_by_id)
        france = self.region_by_id["france_mainland"]
        spain = self.region_by_id["spain_mainland_balearic_context"]
        self.assertEqual(france["detail_tier"], "high")
        self.assertEqual(spain["detail_tier"], "high")
        self.assertGreaterEqual(set(france["countries"]), {"France", "Monaco"})
        self.assertGreaterEqual(set(spain["countries"]), {"Spain", "Andorra"})
        self.assertIn("corsica_mountains", france["required_relief_layers"])
        self.assertIn("balearic_islands_context", spain["required_water_context"])
        for region in [france, spain]:
            with self.subTest(region=region["id"]):
                min_lon, min_lat, max_lon, max_lat = region["bounds"]
                self.assertLess(min_lon, max_lon)
                self.assertLess(min_lat, max_lat)
                self.assertEqual(region["review_status"], "planned")

    def test_required_relief_layers_are_source_backed_and_geographically_linked(self) -> None:
        expected_layers = {
            "western_alps_france",
            "pyrenees_france",
            "pyrenees_spain_andorra",
            "massif_central",
            "vosges_jura",
            "cantabrian_mountains",
            "central_system",
            "iberian_system",
            "sierra_nevada",
            "corsica_mountains",
            "balearic_context",
        }
        self.assertGreaterEqual(set(self.relief_by_id), expected_layers)
        for layer_id in expected_layers:
            with self.subTest(layer=layer_id):
                layer = self.relief_by_id[layer_id]
                self.assertIn("DEM", layer["source_rule"])
                self.assertTrue(layer["lowland_exclusions"])
                self.assertEqual(layer["review_status"], "planned")
                min_lon, min_lat, max_lon, max_lat = layer["bounds"]
                self.assertLess(min_lon, max_lon)
                self.assertLess(min_lat, max_lat)

        self.assertIn("alps_cross_border", self.relief_by_id["western_alps_france"]["continuity_refs"])
        self.assertIn("pyrenees_spain_andorra", self.relief_by_id["pyrenees_france"]["continuity_refs"])
        self.assertIn("pyrenees_france", self.relief_by_id["pyrenees_spain_andorra"]["continuity_refs"])
        self.assertIn("Ebro Basin", self.relief_by_id["pyrenees_spain_andorra"]["lowland_exclusions"])
        self.assertIn("Aquitaine Basin", self.relief_by_id["pyrenees_france"]["lowland_exclusions"])

    def test_city_landmarks_include_major_and_cableway_anchor_cities(self) -> None:
        required = {
            "paris": ("France", "major"),
            "lyon": ("France", "major"),
            "marseille": ("France", "major"),
            "grenoble": ("France", "cableway_anchor"),
            "chamonix": ("France", "cableway_anchor"),
            "madrid": ("Spain", "major"),
            "barcelona": ("Spain", "major"),
            "valencia": ("Spain", "major"),
            "seville": ("Spain", "major"),
            "bilbao": ("Spain", "cableway_anchor"),
            "granada": ("Spain", "cableway_anchor"),
        }
        for city_id, (country, priority) in required.items():
            with self.subTest(city=city_id):
                self.assertIn(city_id, self.city_by_id)
                city = self.city_by_id[city_id]
                self.assertEqual(city["country"], country)
                self.assertEqual(city["priority"], priority)
                self.assertIsInstance(city["lon"], float)
                self.assertIsInstance(city["lat"], float)
                self.assertIn("landmark_icon_id", city)
                self.assertEqual(city["review_status"], "planned")

        self.assertEqual(self.city_by_id["paris"]["landmark_icon_id"], "city_paris")
        self.assertEqual(self.city_by_id["madrid"]["landmark_icon_id"], "city_madrid")
        self.assertEqual(self.city_by_id["barcelona"]["landmark_icon_id"], "city_barcelona")

    def test_transport_candidate_buckets_are_staging_only_and_type_complete(self) -> None:
        buckets = {bucket["id"]: bucket for bucket in self.contract["transport_candidate_buckets"]}
        self.assertIn("france_urban_and_mountain", buckets)
        self.assertIn("spain_urban_and_mountain", buckets)
        for bucket in buckets.values():
            with self.subTest(bucket=bucket["id"]):
                self.assertEqual(bucket["production_policy"], "staging_review_only")
                self.assertTrue(bucket["required_candidate_anchors"])
                self.assertIn("funicular_classic", bucket["required_transport_types"])
        self.assertIn("Grenoble-Bastille cable car", buckets["france_urban_and_mountain"]["required_candidate_anchors"])
        self.assertIn("Bilbao Artxanda funicular", buckets["spain_urban_and_mountain"]["required_candidate_anchors"])
        self.assertIn("cable_urban", buckets["spain_urban_and_mountain"]["required_transport_types"])

    def test_source_requirements_keep_real_geography_before_art(self) -> None:
        sources = self.contract["source_requirements"]
        self.assertIn("Copernicus DEM GLO-30", sources["relief"])
        self.assertIn("EU-DEM", sources["relief"])
        self.assertIn("NASA SRTM 1 Arc-Second Global", sources["relief"])
        for required in ["source_url", "license_note", "download_date", "processing_command", "review_status"]:
            with self.subTest(required=required):
                self.assertIn(required, sources["required_metadata"])


if __name__ == "__main__":
    unittest.main()
