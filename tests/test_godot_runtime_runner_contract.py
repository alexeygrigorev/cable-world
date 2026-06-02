from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_COMMAND = "godot --headless --path . --script tests/godot_runtime_runner.gd"


class GodotRuntimeRunnerContractTest(unittest.TestCase):
    def test_runtime_runner_command_is_documented(self) -> None:
        for path in [
            ROOT / "docs" / "testing-strategy.md",
            ROOT / "process.md",
            ROOT / "docs" / "releases.md",
        ]:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn(RUNTIME_COMMAND, text)

    def test_ci_runs_runtime_tests_separately_from_python_tests(self) -> None:
        workflow_text = (ROOT / ".github" / "workflows" / "checks.yml").read_text(encoding="utf-8")
        self.assertIn("Запустить Python tests", workflow_text)
        self.assertIn("Запустить Godot runtime tests", workflow_text)
        self.assertIn("python3 -m unittest discover -s tests", workflow_text)
        self.assertIn(RUNTIME_COMMAND, workflow_text)
        self.assertLess(
            workflow_text.index("Запустить Python tests"),
            workflow_text.index("Запустить Godot runtime tests"),
        )

    def test_runner_points_to_a_smoke_test(self) -> None:
        runner_text = (ROOT / "tests" / "godot_runtime_runner.gd").read_text(encoding="utf-8")
        smoke_text = (ROOT / "tests" / "godot_runtime_smoke.gd").read_text(encoding="utf-8")
        self.assertIn("res://tests/godot_runtime_smoke.gd", runner_text)
        self.assertIn("res://tests/godot_runtime_app_shell.gd", runner_text)
        self.assertIn("MIR_TROSSOV_GODOT_RUNTIME_TEST_SCRIPTS", runner_text)
        self.assertIn("can_instantiate()", runner_text)
        self.assertIn("test script loaded but cannot be instantiated", runner_text)
        self.assertIn("test_collection_stats_and_achievements_runtime", smoke_text)
        self.assertIn("CollectionStatsScript.calculate", smoke_text)
        self.assertIn("AchievementsScript.calculate", smoke_text)


if __name__ == "__main__":
    unittest.main()
