from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ObjectListContractTest(unittest.TestCase):
    def test_list_scene_has_filter_controls_and_empty_state(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        for node_name in [
            "TypeFilterOption",
            "VisitFilterOption",
            "ListEmptyStateLabel",
        ]:
            self.assertIn(f'name="{node_name}"', scene_text)
            self.assertIn("unique_name_in_owner = true", scene_text)

        for visible_text in [
            "Тип транспорта",
            "Статус посещения",
            "Все виды транспорта",
            "Все объекты",
            "Еще не посещали",
            "Уже посещали",
            "По таким фильтрам ничего не нашлось",
        ]:
            self.assertIn(visible_text, scene_text)

    def test_list_panel_filters_visible_objects_before_emitting_selection(self) -> None:
        script_text = (ROOT / "scripts" / "object_list_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "const FILTER_VISITED",
            "const FILTER_NOT_VISITED",
            "var visible_object_indices: Array[int]",
            "func set_filters(next_type_filter: String, next_visit_filter: String) -> void:",
            "func get_transport_types() -> Array[String]:",
            "func _matches_filters(object_data: Dictionary) -> bool:",
            "func _is_object_visited(object_data: Dictionary) -> bool:",
            "func _visit_status_text(object_data: Dictionary) -> String:",
            "SQLiteStorageAdapter.status_is_visited",
            "SQLiteStorageAdapter.status_title",
            "object_selected.emit(visible_object_indices[index])",
            "Пока нет объектов.",
        ]:
            self.assertIn(expected, script_text)

    def test_main_screen_wires_filters_and_local_data_source_hook(self) -> None:
        script_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for expected in [
            "type_filter_option.item_selected.connect(_on_filter_changed)",
            "visit_filter_option.item_selected.connect(_on_filter_changed)",
            "object_list.set_empty_state_label(list_empty_state_label)",
            "object_list.set_filters(type_filter, visit_filter)",
            "func _load_objects_from_local_source() -> Array[Dictionary]:",
            "return DemoCatalog.get_objects()",
        ]:
            self.assertIn(expected, script_text)


if __name__ == "__main__":
    unittest.main()
