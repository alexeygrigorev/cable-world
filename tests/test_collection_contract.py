from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CollectionContractTest(unittest.TestCase):
    def test_main_scene_declares_collection_screen_in_russian(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        for node_name in [
            "CollectionButton",
            "CollectionSection",
            "CollectionRows",
            "CollectionScroll",
            "CollectionEmptyStateLabel",
            "ListActiveCollectionFilterLabel",
        ]:
            self.assertIn(f'name="{node_name}"', scene_text)
            self.assertIn("unique_name_in_owner = true", scene_text)

        for visible_text in [
            "Коллекция",
            "Прогресс по странам и типам транспорта.",
            "Коллекция пока пуста.",
            "Фильтр: не выбран",
        ]:
            self.assertIn(visible_text, scene_text)

        collection_scroll_block = scene_text.split('name="CollectionScroll" type="ScrollContainer"', 1)[1].split("[node ", 1)[0]
        self.assertIn("custom_minimum_size = Vector2(0, 260)", collection_scroll_block)
        self.assertIn("horizontal_scroll_mode = 0", collection_scroll_block)

    def test_main_screen_builds_collection_progress_and_filters_list(self) -> None:
        script_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for expected in [
            "@onready var collection_button: Button = %CollectionButton",
            "@onready var collection_rows: VBoxContainer = %CollectionRows",
            'const COLLECTION_STATS_SCRIPT_PATH := "res://scripts/collection_stats.gd"',
            'const ACHIEVEMENTS_SCRIPT_PATH := "res://scripts/achievements.gd"',
            "ResourceLoader.exists(COLLECTION_STATS_SCRIPT_PATH)",
            "ResourceLoader.exists(ACHIEVEMENTS_SCRIPT_PATH)",
            "func set_collection_stats(next_stats: Dictionary) -> void:",
            "func _refresh_collection() -> void:",
            "func _calculate_achievements(source_objects: Array[Dictionary]) -> Array[Dictionary]:",
            "achievements_script.calculate(source_objects)",
            'var title_label := Label.new()',
            '"Достижения"',
            '"status_text"',
            '"progress_text"',
            "func _calculate_collection_stats(source_objects: Array[Dictionary]) -> Dictionary:",
            "collection_stats_script.calculate(source_objects)",
            "func _collection_progress_percent(total_count: int, visited_count: int) -> int:",
            '"countries"',
            '"transport_types"',
            '"Страны"',
            '"Типы транспорта"',
            '"%s\\n%d из %d, %d%%"',
            "button.custom_minimum_size = Vector2(0, 52)",
            "button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART",
            "button.pressed.connect(func() -> void: _apply_collection_filter(filter_kind, title))",
            "object_list.set_filters(type_filter, ObjectListPanel.FILTER_ALL, country_filter)",
            'list_active_collection_filter_label.text = "Фильтр: %s\\n%s"',
            '_show_section("list")',
        ]:
            self.assertIn(expected, script_text)

    def test_object_list_accepts_collection_country_filter(self) -> None:
        script_text = (ROOT / "scripts" / "object_list_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "var country_filter: String = FILTER_ALL",
            "next_country_filter: String = FILTER_ALL",
            "country_filter = next_country_filter",
            'object_data.get("country", "") != country_filter',
        ]:
            self.assertIn(expected, script_text)


if __name__ == "__main__":
    unittest.main()
