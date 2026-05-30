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

        self.assertIn("Здесь будет карта объектов", scene_text)
        self.assertIn("Выбранный объект: пока не выбран", scene_text)

    def test_main_controller_routes_selection_between_sections(self) -> None:
        script_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for section_name in ['"map"', '"list"', '"card"', '"journal"']:
            self.assertIn(section_name, script_text)

        self.assertIn("object_list.object_selected.connect(_on_object_selected)", script_text)
        self.assertIn("_select_object(index, true)", script_text)
        self.assertIn('_show_section("card")', script_text)
        self.assertIn("_update_map_selection(objects[index])", script_text)
        self.assertIn("selected_object_label.text", script_text)

    def test_list_panel_can_update_selection_without_reemitting(self) -> None:
        script_text = (ROOT / "scripts" / "object_list_panel.gd").read_text(encoding="utf-8")

        self.assertIn("func select_visual_object(index: int) -> void:", script_text)
        self.assertIn("object_selected.emit(index)", script_text)


if __name__ == "__main__":
    unittest.main()
