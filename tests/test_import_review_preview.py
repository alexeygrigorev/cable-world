from pathlib import Path
import json
import sqlite3
import tempfile
import unittest

import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.import_review_preview import (  # noqa: E402
    ReviewPreviewError,
    build_preview_json,
    build_preview_sql,
    load_staging_records,
)


class ImportReviewPreviewContractTest(unittest.TestCase):
    def test_candidate_and_rejected_records_do_not_reach_preview(self) -> None:
        preview = build_preview_json(
            [
                self._record("candidate-object", "candidate"),
                self._record("approved-object", "approved"),
                self._record("rejected-object", "rejected"),
            ]
        )

        self.assertEqual([record["id"] for record in preview], ["approved-object"])

    def test_preview_sql_contains_only_approved_records(self) -> None:
        sql = build_preview_sql(
            [
                self._record("candidate-object", "candidate"),
                self._record("approved-object", "approved"),
                self._record("rejected-object", "rejected"),
            ]
        )

        self.assertIn("approved-object", sql)
        self.assertNotIn("candidate-object", sql)
        self.assertNotIn("rejected-object", sql)
        self.assertIn("INSERT INTO transport_objects", sql)
        self.assertNotIn("source_ids", sql)
        self.assertNotIn("reviewed_by", sql)
        self.assertNotIn("reviewed_at", sql)

    def test_preview_sql_can_be_applied_to_empty_schema_without_staging_fields(self) -> None:
        sql = build_preview_sql([self._record("approved-object", "approved")])
        connection = sqlite3.connect(":memory:")
        connection.execute("PRAGMA foreign_keys = ON")
        for migration in sorted((ROOT / "scripts" / "storage" / "migrations").glob("*.sql")):
            connection.executescript(migration.read_text(encoding="utf-8"))

        connection.executescript(sql)
        row = connection.execute(
            "SELECT id, title, operational_status FROM transport_objects"
        ).fetchone()

        self.assertEqual(row, ("approved-object", "Тестовая канатная дорога", "unknown"))

    def test_approved_record_requires_review_checklist_fields(self) -> None:
        required_fields = {
            "русский title": (("localized", "ru", "title"), "Test cable car"),
            "русский description": (("localized", "ru", "description"), "Cable car"),
            "transport_type_id": (("transport_type_id",), "missing"),
            "latitude": (("latitude",), 120),
            "longitude": (("longitude",), 220),
            "operator": (("operator",), ""),
            "source_urls": (("source_urls",), []),
            "operational_status": (("operational_status",), "invented"),
        }

        for name, (path, value) in required_fields.items():
            with self.subTest(name=name):
                record = self._record("approved-object", "approved")
                self._set_nested(record, path, value)
                with self.assertRaises(ReviewPreviewError):
                    build_preview_json([record])

    def test_non_unknown_operational_status_requires_fresh_official_source_fields(self) -> None:
        record = self._record("approved-object", "approved")
        record["operational_status"] = "active"
        record["status_checked_at"] = ""
        record["status_source_url"] = ""
        record["status_note"] = ""

        with self.assertRaisesRegex(ReviewPreviewError, "свежий официальный источник"):
            build_preview_json([record])

        record["status_checked_at"] = "2026-05-30"
        record["status_source_url"] = "https://operator.example/status"
        record["status_note"] = "Официальное расписание подтверждает работу."
        preview = build_preview_json([record])

        self.assertEqual(preview[0]["operational_status"], "active")
        self.assertEqual(preview[0]["status_source_url"], "https://operator.example/status")

    def test_load_staging_records_accepts_staging_shapes(self) -> None:
        record = self._record("approved-object", "approved")
        with tempfile.TemporaryDirectory() as directory:
            single_path = Path(directory) / "single.json"
            array_path = Path(directory) / "array.json"
            wrapper_path = Path(directory) / "wrapper.json"
            candidates_path = Path(directory) / "candidates.json"
            single_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            array_path.write_text(json.dumps([record], ensure_ascii=False), encoding="utf-8")
            wrapper_path.write_text(
                json.dumps({"records": [record]}, ensure_ascii=False),
                encoding="utf-8",
            )
            candidates_path.write_text(
                json.dumps({"candidates": [record]}, ensure_ascii=False),
                encoding="utf-8",
            )

            self.assertEqual(load_staging_records(single_path)[0]["id"], "approved-object")
            self.assertEqual(load_staging_records(array_path)[0]["id"], "approved-object")
            self.assertEqual(load_staging_records(wrapper_path)[0]["id"], "approved-object")
            self.assertEqual(load_staging_records(candidates_path)[0]["id"], "approved-object")

    def _record(self, object_id: str, state: str) -> dict:
        return {
            "id": object_id,
            "transport_type_id": "cable_gondola",
            "visit_status_id": "not_visited",
            "country": "Германия",
            "region": "Берлин",
            "city": "Берлин",
            "latitude": 52.5,
            "longitude": 13.4,
            "localized": {
                "ru": {
                    "title": "Тестовая канатная дорога",
                    "description": "Короткое русское описание объекта для preview seed.",
                }
            },
            "opened_year": 2020,
            "operator": "Тестовый оператор",
            "manufacturer": "Тестовый производитель",
            "operational_status": "unknown",
            "status_checked_at": "",
            "status_source_url": "",
            "status_note": "",
            "source_ids": {"osm": ["way/1"]},
            "source_urls": ["https://www.openstreetmap.org/way/1"],
            "review": {"state": state, "reviewed_by": "", "reviewed_at": "", "notes": ""},
        }

    def _set_nested(self, record: dict, path: tuple[str, ...], value: object) -> None:
        target = record
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value


if __name__ == "__main__":
    unittest.main()
