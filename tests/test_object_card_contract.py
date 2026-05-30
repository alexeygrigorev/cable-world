from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


FORBIDDEN_USER_FACING_TERMS = [
    "MVP",
    "MediaAsset",
    "local_path",
    "SQLite",
    "тестовая",
]


def _gd_string_literals(text: str) -> list[str]:
    literals: list[str] = []
    index = 0
    while index < len(text):
        if text[index] != '"':
            index += 1
            continue

        index += 1
        chars: list[str] = []
        escaped = False
        while index < len(text):
            char = text[index]
            if escaped:
                chars.append(char)
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                literals.append("".join(chars))
                break
            else:
                chars.append(char)
            index += 1
        index += 1
    return literals


class ObjectCardContractTest(unittest.TestCase):
    def test_card_script_declares_sections_and_placeholders(self) -> None:
        script_text = (ROOT / "scripts" / "object_card_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "Общая информация",
            "Тип транспорта",
            "Страна",
            "Регион",
            "Город",
            "Координаты",
            "Статус посещения",
            "Работа объекта",
            "Проверено",
            "Источник",
            "Описание",
            "Семейные заметки",
            "Технические поля",
            "Год открытия",
            "Оператор",
            "Производитель",
            "Фотографии",
            "Добавить запись о фото",
            "Сейчас добавляется только запись о фотографии.",
            "локальное хранилище",
            "Видео",
            "Билеты",
            "Посещения",
            "Последние посещения",
            "Короткое название поездки",
            "Заметка о посещении",
            "Сохранить посещение",
            "Записать дату, время и заметку о поездке.",
            "не указано",
            "пока нет",
        ]:
            self.assertIn(expected, script_text)

    def test_visible_photo_strings_do_not_expose_internal_terms(self) -> None:
        card_text = (ROOT / "scripts" / "object_card_panel.gd").read_text(encoding="utf-8")
        main_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        visible_card_literals = [
            literal
            for literal in _gd_string_literals(card_text)
            if any(
                marker in literal
                for marker in [
                    "фото",
                    "Фото",
                    "Фотографии",
                    "Добавить",
                    "файл",
                    "хранилище",
                    "посещ",
                    "поезд",
                    "Журнал",
                ]
            )
        ]
        visible_main_literals = [
            literal
            for literal in _gd_string_literals(main_text)
            if any(marker in literal for marker in ["фото", "Фото", "файл", "хранилище", "посещ", "поезд", "Журнал"])
        ]

        for literal in visible_card_literals + visible_main_literals:
            for forbidden in FORBIDDEN_USER_FACING_TERMS:
                with self.subTest(literal=literal, forbidden=forbidden):
                    self.assertNotIn(forbidden.casefold(), literal.casefold())

    def test_photo_rows_do_not_render_storage_paths(self) -> None:
        card_text = (ROOT / "scripts" / "object_card_panel.gd").read_text(encoding="utf-8")
        photo_formatter = card_text.split("func _photo_collection_text", 1)[1].split(
            "func _photo_hint_text", 1
        )[0]

        self.assertIn('"Фотографии: %d"', photo_formatter)
        self.assertIn('"- Фото %d: %s"', photo_formatter)
        self.assertNotIn('photo.get("local_path"', photo_formatter)
        self.assertNotIn("media/", photo_formatter)
        self.assertNotIn("(%s)", photo_formatter)

    def test_card_formats_and_edits_visit_status(self) -> None:
        card_text = (ROOT / "scripts" / "object_card_panel.gd").read_text(encoding="utf-8")
        main_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        for expected in [
            "signal status_changed(object_id: String, status_id: String)",
            "signal photo_registration_requested(object_id: String)",
            "signal visit_registration_requested(object_id: String, title: String, notes: String)",
            "var status_option: OptionButton",
            "var add_photo_button: Button",
            "var add_visit_button: Button",
            "var visit_title_edit: LineEdit",
            "var visit_notes_edit: TextEdit",
            "_configure_status_option()",
            "SQLiteStorageAdapter.status_ids()",
            "status_option.item_selected.connect(_on_status_selected)",
            "add_photo_button.pressed.connect(_on_add_photo_pressed)",
            "add_visit_button.pressed.connect(_on_add_visit_pressed)",
            "status_changed.emit",
            "photo_registration_requested.emit",
            "visit_registration_requested.emit",
            "SQLiteStorageAdapter.status_title",
            "SQLiteStorageAdapter.operational_status_title",
            "operational_status_label",
            "_operational_status_text",
        ]:
            self.assertIn(expected, card_text)

        for expected in [
            "object_card.status_changed.connect(_on_status_changed)",
            "object_card.photo_registration_requested.connect(_on_photo_registration_requested)",
            "object_card.visit_registration_requested.connect(_on_visit_registration_requested)",
            "func _on_status_changed(object_id: String, status_id: String) -> void:",
            "func _on_photo_registration_requested(object_id: String) -> void:",
            "func _on_visit_registration_requested(object_id: String, title: String, notes: String) -> void:",
            "storage.update_object_status(object_id, normalized_status)",
            "storage.upsert_media_asset",
            "storage.upsert_visit",
            "storage.list_visits(object_id)",
            "storage.list_object_photos(object_id)",
            'objects[index]["visited"] = visited',
            'objects[index]["visit_status_id"] = normalized_status',
            'objects[index]["visits"] = storage.list_visits(object_id)',
            'objects[index]["visit_count"] = objects[index]["visits"].size()',
            "object_card.show_object(objects[index], storage_runtime_enabled)",
        ]:
            self.assertIn(expected, main_text)

    def test_card_controls_keep_mobile_touch_targets(self) -> None:
        card_text = (ROOT / "scripts" / "object_card_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "status_option.custom_minimum_size = Vector2(0, 48)",
            "add_photo_button.custom_minimum_size = Vector2(0, 52)",
            "visit_title_edit.custom_minimum_size = Vector2(0, 48)",
            "visit_notes_edit.custom_minimum_size = Vector2(0, 112)",
            "add_visit_button.custom_minimum_size = Vector2(0, 52)",
            'label.add_theme_font_size_override("font_size", 20)',
        ]:
            self.assertIn(expected, card_text)


if __name__ == "__main__":
    unittest.main()
