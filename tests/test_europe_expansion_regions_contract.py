from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "map_pipeline" / "data" / "europe_expansion_regions.json"


class EuropeExpansionRegionsContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.regions = cls.contract["regions"]
        cls.region_by_id = {region["id"]: region for region in cls.regions}
        cls.group_by_id = {group["id"]: group for group in cls.contract["required_country_groups"]}
        cls.relief_by_id = {layer["id"]: layer for layer in cls.contract["relief_layer_contracts"]}

    def test_contract_exists_and_is_non_render_metadata(self) -> None:
        self.assertTrue(CONTRACT_PATH.is_file())
        self.assertEqual(self.contract["schema"], "cable-world.europe-expansion-regions.v1")
        self.assertEqual(self.contract["issue"], "#63")
        self.assertEqual(self.contract["scope"], "non_render_region_layer_metadata")
        self.assertEqual(self.contract["review_status"], "planning_contract")
        self.assertIn("map_pipeline/data", self.contract["acceptance_contract"]["allowed_file_kinds"])
        for forbidden in [
            "map images/assets",
            "rendered underlay changes",
            "terrain glyph art",
            "runtime list/toggle UI",
            "ride scene",
            "release files",
        ]:
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, self.contract["acceptance_contract"]["forbidden_outputs"])

    def test_child_issues_remain_open_and_not_closed_by_contract(self) -> None:
        child_issues = {entry["issue"]: entry for entry in self.contract["child_issue_links"]}
        self.assertEqual(set(child_issues), {"#74", "#76", "#77"})
        for issue, entry in child_issues.items():
            with self.subTest(issue=issue):
                self.assertEqual(entry["status"], "open")
                self.assertEqual(entry["relationship"], "child_work_not_closed")

    def test_required_issue_63_country_groups_are_represented(self) -> None:
        expected_groups = {
            "france": {"France"},
            "spain": {"Spain"},
            "italy": {"Italy"},
            "switzerland": {"Switzerland"},
            "austria": {"Austria"},
            "germany_neighbors": {"Denmark", "Netherlands", "Belgium", "Luxembourg", "France", "Switzerland", "Austria", "Czechia", "Poland"},
            "nordics": {"Norway", "Sweden", "Denmark", "Iceland"},
            "finland": {"Finland"},
            "baltics": {"Estonia", "Latvia", "Lithuania"},
            "east_to_ukrainian_mountains": {"Russia", "Belarus", "Ukraine"},
            "turkey": {"Turkey"},
        }
        for group_id, countries in expected_groups.items():
            with self.subTest(group=group_id):
                self.assertIn(group_id, self.group_by_id)
                self.assertGreaterEqual(set(self.group_by_id[group_id]["countries"]), countries)

        remaining = self.group_by_id["remaining_europe_low_detail"]
        self.assertEqual(remaining["minimum_detail_tier"], "low")
        self.assertGreaterEqual(
            set(remaining["countries"]),
            {"Portugal", "Romania", "Greece", "Ireland", "United Kingdom", "Slovakia", "Slovenia"},
        )

    def test_regions_have_bounds_layers_sources_and_review_status(self) -> None:
        allowed_source_refs = set(self.contract["source_strategy"])
        allowed_detail_tiers = {"high", "medium", "low"}
        for region in self.regions:
            with self.subTest(region=region["id"]):
                self.assertIn(region["detail_tier"], allowed_detail_tiers)
                self.assertEqual(len(region["bounds"]), 4)
                min_lon, min_lat, max_lon, max_lat = region["bounds"]
                self.assertLess(min_lon, max_lon)
                self.assertLess(min_lat, max_lat)
                self.assertTrue(region["countries"])
                self.assertTrue(region["required_layers"])
                self.assertEqual(region["review_status"], "planned")
                self.assertTrue(set(region["source_strategy_refs"]).issubset(allowed_source_refs))

    def test_required_countries_are_covered_by_region_metadata(self) -> None:
        covered_countries = {
            country
            for region in self.regions
            for country in region["countries"]
        }
        for country in [
            "France",
            "Spain",
            "Italy",
            "Switzerland",
            "Austria",
            "Germany",
            "Denmark",
            "Netherlands",
            "Belgium",
            "Luxembourg",
            "Czechia",
            "Poland",
            "Norway",
            "Sweden",
            "Finland",
            "Estonia",
            "Latvia",
            "Lithuania",
            "Russia",
            "Belarus",
            "Ukraine",
            "Turkey",
        ]:
            with self.subTest(country=country):
                self.assertIn(country, covered_countries)

    def test_source_strategy_requires_reviewable_metadata_and_real_relief_sources(self) -> None:
        source_strategy = self.contract["source_strategy"]
        relief = source_strategy["relief"]
        self.assertEqual(relief["primary_dataset"], "Copernicus DEM GLO-30")
        self.assertIn("EU-DEM", relief["fallback_datasets"])
        self.assertIn("NASA SRTM 1 Arc-Second Global", relief["fallback_datasets"])
        self.assertIn("Natural Earth terrain", relief["context_only_datasets"])
        self.assertEqual(relief["placement_policy"], "real_relief_source_or_named_massif_geometry")
        for forbidden in ["random_decorative_mountains", "border_stopped_relief", "full_map_bitmap_patch"]:
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, relief["forbidden_placement"])
        for source_key in ["admin_boundaries", "cities_and_transport"]:
            with self.subTest(source_key=source_key):
                self.assertIn("source_url", source_strategy[source_key]["required_metadata"])
                self.assertIn("license_note", source_strategy[source_key]["required_metadata"])
                self.assertIn("download_date", source_strategy[source_key]["required_metadata"])

    def test_cross_border_relief_and_lowland_rules_are_explicit(self) -> None:
        rules = {rule["id"]: rule for rule in self.contract["global_rules"]}
        self.assertIn("cross_border_relief_continuity", rules)
        self.assertIn("lowland_exclusions", rules)
        self.assertIn("source_backed_mountains", rules)
        self.assertIn("Alps cannot stop at Germany", rules["cross_border_relief_continuity"]["examples"])
        for lowland in ["Po Valley", "Vienna Basin", "Swiss Plateau", "North European Plain"]:
            with self.subTest(lowland=lowland):
                self.assertIn(lowland, rules["lowland_exclusions"]["required_exclusions"])
        self.assertIn("not decorative placement", rules["source_backed_mountains"]["rule"])

    def test_cross_border_relief_layers_define_required_countries_and_exclusions(self) -> None:
        alps = self.relief_by_id["alps_cross_border"]
        self.assertGreaterEqual(set(alps["required_countries"]), {"France", "Italy", "Switzerland", "Austria", "Germany"})
        self.assertIn("Alps cannot stop at Germany", alps["continuity_rule"])
        self.assertGreaterEqual(set(alps["lowland_exclusions"]), {"Po Valley", "Vienna Basin", "Swiss Plateau"})

        pyrenees = self.relief_by_id["pyrenees"]
        self.assertGreaterEqual(set(pyrenees["required_countries"]), {"France", "Spain", "Andorra"})

        carpathians = self.relief_by_id["carpathians"]
        self.assertGreaterEqual(set(carpathians["required_countries"]), {"Slovakia", "Poland", "Ukraine", "Romania"})
        self.assertIn("Ukraine", carpathians["continuity_rule"])

        scandinavian = self.relief_by_id["scandinavian_mountains"]
        self.assertGreaterEqual(set(scandinavian["required_countries"]), {"Norway", "Sweden"})
        self.assertIn("Finland lowlands", scandinavian["continuity_rule"])

        turkey = self.relief_by_id["anatolian_relief"]
        self.assertEqual(turkey["required_countries"], ["Turkey"])
        self.assertIn("source-backed relief", turkey["continuity_rule"])

    def test_high_detail_regions_cover_france_spain_italy_switzerland_and_austria(self) -> None:
        high_detail_countries = {
            country
            for region in self.regions
            if region["detail_tier"] == "high"
            for country in region["countries"]
        }
        self.assertGreaterEqual(high_detail_countries, {"France", "Spain", "Italy", "Switzerland", "Austria"})


if __name__ == "__main__":
    unittest.main()
