import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProjectContractTest(unittest.TestCase):
    def test_godot_project_points_to_existing_main_scene(self) -> None:
        project_text = (ROOT / "project.godot").read_text(encoding="utf-8")
        match = re.search(r'run/main_scene="res://([^"]+)"', project_text)
        self.assertIsNotNone(match, "В project.godot должна быть главная сцена")
        self.assertTrue((ROOT / match.group(1)).exists(), "Главная сцена должна существовать")

    def test_main_scene_uses_typed_scripts(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")
        scripts = re.findall(r'path="res://(scripts/[^"]+\.gd)"', scene_text)
        self.assertGreaterEqual(len(scripts), 3)
        for script in scripts:
            text = (ROOT / script).read_text(encoding="utf-8")
            self.assertIn("class_name ", text)
            self.assertRegex(text, r"(var|const|func|signal) .+:", f"{script} должен использовать типизацию")

    def test_demo_catalog_contains_mvp_fields(self) -> None:
        text = (ROOT / "scripts" / "demo_catalog.gd").read_text(encoding="utf-8")
        for field in ["id", "name", "kind", "region", "coordinates", "description", "visited", "notes"]:
            self.assertIn(f'"{field}"', text)

    def test_user_facing_docs_are_russian(self) -> None:
        for relative_path in ["README.md", "process.md", "agents.md", "docs/architecture.md"]:
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            cyrillic_letters = len(re.findall(r"[А-Яа-яЁё]", text))
            latin_letters = len(re.findall(r"[A-Za-z]", text))
            self.assertGreater(cyrillic_letters, latin_letters, f"{relative_path} должен быть преимущественно на русском")


if __name__ == "__main__":
    unittest.main()
