from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AppShellContractTest(unittest.TestCase):
    def test_main_scene_declares_mvp_sections_and_navigation(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        for node_name in ["MapSection", "ListSection", "CardSection", "JournalSection"]:
            self.assertIn(f'name="{node_name}"', scene_text)
            self.assertIn("unique_name_in_owner = true", scene_text)

        for button_name, button_text in {
            "MapButton": "Карта",
            "ListButton": "Список",
            "CardButton": "Карточка",
            "JournalButton": "Журнал",
        }.items():
            self.assertIn(f'name="{button_name}" type="Button"', scene_text)
            self.assertIn(f'text = "{button_text}"', scene_text)

        self.assertIn('name="MapPanel" type="PanelContainer"', scene_text)
        self.assertIn('path="res://scripts/map_panel.gd"', scene_text)
        self.assertIn("Выбранный объект: пока не выбран", scene_text)

    def test_main_scene_declares_orientation_setting_in_russian(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        self.assertIn('name="OrientationOption" type="OptionButton"', scene_text)
        for text in ["Ориентация", "Как в системе", "Вертикальная", "Горизонтальная"]:
            self.assertIn(f'text = "{text}"', scene_text)

    def test_main_controller_routes_selection_between_sections(self) -> None:
        script_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for section_name in ['"map"', '"list"', '"card"', '"journal"']:
            self.assertIn(section_name, script_text)

        self.assertIn("object_list.object_selected.connect(_on_object_selected)", script_text)
        self.assertIn("map_panel.object_selected.connect(_on_map_object_selected)", script_text)
        self.assertIn("_select_object(index, true)", script_text)
        self.assertIn("_select_object(index, false)", script_text)
        self.assertIn('_show_section("card")', script_text)
        self.assertIn("map_panel.select_object(index)", script_text)
        self.assertIn("_update_map_selection(objects[index])", script_text)
        self.assertIn("selected_object_label.text", script_text)

    def test_main_controller_persists_and_applies_orientation_setting(self) -> None:
        script_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")
        settings_text = (ROOT / "scripts" / "app_settings.gd").read_text(encoding="utf-8")

        self.assertIn("@onready var orientation_option: OptionButton = %OrientationOption", script_text)
        self.assertIn("orientation_option.item_selected.connect(_on_orientation_selected)", script_text)
        self.assertIn("app_settings.save_orientation(orientation_id)", script_text)
        self.assertIn("DisplayServer.screen_set_orientation", script_text)
        self.assertIn('SETTINGS_PATH := "user://settings.cfg"', settings_text)
        self.assertIn("ConfigFile.new()", settings_text)
        for text in ["Как в системе", "Вертикальная", "Горизонтальная"]:
            self.assertIn(text, settings_text)

    def test_list_panel_can_update_selection_without_reemitting(self) -> None:
        script_text = (ROOT / "scripts" / "object_list_panel.gd").read_text(encoding="utf-8")

        self.assertIn("func select_visual_object(index: int) -> void:", script_text)
        self.assertIn("object_selected.emit(index)", script_text)


if __name__ == "__main__":
    unittest.main()
