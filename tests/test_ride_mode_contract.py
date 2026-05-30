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
            "var direction_option: OptionButton",
            "var route_view: RideRouteView",
            "var progress_label: Label",
            "var segment_label: Label",
            "var direction_label: Label",
            "var previous_button: Button",
            "var next_button: Button",
            "func show_object(object_data: Dictionary) -> void:",
            "card_button.custom_minimum_size = Vector2(0, 56)",
            "direction_option.custom_minimum_size = Vector2(0, 52)",
            "previous_button.custom_minimum_size = Vector2(0, 56)",
            "next_button.custom_minimum_size = Vector2(0, 56)",
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
            "route_view.show_route(current_object, direction, segments, selected_segment_index)",
        ]:
            self.assertIn(expected, script_text)

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
            'ride_button.pressed.connect(func() -> void: _show_section("ride"))',
            'ride_panel.card_requested.connect(func() -> void: _show_section("card"))',
            "ride_panel.show_object(objects[index])",
            "storage.list_object_stations(object_id)",
            "storage.list_route_directions(object_id)",
            "storage.list_route_segments(direction_id)",
        ]:
            self.assertIn(expected, main_text)

    def test_ride_mode_is_data_driven_not_hardcoded_generic_route(self) -> None:
        panel_text = (ROOT / "scripts" / "ride_panel.gd").read_text(encoding="utf-8")
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

        combined_script_text = panel_text + "\n" + view_text
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

    def test_ride_mode_has_russian_empty_state_and_actions(self) -> None:
        script_text = (ROOT / "scripts" / "ride_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "Поездка",
            "Назад",
            "Дальше",
            "К карточке",
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

    def test_ride_mode_keeps_main_navigation_mobile_touch_targets(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")
        button_block = scene_text.split('name="RideButton" type="Button"', 1)[1].split("[node ", 1)[0]

        self.assertIn("custom_minimum_size = Vector2(116, 48)", button_block)
        self.assertIn("toggle_mode = true", button_block)


if __name__ == "__main__":
    unittest.main()
