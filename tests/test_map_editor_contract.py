from pathlib import Path
import json
import unittest

try:
    from PIL import Image
except ModuleNotFoundError:
    Image = None


ROOT = Path(__file__).resolve().parents[1]


class MapEditorContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main_js = (ROOT / "map_editor" / "src" / "main.js").read_text(encoding="utf-8")
        cls.index_html = (ROOT / "map_editor" / "index.html").read_text(encoding="utf-8")
        cls.readme = (ROOT / "map_editor" / "README.md").read_text(encoding="utf-8")
        cls.glyph_doc = (ROOT / "docs" / "pipelines" / "glyph-generation.md").read_text(encoding="utf-8")
        cls.hex_map = json.loads((ROOT / "map_editor" / "src" / "data" / "hex_map.json").read_text(encoding="utf-8"))

    def test_clicked_hex_panel_shows_hex_id_even_without_objects(self) -> None:
        for expected in [
            "selectedHex = key",
            "renderPanelList(list, key)",
            "panelEl.hidden = false",
            "Гекс ${hexKey}",
            "<dt>id</dt><dd>${hexKey}</dd>",
            "Объектов на гексе нет",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.main_js)

    def test_panel_cards_show_glyph_name_and_preview_for_every_feature_type(self) -> None:
        for expected in [
            "function glyphName(f)",
            "function glyphPreviewHtml(f)",
            "function assetUrl(name)",
            "assetVersions",
            "function requestAssetVersions()",
            "/__asset_versions?names=",
            "function glyphDebugPayload(f, hexKey = selectedHex)",
            "function copyGlyphDebug(f)",
            "city_${f.icon}.png",
            "icon_${f.icon}.png",
            "return f.image || \"massif\"",
            "variant(f.anchor || (f.cells || [])[0] || f.id, FOREST_GLYPHS)",
            "<dt>Глиф</dt><dd>${glyphName(f)}</dd>",
            "${glyphPreviewHtml(f)}",
            "copy glyph debug",
            "navigator.clipboard.writeText",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.main_js)

    def test_selected_city_also_gets_anchor_debug_dot(self) -> None:
        self.assertIn("if (hi) {", self.main_js)
        self.assertNotIn("cities aren't highlighted", self.main_js)
        self.assertIn("primaryKeys = [hi.anchor];", self.main_js)

    def test_panel_text_selection_does_not_rerender_cards(self) -> None:
        for expected in [
            "function panelHasTextSelection()",
            "if (panelHasTextSelection()) return;",
            "window.getSelection()",
            "panelEl.contains(range.commonAncestorContainer)",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.main_js)

    def test_multicell_glyph_debug_distinguishes_primary_and_faint_footprints(self) -> None:
        for expected in [
            "function massifCoverage(f)",
            "function glyphMetadata(f)",
            "function glyphRefFor(image)",
            "zoom_factor",
            "primary_offsets",
            "faint_offsets",
            "return offsets.map((offset) => applyOffset(f.anchor, offset));",
            "primaryOffsets: meta.primary_offsets",
            "faintOffsets: meta.faint_offsets",
            "rgba(215,215,215,0.42)",
            "#1e88e5",
            "#f6df9b",
            "anchor_cell: f.anchor",
            "bright blue dots",
            "pale gray dots",
        ]:
            with self.subTest(expected=expected):
                self.assertTrue(
                    expected in self.main_js or expected in self.readme or expected in self.glyph_doc,
                    expected,
                )

    def test_multicell_glyph_footprint_is_metadata_only(self) -> None:
        coverage_fn = self.main_js.split("function massifCoverage(f)", 1)[1].split("// warm the cache", 1)[0]
        self.assertIn("glyphMetadata(f)", coverage_fn)
        self.assertIn("meta.primary_offsets", coverage_fn)
        self.assertIn("meta.faint_offsets", coverage_fn)
        self.assertNotIn("getImageData", coverage_fn)
        self.assertNotIn("state.hexes", coverage_fn)

        occupies_fn = self.main_js.split("function featureOccupiesHex(f, key)", 1)[1].split("function canReset", 1)[0]
        self.assertIn("return false;", occupies_fn)
        massif_branch = occupies_fn.split('const coverage = f.image ? massifCoverage(f) : null;', 1)[1]
        self.assertNotIn("(f.cells || []).includes(key);", massif_branch)

    def test_each_massif_png_has_one_canonical_glyph_ref(self) -> None:
        refs_by_image = {}
        for feature in self.hex_map["features"]:
            if feature.get("glyph") != "massif":
                continue
            refs_by_image.setdefault(feature["image"], set()).add(feature.get("glyph_ref"))
        for image, refs in refs_by_image.items():
            with self.subTest(image=image):
                self.assertEqual(len(refs), 1, refs)
                ref = next(iter(refs))
                self.assertNotIn("@", ref)
                self.assertEqual(ref, f"massif:{Path(image).stem}")

        metadata_by_file = {}
        for ref, meta in self.hex_map["glyphs"].items():
            metadata_by_file.setdefault(meta["file"], set()).add(ref)
        for image, refs in metadata_by_file.items():
            with self.subTest(metadata=image):
                self.assertEqual(len(refs), 1, refs)

    def test_massif_anchor_is_bottom_left_and_visible(self) -> None:
        if Image is None:
            self.skipTest("PIL is required for alpha anchor validation")
        for ref, meta in self.hex_map["glyphs"].items():
            with self.subTest(ref=ref):
                self.assertEqual(meta.get("anchor_offset"), "bottom-left")
                self.assertEqual(meta.get("anchor_point"), "hex-lower-left-0.75")
                self.assertIn("anchor_source_px", meta)
                with Image.open(ROOT / "assets" / "map" / "massifs" / meta["file"]) as source:
                    alpha = source.convert("RGBA").getchannel("A")
                    bbox = alpha.getbbox()
                    self.assertIsNotNone(bbox)
                    pixels = alpha.load()
                    alpha_height = bbox[3] - bbox[1]
                    band_top = max(bbox[1], bbox[3] - max(12, int(alpha_height * 0.08)))
                    xs = [
                        x
                        for y in range(band_top, bbox[3])
                        for x in range(alpha.width)
                        if pixels[x, y] > 50
                    ]
                    self.assertIn(meta["anchor_source_px"][0], xs)
                    self.assertEqual(meta["anchor_source_px"][1], alpha.height - 1)
                x0, y0, x1, y1 = meta["bounds_offset_hex"]
                self.assertLessEqual(x0, 0)
                self.assertGreater(x1, 0)
                self.assertLess(y0, 0)
                self.assertEqual(y1, 0)

        for expected in [
            "if (hi.glyph === \"massif\")",
            "function hexAnchorWorld(q, r)",
            "x: c.x - (SQRT3 * s) / 2",
            "y: c.y + s * 0.75",
            "return hexToContent(q, r);",
            "ctx.arc(c.x, c.y, os * 0.31",
            "ctx.strokeStyle = \"#f6df9b\";",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.main_js)

    def test_object_sprite_size_is_not_viewport_fit_dependent(self) -> None:
        for expected in [
            "const FIXED_MAP_SCALE = 0.64;",
            "return FIXED_MAP_SCALE * zoomVal;",
            "function objectUnit()",
            "return sizeW();",
            "const os = objectUnit();",
            "const objectScreenS = os * sc;",
            "const showLabels = objectScreenS > 13;",
            "massifBounds(f, os)",
            "drawCity(pos.x, pos.y, os, f, showLabels)",
            "drawTransport(pos.x, pos.y, os, f, showLabels)",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.main_js)

        self.assertNotIn("fitScale * zoomVal", self.main_js)
        self.assertNotIn("Math.max(cssW / fw, cssH / fh)", self.main_js)

    def test_clicked_country_gets_current_land_color(self) -> None:
        for expected in [
            "function currentCountry()",
            "return state.hexes[selectedHex]?.country || \"DE\";",
            "return cell.country === currentCountry() ? COLORS.landDE : COLORS.landOther;",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.main_js)
        cell_color_fn = self.main_js.split("function cellColor(cell)", 1)[1].split("// ----- glyphs", 1)[0]
        self.assertNotIn('cell.country === "DE"', cell_color_fn)

    def test_new_city_generation_targets_are_on_hex_map(self) -> None:
        city_ids = {feature["id"]: feature for feature in self.hex_map["features"] if feature.get("glyph") == "city"}
        for city_id in [
            "kharkiv", "dnipro", "chernivtsi", "uzhhorod", "grodno", "brest",
            "vitebsk", "gomel", "kaliningrad", "pskov", "smolensk", "novgorod",
            "nizhny_novgorod", "simferopol", "konya", "kayseri", "samsun",
            "erzurum", "coimbra", "braga", "bolzano", "naples", "bari",
            "palermo", "catania", "thessaloniki", "patras", "ioannina",
            "heraklion", "gdansk", "wroclaw", "poznan", "edinburgh",
            "manchester", "cardiff", "belfast", "trondheim", "stavanger",
            "uppsala", "oulu",
        ]:
            with self.subTest(city_id=city_id):
                self.assertIn(city_id, city_ids)
                self.assertIn(city_ids[city_id]["anchor"], self.hex_map["hexes"])

    def test_crimea_uses_separate_country_code(self) -> None:
        city_ids = {feature["id"]: feature for feature in self.hex_map["features"] if feature.get("glyph") == "city"}
        simferopol = city_ids["simferopol"]
        self.assertEqual(self.hex_map["hexes"][simferopol["anchor"]]["country"], "CR")

    def test_sicily_is_not_connected_to_mainland_by_hex_bridge(self) -> None:
        for key, cell in self.hex_map["hexes"].items():
            lon, lat = cell["center"]
            with self.subTest(key=key):
                self.assertFalse(
                    15.52 < lon < 16.22 and 37.92 < lat < 38.22,
                    f"{key} fills the Strait of Messina water gap",
                )

        city_ids = {feature["id"]: feature for feature in self.hex_map["features"] if feature.get("glyph") == "city"}
        for city_id in ["palermo", "catania"]:
            with self.subTest(city_id=city_id):
                self.assertIn(city_ids[city_id]["anchor"], self.hex_map["hexes"])

    def test_zoom_keeps_current_viewport_center_after_pan(self) -> None:
        for expected in [
            "function viewportCenterContent()",
            "const center = viewportCenterContent();",
            "panX = (fc.x - center.x) * sc;",
            "panY = (fc.y - center.y) * sc;",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.main_js)

    def test_palette_toggle_does_not_resize_map_viewport(self) -> None:
        palette_block = self.index_html.split('<aside id="palette">', 1)[1].split("</aside>", 1)[0]
        self.assertIn('id="paletteToggle"', palette_block)

        handler = self.main_js.split('paletteToggle.addEventListener("click"', 1)[1].split("});", 1)[0]
        self.assertIn('document.body.classList.toggle("palette-hidden")', handler)
        self.assertIn("syncPaletteToggle();", handler)
        self.assertNotIn("setupCanvas()", handler)


if __name__ == "__main__":
    unittest.main()
