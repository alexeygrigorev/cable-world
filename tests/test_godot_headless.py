import shutil
import subprocess
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "build" / "logs"


class GodotHeadlessTest(unittest.TestCase):
    def test_project_imports_and_main_scene_loads(self) -> None:
        godot = shutil.which("godot") or shutil.which("godot4")
        if godot is None:
            self.skipTest("Godot не установлен в PATH")

        LOG_DIR.mkdir(parents=True, exist_ok=True)
        commands = [
            [godot, "--headless", "--path", str(ROOT), "--import", "--quit", "--log-file", str(LOG_DIR / "godot-import.log")],
            [godot, "--headless", "--path", str(ROOT), "--quit-after", "1", "--log-file", str(LOG_DIR / "godot-run.log")],
        ]

        for command in commands:
            result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout)

        combined_log = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in LOG_DIR.glob("godot-*.log"))
        self.assertNotIn("SCRIPT ERROR", combined_log)
        self.assertNotIn("ERROR:", combined_log)


if __name__ == "__main__":
    unittest.main()
