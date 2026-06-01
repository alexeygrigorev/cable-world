import importlib.util
import unittest


@unittest.skipUnless(
    importlib.util.find_spec("geopandas") and importlib.util.find_spec("shapely"),
    "map geography audit requires the map pipeline dependencies",
)
class MapGeographyAuditTest(unittest.TestCase):
    def test_manual_map_layers_pass_geography_audit(self) -> None:
        from map_pipeline.compose_map import audit_geography_layers

        self.assertEqual([], audit_geography_layers())

    def test_massif_source_layers_have_valid_manifest(self) -> None:
        from map_pipeline.compose_map import audit_massif_source_manifest

        self.assertEqual([], audit_massif_source_manifest())

    def test_massif_source_manifest_rejects_monolithic_or_unscaled_layers(self) -> None:
        import json
        import tempfile
        import map_pipeline.compose_map as compose_map

        with open(compose_map.MASSIF_MANIFEST_PATH, "r", encoding="utf-8") as file:
            manifest = json.load(file)

        original_manifest_path = compose_map.MASSIF_MANIFEST_PATH
        try:
            manifest["layers"][0] = dict(manifest["layers"][0])
            layer_id = manifest["layers"][0]["id"]
            manifest["layers"][0]["image"] = "germany_styled.png"
            del manifest["layers"][0]["map_bbox_px"]

            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as file:
                json.dump(manifest, file)
                file.flush()
                compose_map.MASSIF_MANIFEST_PATH = file.name
                errors = compose_map.audit_massif_source_manifest()

            self.assertTrue(
                any(f"massif source layer {layer_id} must use its own source layer PNG" in error for error in errors)
            )
            self.assertTrue(
                any(f"massif source layer {layer_id} must declare map_bbox_px" in error for error in errors)
            )
        finally:
            compose_map.MASSIF_MANIFEST_PATH = original_manifest_path

    def test_alpine_relief_extents_pass_source_and_coverage_audit(self) -> None:
        from map_pipeline.compose_map import audit_alpine_relief_contract

        self.assertEqual([], audit_alpine_relief_contract())

    def test_terrain_massif_layers_pass_named_layer_contract(self) -> None:
        from map_pipeline.compose_map import audit_terrain_massif_layer_contract

        self.assertEqual([], audit_terrain_massif_layer_contract())

    def test_terrain_massif_contract_requires_production_asset_metadata(self) -> None:
        import json
        import tempfile
        import map_pipeline.compose_map as compose_map

        with open(compose_map.TERRAIN_MASSIF_LAYERS_PATH, "r", encoding="utf-8") as file:
            contract = json.load(file)

        original_contract_path = compose_map.TERRAIN_MASSIF_LAYERS_PATH
        try:
            del contract["production_asset_contract"]
            contract["source_layers"][0] = dict(contract["source_layers"][0])
            layer_id = contract["source_layers"][0]["id"]
            del contract["source_layers"][0]["production_asset_id"]

            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as file:
                json.dump(contract, file)
                file.flush()
                compose_map.TERRAIN_MASSIF_LAYERS_PATH = file.name
                errors = compose_map.audit_terrain_massif_layer_contract()

            self.assertTrue(
                any("terrain massif production asset contract must require source_extent_id" in error for error in errors)
            )
            self.assertTrue(
                any(f"terrain source layer {layer_id} must declare matching production_asset_id" in error for error in errors)
            )
        finally:
            compose_map.TERRAIN_MASSIF_LAYERS_PATH = original_contract_path

    def test_germany_terrain_accuracy_contract_passes_current_underlay(self) -> None:
        from map_pipeline.compose_map import audit_germany_terrain_accuracy_contract

        self.assertEqual([], audit_germany_terrain_accuracy_contract())

    def test_germany_terrain_audit_rejects_large_lowland_mountains(self) -> None:
        import map_pipeline.compose_map as compose_map

        original_regions = [dict(region) for region in compose_map.RELIEF_REGIONS]
        try:
            compose_map.RELIEF_REGIONS = original_regions + [
                {
                    "id": "false_hamburg_mountains",
                    "label": "False Hamburg Mountains",
                    "points": [(9.2, 53.3), (10.1, 53.3), (10.1, 53.9), (9.2, 53.9)],
                    "mountain_glyphs": [("highland_forest_1", 9.75, 53.55, 180)],
                }
            ]
            errors = compose_map.audit_germany_terrain_accuracy_contract()
            self.assertTrue(
                any("hamburg_lower_elbe_plain" in error for error in errors),
                "Large relief glyphs near Hamburg must fail the North German Plain exclusion audit.",
            )
        finally:
            compose_map.RELIEF_REGIONS = original_regions

    def test_germany_terrain_audit_requires_ruegen_and_major_water(self) -> None:
        import map_pipeline.compose_map as compose_map

        original_labels = [dict(label) for label in compose_map.MAP_LABELS]
        original_water = [dict(water) for water in compose_map.NAMED_WATER_BODIES]
        try:
            compose_map.MAP_LABELS = [label for label in original_labels if label["name"] != "Rügen"]
            compose_map.NAMED_WATER_BODIES = [water for water in original_water if water["id"] != "mueritz"]
            errors = compose_map.audit_germany_terrain_accuracy_contract()
            self.assertTrue(any("Rügen" in error for error in errors))
            self.assertTrue(any("mueritz" in error for error in errors))
        finally:
            compose_map.MAP_LABELS = original_labels
            compose_map.NAMED_WATER_BODIES = original_water

    def test_rostock_runtime_landmark_requires_landward_icon_offset(self) -> None:
        import map_pipeline.compose_map as compose_map

        original_audits = [dict(landmark) for landmark in compose_map.CITY_LANDMARK_PLACEMENT_AUDITS]
        try:
            current_errors = compose_map.audit_runtime_landmark_placement()
            self.assertEqual([], current_errors)

            rostock = next(landmark for landmark in original_audits if landmark["name"] == "Rostock")
            compose_map.CITY_LANDMARK_PLACEMENT_AUDITS = [
                dict(rostock, icon_offset=(0.0, 0.0)),
            ]
            unadjusted_errors = compose_map.audit_runtime_landmark_placement()
            self.assertTrue(
                any("runtime landmark Rostock" in error for error in unadjusted_errors),
                "Rostock's raw city coordinate places the icon over Baltic water; keep the landward offset.",
            )
        finally:
            compose_map.CITY_LANDMARK_PLACEMENT_AUDITS = original_audits

    def test_coastal_city_landmarks_are_part_of_runtime_land_audit(self) -> None:
        from map_pipeline.compose_map import CITY_LANDMARK_PLACEMENT_AUDITS

        audited_names = {landmark["name"] for landmark in CITY_LANDMARK_PLACEMENT_AUDITS}
        self.assertGreaterEqual(audited_names, {"Hamburg", "Kiel", "Lübeck", "Rostock"})

    def test_default_map_rejects_tiny_decorative_detail_sources(self) -> None:
        from map_pipeline.compose_map import (
            ATLAS_DETAILS,
            ATLAS_ROUTE_DOT_MIN_RADIUS,
            ATLAS_ROUTE_DOT_SPACING_SCALE,
            DEFAULT_ATLAS_ROUTES_ENABLED,
            DEFAULT_ATLAS_DETAIL_KINDS,
            FOREST_CLUSTER_MIN_SOURCE_WIDTH,
            FOREST_MASS_MIN_WIDTH,
            FOREST_MASS_VISUAL_SCALE,
            ATLAS_FOREST_MASSES,
            GROUND_TEXTURE_LAT_STEP,
            GROUND_TEXTURE_LON_STEP,
            INTEGRATED_LAND_PATTERN_ALPHA_SCALE,
            INTEGRATED_LAND_PATTERN_LAT_STEP,
            INTEGRATED_LAND_PATTERN_LON_STEP,
            INTEGRATED_LAND_PATTERN_MIN_SIZE,
            MIN_ATLAS_DETAIL_WIDTH,
            RELIEF_REGIONS,
            RELIEF_TREE_CLUSTER_MIN_WIDTH,
            _relief_tree_cluster_width,
        )

        self.assertEqual({"ship"}, DEFAULT_ATLAS_DETAIL_KINDS)
        self.assertFalse(DEFAULT_ATLAS_ROUTES_ENABLED)
        self.assertGreaterEqual(MIN_ATLAS_DETAIL_WIDTH, 118)
        for detail in ATLAS_DETAILS:
            if detail["kind"] in DEFAULT_ATLAS_DETAIL_KINDS:
                self.assertNotIn(detail["kind"], {"bridge", "castle", "chapel", "lighthouse", "port", "ruins", "tower", "village", "watermill", "windmill"})

        self.assertGreaterEqual(GROUND_TEXTURE_LON_STEP, 0.60)
        self.assertGreaterEqual(GROUND_TEXTURE_LAT_STEP, 0.56)
        self.assertGreaterEqual(GROUND_TEXTURE_LON_STEP, 0.70)
        self.assertGreaterEqual(GROUND_TEXTURE_LAT_STEP, 0.66)
        self.assertGreaterEqual(INTEGRATED_LAND_PATTERN_LON_STEP, 0.90)
        self.assertGreaterEqual(INTEGRATED_LAND_PATTERN_LAT_STEP, 0.80)
        self.assertLessEqual(INTEGRATED_LAND_PATTERN_ALPHA_SCALE, 0.22)
        self.assertGreaterEqual(INTEGRATED_LAND_PATTERN_MIN_SIZE, 30)
        self.assertGreaterEqual(ATLAS_ROUTE_DOT_SPACING_SCALE, 1.50)
        self.assertGreaterEqual(ATLAS_ROUTE_DOT_MIN_RADIUS, 4)

        for mass in ATLAS_FOREST_MASSES:
            for glyph_name, _lon, _lat, width in mass["clusters"]:
                with self.subTest(forest=mass["id"], glyph=glyph_name):
                    self.assertGreaterEqual(width, FOREST_CLUSTER_MIN_SOURCE_WIDTH)
                    self.assertGreaterEqual(max(FOREST_MASS_MIN_WIDTH, int(width * FOREST_MASS_VISUAL_SCALE)), 170)

        for region in RELIEF_REGIONS:
            for _lon, _lat, tree_size in region.get("trees", []):
                with self.subTest(region=region["id"], tree_size=tree_size):
                    self.assertGreaterEqual(_relief_tree_cluster_width(tree_size), RELIEF_TREE_CLUSTER_MIN_WIDTH)

    def test_alpine_rendered_segments_are_not_decorative_only_anchors(self) -> None:
        from map_pipeline.compose_map import ALPINE_MASSIF_SEGMENTS, ALPINE_RELIEF_EXTENTS_PATH
        import json

        with open(ALPINE_RELIEF_EXTENTS_PATH, "r", encoding="utf-8") as file:
            contract = json.load(file)

        extent_segments = {segment["id"]: segment for segment in contract["massif_segments"]}
        self.assertEqual(
            {segment["id"] for segment in ALPINE_MASSIF_SEGMENTS},
            set(extent_segments),
        )
        for segment in ALPINE_MASSIF_SEGMENTS:
            with self.subTest(segment=segment["id"]):
                extent = extent_segments[segment["id"]]
                self.assertEqual(segment["id"], segment["source_extent_id"])
                self.assertNotRegex(extent["geometry_source"], r"(random|decorative|sticker)")
                self.assertIn("named_massif", extent["geometry_source"])
                self.assertIn("pending_dem", extent["geometry_source"])
                self.assertTrue(extent["coverage_regions"])

    def test_exported_relief_regions_have_source_extent_contract(self) -> None:
        from map_pipeline.compose_map import RELIEF_REGIONS, TERRAIN_MASSIF_LAYERS_PATH
        import json

        with open(TERRAIN_MASSIF_LAYERS_PATH, "r", encoding="utf-8") as file:
            contract = json.load(file)

        source_layers = {layer["id"]: layer for layer in contract["source_layers"]}
        exported_regions = {
            region["id"]: region
            for region in RELIEF_REGIONS
            if region["id"] != "northern_lowlands" and any(
                region.get(key) for key in ("trees", "ridge_bands", "massif_segments", "mountain_glyphs", "mountains")
            )
        }
        self.assertEqual(set(exported_regions), set(source_layers))
        for layer_id, layer in source_layers.items():
            with self.subTest(layer=layer_id):
                self.assertTrue(layer["source_extent_id"])
                self.assertNotRegex(layer["placement_policy"], r"(random|decorative|full_map)")
                self.assertTrue(layer["source_confidence"])
                self.assertTrue(layer["replacement_status"])


if __name__ == "__main__":
    unittest.main()
