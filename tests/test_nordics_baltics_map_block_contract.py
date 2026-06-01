from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "map_pipeline" / "data" / "nordics_baltics_map_block.json"


class NordicsBalticsMapBlockContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.region_by_id = {region["id"]: region for region in cls.contract["regions"]}
        cls.relief_by_id = {layer["id"]: layer for layer in cls.contract["relief_layers"]}
        cls.water_by_id = {entry["id"]: entry for entry in cls.contract["water_and_islands"]}
        cls.city_by_id = {city["id"]: city for city in cls.contract["city_landmarks"]}

    def test_contract_is_non_render_scope_for_issue_77(self) -> None:
        self.assertEqual(self.contract["schema"], "cable-world.nordics-baltics-map-block.v1")
        self.assertEqual(self.contract["issue"], "#77")
        self.assertEqual(self.contract["parent_issue"], "#63")
        self.assertEqual(self.contract["scope"], "non_render_nordics_baltics_metadata")
        self.assertEqual(self.contract["review_status"], "planning_contract")
        self.assertIn("Northern latitude is not a relief rule", " ".join(self.contract["notes"]))
        for forbidden in [
            "map images/assets",
            "rendered underlay changes",
            "terrain glyph art",
            "runtime UI",
            "release files",
        ]:
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, self.contract["acceptance_contract"]["forbidden_outputs"])

    def test_regions_cover_nordics_finland_baltics_and_island_context(self) -> None:
        expected = {
            "scandinavia_mountain_core": {"Norway", "Sweden"},
            "denmark_north_sea_baltic_connector": {"Denmark"},
            "finland_lakeland_low_relief": {"Finland"},
            "baltics_lowland_coast": {"Estonia", "Latvia", "Lithuania"},
            "iceland_context": {"Iceland"},
        }
        self.assertEqual(set(self.region_by_id), set(expected))
        for region_id, countries in expected.items():
            with self.subTest(region=region_id):
                region = self.region_by_id[region_id]
                self.assertGreaterEqual(set(region["countries"]), countries)
                self.assertEqual(region["detail_tier"], "medium")
                self.assertTrue(region["required_relief_layers"])
                self.assertTrue(region["required_water_island_context"])
                min_lon, min_lat, max_lon, max_lat = region["bounds"]
                self.assertLess(min_lon, max_lon)
                self.assertLess(min_lat, max_lat)
                self.assertEqual(region["review_status"], "planned")

    def test_relief_contract_distinguishes_mountains_from_lowlands(self) -> None:
        mountains = self.relief_by_id["scandinavian_mountains"]
        self.assertGreaterEqual(set(mountains["countries"]), {"Norway", "Sweden"})
        self.assertIn("DEM-derived ridge/elevation bands", mountains["source_rule"])
        self.assertIn("Finnish lowlands", mountains["lowland_exclusions"])
        self.assertIn("Denmark lowlands", mountains["lowland_exclusions"])

        for layer_id in ["denmark_lowland_exclusion", "finland_low_relief_context", "baltic_lowland_exclusion"]:
            with self.subTest(layer=layer_id):
                layer = self.relief_by_id[layer_id]
                self.assertIn("DEM-derived", layer["source_rule"])
                self.assertTrue(layer["lowland_exclusions"])
                self.assertEqual(layer["review_status"], "planned")
                self.assertNotIn("Alpine", layer["source_rule"])

        self.assertIn("do not copy Scandinavian mountain glyphs", self.relief_by_id["finland_low_relief_context"]["source_rule"])
        self.assertIn("no large mountain glyphs", self.relief_by_id["baltic_lowland_exclusion"]["source_rule"])

    def test_water_lakes_coasts_and_islands_are_explicit(self) -> None:
        required = {
            "north_sea",
            "skagerrak",
            "kattegat",
            "baltic_sea",
            "gulf_of_bothnia",
            "norwegian_coast",
            "lofoten_vesteralen",
            "finnish_lakeland",
            "saimaa",
            "paijanne",
            "inari",
            "aland_islands",
            "saaremaa",
            "hiiumaa",
            "curonian_lagoon",
            "curonian_spit",
            "jutland",
            "bornholm",
            "zealand",
            "funen",
            "gulf_of_riga",
            "gulf_of_finland",
            "north_atlantic",
            "iceland_coastline",
            "westfjords",
        }
        self.assertGreaterEqual(set(self.water_by_id), required)
        for water_id in required:
            with self.subTest(water=water_id):
                entry = self.water_by_id[water_id]
                self.assertTrue(entry["countries"])
                self.assertIn("source_rule", entry)
                self.assertEqual(entry["review_status"], "planned")

        self.assertEqual(self.water_by_id["saimaa"]["kind"], "named_lake")
        self.assertEqual(self.water_by_id["curonian_spit"]["kind"], "coastal_spit")

    def test_every_region_water_context_resolves_to_source_backed_entry(self) -> None:
        for region in self.contract["regions"]:
            for water_id in region["required_water_island_context"]:
                with self.subTest(region=region["id"], water=water_id):
                    self.assertIn(water_id, self.water_by_id)
                    entry = self.water_by_id[water_id]
                    self.assertTrue(entry["source_rule"])
                    self.assertEqual(entry["review_status"], "planned")

    def test_city_landmarks_include_capitals_and_cableway_anchors(self) -> None:
        required = {
            "oslo": ("Norway", "major"),
            "bergen": ("Norway", "cableway_anchor"),
            "tromso": ("Norway", "cableway_anchor"),
            "stockholm": ("Sweden", "major"),
            "copenhagen": ("Denmark", "major"),
            "helsinki": ("Finland", "major"),
            "tallinn": ("Estonia", "major"),
            "riga": ("Latvia", "major"),
            "vilnius": ("Lithuania", "major"),
            "reykjavik": ("Iceland", "major"),
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

        self.assertEqual(self.city_by_id["oslo"]["landmark_icon_id"], "city_oslo")
        self.assertEqual(self.city_by_id["stockholm"]["landmark_icon_id"], "city_stockholm")
        self.assertEqual(self.city_by_id["copenhagen"]["landmark_icon_id"], "city_copenhagen")

    def test_transport_candidate_buckets_are_staging_only(self) -> None:
        buckets = {bucket["id"]: bucket for bucket in self.contract["transport_candidate_buckets"]}
        self.assertIn("norway_mountain_and_city_cableways", buckets)
        self.assertIn("sweden_denmark_finland_urban_candidates", buckets)
        self.assertIn("baltics_candidates", buckets)
        for bucket in buckets.values():
            with self.subTest(bucket=bucket["id"]):
                self.assertEqual(bucket["production_policy"], "staging_review_only")
                self.assertTrue(bucket["required_candidate_anchors"])
                self.assertTrue(bucket["required_transport_types"])
        self.assertIn("Bergen Floibanen funicular", buckets["norway_mountain_and_city_cableways"]["required_candidate_anchors"])
        self.assertIn("cable_tourist", buckets["norway_mountain_and_city_cableways"]["required_transport_types"])

    def test_source_requirements_keep_relief_and_water_source_backed(self) -> None:
        sources = self.contract["source_requirements"]
        self.assertIn("Copernicus DEM GLO-30", sources["relief"])
        self.assertIn("EU-DEM", sources["relief"])
        self.assertIn("NASA SRTM 1 Arc-Second Global", sources["relief"])
        self.assertIn("OpenStreetMap coastline/water/island relations for detailed passes", sources["coastline_water"])
        for required in ["source_url", "license_note", "download_date", "processing_command", "review_status"]:
            with self.subTest(required=required):
                self.assertIn(required, sources["required_metadata"])


if __name__ == "__main__":
    unittest.main()
