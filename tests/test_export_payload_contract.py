from configparser import ConfigParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def _unquote(value: str) -> str:
    return value.strip().strip('"')


class ExportPayloadContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        parser = ConfigParser(strict=False)
        parser.optionxform = str
        parser.read(ROOT / "export_presets.cfg", encoding="utf-8")
        cls.parser = parser

    def test_export_presets_exclude_source_only_sprite_assets(self) -> None:
        required_excludes = [
            "assets/map/glyphs/**",
            "assets/map/glyphs/map_glyph_sheet.png",
            "assets/map/glyphs/map_glyph_sheet.png.import",
            "assets/map/glyphs/terrain_forest_sheet.png",
            "assets/map/glyphs/terrain_forest_sheet.png.import",
            "asset_archive/**",
            "assets/map/massifs/alps.png",
            "assets/map/massifs/alps.png.import",
            "assets/map/massifs/normal_mountains_contact.png",
            "assets/map/massifs/normal_mountains_contact.png.import",
            "assets/sprites/icon_*.png",
            "assets/sprites/icon_*.png.import",
            "assets/sprites/city_landmark_clusters_hi_res/city_*.png",
            "assets/sprites/city_landmark_clusters_hi_res/city_*.png.import",
        ]

        for section in self.parser.sections():
            if not section.startswith("preset.") or section.endswith(".options"):
                continue
            exclude_filter = _unquote(self.parser[section].get("exclude_filter", ""))
            for required_exclude in required_excludes:
                with self.subTest(section=section, required_exclude=required_exclude):
                    self.assertIn(required_exclude, exclude_filter)


if __name__ == "__main__":
    unittest.main()
