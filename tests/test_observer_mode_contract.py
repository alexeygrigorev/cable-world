from pathlib import Path
import sqlite3
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "scripts" / "storage" / "migrations"
DEMO_SEED = ROOT / "scripts" / "storage" / "seeds" / "demo_objects.sql"


class ObserverModeContractTest(unittest.TestCase):
    def test_scene_exposes_observer_screen_for_mobile_navigation(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        for expected in [
            'name="ObserverButton" type="Button"',
            'text = "Наблюдатель"',
            'name="ObserverSection" type="VBoxContainer"',
            'name="ObserverPanel" type="PanelContainer"',
            'path="res://scripts/observer_panel.gd"',
            "custom_minimum_size = Vector2(144, 48)",
            "custom_minimum_size = Vector2(0, 420)",
        ]:
            self.assertIn(expected, scene_text)

    def test_main_controller_routes_selected_object_to_observer(self) -> None:
        script_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for expected in [
            "@onready var observer_panel: ObserverPanel = %ObserverPanel",
            "@onready var observer_button: Button = %ObserverButton",
            "@onready var observer_section: VBoxContainer = %ObserverSection",
            '"observer": observer_section',
            '"observer": observer_button',
            'observer_button.pressed.connect(func() -> void: _show_section("observer"))',
            'object_card.observer_requested.connect(func() -> void: _show_section("observer"))',
            'observer_panel.back_requested.connect(func() -> void: _show_section("card"))',
            "observer_panel.show_object(objects[index])",
        ]:
            self.assertIn(expected, script_text)

    def test_card_has_large_observer_entrypoint(self) -> None:
        card_text = (ROOT / "scripts" / "object_card_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "signal observer_requested",
            "var observer_button: Button",
            'observer_button.text = "Открыть наблюдателя"',
            'observer_button.tooltip_text = "Показать выбранный объект как схему со стороны."',
            "observer_button.custom_minimum_size = Vector2(0, 52)",
            "observer_button.pressed.connect(_on_observer_pressed)",
            "observer_requested.emit()",
        ]:
            self.assertIn(expected, card_text)

    def test_observer_panel_uses_route_data_and_russian_states(self) -> None:
        panel_text = (ROOT / "scripts" / "observer_panel.gd").read_text(encoding="utf-8")
        scheme_text = (ROOT / "scripts" / "observer_scheme_view.gd").read_text(encoding="utf-8")

        for expected in [
            "class_name ObserverPanel",
            "К карточке объекта",
            "Наблюдатель",
            "Вид: линия",
            "Вид: станции",
            "Сменить направление",
            "Точка наблюдения",
            "Отрезки",
            "_segment_labels_text",
            "Для наблюдения пока нет схемы маршрута.",
            "Выберите объект с детальной схемой маршрута",
            '"stations"',
            '"route_directions"',
            '"route_segments_by_direction"',
            "direction_label",
            "custom_minimum_size = Vector2(0, 56)",
            "button.custom_minimum_size = Vector2(0, 56)",
        ]:
            self.assertIn(expected, panel_text + scheme_text)

        for forbidden in ["3D", "photogrammetry", "MVP", "RouteSegment", "ObjectStation"]:
            self.assertNotIn(forbidden, panel_text)
            self.assertNotIn(forbidden, scheme_text)

    def test_observer_mobile_width_and_wrap_contract(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")
        panel_text = (ROOT / "scripts" / "observer_panel.gd").read_text(encoding="utf-8")
        scheme_text = (ROOT / "scripts" / "observer_scheme_view.gd").read_text(encoding="utf-8")

        observer_section = scene_text.split('name="ObserverSection" type="VBoxContainer"', 1)[1].split('[node name="MemorySection"', 1)[0]
        for expected in [
            "size_flags_horizontal = 3",
            'name="НаблюдательЗаголовок" type="Label"',
            "autowrap_mode = 3",
            'name="ObserverPanel" type="PanelContainer"',
            "custom_minimum_size = Vector2(0, 420)",
        ]:
            self.assertIn(expected, observer_section)

        for expected in [
            "station_buttons = GridContainer.new()",
            "station_buttons.columns = 1",
            "button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART",
            "summary_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL",
            "title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL",
            "controls.columns = 1",
        ]:
            self.assertIn(expected, panel_text)

        for expected in [
            "size_flags_horizontal = Control.SIZE_EXPAND_FILL",
            "_route_rect(drawing_rect)",
            "label_width: float = min(132.0",
            "drawing_rect.end.x - label_width",
        ]:
            self.assertIn(expected, scheme_text)

    def test_gaerten_der_welt_seed_has_concrete_observer_route(self) -> None:
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
            SELECT direction_label
            FROM route_segments
            WHERE route_direction_id = 'berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten'
            ORDER BY segment_order
            """
        ).fetchall()
        self.assertEqual(
            [label for (label,) in segments],
            ["вверх к Волькенхайну", "вниз к Садам мира"],
        )


if __name__ == "__main__":
    unittest.main()
