from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RideModeContractTest(unittest.TestCase):
    def test_ride_panel_declares_mobile_route_mode(self) -> None:
        script_text = (ROOT / "scripts" / "ride_panel.gd").read_text(encoding="utf-8")
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        for expected in [
            "class_name RidePanel",
            "signal card_requested",
            "signal back_requested",
            "var direction_option: OptionButton",
            "var ride_game_view: RideGameView",
            "var route_view: RideRouteView",
            "var speed_label: Label",
            "var passenger_label: Label",
            "var score_label: Label",
            "var speed_slider: HSlider",
            "var progress_label: Label",
            "var segment_label: Label",
            "var direction_label: Label",
            "var previous_button: Button",
            "var next_button: Button",
            "func show_object(object_data: Dictionary) -> void:",
            "func set_back_button_text(text: String) -> void:",
            "card_button.custom_minimum_size = Vector2(0, 56)",
            "direction_option.custom_minimum_size = Vector2(0, 52)",
            "previous_button.custom_minimum_size = Vector2(0, 56)",
            "next_button.custom_minimum_size = Vector2(0, 56)",
            "ride_game_view.custom_minimum_size = Vector2(0, 260)",
            "speed_slider.min_value = 0.5",
            "speed_slider.max_value = 2.0",
            "speed_slider.step = 0.25",
            "route_view.custom_minimum_size = Vector2(0, 170)",
        ]:
            self.assertIn(expected, script_text)

        for expected in [
            'name="RideSection"',
            'name="RideButton" type="Button"',
            'text = "Поездка"',
            'name="RidePanel" type="PanelContainer"',
            'path="res://scripts/ride_panel.gd"',
        ]:
            self.assertIn(expected, scene_text)

    def test_ride_mode_uses_existing_route_data_contract(self) -> None:
        script_text = (ROOT / "scripts" / "ride_panel.gd").read_text(encoding="utf-8")
        game_text = (ROOT / "scripts" / "ride_game_view.gd").read_text(encoding="utf-8")
        view_text = (ROOT / "scripts" / "ride_route_view.gd").read_text(encoding="utf-8")
        main_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for expected in [
            '_array_field(current_object, "route_directions")',
            'current_object.get("route_segments_by_direction", {})',
            '_array_field(current_object, "stations")',
            'direction.get("from_station_id", "")',
            'direction.get("to_station_id", "")',
            'segment.get("from_station_id", "")',
            'segment.get("to_station_id", "")',
            'segment.get("direction_label", "")',
            'segment.get("note", "")',
            '"%s → %s"',
            '"Шаг %d из %d"',
            "ride_game_view.setup_route(current_object, direction, segments, selected_segment_index)",
            "route_view.show_route(current_object, direction, segments, selected_segment_index)",
        ]:
            self.assertIn(expected, script_text)

        for expected in [
            "class_name RideGameView",
            "signal ride_state_changed(state: Dictionary)",
            'preload("res://assets/sprites/ride/ride_sprite_sheet.png")',
            "const SPRITE_CABIN_RED := Rect2",
            "const SPRITE_LOWER_STATION := Rect2",
            "const SPRITE_UPPER_STATION := Rect2",
            "const SPRITE_TOWER_TALL := Rect2",
            "const SPRITE_TOWER_SHORT := Rect2",
            "func setup_route(object_data: Dictionary, direction: Dictionary, segments: Array, segment_index: int) -> void:",
            '_station_for_segment_end("from_station_id")',
            '_station_for_segment_end("to_station_id")',
            'active_segment.get(key, "")',
            '_array_field(current_object, "stations")',
            "func advance_ride(delta: float) -> void:",
            "func set_speed_multiplier(value: float) -> void:",
            "func state_snapshot() -> Dictionary:",
            "passengers_onboard",
            "delivered_passengers",
            "smoothness_score",
            "func _draw_sprite(source: Rect2, destination: Rect2) -> void:",
            "draw_texture_rect_region(RIDE_SPRITE_SHEET, destination, source)",
            "func _support_points(lower_point: Vector2, upper_point: Vector2) -> Array[Vector2]:",
        ]:
            self.assertIn(expected, game_text)

        for expected in [
            "class_name RideRouteView",
            "func show_route(object_data: Dictionary, direction: Dictionary, segments: Array, segment_index: int) -> void:",
            "var current_segments: Array = []",
            "current_segment_index",
            "func _ordered_station_ids() -> Array[String]:",
            'segment.get("from_station_id", "")',
            'segment.get("to_station_id", "")',
            '_array_field(current_object, "stations")',
            'station.get("latitude", 0.0)',
            'station.get("longitude", 0.0)',
            "_coordinate_station_points",
            "_draw_current_segment",
            "draw_colored_polygon",
        ]:
            self.assertIn(expected, view_text)

        for expected in [
            'const RidePanelScript := preload("res://scripts/ride_panel.gd")',
            "@onready var ride_panel: RidePanelScript = %RidePanel",
            "@onready var ride_button: Button = %RideButton",
            "@onready var ride_section: VBoxContainer = %RideSection",
            '"ride": ride_section',
            '"ride": ride_button',
            'ride_button.pressed.connect(func() -> void: _open_ride_from_context(active_section_name))',
            'object_mode_panel.ride_requested.connect(func() -> void: _open_ride_from_context("object_mode"))',
            "ride_panel.back_requested.connect(_on_ride_back_requested)",
            "var ride_return_section_name := \"card\"",
            "func _open_ride_from_context(return_section_name: String) -> void:",
            "func _on_ride_back_requested() -> void:",
            "ride_panel.show_object(objects[index])",
            "storage.list_object_stations(object_id)",
            "storage.list_route_directions(object_id)",
            "storage.list_route_segments(direction_id)",
        ]:
            self.assertIn(expected, main_text)

    def test_ride_mode_is_data_driven_not_hardcoded_generic_route(self) -> None:
        panel_text = (ROOT / "scripts" / "ride_panel.gd").read_text(encoding="utf-8")
        game_text = (ROOT / "scripts" / "ride_game_view.gd").read_text(encoding="utf-8")
        view_text = (ROOT / "scripts" / "ride_route_view.gd").read_text(encoding="utf-8")
        seed_text = (ROOT / "scripts" / "storage" / "seeds" / "demo_objects.sql").read_text(encoding="utf-8")

        for expected in [
            "'berlin-gaerten-der-welt-station-kienbergpark'",
            "'berlin-gaerten-der-welt-station-wolkenhain'",
            "'berlin-gaerten-der-welt-station-gaerten-der-welt'",
            "'berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten'",
            "'berlin-gaerten-der-welt-segment-kienbergpark-wolkenhain'",
            "'berlin-gaerten-der-welt-segment-wolkenhain-gaerten'",
            "'вверх к Волькенхайну'",
            "'вниз к Садам мира'",
        ]:
            self.assertIn(expected, seed_text)

        combined_script_text = panel_text + "\n" + view_text + "\n" + game_text
        for forbidden in [
            "Киенбергпарк",
            "Волькенхайн",
            "Сады мира",
            "berlin-gaerten-der-welt-station",
            "randf",
            "randi",
            "shuffle",
            "Станция 1",
            "Станция 2",
            "Станция 3",
        ]:
            self.assertNotIn(forbidden, combined_script_text)

    def test_ride_art_is_reusable_and_documented(self) -> None:
        game_text = (ROOT / "scripts" / "ride_game_view.gd").read_text(encoding="utf-8")

        for asset_path in [
            ROOT / "assets" / "sprites" / "ride" / "ride_sprite_sheet.png",
            ROOT / "asset_sources" / "ride" / "ride_sprite_sheet_source_chroma.png",
        ]:
            self.assertTrue(asset_path.is_file(), f"Missing ride asset: {asset_path}")
            self.assertGreater(asset_path.stat().st_size, 100_000, f"Ride asset looks too small: {asset_path}")
        self.assertTrue((ROOT / "asset_sources" / "ride" / ".gdignore").is_file())

        for expected in [
            "cabin_point - grip_offset",
            "lower_point.lerp(upper_point, 0.36)",
            "lower_point.lerp(upper_point, 0.66)",
            "anchor - sheave_offset",
            "_draw_supports(support_points)",
            "return Vector2(rect.size.x * LOWER_STATION_RATIO, rect.size.y * 0.50)",
            "label_panel := Rect2",
        ]:
            self.assertIn(expected, game_text)

        self.assertTrue((ROOT / "scripts" / "capture_ride_art_screenshot.gd").is_file())

        for forbidden in [
            "var width := 68.0",
            "draw_circle(trunk_bottom",
            "draw_rect(body, Color",
            "body.position + Vector2(7, 7)",
        ]:
            self.assertNotIn(forbidden, game_text)

    def test_ride_mode_has_russian_empty_state_and_actions(self) -> None:
        script_text = (ROOT / "scripts" / "ride_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "Поездка",
            "Назад",
            "Дальше",
            "К карточке",
            "Начать заново",
            "Скорость",
            "Пассажиры",
            "Итог",
            "плавность",
            "доставлено",
            "Объект не выбран",
            "Выберите объект с маршрутом, чтобы открыть поездку.",
            "Для этого объекта маршрут поездки пока не добавлен.",
            "Откройте карточку объекта, чтобы посмотреть общую информацию.",
            "Шаг",
            "Откуда → куда",
            "Направление",
            "маршрут не выбран",
            "нет данных маршрута",
        ]:
            self.assertIn(expected, script_text)

        for forbidden in ["RouteDirection", "RouteSegment", "ObjectStation", "SQLite", "res://", "user://", "MVP"]:
            self.assertNotIn(forbidden, script_text)

    def test_map_object_flow_can_open_ride_and_return_to_map_context(self) -> None:
        script_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for expected in [
            "var map_ride_button: Button = null",
            "const MAP_RIDE_BUTTON_SIZE := Vector2(152.0, 56.0)",
            "const MAP_RIDE_BUTTON_MARGIN := Vector2(14.0, 84.0)",
            '_create_map_ride_button()',
            'map_ride_button.name = "MapRideButton"',
            'map_ride_button.text = "Поездка"',
            'map_ride_button.pressed.connect(func() -> void: _open_ride_from_context("map"))',
            'map_ride_button.visible = active_section_name == "map" and selected_index >= 0',
            '"Открыть пустое состояние поездки: маршрут пока не добавлен"',
            'if return_section_name == "map":',
            "_capture_map_return_state()",
            'return "К карте"',
            "_show_section(ride_return_section_name)",
            "func _object_has_playable_route(object_data: Dictionary) -> bool:",
            'object_data.get("route_directions") is Array',
            'object_data.get("route_segments_by_direction", {})',
        ]:
            self.assertIn(expected, script_text)

    def test_ride_mode_keeps_main_navigation_mobile_touch_targets(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")
        button_block = scene_text.split('name="RideButton" type="Button"', 1)[1].split("[node ", 1)[0]

        self.assertIn("custom_minimum_size = Vector2(116, 48)", button_block)
        self.assertIn("toggle_mode = true", button_block)


if __name__ == "__main__":
    unittest.main()
