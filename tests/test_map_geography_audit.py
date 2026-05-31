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

    def test_alpine_relief_extents_pass_source_and_coverage_audit(self) -> None:
        from map_pipeline.compose_map import audit_alpine_relief_contract

        self.assertEqual([], audit_alpine_relief_contract())

    def test_terrain_massif_layers_pass_named_layer_contract(self) -> None:
        from map_pipeline.compose_map import audit_terrain_massif_layer_contract

        self.assertEqual([], audit_terrain_massif_layer_contract())

    def test_default_map_rejects_tiny_decorative_detail_sources(self) -> None:
        from map_pipeline.compose_map import (
            ATLAS_DETAILS,
            ATLAS_ROUTE_DOT_MIN_RADIUS,
            ATLAS_ROUTE_DOT_SPACING_SCALE,
            DEFAULT_ATLAS_DETAIL_KINDS,
            FOREST_CLUSTER_MIN_SOURCE_WIDTH,
            FOREST_MASS_MIN_WIDTH,
            FOREST_MASS_VISUAL_SCALE,
            ATLAS_FOREST_MASSES,
            GROUND_TEXTURE_LAT_STEP,
            GROUND_TEXTURE_LON_STEP,
            INTEGRATED_LAND_PATTERN_LAT_STEP,
            INTEGRATED_LAND_PATTERN_LON_STEP,
            MIN_ATLAS_DETAIL_WIDTH,
            RELIEF_REGIONS,
            RELIEF_TREE_CLUSTER_MIN_WIDTH,
            _relief_tree_cluster_width,
        )

        self.assertEqual({"bridge", "port", "ship"}, DEFAULT_ATLAS_DETAIL_KINDS)
        self.assertGreaterEqual(MIN_ATLAS_DETAIL_WIDTH, 104)
        for detail in ATLAS_DETAILS:
            if detail["kind"] in DEFAULT_ATLAS_DETAIL_KINDS:
                self.assertNotIn(detail["kind"], {"castle", "chapel", "lighthouse", "ruins", "tower", "village", "watermill", "windmill"})

        self.assertGreaterEqual(GROUND_TEXTURE_LON_STEP, 0.60)
        self.assertGreaterEqual(GROUND_TEXTURE_LAT_STEP, 0.56)
        self.assertGreaterEqual(INTEGRATED_LAND_PATTERN_LON_STEP, 0.40)
        self.assertGreaterEqual(INTEGRATED_LAND_PATTERN_LAT_STEP, 0.36)
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
