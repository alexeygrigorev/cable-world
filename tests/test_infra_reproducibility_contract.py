from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InfraReproducibilityContractTest(unittest.TestCase):
    def test_bootstrap_module_defines_remote_state_resources(self) -> None:
        backend_tf = (ROOT / "infra" / "aws-bootstrap" / "backend.tf").read_text(encoding="utf-8")
        main_tf = (ROOT / "infra" / "aws-bootstrap" / "main.tf").read_text(encoding="utf-8")
        variables_tf = (ROOT / "infra" / "aws-bootstrap" / "variables.tf").read_text(encoding="utf-8")
        outputs_tf = (ROOT / "infra" / "aws-bootstrap" / "outputs.tf").read_text(encoding="utf-8")

        for expected in [
            'resource "aws_s3_bucket" "terraform_state"',
            'resource "aws_s3_bucket_versioning" "terraform_state"',
            'resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state"',
            'resource "aws_s3_bucket_public_access_block" "terraform_state"',
            'resource "aws_dynamodb_table" "terraform_locks"',
            'hash_key     = "LockID"',
            'billing_mode = "PAY_PER_REQUEST"',
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, main_tf)

        for expected in [
            'default     = "eu-west-1"',
            'default     = "cable-world-terraform-state-817685572750"',
            'default     = "cable-world-terraform-locks"',
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, variables_tf)

        for expected in ["state_bucket_name", "lock_table_name", "aws_region"]:
            with self.subTest(expected=expected):
                self.assertIn(expected, outputs_tf)

        for expected in [
            'backend "s3"',
            'bucket       = "cable-world-terraform-state-817685572750"',
            'key          = "aws-bootstrap/terraform.tfstate"',
            'region       = "eu-west-1"',
            "use_lockfile = true",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, backend_tf)

    def test_web_backend_points_to_bootstrap_defaults(self) -> None:
        backend_tf = (ROOT / "infra" / "aws-web" / "backend.tf").read_text(encoding="utf-8")

        for expected in [
            'backend "s3"',
            'bucket       = "cable-world-terraform-state-817685572750"',
            'key          = "aws-web/terraform.tfstate"',
            'region       = "eu-west-1"',
            "encrypt      = true",
            "use_lockfile = true",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, backend_tf)

    def test_infra_runbook_covers_bootstrap_migrate_import_and_outputs(self) -> None:
        readme = (ROOT / "infra" / "aws-web" / "README.md").read_text(encoding="utf-8")

        for expected in [
            "Bootstrap remote state",
            "terraform -chdir=infra/aws-bootstrap init",
            "terraform -chdir=infra/aws-bootstrap apply",
            "terraform -chdir=infra/aws-bootstrap init -migrate-state",
            "terraform -chdir=infra/aws-web init -migrate-state",
            "Восстановление из чистого checkout",
            "terraform -chdir=infra/aws-web import",
            "terraform -chdir=infra/aws-web output -raw bucket_name",
            "AWS_REGION=eu-west-1",
            "AWS_WEB_BUCKET=cable-world-web-817685572750",
            "AWS_ROLE_ARN=arn:aws:iam::817685572750:role/cable-world-github-deploy",
            "http://cable-world-web-817685572750.s3-website-eu-west-1.amazonaws.com",
            "не является финальным публичным HTTPS",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, readme)

    def test_ci_runs_terraform_checks_and_release_has_variable_guard(self) -> None:
        checks = (ROOT / ".github" / "workflows" / "checks.yml").read_text(encoding="utf-8")
        release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

        for expected in [
            "hashicorp/setup-terraform@v4",
            "terraform -chdir=infra/aws-bootstrap fmt -check",
            "terraform -chdir=infra/aws-bootstrap init -backend=false",
            "terraform -chdir=infra/aws-bootstrap validate",
            "terraform -chdir=infra/aws-web fmt -check",
            "terraform -chdir=infra/aws-web init -backend=false",
            "terraform -chdir=infra/aws-web validate",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, checks)

        guard_index = release.index("Проверить AWS variables для Web deploy")
        build_index = release.index("Собрать Web, Linux и Android")
        self.assertLess(guard_index, build_index)

        for expected in [
            "AWS_REGION_VAR",
            "AWS_WEB_BUCKET_VAR",
            "AWS_ROLE_ARN_VAR",
            "GitHub repository variable",
            "Set AWS_REGION, AWS_WEB_BUCKET and AWS_ROLE_ARN",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, release)

    def test_ci_actions_use_node24_compatible_major_versions(self) -> None:
        workflow_text = "\n".join(
            [
                (ROOT / ".github" / "workflows" / "checks.yml").read_text(encoding="utf-8"),
                (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8"),
            ]
        )

        for expected in [
            "actions/checkout@v6",
            "actions/setup-python@v6",
            "hashicorp/setup-terraform@v4",
            "actions/setup-java@v5",
            "android-actions/setup-android@v4",
            "actions/upload-artifact@v7",
            "softprops/action-gh-release@v3",
            "aws-actions/configure-aws-credentials@v6",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, workflow_text)

        for deprecated in [
            "actions/checkout@v4",
            "actions/setup-python@v5",
            "hashicorp/setup-terraform@v3",
            "actions/setup-java@v4",
            "android-actions/setup-android@v3",
            "actions/upload-artifact@v4",
            "softprops/action-gh-release@v2",
            "aws-actions/configure-aws-credentials@v4",
        ]:
            with self.subTest(deprecated=deprecated):
                self.assertNotIn(deprecated, workflow_text)


if __name__ == "__main__":
    unittest.main()
