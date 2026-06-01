from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "map_pipeline" / "data" / "eastern_europe_turkey_map_block.json"


class EasternEuropeTurkeyMapBlockContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.region_by_id = {region["id"]: region for region in cls.contract["regions"]}
        cls.relief_by_id = {layer["id"]: layer for layer in cls.contract["relief_layers"]}
        cls.water_by_id = {entry["id"]: entry for entry in cls.contract["water_and_islands"]}
        cls.city_by_id = {city["id"]: city for city in cls.contract["city_landmarks"]}

    def test_contract_is_non_render_scope_for_issue_74(self) -> None:
        self.assertEqual(self.contract["schema"], "cable-world.eastern-europe-turkey-map-block.v1")
        self.assertEqual(self.contract["issue"], "#74")
        self.assertEqual(self.contract["parent_issue"], "#63")
        self.assertEqual(self.contract["scope"], "non_render_eastern_europe_turkey_metadata")
        self.assertEqual(self.contract["review_status"], "planning_contract")
        self.assertIn("Ukrainian mountain cutoff", " ".join(self.contract["notes"]))
        for forbidden in [
            "map images/assets",
            "rendered underlay changes",
            "terrain glyph art",
            "runtime UI",
            "release files",
        ]:
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, self.contract["acceptance_contract"]["forbidden_outputs"])

    def test_regions_cover_eastern_europe_balkans_russia_and_turkey(self) -> None:
        expected = {
            "central_eastern_neighbors": {"Poland", "Czechia", "Slovakia", "Hungary"},
            "romania_balkans": {"Romania", "Bulgaria", "Serbia", "Croatia", "Bosnia and Herzegovina", "Slovenia", "North Macedonia", "Albania"},
            "belarus_ukraine_mountain_cutoff": {"Belarus", "Ukraine", "Moldova"},
            "western_russia_context": {"Russia"},
            "turkey_bridge_region": {"Turkey"},
        }
        self.assertEqual(set(self.region_by_id), set(expected))
        self.assertEqual(self.region_by_id["central_eastern_neighbors"]["detail_tier"], "high")
        self.assertEqual(self.region_by_id["western_russia_context"]["detail_tier"], "low")
        self.assertEqual(self.region_by_id["turkey_bridge_region"]["detail_tier"], "medium")
        for region_id, countries in expected.items():
            with self.subTest(region=region_id):
                region = self.region_by_id[region_id]
                self.assertGreaterEqual(set(region["countries"]), countries)
                self.assertTrue(region["required_relief_layers"])
                self.assertTrue(region["required_water_island_context"])
                min_lon, min_lat, max_lon, max_lat = region["bounds"]
                self.assertLess(min_lon, max_lon)
                self.assertLess(min_lat, max_lat)
                self.assertEqual(region["review_status"], "planned")

    def test_relief_layers_are_source_backed_and_include_lowland_exclusions(self) -> None:
        expected_layers = {
            "sudetes",
            "western_carpathians",
            "eastern_carpathians",
            "southern_carpathians",
            "dinaric_alps",
            "balkan_mountains_stara_planina",
            "rhodope_pindus_context",
            "ukrainian_carpathians_cutoff",
            "crimean_mountains",
            "pontic_mountains",
            "taurus_mountains",
            "anatolian_plateau",
            "caucasus_armenian_highlands_context",
            "north_european_plain_lowland_exclusion",
            "pannonian_basin_lowland_exclusion",
            "danube_lowlands_exclusion",
            "ukrainian_steppe_lowland_exclusion",
            "belarus_lowlands_exclusion",
            "russian_plain_lowland_exclusion",
            "anatolian_central_basins_lowland_exclusion",
        }
        self.assertGreaterEqual(set(self.relief_by_id), expected_layers)
        for layer_id in expected_layers:
            with self.subTest(layer=layer_id):
                layer = self.relief_by_id[layer_id]
                self.assertIn("DEM-derived", layer["source_rule"])
                self.assertTrue(layer["lowland_exclusions"])
                self.assertEqual(layer["review_status"], "planned")
                min_lon, min_lat, max_lon, max_lat = layer["bounds"]
                self.assertLess(min_lon, max_lon)
                self.assertLess(min_lat, max_lat)

        self.assertIn("eastern_carpathians", self.relief_by_id["western_carpathians"]["continuity_refs"])
        self.assertIn("ukrainian_carpathians_cutoff", self.relief_by_id["eastern_carpathians"]["continuity_refs"])
        self.assertIn("Southern Carpathians", self.relief_by_id["southern_carpathians"]["display_name"])
        self.assertIn("North European Plain", self.relief_by_id["north_european_plain_lowland_exclusion"]["lowland_exclusions"])
        self.assertIn("Pannonian Basin", self.relief_by_id["pannonian_basin_lowland_exclusion"]["lowland_exclusions"])
        self.assertIn("Danube lowlands", self.relief_by_id["danube_lowlands_exclusion"]["lowland_exclusions"])
        self.assertIn("Ukrainian steppe", self.relief_by_id["ukrainian_steppe_lowland_exclusion"]["lowland_exclusions"])
        self.assertIn("Belarus lowlands", self.relief_by_id["belarus_lowlands_exclusion"]["lowland_exclusions"])
        self.assertIn("Russian Plain", self.relief_by_id["russian_plain_lowland_exclusion"]["lowland_exclusions"])
        self.assertIn("Anatolian central basins", self.relief_by_id["anatolian_central_basins_lowland_exclusion"]["lowland_exclusions"])

    def test_water_coasts_rivers_and_lakes_are_explicit(self) -> None:
        required = {
            "baltic_coast",
            "black_sea_west_coast",
            "black_sea_north_coast",
            "sea_of_azov",
            "danube_delta",
            "danube_context",
            "dnieper_context",
            "dniester_context",
            "bosporus_marmara",
            "black_sea_turkey_coast",
            "aegean_turkey_coast",
            "mediterranean_turkey_coast",
            "lake_van_context",
            "lake_tuz_context",
        }
        self.assertGreaterEqual(set(self.water_by_id), required)
        self.assertEqual(self.water_by_id["danube_delta"]["kind"], "delta")
        self.assertEqual(self.water_by_id["bosporus_marmara"]["kind"], "strait_sea")
        for water_id in required:
            with self.subTest(water=water_id):
                entry = self.water_by_id[water_id]
                self.assertTrue(entry["countries"])
                self.assertTrue(entry["source_rule"])
                self.assertEqual(entry["review_status"], "planned")

    def test_every_region_water_context_resolves_to_source_backed_entry(self) -> None:
        for region in self.contract["regions"]:
            for water_id in region["required_water_island_context"]:
                with self.subTest(region=region["id"], water=water_id):
                    self.assertIn(water_id, self.water_by_id)
                    entry = self.water_by_id[water_id]
                    self.assertTrue(entry["source_rule"])
                    self.assertEqual(entry["review_status"], "planned")

    def test_city_landmarks_include_required_places_and_candidate_anchors(self) -> None:
        required = {
            "warsaw": ("Poland", "major"),
            "krakow": ("Poland", "regional"),
            "prague": ("Czechia", "major"),
            "brno": ("Czechia", "regional"),
            "bratislava": ("Slovakia", "major"),
            "budapest": ("Hungary", "major"),
            "bucharest": ("Romania", "major"),
            "cluj_napoca": ("Romania", "regional"),
            "sofia": ("Bulgaria", "major"),
            "belgrade": ("Serbia", "major"),
            "zagreb": ("Croatia", "major"),
            "sarajevo": ("Bosnia and Herzegovina", "regional"),
            "ljubljana": ("Slovenia", "regional"),
            "skopje": ("North Macedonia", "regional"),
            "tirana": ("Albania", "regional"),
            "kyiv": ("Ukraine", "major"),
            "lviv": ("Ukraine", "regional"),
            "odesa": ("Ukraine", "regional"),
            "minsk": ("Belarus", "major"),
            "moscow": ("Russia", "context"),
            "st_petersburg": ("Russia", "context"),
            "istanbul": ("Turkey", "major"),
            "ankara": ("Turkey", "major"),
            "izmir": ("Turkey", "regional"),
            "antalya": ("Turkey", "cableway_anchor"),
            "bursa": ("Turkey", "cableway_anchor"),
            "trabzon": ("Turkey", "cableway_anchor"),
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

        self.assertEqual(self.city_by_id["warsaw"]["landmark_icon_id"], "city_warsaw")
        self.assertEqual(self.city_by_id["kyiv"]["landmark_icon_id"], "city_kyiv")
        self.assertEqual(self.city_by_id["istanbul"]["landmark_icon_id"], "city_istanbul")
        self.assertEqual(self.city_by_id["brno"]["landmark_icon_id"], "missing_landmark_icon")

    def test_transport_candidate_buckets_are_staging_only_and_cover_scope(self) -> None:
        buckets = {bucket["id"]: bucket for bucket in self.contract["transport_candidate_buckets"]}
        expected = {
            "central_eastern_urban_and_mountain_candidates",
            "romania_balkans_candidates",
            "belarus_ukraine_western_russia_candidates",
            "turkey_bridge_candidates",
        }
        self.assertEqual(set(buckets), expected)
        for bucket in buckets.values():
            with self.subTest(bucket=bucket["id"]):
                self.assertEqual(bucket["production_policy"], "staging_review_only")
                self.assertTrue(bucket["required_candidate_anchors"])
                self.assertTrue(bucket["required_transport_types"])
        self.assertIn("Budapest Castle Hill funicular", buckets["central_eastern_urban_and_mountain_candidates"]["required_candidate_anchors"])
        self.assertIn("Sarajevo Trebevic cable car", buckets["romania_balkans_candidates"]["required_candidate_anchors"])
        self.assertIn("Kyiv funicular", buckets["belarus_ukraine_western_russia_candidates"]["required_candidate_anchors"])
        self.assertIn("Bursa Uludag cable car", buckets["turkey_bridge_candidates"]["required_candidate_anchors"])
        self.assertIn("cable_urban", buckets["turkey_bridge_candidates"]["required_transport_types"])

    def test_source_requirements_keep_relief_water_and_candidates_source_backed(self) -> None:
        sources = self.contract["source_requirements"]
        self.assertIn("Copernicus DEM GLO-30", sources["relief"])
        self.assertIn("EU-DEM", sources["relief"])
        self.assertIn("NASA SRTM 1 Arc-Second Global", sources["relief"])
        self.assertIn("OpenStreetMap coastline/water/island/river relations for detailed passes", sources["coastline_water"])
        self.assertIn("OpenStreetMap", sources["candidate_seed"])
        self.assertIn("Wikidata", sources["candidate_seed"])
        for required in ["source_url", "license_note", "download_date", "processing_command", "review_status"]:
            with self.subTest(required=required):
                self.assertIn(required, sources["required_metadata"])


if __name__ == "__main__":
    unittest.main()
