from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ObjectCardContractTest(unittest.TestCase):
    def test_card_script_declares_mvp_sections_and_placeholders(self) -> None:
        script_text = (ROOT / "scripts" / "object_card_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "Общая информация",
            "Тип транспорта",
            "Страна",
            "Регион",
            "Город",
            "Координаты",
            "Статус посещения",
            "Описание",
            "Семейные заметки",
            "Технические поля",
            "Год открытия",
            "Оператор",
            "Производитель",
            "Фотографии",
            "Видео",
            "Билеты",
            "Посещения",
            "не указано",
            "пока нет",
        ]:
            self.assertIn(expected, script_text)

    def test_card_formats_and_edits_visit_status(self) -> None:
        card_text = (ROOT / "scripts" / "object_card_panel.gd").read_text(encoding="utf-8")
        main_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for expected in [
            "signal status_changed(object_id: String, status_id: String)",
            "var status_option: OptionButton",
            "_configure_status_option()",
            "SQLiteStorageAdapter.status_ids()",
            "status_option.item_selected.connect(_on_status_selected)",
            "status_changed.emit",
            "SQLiteStorageAdapter.status_title",
        ]:
            self.assertIn(expected, card_text)

        for expected in [
            "object_card.status_changed.connect(_on_status_changed)",
            "func _on_status_changed(object_id: String, status_id: String) -> void:",
            "storage.update_object_status(object_id, normalized_status)",
            'objects[index]["visited"] = visited',
            'objects[index]["visit_status_id"] = normalized_status',
            "object_card.show_object(objects[index])",
        ]:
            self.assertIn(expected, main_text)


if __name__ == "__main__":
    unittest.main()
