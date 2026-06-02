from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MapEditorContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main_js = (ROOT / "map_editor" / "src" / "main.js").read_text(encoding="utf-8")
        cls.index_html = (ROOT / "map_editor" / "index.html").read_text(encoding="utf-8")
        cls.readme = (ROOT / "map_editor" / "README.md").read_text(encoding="utf-8")
        cls.glyph_doc = (ROOT / "docs" / "pipelines" / "glyph-generation.md").read_text(encoding="utf-8")

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
            "coverageCache",
            "function massifCoverage(f)",
            "function glyphMetadata(f)",
            "function glyphRefFor(image, zoomFactor)",
            "zoom_factor",
            "primary_offsets",
            "faint_offsets",
            "function pointInsideHex(dx, dy, s)",
            "HEX_ALPHA_STEP",
            "PRIMARY_ALPHA_RATIO",
            "primaryOffsets.push(key)",
            "faintOffsets.push(key)",
            "rgba(215,215,215,0.42)",
            "#1e88e5",
            "bright blue dots",
            "pale gray dots",
        ]:
            with self.subTest(expected=expected):
                self.assertTrue(
                    expected in self.main_js or expected in self.readme or expected in self.glyph_doc,
                    expected,
                )

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
