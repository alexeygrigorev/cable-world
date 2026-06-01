from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ObjectListContractTest(unittest.TestCase):
    def test_list_scene_has_filter_controls_and_empty_state(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        for node_name in [
            "SearchLineEdit",
            "CountryFilterOption",
            "TypeFilterOption",
            "VisitFilterOption",
            "ListEmptyStateLabel",
        ]:
            self.assertIn(f'name="{node_name}"', scene_text)
            self.assertIn("unique_name_in_owner = true", scene_text)

        for visible_text in [
            "Атлас объектов",
            "Название, город или страна",
            "Все страны",
            "Все виды транспорта",
            "Все объекты",
            "Еще не посещали",
            "Уже посещали",
            "По этому поиску и фильтрам ничего не нашлось",
        ]:
            self.assertIn(visible_text, scene_text)

    def test_list_panel_filters_visible_objects_before_emitting_selection(self) -> None:
        script_text = (ROOT / "scripts" / "object_list_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "const FILTER_VISITED",
            "const FILTER_NOT_VISITED",
            "var visible_object_indices: Array[int]",
            'var search_query: String = ""',
            "func set_filters(next_type_filter: String, next_visit_filter: String, next_country_filter: String = FILTER_ALL) -> void:",
            "func set_search_query(next_search_query: String) -> void:",
            "func get_transport_types() -> Array[String]:",
            "func get_countries() -> Array[String]:",
            "func _matches_filters(object_data: Dictionary) -> bool:",
            "func _matches_search(object_data: Dictionary) -> bool:",
            "func _is_object_visited(object_data: Dictionary) -> bool:",
            "func _location_text(object_data: Dictionary) -> String:",
            "func _visit_status_text(object_data: Dictionary) -> String:",
            "func _operational_status_text(object_data: Dictionary) -> String:",
            "func _row_type_text(object_data: Dictionary) -> String:",
            "func _object_icon_texture(object_data: Dictionary) -> Texture2D:",
            "func _draw_transport_pictogram(image: Image, family: String) -> void:",
            "SQLiteStorageAdapter.status_is_visited",
            "SQLiteStorageAdapter.status_title",
            "SQLiteStorageAdapter.operational_status_title",
            'object_data.get("city", "")',
            "object_selected.emit(object_index)",
            "Пока нет объектов.",
            "изменить запрос, страну, тип или статус",
            "func _add_row(object_data: Dictionary, object_index: int, visible_index: int) -> void:",
            "name_label.text = _compact_name",
            "type_label.text = _row_type_text(object_data)",
            "meta_label.text = _row_meta_text(object_data)",
            'open_hint.text = "›"',
            "const LIST_ICON_SIZE := Vector2i(44, 44)",
            "const ROW_NUMBER_WIDTH := 42",
            "const ROW_NAME_MAX_CHARS := 34",
            "const ROW_TYPE_MAX_CHARS := 32",
            "const ROW_META_MAX_CHARS := 42",
            "row.custom_minimum_size = Vector2(0, 76)",
            'ledger_number.text = "№%02d" % (visible_index + 1)',
            "ledger_rule.color = ATLAS_LEDGER_RULE_COLOR",
            "func _trim_for_row(text: String, max_chars: int) -> String:",
            "func _sync_row_visual_state(ledger_number: Label, type_label: Label, meta_label: Label, open_hint: Label, name_label: Label, selected: bool) -> void:",
            "func _empty_state_style() -> StyleBoxFlat:",
            "row.pressed.connect(func() -> void: _on_row_pressed(object_index))",
        ]:
            self.assertIn(expected, script_text)

    def test_list_panel_has_touch_scroll_safety_contract(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")
        script_text = (ROOT / "scripts" / "object_list_panel.gd").read_text(encoding="utf-8")

        object_list_block = scene_text.split('name="ObjectList" type="ScrollContainer"', 1)[1].split("[node ", 1)[0]
        content_scroll_block = scene_text.split('name="ContentScroll" type="ScrollContainer"', 1)[1].split("[node ", 1)[0]

        for expected in [
            "size_flags_horizontal = 3",
            "size_flags_vertical = 3",
            "custom_minimum_size = Vector2(0, 300)",
            "horizontal_scroll_mode = 0",
        ]:
            self.assertIn(expected, object_list_block)

        self.assertIn("horizontal_scroll_mode = 0", content_scroll_block)
        self.assertIn("scroll_deadzone = 18", content_scroll_block)

        for expected in [
            "const TOUCH_DRAG_THRESHOLD := 18.0",
            "const SELECTION_SUPPRESS_MSEC := 250",
            "const TAP_SELECTION_DELAY_SEC := 0.12",
            "func _gui_input(event: InputEvent) -> void:",
            "event is InputEventScreenDrag",
            "suppress_selection_until_msec",
            "visual_selection_refreshing",
            "await get_tree().create_timer(TAP_SELECTION_DELAY_SEC).timeout",
            "if touch_is_dragging or Time.get_ticks_msec() < suppress_selection_until_msec:",
        ]:
            self.assertIn(expected, script_text)

    def test_list_section_has_left_safe_area_without_horizontal_overflow(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")
        script_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        list_section_block = scene_text.split('name="ListSection" type="VBoxContainer"', 1)[1].split("[node ", 1)[0]
        list_safe_area_block = scene_text.split('name="ListSafeArea" type="MarginContainer"', 1)[1].split("[node ", 1)[0]
        list_content_block = scene_text.split('name="ListContent" type="VBoxContainer"', 1)[1].split("[node ", 1)[0]
        object_list_viewport_path = (
            'parent="Отступы/Оболочка/Содержимое/ContentViewport/ContentScroll/Секции/ListSection/'
            'ListSafeArea/ListContent"'
        )
        object_list_path = (
            'parent="Отступы/Оболочка/Содержимое/ContentViewport/ContentScroll/Секции/ListSection/'
            'ListSafeArea/ListContent/ObjectListViewport"'
        )

        self.assertIn("theme_override_constants/separation = 0", list_section_block)
        for expected in [
            "unique_name_in_owner = true",
            "size_flags_horizontal = 3",
            "theme_override_constants/margin_left = 12",
            "theme_override_constants/margin_top = 14",
            "theme_override_constants/margin_right = 12",
            "theme_override_constants/margin_bottom = 14",
        ]:
            self.assertIn(expected, list_safe_area_block)
        self.assertIn("theme_override_constants/separation = 8", list_content_block)
        filters_block = scene_text.split('name="ФильтрыСписка" type="GridContainer"', 1)[1].split("[node ", 1)[0]
        title_block = scene_text.split('name="СписокЗаголовок" type="Label"', 1)[1].split("[node ", 1)[0]
        self.assertIn("columns = 1", filters_block)
        self.assertIn("theme_override_colors/font_color", title_block)
        self.assertIn(object_list_viewport_path, scene_text)
        self.assertIn(object_list_path, scene_text)

        for expected in [
            "const CONTENT_WIDTH_GUARD := 2.0",
            "@onready var content_scroll: ScrollContainer = %ContentScroll",
            "var content_width: float = max(0.0, content_viewport.size.x - CONTENT_WIDTH_GUARD)",
            "sections_container.custom_minimum_size.x = content_width",
            "section.custom_minimum_size.x = content_width",
            "content_scroll.scroll_horizontal = 0",
            'content_scroll.set_deferred("scroll_horizontal", 0)',
            "_sync_content_width_after_layout()",
            'call_deferred("_sync_content_width")',
            'call_deferred("_reset_content_horizontal_scroll")',
            "await get_tree().process_frame",
            "content_viewport.position.x = 0.0",
            "content_scroll.position.x = 0.0",
            "sections_container.position.x = 0.0",
            "section.position.x = 0.0",
            "func _sync_list_ledger_width(content_width: float) -> void:",
            "list_safe_area.size_flags_horizontal = Control.SIZE_SHRINK_CENTER",
            "list_safe_area.custom_minimum_size.x = ledger_width",
        ]:
            self.assertIn(expected, script_text)

    def test_main_screen_wires_filters_and_local_data_source_hook(self) -> None:
        script_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for expected in [
            "@onready var search_line_edit: LineEdit = %SearchLineEdit",
            "@onready var country_filter_option: OptionButton = %CountryFilterOption",
            "search_line_edit.text_changed.connect(_on_search_changed)",
            "type_filter_option.item_selected.connect(_on_filter_changed)",
            "visit_filter_option.item_selected.connect(_on_filter_changed)",
            "country_filter_option.item_selected.connect(_on_filter_changed)",
            "object_list.set_empty_state_label(list_empty_state_label)",
            "object_list.set_filters(type_filter, visit_filter, country_filter)",
            "object_list.set_search_query(next_text)",
            'country_filter_option.add_item("Все страны")',
            "for country in object_list.get_countries():",
            "func _load_objects_from_local_source() -> Array[Dictionary]:",
            "return DemoCatalog.get_objects()",
        ]:
            self.assertIn(expected, script_text)

    def test_country_filter_has_seed_countries_available_from_demo_catalog(self) -> None:
        demo_catalog_text = (ROOT / "scripts" / "demo_catalog.gd").read_text(encoding="utf-8")
        europe_text = (ROOT / "scripts" / "demo_catalog_europe.gd").read_text(encoding="utf-8")
        russia_text = (ROOT / "scripts" / "demo_catalog_russia.gd").read_text(encoding="utf-8")

        self.assertIn("for country in object_list.get_countries():", (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8"))
        self.assertIn("countries.sort()", (ROOT / "scripts" / "object_list_panel.gd").read_text(encoding="utf-8"))
        self.assertIn("DemoCatalogEuropeScript.get_objects()", demo_catalog_text)
        self.assertIn("DemoCatalogRussiaScript.get_objects()", demo_catalog_text)

        for country in ["Португалия", "Франция", "Италия", "Чехия", "Словакия", "Польша", "Россия"]:
            with self.subTest(country=country):
                self.assertIn(f'"country": "{country}"', europe_text + russia_text)


if __name__ == "__main__":
    unittest.main()
