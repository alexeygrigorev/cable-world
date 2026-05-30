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

    def test_card_formats_visit_status_and_refreshes_after_toggle(self) -> None:
        card_text = (ROOT / "scripts" / "object_card_panel.gd").read_text(encoding="utf-8")
        main_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for expected in [
            'match status_id:',
            '"not_visited"',
            '"planned"',
            '"visited"',
            '"favorite"',
            "visit_toggled.emit",
            "Снять отметку посещения",
            "Отметить как посещенное",
        ]:
            self.assertIn(expected, card_text)

        for expected in [
            'objects[index]["visited"] = visited',
            'objects[index]["visit_status_id"] = SQLiteStorageAdapter.STATUS_VISITED if visited else SQLiteStorageAdapter.STATUS_NOT_VISITED',
            "object_card.show_object(objects[index])",
        ]:
            self.assertIn(expected, main_text)


if __name__ == "__main__":
    unittest.main()
