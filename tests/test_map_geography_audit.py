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
