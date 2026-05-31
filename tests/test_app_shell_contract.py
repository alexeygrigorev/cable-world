from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AppShellContractTest(unittest.TestCase):
    def test_main_scene_declares_mvp_sections_and_navigation(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        for node_name in [
            "MapSection",
            "ListSection",
            "CardSection",
            "CollectionSection",
            "JournalSection",
            "MemorySection",
            "RideSection",
            "ObserverSection",
            "ObjectModeSection",
            "SettingsSection",
        ]:
            self.assertIn(f'name="{node_name}"', scene_text)
            self.assertIn("unique_name_in_owner = true", scene_text)

        for button_name, button_text in {
            "MapButton": "Карта",
            "ListButton": "Список",
            "CardButton": "Карточка",
            "CollectionButton": "Коллекция",
            "JournalButton": "Журнал",
            "MemoryButton": "Воспоминание",
            "RideButton": "Поездка",
            "ObserverButton": "Наблюдатель",
            "ObjectModeButton": "Объект",
            "SettingsButton": "Настройки",
        }.items():
            self.assertIn(f'name="{button_name}" type="Button"', scene_text)
            self.assertIn(f'text = "{button_text}"', scene_text)

        self.assertIn('name="MapPanel" type="PanelContainer"', scene_text)
        self.assertIn('name="MemoryPanel" type="PanelContainer"', scene_text)
        self.assertIn('path="res://scripts/map_panel.gd"', scene_text)
        self.assertIn('path="res://scripts/memory_panel.gd"', scene_text)
        self.assertIn("Выбрано: пока нет", scene_text)

    def test_main_scene_uses_mobile_readable_theme_and_touch_targets(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")
        project_text = (ROOT / "project.godot").read_text(encoding="utf-8")

        for expected in [
            "window/size/viewport_width=390",
            "window/size/viewport_height=844",
            'window/stretch/mode="canvas_items"',
            'window/stretch/aspect="expand"',
        ]:
            self.assertIn(expected, project_text)

        for expected in [
            'SubResource("Theme_mobile_touch")',
            "default_font_size = 18",
            "Button/font_sizes/font_size = 18",
            'name="НавигацияПрокрутка" type="ScrollContainer"',
            'name="Навигация" type="HBoxContainer"',
            'name="CurrentSectionLabel" type="Label"',
            'text = "Раздел: Карта"',
            'name="ContentScroll" type="ScrollContainer"',
            "horizontal_scroll_mode = 0",
            "horizontal_scroll_mode = 1",
        ]:
            self.assertIn(expected, scene_text)

        for button_name in ["MapButton", "ListButton"]:
            button_block = scene_text.split(f'name="{button_name}" type="Button"', 1)[1].split("[node ", 1)[0]
            self.assertIn("custom_minimum_size = Vector2(0, 48)", button_block)
            self.assertIn("size_flags_horizontal = 3", button_block)
            self.assertNotIn("visible = false", button_block)

        for button_name in ["CardButton", "CollectionButton", "JournalButton", "RideButton", "SettingsButton"]:
            button_block = scene_text.split(f'name="{button_name}" type="Button"', 1)[1].split("[node ", 1)[0]
            self.assertIn("custom_minimum_size = Vector2(116, 48)", button_block)
            self.assertIn("visible = false", button_block)

        for button_name in ["MemoryButton", "ObserverButton", "ObjectModeButton"]:
            button_block = scene_text.split(f'name="{button_name}" type="Button"', 1)[1].split("[node ", 1)[0]
            self.assertIn("custom_minimum_size = Vector2(144, 48)", button_block)
            self.assertIn("visible = false", button_block)

        for control_name in ["OrientationOption", "SearchLineEdit", "CountryFilterOption", "TypeFilterOption", "VisitFilterOption"]:
            control_block = scene_text.split(f'name="{control_name}"', 1)[1].split("[node ", 1)[0]
            self.assertIn("custom_minimum_size = Vector2(0, 48)", control_block)

        self.assertNotIn("Канатные дороги, фуникулеры и другие инженерные маршруты", scene_text)
        self.assertIn("Канатные дороги и фуникулеры", scene_text)

    def test_start_navigation_only_exposes_map_and_list(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        for button_name in ["MapButton", "ListButton"]:
            button_block = scene_text.split(f'name="{button_name}" type="Button"', 1)[1].split("[node ", 1)[0]
            self.assertNotIn("visible = false", button_block)

        for button_name in [
            "CardButton",
            "ObjectModeButton",
            "CollectionButton",
            "JournalButton",
            "MemoryButton",
            "RideButton",
            "ObserverButton",
            "SettingsButton",
        ]:
            button_block = scene_text.split(f'name="{button_name}" type="Button"', 1)[1].split("[node ", 1)[0]
            self.assertIn("visible = false", button_block)

    def test_main_scene_declares_orientation_setting_in_russian(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        settings_section = scene_text.split('name="SettingsSection" type="VBoxContainer"', 1)[1]
        self.assertIn('name="OrientationOption" type="OptionButton"', scene_text)
        for text in ["Ориентация", "Как в системе", "Вертикальная", "Горизонтальная"]:
            self.assertIn(f'text = "{text}"', settings_section)

        header_text = scene_text.split('name="Содержимое" type="PanelContainer"', 1)[0]
        self.assertNotIn('name="OrientationOption" type="OptionButton"', header_text)

    def test_main_controller_routes_selection_between_sections(self) -> None:
        script_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for section_name in ['"map"', '"list"', '"card"', '"collection"', '"journal"', '"memory"', '"ride"', '"observer"', '"settings"']:
            self.assertIn(section_name, script_text)

        self.assertIn("object_list.object_selected.connect(_on_object_selected)", script_text)
        self.assertIn("map_panel.object_selected.connect(_on_map_object_selected)", script_text)
        self.assertIn("memory_panel.back_requested.connect", script_text)
        self.assertIn("_select_object(index, true)", script_text)
        self.assertIn("_select_object(index, false)", script_text)
        self.assertIn('_show_section("card")', script_text)
        self.assertIn('_show_section("memory")', script_text)
        self.assertIn("map_panel.select_object(index)", script_text)
        self.assertIn("memory_panel.show_object(objects[index])", script_text)
        self.assertIn("_update_map_selection(objects[index])", script_text)
        self.assertIn("settings_button.pressed.connect", script_text)
        self.assertIn("selected_object_label.text", script_text)
        self.assertIn('selected_object_label.text = "Выбрано: %s, %s"', script_text)

    def test_map_list_toggle_opens_secondary_list_without_breaking_map_first_chrome(self) -> None:
        script_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for expected in [
            'map_list_toggle_button.name = "MapListToggle"',
            'map_list_toggle_button.text = ""',
            'map_list_toggle_button.icon = _make_map_list_icon("list")',
            'map_list_toggle_button.tooltip_text = "Открыть список объектов"',
            'map_list_toggle_button.pressed.connect(func() -> void: _show_section("list"))',
            "map_list_toggle_button.visible = is_map",
            'map_button.icon = _make_map_list_icon("map")',
            'list_button.icon = _make_map_list_icon("list")',
            "func _draw_map_icon(image: Image) -> void:",
            "func _draw_list_icon(image: Image) -> void:",
            "var margin := 0 if is_map else 12",
            "navigation_area.visible = not is_map",
            "app_title_label.visible = not is_map",
            "content_panel.add_theme_stylebox_override(\"panel\", panel_style)",
        ]:
            self.assertIn(expected, script_text)

    def test_current_section_indicator_and_navigation_scroll_contract(self) -> None:
        script_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        for expected in [
            "@onready var navigation_scroll: ScrollContainer = %НавигацияПрокрутка",
            "@onready var current_section_label: Label = %CurrentSectionLabel",
            "var section_titles: Dictionary = {}",
            '"observer": "Наблюдатель"',
            '"ride": "Поездка"',
            '"settings": "Настройки"',
            'current_section_label.text = "Раздел: %s" % title',
            "_scroll_navigation_to_current(section_name)",
            "if not button.visible:",
            'navigation_scroll.set_deferred("scroll_horizontal"',
        ]:
            self.assertIn(expected, script_text)

        current_section_block = scene_text.split('name="CurrentSectionLabel" type="Label"', 1)[1].split("[node ", 1)[0]
        self.assertIn("unique_name_in_owner = true", current_section_block)
        self.assertIn("visible = false", current_section_block)
        self.assertIn('text = "Раздел: Карта"', current_section_block)
        self.assertIn("autowrap_mode = 3", current_section_block)

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

    def test_layout_settings_ux_analysis_is_documented(self) -> None:
        doc_text = (ROOT / "docs" / "layout-settings-ux.md").read_text(encoding="utf-8")

        for expected in [
            "Главная навигация",
            "Настройки",
            "Карточка объекта",
            "Mobile portrait",
            "`Карта`",
            "`Список`",
            "`Карточка`",
            "`Коллекция`",
            "`Журнал`",
            "`Воспоминание`",
            "`Поездка`",
            "`Наблюдатель`",
            "`Настройки`",
            "`Ориентация`",
            "не должна занимать место на стартовой карте",
        ]:
            self.assertIn(expected, doc_text)

    def test_list_panel_can_update_selection_without_reemitting(self) -> None:
        script_text = (ROOT / "scripts" / "object_list_panel.gd").read_text(encoding="utf-8")

        self.assertIn("func select_visual_object(index: int) -> void:", script_text)
        self.assertIn("object_selected.emit(index)", script_text)

    def test_list_panel_uses_atlas_parchment_style(self) -> None:
        script_text = (ROOT / "scripts" / "object_list_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "const ATLAS_PARCHMENT_COLOR := Color(0.96, 0.90, 0.72, 0.94)",
            'const ATLAS_BORDER_COLOR := Color("#3b2a18")',
            'const ATLAS_TEXT_COLOR := Color("#27321f")',
            'const ATLAS_SELECTED_COLOR := Color("#31544d")',
            'const ATLAS_SELECTED_TEXT_COLOR := Color("#f7e4b0")',
            "const LIST_ICON_SIZE := Vector2i(36, 36)",
            "func _apply_atlas_list_style() -> void:",
            "_apply_atlas_list_style()",
            "extends ScrollContainer",
            "horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED",
            "rows_container = VBoxContainer.new()",
            "var row := Button.new()",
            "var icon := TextureRect.new()",
            "var name_label := Label.new()",
            "var meta_label := Label.new()",
            "name_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS",
            "meta_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS",
            "icon.texture = _object_icon_texture(object_data)",
            "row.add_theme_stylebox_override(\"normal\", _row_style(visible_index, false))",
        ]:
            self.assertIn(expected, script_text)


if __name__ == "__main__":
    unittest.main()
