from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "staging_catalog_candidate.schema.json"
VALID_EXAMPLE = ROOT / "examples" / "staging" / "valid_catalog_candidate.json"
INVALID_EXAMPLE = ROOT / "examples" / "staging" / "invalid_catalog_candidate.json"
VALIDATOR = ROOT / "scripts" / "validate_staging_candidates.py"
INITIAL_SCHEMA = ROOT / "scripts" / "storage" / "migrations" / "001_initial_schema.sql"
OPERATIONAL_SCHEMA = ROOT / "scripts" / "storage" / "migrations" / "002_operational_status.sql"


def _inserted_ids(sql: str, table: str) -> list[str]:
    match = re.search(
        rf"INSERT INTO {table} .*? VALUES\n(?P<rows>.*?);",
        sql,
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"Не найден INSERT для {table}")
    return re.findall(r"\('([^']+)'", match.group("rows"))


def _operational_status_ids(sql: str) -> list[str]:
    match = re.search(
        r"CHECK \(operational_status IN \(\n(?P<values>.*?)\n\)\)",
        sql,
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError("Не найден CHECK для operational_status")
    return re.findall(r"'([^']+)'", match.group("values"))


class StagingCandidateValidatorContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cls.valid_example = json.loads(VALID_EXAMPLE.read_text(encoding="utf-8"))
        cls.invalid_example = json.loads(INVALID_EXAMPLE.read_text(encoding="utf-8"))

    def test_schema_exists_and_requires_catalog_candidate_core(self) -> None:
        required = set(self.schema["required"])
        for field in [
            "id",
            "transport_type_id",
            "visit_status_id",
            "latitude",
            "longitude",
            "localized",
            "operational_status",
        ]:
            self.assertIn(field, required)

        self.assertEqual(self.schema["properties"]["id"]["pattern"], "^[a-z][a-z0-9-]*$")
        localized = self.schema["properties"]["localized"]
        self.assertIn("ru", localized["required"])
        self.assertEqual(
            localized["properties"]["ru"]["$ref"],
            "#/$defs/required_localized_text",
        )

    def test_schema_enums_match_current_domain_model(self) -> None:
        migration_text = INITIAL_SCHEMA.read_text(encoding="utf-8")
        operational_text = OPERATIONAL_SCHEMA.read_text(encoding="utf-8")

        self.assertEqual(
            self.schema["properties"]["transport_type_id"]["enum"],
            _inserted_ids(migration_text, "transport_types"),
        )
        self.assertEqual(
            self.schema["properties"]["visit_status_id"]["enum"],
            _inserted_ids(migration_text, "visit_statuses"),
        )
        self.assertEqual(
            self.schema["properties"]["operational_status"]["enum"],
            _operational_status_ids(operational_text),
        )

    def test_staging_fields_are_not_transport_object_sqlite_columns(self) -> None:
        migration_text = INITIAL_SCHEMA.read_text(encoding="utf-8")
        transport_object_sql = re.search(
            r"CREATE TABLE transport_objects \(\n(?P<body>.*?)\n\);",
            migration_text,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(transport_object_sql)
        body = transport_object_sql.group("body")

        for staging_field in ["source_ids", "source_urls", "review"]:
            self.assertIn(staging_field, self.schema["properties"])
            self.assertNotIn(staging_field, body)

    def test_valid_example_passes_validator(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(VALID_EXAMPLE)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("прошли проверку", result.stdout)

    def test_invalid_example_fails_validator_with_contract_errors(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(INVALID_EXAMPLE)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("$.id", result.stderr)
        self.assertIn("$.transport_type_id", result.stderr)
        self.assertIn("$.latitude", result.stderr)
        self.assertIn("$.localized.ru", result.stderr)
        self.assertIn("$.operational_status", result.stderr)

    def test_valid_example_keeps_russian_localized_text_required(self) -> None:
        ru = self.valid_example["localized"]["ru"]
        self.assertRegex(self.valid_example["id"], r"^[a-z][a-z0-9-]*$")
        self.assertTrue(ru["title"])
        self.assertTrue(ru["description"])
        self.assertIn("source_ids", self.valid_example)
        self.assertIn("source_urls", self.valid_example)
        self.assertIn("review", self.valid_example)


if __name__ == "__main__":
    unittest.main()
