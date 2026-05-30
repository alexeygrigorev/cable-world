from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MemoryScreenContractTest(unittest.TestCase):
    def test_memory_panel_declares_mobile_trip_memory_screen(self) -> None:
        script_text = (ROOT / "scripts" / "memory_panel.gd").read_text(encoding="utf-8")
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        for expected in [
            "class_name MemoryPanel",
            "signal back_requested",
            "var title_label: Label",
            "var visit_label: Label",
            "var note_label: Label",
            "var rating_label: Label",
            "var photos_label: Label",
            "var tickets_label: Label",
            "func show_object(object_data: Dictionary) -> void:",
            "custom_minimum_size = Vector2(0, 52)",
            "label.add_theme_font_size_override(\"font_size\", 20)",
            "title_label.add_theme_font_size_override(\"font_size\", 24)",
        ]:
            self.assertIn(expected, script_text)

        for expected in [
            'name="MemorySection"',
            'name="MemoryButton" type="Button"',
            'text = "Воспоминание"',
            'name="MemoryPanel" type="PanelContainer"',
            'path="res://scripts/memory_panel.gd"',
        ]:
            self.assertIn(expected, scene_text)

    def test_memory_panel_uses_russian_empty_states_and_return_action(self) -> None:
        script_text = (ROOT / "scripts" / "memory_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "Воспоминание",
            "Выберите объект, чтобы увидеть историю поездки.",
            "Посещений пока нет. Когда вы сохраните поездку, здесь появятся дата, заметка и оценка.",
            "Дата посещения",
            "Заметка",
            "Оценка",
            "пока нет",
            "Фотографии: пока нет добавленных снимков.",
            "Билеты: пока нет сохраненных билетов.",
            "Вернуться к карточке",
        ]:
            self.assertIn(expected, script_text)

        for forbidden in ["MediaAsset", "local_path", "SQLite", "res://", "user://"]:
            self.assertNotIn(forbidden, script_text)

    def test_memory_contract_uses_existing_visits_photos_and_tickets(self) -> None:
        script_text = (ROOT / "scripts" / "memory_panel.gd").read_text(encoding="utf-8")
        main_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for expected in [
            '_array_field(object_data, "visits")',
            '_array_field(object_data, "photos")',
            '_array_field(object_data, "tickets")',
            'visit.get("visited_on", "")',
            'visit.get("notes", "")',
            'visit.get("impression_rating", null)',
            'photo.get("caption", "")',
            'ticket.get("title", "")',
            'ticket.get("issued_on", "")',
            'ticket.get("notes", "")',
        ]:
            self.assertIn(expected, script_text)

        for expected in [
            "var tickets := storage.list_tickets(object_id)",
            'enriched_object["tickets"] = tickets',
            'enriched_object["ticket_count"] = tickets.size()',
            'objects[index]["tickets"] = storage.list_tickets(object_id)',
            'objects[index]["ticket_count"] = objects[index]["tickets"].size()',
            "memory_panel.show_object(objects[index])",
        ]:
            self.assertIn(expected, main_text)


if __name__ == "__main__":
    unittest.main()
