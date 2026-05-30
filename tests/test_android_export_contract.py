from configparser import ConfigParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def _unquote(value: str) -> str:
    return value.strip().strip('"')


class AndroidExportContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        parser = ConfigParser(strict=False)
        parser.optionxform = str
        parser.read(ROOT / "export_presets.cfg", encoding="utf-8")
        cls.parser = parser

        cls.android_preset = None
        for section in parser.sections():
            if not section.startswith("preset.") or section.endswith(".options"):
                continue
            if _unquote(parser[section].get("name", "")) == "Android":
                cls.android_preset = section
                break

    def test_android_preset_exists_for_apk_export(self) -> None:
        self.assertIsNotNone(self.android_preset, "Нужен Android export preset")
        preset = self.parser[self.android_preset]
        self.assertEqual(_unquote(preset.get("platform", "")), "Android")
        self.assertEqual(_unquote(preset.get("export_path", "")), "build/android/mir-trossov.apk")

    def test_android_identity_and_version_are_stable(self) -> None:
        self.assertIsNotNone(self.android_preset, "Нужен Android export preset")
        options = self.parser[f"{self.android_preset}.options"]
        project_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(project_version, r"^\d+\.\d+\.\d+$")
        expected_version_code = int(project_version.split(".")[2])

        self.assertEqual(_unquote(options["package/unique_name"]), "com.mirtrossov.app")
        self.assertEqual(_unquote(options["package/name"]), "Мир Троссов")
        self.assertEqual(_unquote(options["version/name"]), project_version)
        self.assertEqual(int(options["version/code"]), expected_version_code)
        self.assertGreater(int(options["version/code"]), 0)
        self.assertEqual(_unquote(options["gradle_build/export_format"]), "0")

    def test_android_signing_uses_committed_debug_keystore(self) -> None:
        self.assertIsNotNone(self.android_preset, "Нужен Android export preset")
        options = self.parser[f"{self.android_preset}.options"]

        self.assertEqual(_unquote(options["package/signed"]), "true")
        self.assertEqual(_unquote(options["keystore/debug"]), "android/debug.keystore")
        self.assertEqual(_unquote(options["keystore/release"]), "android/debug.keystore")
        self.assertEqual(_unquote(options["keystore/debug_user"]), "androiddebugkey")
        self.assertEqual(_unquote(options["keystore/release_user"]), "androiddebugkey")
        self.assertEqual(_unquote(options["keystore/debug_password"]), "android")
        self.assertEqual(_unquote(options["keystore/release_password"]), "android")
        self.assertTrue((ROOT / "android" / "debug.keystore").is_file())

    def test_android_texture_import_is_enabled(self) -> None:
        project_text = (ROOT / "project.godot").read_text(encoding="utf-8")
        self.assertIn("textures/vram_compression/import_etc2_astc=true", project_text)


if __name__ == "__main__":
    unittest.main()
