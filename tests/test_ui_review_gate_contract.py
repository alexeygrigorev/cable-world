from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class UiReviewGateContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate_doc = (ROOT / "docs" / "ui-review-gate.md").read_text(encoding="utf-8")
        cls.protocol_doc = (ROOT / "docs" / "agent-operating-protocol.md").read_text(encoding="utf-8")
        cls.screenshot_script = (ROOT / "scripts" / "capture_ui_review_screenshots.gd").read_text(encoding="utf-8")
        cls.runtime_runner = (ROOT / "tests" / "godot_runtime_runner.gd").read_text(encoding="utf-8")
        cls.runtime_app_shell = (ROOT / "tests" / "godot_runtime_app_shell.gd").read_text(encoding="utf-8")

    def test_gate_defines_strict_accept_reject_and_map_gate_boundary(self) -> None:
        for expected in [
            "Decision",
            "`ACCEPT`",
            "`REJECT`",
            "Без явного `ACCEPT` UI-задача не интегрируется",
            "не заменяет [Map Reviewer Gate](map-reviewer-gate.md)",
            "если задача меняет карту",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.gate_doc)

    def test_gate_requires_map_list_screenshot_matrix(self) -> None:
        for expected in [
            "mobile-390x844-map.png",
            "mobile-390x844-list.png",
            "landscape-844x390-map.png",
            "landscape-844x390-list.png",
            "xvfb-run -a godot --path . --script scripts/capture_ui_review_screenshots.gd",
            "tmp/ui-review/",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.gate_doc)

    def test_screenshot_script_captures_required_map_and_list_states(self) -> None:
        for expected in [
            'OUTPUT_DIR := "tmp/ui-review"',
            '"mobile-390x844-map"',
            '"mobile-390x844-list"',
            '"landscape-844x390-map"',
            '"landscape-844x390-list"',
            "screen.set_anchors_preset(Control.PRESET_FULL_RECT)",
            "screen.offset_left = 0.0",
            "screen.set_deferred(\"size\", Vector2(scenario[\"size\"]))",
            'screen._show_section("list")',
            "image.save_png(output_path)",
            "if image == null",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.screenshot_script)

    def test_gate_requires_godot_native_runtime_coverage(self) -> None:
        for expected in [
            "godot --headless --path . --script tests/godot_runtime_runner.gd",
            "Python static tests",
            "не заменяют Godot-native runtime checks",
            "return-to-map восстанавливает pan, zoom",
            "scroll/tap behavior",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.gate_doc)

        self.assertIn("res://tests/godot_runtime_app_shell.gd", self.runtime_runner)
        for expected in [
            "test_main_scene_map_list_toggle_runtime",
            "Main scene must start on the fullscreen map section.",
            "Map/list return must preserve the previous map pan offset.",
            "Map/list return must preserve the previous map zoom.",
            "test_object_list_filtering_and_selection_runtime",
            "Selecting a visible list object must emit its source object index.",
            "test_object_list_drag_suppresses_tap_selection_runtime",
            "InputEventScreenDrag",
            "A list scroll drag must suppress row tap selection immediately after release.",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.runtime_app_shell)

    def test_protocol_points_ui_tasks_to_the_ui_review_gate(self) -> None:
        for expected in [
            "docs/ui-review-gate.md",
            "mobile-390x844-map.png",
            "mobile-390x844-list.png",
            "landscape-844x390-map.png",
            "landscape-844x390-list.png",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.protocol_doc)


if __name__ == "__main__":
    unittest.main()
