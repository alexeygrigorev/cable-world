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


if __name__ == "__main__":
    unittest.main()
