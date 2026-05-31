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


if __name__ == "__main__":
    unittest.main()
