from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
READINESS_DOC = ROOT / "docs" / "1-0-readiness.md"


class OneZeroReadinessContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.readiness_text = READINESS_DOC.read_text(encoding="utf-8")

    def test_readiness_document_declares_candidate_verdict_and_scope(self) -> None:
        self.assertTrue(READINESS_DOC.is_file())
        for expected in [
            "READY_FOR_1_0_CANDIDATE",
            "v0.1.14",
            "0.1.14",
            "не команда выпускать `v1.0.0`",
            "семейным sideload APK",
            "не Google Play production release",
            "реальные blockers для 1.0 candidate не обнаружены",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.readiness_text)

    def test_mvp_feature_gates_are_documented(self) -> None:
        for expected in [
            "Русский интерфейс",
            "«Карта», «Список», «Карточка», «Воспоминание», «Коллекция», «Журнал»",
            "локальная схема объектов",
            "pan/zoom",
            "«Все», «Посещенные», «Непосещенные»",
            "фильтры по типу, статусу посещения и стране",
            "описание, координаты, статус посещения, статус работы объекта",
            "SQLite-хранилище",
            "fallback на `DemoCatalog`",
            "объектов Германии",
            "com.mirtrossov.app",
            "android/debug.keystore",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.readiness_text)

    def test_release_ci_android_assets_and_visual_review_gates_are_fixed(self) -> None:
        checks_workflow = (ROOT / ".github" / "workflows" / "checks.yml").read_text(encoding="utf-8")
        release_workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        release_script = (ROOT / "scripts" / "export-release.sh").read_text(encoding="utf-8")
        agents_text = (ROOT / "agents.md").read_text(encoding="utf-8")
        checklist_text = (ROOT / "docs" / "release-mvp-checklist.md").read_text(encoding="utf-8")

        self.assertIn("python3 -m unittest discover -s tests", checks_workflow)
        self.assertIn("python3 -m unittest discover -s tests", release_workflow)
        self.assertLess(
            release_workflow.index("python3 -m unittest discover -s tests"),
            release_workflow.index("scripts/export-release.sh"),
        )
        for expected in [
            'tags:\n      - "v*"',
            "workflow_dispatch",
            "softprops/action-gh-release",
            "*.apk",
            "*.zip",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, release_workflow)

        for expected in ["--export-release Web", "--export-release Linux", "--export-release Android"]:
            with self.subTest(expected=expected):
                self.assertIn(expected, release_script)

        for expected in [
            "mir-trossov-web-<version>.zip",
            "mir-trossov-linux-<version>.zip",
            "mir-trossov-android-<version>.apk",
            "GitHub Release",
            "Assets",
            "v0.1.14",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.readiness_text)

        for expected in ["390x844", "ACCEPT", "карт"]:
            with self.subTest(expected=expected):
                self.assertIn(expected, agents_text)
                self.assertIn(expected, self.readiness_text)
        self.assertIn("ACCEPT", checklist_text)

    def test_aws_reproducibility_gate_is_documented_and_wired(self) -> None:
        terraform_text = (ROOT / "infra" / "aws-web" / "main.tf").read_text(encoding="utf-8")
        releases_text = (ROOT / "docs" / "releases.md").read_text(encoding="utf-8")
        release_workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

        for expected in [
            "aws_s3_bucket",
            "aws_s3_bucket_website_configuration",
            "aws_iam_role",
            "token.actions.githubusercontent.com",
            "repo:${var.github_repository}",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, terraform_text)

        for expected in [
            "terraform init",
            "terraform apply",
            "AWS_REGION",
            "AWS_WEB_BUCKET",
            "AWS_ROLE_ARN",
            "deploy_web=true",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, releases_text)
                self.assertIn(expected, self.readiness_text)

        for expected in [
            "aws-actions/configure-aws-credentials",
            "vars.AWS_ROLE_ARN",
            "vars.AWS_REGION",
            "vars.AWS_WEB_BUCKET",
            "aws s3 sync",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, release_workflow)

    def test_open_issues_are_classified_as_post_1_0_v3(self) -> None:
        for issue_number in ["#31", "#32", "#33", "#34"]:
            with self.subTest(issue_number=issue_number):
                self.assertRegex(self.readiness_text, rf"`{re.escape(issue_number)}` V3:")

        self.assertIn("не блокируют MVP", self.readiness_text)


if __name__ == "__main__":
    unittest.main()
