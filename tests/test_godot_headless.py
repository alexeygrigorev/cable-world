import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GodotProjectSmokeTest(unittest.TestCase):
    def test_project_declares_resolvable_main_scene_contract(self) -> None:
        project_text = (ROOT / "project.godot").read_text(encoding="utf-8")
        main_scene_match = re.search(r'run/main_scene="res://([^"]+)"', project_text)
        self.assertIsNotNone(main_scene_match, "В project.godot должна быть главная сцена")

        scene_path = ROOT / main_scene_match.group(1)
        self.assertTrue(scene_path.is_file(), "Главная сцена должна существовать")

        scene_text = scene_path.read_text(encoding="utf-8")
        self.assertRegex(scene_text, r"^\[gd_scene load_steps=\d+ format=3", "Главная сцена должна быть Godot 4 scene")
        self.assertRegex(scene_text, r'(?m)^\[node name="[^"]+" type="Control"\]', "Главная сцена должна иметь Control root node")

        ext_resource_lines = re.findall(r'^\[ext_resource [^\]]*path="res://([^"]+)"[^\]]*id="([^"]+)"[^\]]*\]', scene_text, re.MULTILINE)
        self.assertGreaterEqual(len(ext_resource_lines), 1, "Главная сцена должна объявлять внешние ресурсы")

        ext_resource_ids = {resource_id for _, resource_id in ext_resource_lines}
        used_resource_ids = set(re.findall(r'ExtResource\("([^"]+)"\)', scene_text))
        self.assertTrue(used_resource_ids <= ext_resource_ids, f"Необъявленные ExtResource id: {used_resource_ids - ext_resource_ids}")

        for relative_path, _ in ext_resource_lines:
            self.assertTrue((ROOT / relative_path).is_file(), f"Ресурс главной сцены должен существовать: {relative_path}")


if __name__ == "__main__":
    unittest.main()
