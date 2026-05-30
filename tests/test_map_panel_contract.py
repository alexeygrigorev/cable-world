from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MapPanelContractTest(unittest.TestCase):
    def test_map_panel_declares_local_object_marker_api(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "extends PanelContainer",
            "class_name MapPanel",
            "signal object_selected(index: int)",
            "func set_objects(next_objects: Array[Dictionary]) -> void:",
            "func select_object(index: int) -> void:",
            "Button.new()",
            "marker.pressed.connect(_on_marker_pressed.bind(index))",
            "object_selected.emit(index)",
        ]:
            self.assertIn(expected, script_text)

    def test_map_panel_uses_transport_object_coordinates_only(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")

        for expected in [
            '"coordinates"',
            "coordinates.x",
            "coordinates.y",
            '"longitude"',
            '"latitude"',
            "Vector2(float(object_data.get(\"longitude\", 0.0)), float(object_data.get(\"latitude\", 0.0)))",
        ]:
            self.assertIn(expected, script_text)

        forbidden_details = [
            "station",
            "platform",
            "станц",
            "платформ",
            "колес",
        ]
        lowered = script_text.lower()
        for forbidden in forbidden_details:
            self.assertNotIn(forbidden, lowered)

    def test_map_panel_is_offline_and_russian(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")

        self.assertNotIn("MapLibre", script_text)
        self.assertNotIn("http://", script_text)
        self.assertNotIn("https://", script_text)
        for text in [
            "Карта объектов",
            "Выбранная точка: пока не выбрана",
            "Выбрать объект",
            "Нет точек с координатами",
            "Вписать все точки на экран",
            "Приблизить карту",
            "Отдалить карту",
            "Выбрано:",
        ]:
            self.assertIn(text, script_text)

        user_strings = re.findall(r'"([^"]*[А-Яа-яЁё][^"]*)"', script_text)
        self.assertGreaterEqual(len(user_strings), 8)

    def test_mobile_map_has_visible_contract(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        self.assertIn("const MARKER_SIZE := Vector2(52.0, 48.0)", script_text)
        self.assertIn("const MAP_MIN_HEIGHT := 620.0", script_text)
        self.assertIn("const MAP_VIEW_HEIGHT := 560.0", script_text)
        self.assertIn("const MAP_LANDSCAPE_MIN_HEIGHT := 360.0", script_text)
        self.assertIn("custom_minimum_size = Vector2(0, 420)", scene_text)
        self.assertIn('map_layer.custom_minimum_size = Vector2(0.0, MAP_VIEW_HEIGHT)', script_text)
        self.assertIn("resized.connect(_sync_map_canvas_height)", script_text)
        self.assertIn('call_deferred("_sync_map_canvas_height")', script_text)
        self.assertIn("func _sync_map_canvas_height() -> void:", script_text)
        self.assertIn("map_layer.custom_minimum_size.y = target_height", script_text)
        self.assertIn("if size.x > size.y:", script_text)
        self.assertIn("OfflineMapLayer.new()", script_text)
        self.assertIn("draw_rect(rect", script_text)
        self.assertIn("draw_line", script_text)
        self.assertIn("geo_bounds", script_text)
        self.assertIn("_draw_graticule()", script_text)
        self.assertIn("_draw_scale_bar()", script_text)
        self.assertIn("static func _project_coordinates(", script_text)
        self.assertIn("static func _mercator_y(", script_text)
        self.assertIn("_update_map_reference_data()", script_text)
        self.assertIn("summary_label.visible = false", script_text)
        self.assertIn("selected_label.mouse_filter = Control.MOUSE_FILTER_IGNORE", script_text)
        self.assertNotIn("hint_label", script_text)
        self.assertIn("MARKER_SPREAD_DISTANCE", script_text)
        self.assertIn("MARKER_SPREAD_STEP", script_text)
        self.assertNotIn("GRID_LAYOUT_MIN_MARKERS", script_text)
        self.assertNotIn("func _grid_marker_position(", script_text)
        self.assertNotIn("сетка для читаемости", script_text)
        self.assertNotIn("func _draw_land_mass(", script_text)
        self.assertNotIn("func _draw_reference_routes(", script_text)
        self.assertNotIn("_draw_geo_labels(", script_text)
        self.assertIn("func _spread_marker_position(", script_text)
        self.assertIn("func _is_clear_marker_position(", script_text)
        self.assertIn("func _compact_text(", script_text)
        self.assertIn("empty_state_label.visible = marker_buttons.is_empty()", script_text)

    def test_map_panel_supports_pan_zoom_and_touch_controls(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "var pan_offset := Vector2.ZERO",
            "var zoom := 1.0",
            "func _on_map_layer_gui_input(event: InputEvent) -> void:",
            "InputEventMouseButton",
            "InputEventMouseMotion",
            "InputEventScreenTouch",
            "InputEventScreenDrag",
            "InputEventMagnifyGesture",
            "MOUSE_BUTTON_WHEEL_UP",
            "MOUSE_BUTTON_WHEEL_DOWN",
            "pan_offset += event.relative",
            "func _zoom_at(pivot: Vector2, factor: float) -> void:",
            "clamp(zoom * factor, MIN_ZOOM, MAX_ZOOM)",
            "func _reset_map_view() -> void:",
            "func _clamp_pan_offset() -> void:",
            "const MIN_ZOOM := 0.45",
            "const MAX_ZOOM := 4.0",
            "const FIT_CONTROL_SIZE := Vector2(104.0, 56.0)",
            "const PAN_LIMIT_PADDING := 72.0",
            "const DRAG_TAP_SUPPRESS_DISTANCE := 10.0",
            'button.text = title',
            '"+"',
            '"-"',
            '"Вписать"',
            "const MAP_CONTROL_SIZE := Vector2(64.0, 56.0)",
            'filter_controls.name = "ФильтрКарты"',
            "button.custom_minimum_size = Vector2(52.0, 48.0)",
            "button.custom_minimum_size = minimum_size",
            "_add_fit_button(zoom_controls)",
            '_add_filter_button(filter_controls, "✓", MAP_FILTER_VISITED)',
            '_add_filter_button(filter_controls, "○", MAP_FILTER_NOT_VISITED)',
            "marker.mouse_filter = Control.MOUSE_FILTER_PASS",
            "zoom_controls.position = Vector2(max(10.0, map_layer.size.x - FIT_CONTROL_SIZE.x - 10.0), 10.0)",
            "var suppress_next_marker_press := false",
            "marker.gui_input.connect(_on_marker_gui_input)",
            "func _on_marker_gui_input(event: InputEvent) -> void:",
            "if suppress_next_marker_press:",
            "suppress_next_marker_press = true",
        ]:
            self.assertIn(expected, script_text)

    def test_map_panel_filters_markers_by_visit_status(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")

        for expected in [
            'const MAP_FILTER_ALL := "all"',
            'const MAP_FILTER_VISITED := "visited"',
            'const MAP_FILTER_NOT_VISITED := "not_visited"',
            "var map_filter := MAP_FILTER_ALL",
            "func set_map_filter(next_filter: String) -> void:",
            "func _object_matches_filter(object_data: Dictionary) -> bool:",
            "func _is_object_visited(object_data: Dictionary) -> bool:",
            'status_id == "visited" or status_id == "favorite"',
            'return object_data.get("visited", false)',
            'marker.visible = _object_matches_filter(objects[index])',
            "Выбранная точка скрыта фильтром карты",
            "Нет точек для выбранного фильтра",
            '"Все"',
            '"✓"',
            '"○"',
            "Показать посещенные",
            "Показать непосещенные",
        ]:
            self.assertIn(expected, script_text)

    def test_real_map_tiles_follow_up_is_documented(self) -> None:
        doc_text = (ROOT / "docs" / "real-map-tiles-plan.md").read_text(encoding="utf-8")

        for expected in [
            "Real map tiles follow-up",
            "OpenStreetMap",
            "MapLibre",
            "Android",
            "Raster tiles внутри Godot",
            "disk cache",
            "OfflineMapLayer",
            "© OpenStreetMap contributors",
            "feature flag",
        ]:
            self.assertIn(expected, doc_text)

    def test_main_scene_and_controller_wire_map_selection(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")
        main_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        self.assertIn('path="res://scripts/map_panel.gd"', scene_text)
        self.assertIn('name="MapPanel" type="PanelContainer"', scene_text)
        self.assertNotIn("Здесь будет карта объектов", scene_text)

        for expected in [
            'const MapPanelScript := preload("res://scripts/map_panel.gd")',
            "@onready var map_panel: MapPanelScript = %MapPanel",
            "map_panel.set_objects(objects)",
            "map_panel.object_selected.connect(_on_map_object_selected)",
            "func _on_map_object_selected(index: int) -> void:",
            "_select_object(index, false)",
            "map_panel.select_object(index)",
            "object_card.show_object(objects[index], storage_runtime_enabled)",
            "map_panel.set_objects(objects)",
        ]:
            self.assertIn(expected, main_text)


if __name__ == "__main__":
    unittest.main()
