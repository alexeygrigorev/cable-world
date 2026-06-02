from pathlib import Path
import re
import sqlite3
import unittest


ROOT = Path(__file__).resolve().parents[1]
INITIAL_SCHEMA = ROOT / "scripts" / "storage" / "migrations" / "001_initial_schema.sql"
MIGRATIONS_DIR = ROOT / "scripts" / "storage" / "migrations"
DEMO_SEED = ROOT / "scripts" / "storage" / "seeds" / "demo_objects.sql"
STORAGE_ADAPTER = ROOT / "scripts" / "storage" / "sqlite_storage_adapter.gd"

ASCII_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
ASCII_DEMO_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")


def _insert_rows(sql: str, table: str) -> list[tuple[str, ...]]:
    pattern = re.compile(
        rf"INSERT INTO {table} \([^)]+\) VALUES\s*(.*?);",
        re.DOTALL,
    )
    match = pattern.search(sql)
    if match is None:
        return []
    rows: list[tuple[str, ...]] = []
    for row_text in re.findall(r"\(([^()]*)\)", match.group(1)):
        values = tuple(re.findall(r"'([^']*)'", row_text))
        if values:
            rows.append(values)
    return rows


class I18nContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema_text = INITIAL_SCHEMA.read_text(encoding="utf-8")
        cls.seed_text = DEMO_SEED.read_text(encoding="utf-8")
        cls.adapter_text = STORAGE_ADAPTER.read_text(encoding="utf-8")

    def test_reference_ids_are_ascii_and_labels_are_display_text(self) -> None:
        for table, label_indexes in {
            "visit_statuses": (1,),
            "transport_types": (1, 2),
        }.items():
            rows = _insert_rows(self.schema_text, table)
            self.assertGreater(len(rows), 0, f"{table} должен иметь seed-значения")
            for row in rows:
                stable_id = row[0]
                with self.subTest(table=table, stable_id=stable_id):
                    self.assertRegex(stable_id, ASCII_ID_RE)
                    self.assertNotRegex(stable_id, CYRILLIC_RE)
                    for label_index in label_indexes:
                        self.assertNotEqual(stable_id, row[label_index])
                        self.assertRegex(row[label_index], CYRILLIC_RE)

    def test_operational_status_ids_are_ascii_and_have_russian_labels(self) -> None:
        constants = dict(
            re.findall(
                r"const (OPERATIONAL_[A-Z_]+): String = \"([a-z0-9_]+)\"",
                self.adapter_text,
            )
        )
        self.assertGreaterEqual(len(constants), 7)
        for name, stable_id in constants.items():
            with self.subTest(name=name):
                self.assertRegex(stable_id, ASCII_ID_RE)
                self.assertNotRegex(stable_id, CYRILLIC_RE)
                if name != "OPERATIONAL_UNKNOWN":
                    self.assertIn(f"if normalized_status == {name}:", self.adapter_text)

        labels = re.findall(r"return \"([А-Яа-яЁё][^\"]*)\"", self.adapter_text)
        self.assertIn("работает", labels)
        self.assertIn("статус неизвестен", labels)

    def test_demo_seed_uses_reference_ids_not_russian_labels(self) -> None:
        transport_type_ids = {
            row[0] for row in _insert_rows(self.schema_text, "transport_types")
        }
        visit_status_ids = {row[0] for row in _insert_rows(self.schema_text, "visit_statuses")}
        operational_status_ids = set(
            re.findall(r"const OPERATIONAL_[A-Z_]+: String = \"([a-z0-9_]+)\"", self.adapter_text)
        )

        connection = sqlite3.connect(":memory:")
        connection.execute("PRAGMA foreign_keys = ON")
        for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
            connection.executescript(migration.read_text(encoding="utf-8"))
        connection.executescript(self.seed_text)
        seed_rows = connection.execute(
            """
            SELECT id, transport_type_id, visit_status_id, operational_status
            FROM transport_objects
            """
        ).fetchall()
        self.assertGreater(len(seed_rows), 0)
        for object_id, transport_type_id, visit_status_id, operational_status_id in seed_rows:
            with self.subTest(object_id=object_id):
                self.assertNotRegex(object_id, CYRILLIC_RE)
                self.assertIn(transport_type_id, transport_type_ids)
                self.assertIn(visit_status_id, visit_status_ids)
                self.assertIn(operational_status_id, operational_status_ids)
                self.assertNotRegex(transport_type_id, CYRILLIC_RE)
                self.assertNotRegex(visit_status_id, CYRILLIC_RE)
                self.assertNotRegex(operational_status_id, CYRILLIC_RE)

    def test_route_demo_ids_are_ascii_and_labels_are_russian(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.execute("PRAGMA foreign_keys = ON")
        for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
            connection.executescript(migration.read_text(encoding="utf-8"))
        connection.executescript(self.seed_text)

        station_rows = connection.execute(
            """
            SELECT id, title, note
            FROM object_stations
            WHERE transport_object_id = 'berlin-gaerten-der-welt'
            ORDER BY sort_order
            """
        ).fetchall()
        self.assertEqual(len(station_rows), 3)
        for stable_id, title, note in station_rows:
            with self.subTest(stable_id=stable_id):
                self.assertRegex(stable_id, ASCII_DEMO_ID_RE)
                self.assertNotRegex(stable_id, CYRILLIC_RE)
                self.assertRegex(title, CYRILLIC_RE)
                self.assertRegex(note, CYRILLIC_RE)

        direction_rows = connection.execute(
            """
            SELECT id, title, direction_label, note
            FROM route_directions
            WHERE transport_object_id = 'berlin-gaerten-der-welt'
            ORDER BY sort_order
            """
        ).fetchall()
        self.assertEqual(len(direction_rows), 2)
        for stable_id, title, direction_label, note in direction_rows:
            with self.subTest(stable_id=stable_id):
                self.assertRegex(stable_id, ASCII_DEMO_ID_RE)
                self.assertNotRegex(stable_id, CYRILLIC_RE)
                self.assertRegex(title, CYRILLIC_RE)
                self.assertRegex(direction_label, CYRILLIC_RE)
                self.assertRegex(note, CYRILLIC_RE)

        media_row = connection.execute(
            """
            SELECT id, caption, coordinate_source, geo_note
            FROM media_assets
            WHERE id = 'berlin-gaerten-der-welt-demo-video-kienbergpark-to-gaerten'
            """
        ).fetchone()
        self.assertIsNotNone(media_row)
        stable_id, caption, coordinate_source, geo_note = media_row
        self.assertRegex(stable_id, ASCII_DEMO_ID_RE)
        self.assertNotRegex(stable_id, CYRILLIC_RE)
        self.assertRegex(caption, CYRILLIC_RE)
        self.assertRegex(geo_note, CYRILLIC_RE)
        self.assertEqual(coordinate_source, "manual")


if __name__ == "__main__":
    unittest.main()
