from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TestingStrategyContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.strategy_text = (ROOT / "docs" / "testing-strategy.md").read_text(encoding="utf-8")

    def test_testing_strategy_documents_python_and_godot_boundaries(self) -> None:
        for expected in [
            "map generation pipeline",
            "geographic audits",
            "JSON/schema/staging validation",
            "export payload contracts",
            "static contracts",
            "GDScript runtime",
            "UI state transitions",
            "input gestures",
            "map marker transforms",
            "runtime resource loading",
            "Python не должен утверждать",
            "Godot-native tests являются дефолтом",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.strategy_text)

    def test_testing_strategy_categorizes_existing_python_tests(self) -> None:
        for expected in [
            "tests/test_map_panel_contract.py",
            "tests/test_map_geography_audit.py",
            "tests/test_export_payload_contract.py",
            "tests/test_import_candidate_collector.py",
            "tests/test_staging_candidate_validator.py",
            "tests/test_project_contract.py",
            "tests/test_release_mvp_checklist.py",
            "tests/test_godot_headless.py",
            "tests/test_godot_storage_contract.py",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.strategy_text)

    def test_process_and_release_protocol_name_both_test_gates(self) -> None:
        process_text = (ROOT / "process.md").read_text(encoding="utf-8")
        protocol_text = (ROOT / "docs" / "agent-operating-protocol.md").read_text(encoding="utf-8")
        releases_text = (ROOT / "docs" / "releases.md").read_text(encoding="utf-8")

        for text in [process_text, protocol_text, releases_text, self.strategy_text]:
            with self.subTest(document=text[:50]):
                for expected in [
                    "python3 -m unittest discover -s tests",
                    "godot --headless --path . --import --quit",
                    "godot --headless --path . --quit-after 1",
                    "Testing Strategy",
                    "Python",
                    "Godot",
                ]:
                    self.assertIn(expected, text)

        self.assertIn("Python static assertions не считаются заменой runtime acceptance", protocol_text)
        self.assertIn("не заменяет runtime/UI тесты Godot", process_text)
        self.assertIn("pipeline/data/schema/export/static contracts", releases_text)


if __name__ == "__main__":
    unittest.main()
