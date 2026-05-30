from pathlib import Path
import sqlite3
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "scripts" / "storage" / "migrations" / "001_initial_schema.sql"
DEMO_SEED = ROOT / "scripts" / "storage" / "seeds" / "demo_objects.sql"

import sys

sys.path.insert(0, str(ROOT))

from scripts.storage import SQLiteStorage  # noqa: E402


MIN_GERMAN_DEMO_OBJECTS = 21

REQUIRED_GERMAN_OBJECTS = {
    "berlin-gaerten-der-welt": ("Берлин", "cable_gondola"),
    "thale-hexentanzplatz": ("Саксония-Анхальт", "cable_gondola"),
    "thale-rosstrappe": ("Саксония-Анхальт", "cable_tourist"),
    "stuttgart-standseilbahn": ("Баден-Вюртемберг", "funicular_classic"),
    "stuttgart-zahnradbahn": ("Баден-Вюртемберг", "rail_cog"),
    "bayerische-zugspitzbahn": ("Бавария", "rail_cog"),
    "seilbahn-zugspitze": ("Бавария", "cable_aerial_tram"),
    "zugspitze-gletscherbahn": ("Бавария", "cable_aerial_tram"),
    "wuppertaler-schwebebahn": ("Северный Рейн-Вестфалия", "rail_suspended"),
    "dresden-schwebebahn": ("Саксония", "rail_suspended"),
    "dresden-standseilbahn": ("Саксония", "funicular_classic"),
    "nerobergbahn": ("Гессен", "funicular_water"),
    "bad-schandau-lift": ("Саксония", "elevator_vertical"),
    "heidelberg-bergbahn": ("Баден-Вюртемберг", "funicular_classic"),
    "bad-harzburg-burgbergseilbahn": ("Нижняя Саксония", "cable_aerial_tram"),
    "wurmbergseilbahn": ("Нижняя Саксония", "cable_gondola"),
    "dortmund-h-bahn": ("Северный Рейн-Вестфалия", "suspended_train"),
    "duesseldorf-skytrain": ("Северный Рейн-Вестфалия", "suspended_train"),
    "baden-baden-merkurbergbahn": ("Баден-Вюртемберг", "funicular_classic"),
    "koblenz-seilbahn": ("Рейнланд-Пфальц", "cable_urban"),
    "koeln-seilbahn": ("Северный Рейн-Вестфалия", "cable_tourist"),
}


class StorageContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "mir-trossov.sqlite3"
        self.storage = SQLiteStorage(self.database_path)
        self.storage.migrate()

    def tearDown(self) -> None:
        self.storage.close()
        self.temp_dir.cleanup()

    def test_migration_file_is_real_sqlite_schema(self) -> None:
        self.assertTrue(MIGRATION.exists())
        self.assertTrue(DEMO_SEED.exists())

        connection = sqlite3.connect(":memory:")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(MIGRATION.read_text(encoding="utf-8"))

        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        self.assertGreaterEqual(
            tables,
            {
                "schema_migrations",
                "visit_statuses",
                "transport_types",
                "transport_objects",
                "visits",
                "media_assets",
                "tickets",
            },
        )
        self.assertEqual(
            connection.execute("SELECT count(*) FROM visit_statuses").fetchone()[0],
            4,
        )
        self.assertEqual(
            connection.execute("SELECT count(*) FROM transport_types").fetchone()[0],
            19,
        )

    def test_demo_seed_initializes_objects_once(self) -> None:
        self.storage.seed_demo_objects()
        self.storage.update_object_status("vorobyovy-gory", "visited")
        self.storage.update_object_status("berlin-gaerten-der-welt", "planned")
        self.storage.seed_demo_objects()

        objects = self.storage.list_objects()
        self.assertGreaterEqual(len(objects), 15)
        self.assertIn("vorobyovy-gory", {obj["id"] for obj in objects})
        self.assertIn("berlin-gaerten-der-welt", {obj["id"] for obj in objects})
        self.assertEqual(
            self.storage.get_object("vorobyovy-gory")["transport_type_id"],
            "cable_urban",
        )
        self.assertEqual(
            self.storage.get_object("vorobyovy-gory")["visit_status_id"],
            "visited",
        )
        self.assertEqual(
            self.storage.get_object("berlin-gaerten-der-welt")["visit_status_id"],
            "planned",
        )

    def test_demo_seed_contains_required_german_catalog_objects(self) -> None:
        self.storage.seed_demo_objects()

        objects_by_id = {obj["id"]: obj for obj in self.storage.list_objects()}
        german_objects_by_id = {
            object_id: obj
            for object_id, obj in objects_by_id.items()
            if obj["country"] == "Германия"
        }
        self.assertGreaterEqual(
            len(german_objects_by_id),
            MIN_GERMAN_DEMO_OBJECTS,
        )

        for object_id, (expected_region, expected_type) in REQUIRED_GERMAN_OBJECTS.items():
            with self.subTest(object_id=object_id):
                obj = german_objects_by_id.get(object_id)
                self.assertIsNotNone(obj)
                assert obj is not None
                self.assertEqual(obj["region"], expected_region)
                self.assertEqual(obj["transport_type_id"], expected_type)
                self.assertTrue(obj["city"])
                self.assertTrue(obj["description"])

    def test_object_crud_and_status_persist_after_reopen(self) -> None:
        self.storage.upsert_object(
            {
                "id": "test-lift",
                "title": "Тестовый лифт",
                "transport_type_id": "elevator_vertical",
                "visit_status_id": "planned",
                "country": "Россия",
                "region": "Тестовый регион",
                "city": "Тестовый город",
                "latitude": 55.0,
                "longitude": 37.0,
                "description": "Черновой объект для проверки CRUD.",
            }
        )
        self.storage.update_object_status("test-lift", "visited")
        self.assertEqual(self.storage.get_object("test-lift")["visit_status_id"], "visited")

        self.storage.close()
        self.storage = SQLiteStorage(self.database_path)
        self.storage.migrate()

        restored = self.storage.get_object("test-lift")
        self.assertIsNotNone(restored)
        self.assertEqual(restored["visit_status_id"], "visited")

        self.storage.delete_object("test-lift")
        self.assertIsNone(self.storage.get_object("test-lift"))

    def test_visit_status_transitions_persist_after_reopen(self) -> None:
        self.storage.seed_demo_objects()
        expected_statuses = ["not_visited", "planned", "visited", "favorite"]

        for status_id in expected_statuses:
            updated = self.storage.update_object_status("vorobyovy-gory", status_id)
            self.assertEqual(updated["visit_status_id"], status_id)
            self.assertEqual(
                self.storage.get_object("vorobyovy-gory")["visit_status_id"],
                status_id,
            )

        self.storage.close()
        self.storage = SQLiteStorage(self.database_path)
        self.storage.migrate()

        restored = self.storage.get_object("vorobyovy-gory")
        self.assertIsNotNone(restored)
        self.assertEqual(restored["visit_status_id"], "favorite")

    def test_visit_crud_and_cascade_delete(self) -> None:
        self.storage.seed_demo_objects()

        self.storage.upsert_visit(
            {
                "id": "visit-vorobyovy-2026",
                "transport_object_id": "vorobyovy-gory",
                "visited_on": "2026-05-30",
                "title": "Семейная поездка",
                "notes": "Проверка журнала посещений.",
                "impression_rating": 5,
            }
        )
        visit = self.storage.get_visit("visit-vorobyovy-2026")
        self.assertEqual(visit["impression_rating"], 5)
        self.assertEqual(len(self.storage.list_visits("vorobyovy-gory")), 1)

        self.storage.upsert_visit(
            {
                "id": "visit-vorobyovy-2026",
                "transport_object_id": "vorobyovy-gory",
                "visited_on": "2026-05-30",
                "title": "Семейная поездка",
                "notes": "Обновленные заметки.",
                "impression_rating": 4,
            }
        )
        self.assertEqual(self.storage.get_visit("visit-vorobyovy-2026")["notes"], "Обновленные заметки.")

        self.storage.delete_visit("visit-vorobyovy-2026")
        self.assertIsNone(self.storage.get_visit("visit-vorobyovy-2026"))

        self.storage.upsert_visit(
            {
                "id": "visit-vorobyovy-2026",
                "transport_object_id": "vorobyovy-gory",
                "visited_on": "2026-05-30",
            }
        )
        self.storage.delete_object("vorobyovy-gory")
        self.assertEqual(self.storage.list_visits("vorobyovy-gory"), [])

    def test_constraints_reject_invalid_references_and_ratings(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.storage.upsert_object(
                {
                    "id": "bad-type",
                    "title": "Некорректный тип",
                    "transport_type_id": "missing",
                    "visit_status_id": "planned",
                    "country": "Россия",
                    "latitude": 55.0,
                    "longitude": 37.0,
                }
            )

        self.storage.seed_demo_objects()
        with self.assertRaises(sqlite3.IntegrityError):
            self.storage.upsert_visit(
                {
                    "id": "bad-rating",
                    "transport_object_id": "vorobyovy-gory",
                    "visited_on": "2026-05-30",
                    "impression_rating": 6,
                }
            )


if __name__ == "__main__":
    unittest.main()
