from pathlib import Path
import sqlite3
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "scripts" / "storage" / "migrations"
DEMO_SEED = ROOT / "scripts" / "storage" / "seeds" / "demo_objects.sql"


class ObjectModeUiContractTest(unittest.TestCase):
    def test_scene_exposes_object_mode_for_mobile_navigation(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")
        project_text = (ROOT / "project.godot").read_text(encoding="utf-8")

        for expected in [
            "window/size/viewport_width=390",
            "window/size/viewport_height=844",
        ]:
            self.assertIn(expected, project_text)

        for expected in [
            'name="ObjectModeButton" type="Button"',
            'text = "Объект"',
            "custom_minimum_size = Vector2(144, 48)",
            'name="ObjectModeSection" type="VBoxContainer"',
            'name="ObjectModePanel" type="PanelContainer"',
            'path="res://scripts/object_mode_panel.gd"',
            "custom_minimum_size = Vector2(0, 420)",
            'text = "Режим объекта"',
        ]:
            self.assertIn(expected, scene_text)

    def test_main_and_card_route_selected_object_to_object_mode(self) -> None:
        main_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")
        card_text = (ROOT / "scripts" / "object_card_panel.gd").read_text(encoding="utf-8")

        for expected in [
            'const ObjectModePanelScript := preload("res://scripts/object_mode_panel.gd")',
            "@onready var object_mode_panel: ObjectModePanelScript = %ObjectModePanel",
            "@onready var object_mode_button: Button = %ObjectModeButton",
            "@onready var object_mode_section: VBoxContainer = %ObjectModeSection",
            '"object_mode": object_mode_section',
            '"object_mode": object_mode_button',
            'object_mode_button.pressed.connect(func() -> void: _show_section("object_mode"))',
            'object_card.object_mode_requested.connect(func() -> void: _show_section("object_mode"))',
            'object_mode_panel.card_requested.connect(func() -> void: _show_section("card"))',
            'object_mode_panel.ride_requested.connect(func() -> void: _show_section("ride"))',
            "object_mode_panel.show_object(objects[index])",
            "_ensure_route_details(index)",
            "storage.list_object_stations(object_id)",
            "storage.list_route_directions(object_id)",
            "storage.list_route_segments(direction_id)",
        ]:
            self.assertIn(expected, main_text)

        for expected in [
            "signal object_mode_requested",
            "var object_mode_button: Button",
            'object_mode_button.text = "Открыть режим объекта"',
            'object_mode_button.tooltip_text = "Показать схему станций и отрезков выбранного объекта."',
            "object_mode_button.custom_minimum_size = Vector2(0, 52)",
            "object_mode_button.pressed.connect(_on_object_mode_pressed)",
            "object_mode_requested.emit()",
        ]:
            self.assertIn(expected, card_text)

    def test_object_mode_panel_is_data_driven_and_has_russian_empty_states(self) -> None:
        panel_text = (ROOT / "scripts" / "object_mode_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "class_name ObjectModePanel",
            "signal card_requested",
            "signal ride_requested",
            "Режим объекта",
            "К карточке",
            "Открыть поездку",
            "Станции и точки",
            "Объект не выбран",
            "Выберите объект, чтобы открыть детальную схему.",
            "Для этого объекта пока нет станций схемы.",
            "Для этого объекта пока нет направления поездки.",
            "Для этого направления пока нет отрезков маршрута.",
            "Отрезки маршрута",
            '"stations"',
            '"route_directions"',
            '"route_segments_by_direction"',
            'direction.get("from_station_id", "")',
            'direction.get("to_station_id", "")',
            'segment.get("from_station_id", "")',
            'segment.get("to_station_id", "")',
            'segment.get("direction_label", "")',
            "scheme_view.show_object(current_object, selected_direction_id, selected_station_id)",
        ]:
            self.assertIn(expected, panel_text)

        for forbidden in [
            "Киенбергпарк",
            "Волькенхайн",
            "Сады мира",
            "berlin-gaerten-der-welt",
            "RouteDirection",
            "RouteSegment",
            "ObjectStation",
            "SQLite",
            "MVP",
        ]:
            self.assertNotIn(forbidden, panel_text)

    def test_object_mode_touch_targets_are_large_enough(self) -> None:
        panel_text = (ROOT / "scripts" / "object_mode_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "back_button.custom_minimum_size = Vector2(0, 56)",
            "direction_option.custom_minimum_size = Vector2(0, 52)",
            "ride_button.custom_minimum_size = Vector2(0, 56)",
            "button.custom_minimum_size = Vector2(0, 56)",
            "button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART",
            "station_buttons.columns = 1",
            "scheme_view.custom_minimum_size = Vector2(0, 280)",
        ]:
            self.assertIn(expected, panel_text)

    def test_gaerten_der_welt_route_data_drives_visible_station_names(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.execute("PRAGMA foreign_keys = ON")
        for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
            connection.executescript(migration.read_text(encoding="utf-8"))
        connection.executescript(DEMO_SEED.read_text(encoding="utf-8"))

        stations = connection.execute(
            """
            SELECT title
            FROM object_stations
            WHERE transport_object_id = 'berlin-gaerten-der-welt'
            ORDER BY sort_order
            """
        ).fetchall()
        self.assertEqual(
            [title for (title,) in stations],
            ["Киенбергпарк", "Волькенхайн", "Сады мира"],
        )

        segments = connection.execute(
            """
            SELECT from_station_id, to_station_id, direction_label
            FROM route_segments
            WHERE route_direction_id = 'berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten'
            ORDER BY segment_order
            """
        ).fetchall()
        self.assertEqual(
            [label for (_, _, label) in segments],
            ["вверх к Волькенхайну", "вниз к Садам мира"],
        )


if __name__ == "__main__":
    unittest.main()
