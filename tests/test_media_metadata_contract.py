from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "media-metadata-android-godot.md"


class MediaMetadataResearchContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DOC.read_text(encoding="utf-8")

    def test_document_exists_and_is_russian(self) -> None:
        self.assertTrue(DOC.exists(), "Research-документ по EXIF/GPS должен существовать")
        cyrillic_letters = len(re.findall(r"[А-Яа-яЁё]", self.text))
        latin_letters = len(re.findall(r"[A-Za-z]", self.text))
        self.assertGreater(cyrillic_letters, latin_letters)

    def test_android_and_godot_limits_are_documented(self) -> None:
        for term in [
            "AndroidX ExifInterface",
            "MediaMetadataRetriever",
            "METADATA_KEY_LOCATION",
            "ACCESS_MEDIA_LOCATION",
            "MediaStore.setRequireOriginal",
            "scoped storage",
            "Photo Picker",
            "Image.load_from_file",
            "Image.load_jpg_from_buffer",
            "FileAccess",
            "OS.request_permission",
            "Android plugins",
            "недостаточно для надежного чтения GPS",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, self.text)

    def test_mvp_decision_does_not_require_native_plugin_or_schema_change(self) -> None:
        for term in [
            "Сейчас native plugin не нужен",
            "native plugin не делаем",
            "schema storage не меняем",
            "ручной привязки",
            "привязать медиа к `ObjectStation`, `RouteDirection`, `RouteSegment`",
            "приватность координат локальная",
            "локальной SQLite-базе",
            "не синхронизируются наружу",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, self.text)

    def test_coordinate_source_contract_is_fixed(self) -> None:
        expected = {
            "exif": "координаты прочитаны",
            "manual": "координаты или привязка",
            "unknown": "координаты отсутствуют",
        }
        for source, meaning in expected.items():
            with self.subTest(source=source):
                self.assertIn(f"`{source}`", self.text)
                self.assertIn(meaning, self.text)

        self.assertIn("`exif` не должен выставляться просто потому", self.text)

    def test_future_fixture_matrix_is_documented(self) -> None:
        for fixture in [
            "photo_with_gps.jpg",
            "photo_without_gps.jpg",
            "video_with_location.mp4",
            "file_without_metadata.bin",
            "image_plain.png",
            "photo_redacted_by_android.jpg",
            "permission_denied_access_media_location",
            "selected_media_read_grant_only",
            "local_app_copy_preserves_privacy",
        ]:
            with self.subTest(fixture=fixture):
                self.assertIn(fixture, self.text)

        for expected in [
            "ожидаемый результат `coordinate_source = 'exif'`",
            "ожидаемый результат `coordinate_source = 'unknown'`",
            "импорт не падает",
            "не выставляет `exif`",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.text)


if __name__ == "__main__":
    unittest.main()
