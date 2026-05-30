from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseMvpChecklistTest(unittest.TestCase):
    def test_manual_apk_smoke_checklist_covers_current_mvp(self) -> None:
        checklist_text = (ROOT / "docs" / "release-mvp-checklist.md").read_text(encoding="utf-8")

        for expected in [
            "Запустить приложение",
            "Ориентация",
            "Карта",
            "Список",
            "Германии",
            "карточку",
            "координаты",
            "статус посещения",
            "Работа объекта",
            "фото",
            "Журнал",
            "после релиза",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected.casefold(), checklist_text.casefold())

        smoke_items = re.findall(r"^- ", checklist_text, flags=re.MULTILINE)
        self.assertGreaterEqual(len(smoke_items), 15)

    def test_release_docs_tell_where_to_download_apk(self) -> None:
        releases_text = (ROOT / "docs" / "releases.md").read_text(encoding="utf-8")
        checklist_text = (ROOT / "docs" / "release-mvp-checklist.md").read_text(encoding="utf-8")
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

        for text in [releases_text, checklist_text]:
            with self.subTest(document=text[:40]):
                self.assertIn("https://github.com/alexeygrigorev/cable-world/releases", text)
                self.assertIn("mir-trossov-android-<version>.apk", text)
                self.assertIn("Assets", text)

        self.assertIn("docs/release-mvp-checklist.md", readme_text)

    def test_ci_and_release_workflows_run_contract_tests(self) -> None:
        checks_workflow = (ROOT / ".github" / "workflows" / "checks.yml").read_text(encoding="utf-8")
        release_workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

        for workflow_text in [checks_workflow, release_workflow]:
            with self.subTest(workflow=workflow_text.splitlines()[0]):
                self.assertIn("python3 -m unittest discover -s tests", workflow_text)

        release_test_index = release_workflow.index("python3 -m unittest discover -s tests")
        export_index = release_workflow.index("scripts/export-release.sh")
        self.assertLess(release_test_index, export_index)


if __name__ == "__main__":
    unittest.main()
