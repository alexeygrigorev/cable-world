from pathlib import Path
import sqlite3
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "scripts" / "storage" / "migrations"
MIGRATION = MIGRATIONS_DIR / "001_initial_schema.sql"
OPERATIONAL_MIGRATION = MIGRATIONS_DIR / "002_operational_status.sql"
MEDIA_GEO_ROUTES_MIGRATION = MIGRATIONS_DIR / "003_media_geo_routes.sql"
DEMO_SEED = ROOT / "scripts" / "storage" / "seeds" / "demo_objects.sql"

import sys

sys.path.insert(0, str(ROOT))

from scripts.storage import MediaAsset, SQLiteStorage, Ticket  # noqa: E402


MIN_GERMAN_DEMO_OBJECTS = 21
EXPECTED_SQLITE_DEMO_OBJECTS = 34

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

REPLACED_LEGACY_RUSSIA_IDS = {
    "vorobyovy-gory",
    "nizhny-novgorod",
}

REQUIRED_EUROPE_OBJECTS = {
    "braga-bom-jesus-funicular": ("Португалия", "funicular_water", "unknown"),
    "grenoble-bastille-cable-car": ("Франция", "cable_tourist", "unknown"),
    "como-brunate-funicular": ("Италия", "funicular_classic", "unknown"),
    "prague-petrin-funicular": ("Чехия", "funicular_classic", "temporarily_closed_planned"),
    "stary-smokovec-hrebienok-funicular": ("Словакия", "funicular_classic", "unknown"),
    "zakopane-kasprowy-wierch-cable-car": ("Польша", "cable_aerial_tram", "unknown"),
}

REQUIRED_RUSSIA_OBJECTS = {
    "nizhny-novgorod-bor-cable-car": ("Россия", "cable_urban", "active"),
    "moscow-vorobyovy-gory-cable-car": ("Россия", "cable_urban", "active"),
    "vladivostok-funicular": ("Россия", "funicular_classic", "active"),
    "nizhny-novgorod-kremlin-funicular": ("Россия", "funicular_modern", "active"),
    "pyatigorsk-mashuk-cable-car": ("Россия", "cable_aerial_tram", "active"),
    "svetlogorsk-panorama-elevator": ("Россия", "elevator_panoramic", "active"),
    "moscow-monorail": ("Россия", "monorail", "historical"),
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
        self.assertTrue(OPERATIONAL_MIGRATION.exists())
        self.assertTrue(MEDIA_GEO_ROUTES_MIGRATION.exists())
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

    def test_operational_status_migration_adds_independent_fields(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.execute("PRAGMA foreign_keys = ON")
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            connection.executescript(path.read_text(encoding="utf-8"))

        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(transport_objects)").fetchall()
        }
        for column in [
            "visit_status_id",
            "operational_status",
            "status_checked_at",
            "status_source_url",
            "status_note",
        ]:
            self.assertIn(column, columns)
        self.assertEqual(
            connection.execute("SELECT version FROM schema_migrations WHERE version = '002_operational_status'").fetchone()[0],
            "002_operational_status",
        )

    def test_media_geo_routes_migration_adds_ui_foundation(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.execute("PRAGMA foreign_keys = ON")
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            connection.executescript(path.read_text(encoding="utf-8"))

        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        self.assertGreaterEqual(
            tables,
            {
                "object_stations",
                "route_directions",
                "route_segments",
            },
        )
        media_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(media_assets)").fetchall()
        }
        for column in [
            "latitude",
            "longitude",
            "coordinate_source",
            "geo_note",
            "station_id",
            "route_direction_id",
            "route_segment_id",
        ]:
            self.assertIn(column, media_columns)
        self.assertEqual(
            connection.execute("SELECT version FROM schema_migrations WHERE version = '003_media_geo_routes'").fetchone()[0],
            "003_media_geo_routes",
        )

    def test_demo_seed_initializes_objects_once(self) -> None:
        self.storage.seed_demo_objects()
        self.storage.update_object_status("moscow-vorobyovy-gory-cable-car", "visited")
        self.storage.update_object_status("berlin-gaerten-der-welt", "planned")
        self.storage.seed_demo_objects()

        objects = self.storage.list_objects()
        self.assertGreaterEqual(len(objects), 15)
        self.assertIn("moscow-vorobyovy-gory-cable-car", {obj["id"] for obj in objects})
        self.assertIn("berlin-gaerten-der-welt", {obj["id"] for obj in objects})
        self.assertEqual(
            self.storage.get_object("moscow-vorobyovy-gory-cable-car")["transport_type_id"],
            "cable_urban",
        )
        self.assertEqual(
            self.storage.get_object("moscow-vorobyovy-gory-cable-car")["visit_status_id"],
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
                self.assertIn("operational_status", obj)
                self.assertIn(
                    obj["operational_status"],
                    {
                        "active",
                        "active_seasonal",
                        "temporarily_closed_planned",
                        "temporarily_closed_unplanned",
                        "closed",
                        "historical",
                        "unknown",
                    },
                )

    def test_demo_seed_matches_integrated_catalog_for_europe_and_russia(self) -> None:
        self.storage.seed_demo_objects()

        objects_by_id = {obj["id"]: obj for obj in self.storage.list_objects()}
        self.assertEqual(len(objects_by_id), EXPECTED_SQLITE_DEMO_OBJECTS)
        self.assertTrue(REPLACED_LEGACY_RUSSIA_IDS.isdisjoint(objects_by_id))

        for object_id, (country, transport_type, operational_status) in {
            **REQUIRED_EUROPE_OBJECTS,
            **REQUIRED_RUSSIA_OBJECTS,
        }.items():
            with self.subTest(object_id=object_id):
                obj = objects_by_id.get(object_id)
                self.assertIsNotNone(obj)
                assert obj is not None
                self.assertEqual(obj["country"], country)
                self.assertEqual(obj["transport_type_id"], transport_type)
                self.assertEqual(obj["operational_status"], operational_status)
                self.assertEqual(obj["status_checked_at"], "2026-05-30")
                self.assertTrue(obj["status_source_url"])
                self.assertTrue(obj["status_note"])

        self.assertEqual(objects_by_id["vladivostok-funicular"]["region"], "Приморский край")
        self.assertEqual(objects_by_id["vladivostok-funicular"]["opened_year"], 1962)

    def test_demo_seed_merges_legacy_russia_ids_without_losing_user_data(self) -> None:
        self.storage.upsert_object(
            {
                "id": "vorobyovy-gory",
                "title": "Канатная дорога на Воробьевых горах",
                "transport_type_id": "cable_urban",
                "visit_status_id": "favorite",
                "country": "Россия",
                "region": "Москва",
                "city": "Москва",
                "latitude": 55.7103,
                "longitude": 37.5517,
                "description": "Legacy объект из v0.1.15.",
            }
        )
        self.storage.upsert_object(
            {
                "id": "nizhny-novgorod",
                "title": "Нижегородская канатная дорога",
                "transport_type_id": "cable_aerial_tram",
                "visit_status_id": "planned",
                "country": "Россия",
                "region": "Нижний Новгород",
                "city": "Нижний Новгород",
                "latitude": 56.3299,
                "longitude": 44.0186,
                "description": "Legacy объект из v0.1.15.",
            }
        )
        self.storage.upsert_visit(
            {
                "id": "visit-legacy-vorobyovy",
                "transport_object_id": "vorobyovy-gory",
                "visited_on": "2026-05-30",
                "title": "Старая поездка",
            }
        )
        self.storage.upsert_media_asset(
            MediaAsset(
                id="photo-legacy-vorobyovy",
                transport_object_id="vorobyovy-gory",
                visit_id="visit-legacy-vorobyovy",
                kind="photo",
                local_path="media/vorobyovy-gory/photo-legacy-vorobyovy.jpg",
                caption="Фото до миграции id.",
            )
        )
        self.storage.upsert_ticket(
            Ticket(
                id="ticket-legacy-vorobyovy",
                transport_object_id="vorobyovy-gory",
                visit_id="visit-legacy-vorobyovy",
                media_asset_id="photo-legacy-vorobyovy",
                title="Билет до миграции",
                price_currency="RUB",
            )
        )

        self.storage.seed_demo_objects()
        self.storage.seed_demo_objects()

        objects_by_id = {obj["id"]: obj for obj in self.storage.list_objects()}
        self.assertEqual(len(objects_by_id), EXPECTED_SQLITE_DEMO_OBJECTS)
        self.assertNotIn("vorobyovy-gory", objects_by_id)
        self.assertNotIn("nizhny-novgorod", objects_by_id)
        self.assertEqual(
            objects_by_id["moscow-vorobyovy-gory-cable-car"]["visit_status_id"],
            "favorite",
        )
        self.assertEqual(
            objects_by_id["nizhny-novgorod-bor-cable-car"]["visit_status_id"],
            "planned",
        )

        visit = self.storage.get_visit("visit-legacy-vorobyovy")
        self.assertEqual(
            visit["transport_object_id"],
            "moscow-vorobyovy-gory-cable-car",
        )
        self.assertEqual(
            [row["id"] for row in self.storage.list_visits("moscow-vorobyovy-gory-cable-car")],
            ["visit-legacy-vorobyovy"],
        )

        photo = self.storage.get_media_asset("photo-legacy-vorobyovy")
        self.assertEqual(
            photo["transport_object_id"],
            "moscow-vorobyovy-gory-cable-car",
        )
        self.assertEqual(
            [row["id"] for row in self.storage.list_object_photos("moscow-vorobyovy-gory-cable-car")],
            ["photo-legacy-vorobyovy"],
        )

        ticket = self.storage.get_ticket("ticket-legacy-vorobyovy")
        self.assertEqual(
            ticket["transport_object_id"],
            "moscow-vorobyovy-gory-cable-car",
        )
        self.assertEqual(
            [row["id"] for row in self.storage.list_tickets(object_id="moscow-vorobyovy-gory-cable-car")],
            ["ticket-legacy-vorobyovy"],
        )

    def test_demo_seed_records_operational_status_source_and_check_date(self) -> None:
        self.storage.seed_demo_objects()

        berlin = self.storage.get_object("berlin-gaerten-der-welt")
        self.assertIsNotNone(berlin)
        assert berlin is not None
        self.assertEqual(berlin["visit_status_id"], "not_visited")
        self.assertEqual(berlin["operational_status"], "active_seasonal")
        self.assertEqual(berlin["status_checked_at"], "2026-05-30")
        self.assertIn("gaertenderwelt.de", berlin["status_source_url"])
        self.assertIn("Сезонный график", berlin["status_note"])

    def test_demo_seed_adds_gaerten_der_welt_route_contract(self) -> None:
        self.storage.seed_demo_objects()

        stations = self.storage.list_object_stations("berlin-gaerten-der-welt")
        self.assertEqual(
            [station["id"] for station in stations],
            [
                "berlin-gaerten-der-welt-station-kienbergpark",
                "berlin-gaerten-der-welt-station-wolkenhain",
                "berlin-gaerten-der-welt-station-gaerten-der-welt",
            ],
        )
        self.assertEqual(
            [station["title"] for station in stations],
            ["Киенбергпарк", "Волькенхайн", "Сады мира"],
        )
        self.assertEqual(
            [station["station_role"] for station in stations],
            ["lower", "upper", "lower"],
        )
        self.assertTrue(all(station["latitude"] and station["longitude"] for station in stations))

        directions = self.storage.list_route_directions("berlin-gaerten-der-welt")
        self.assertEqual(
            [direction["id"] for direction in directions],
            [
                "berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten",
                "berlin-gaerten-der-welt-direction-gaerten-to-kienbergpark",
            ],
        )
        self.assertEqual(
            [direction["direction_label"] for direction in directions],
            ["от Киенбергпарка к Садам мира", "от Садов мира к Киенбергпарку"],
        )
        self.assertEqual(
            [(direction["from_station_id"], direction["to_station_id"]) for direction in directions],
            [
                (
                    "berlin-gaerten-der-welt-station-kienbergpark",
                    "berlin-gaerten-der-welt-station-gaerten-der-welt",
                ),
                (
                    "berlin-gaerten-der-welt-station-gaerten-der-welt",
                    "berlin-gaerten-der-welt-station-kienbergpark",
                ),
            ],
        )

        outbound_segments = self.storage.list_route_segments(
            "berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten"
        )
        self.assertEqual(
            [segment["direction_label"] for segment in outbound_segments],
            ["вверх к Волькенхайну", "вниз к Садам мира"],
        )
        self.assertEqual(
            [(segment["from_station_id"], segment["to_station_id"]) for segment in outbound_segments],
            [
                (
                    "berlin-gaerten-der-welt-station-kienbergpark",
                    "berlin-gaerten-der-welt-station-wolkenhain",
                ),
                (
                    "berlin-gaerten-der-welt-station-wolkenhain",
                    "berlin-gaerten-der-welt-station-gaerten-der-welt",
                ),
            ],
        )
        inbound_segments = self.storage.list_route_segments(
            "berlin-gaerten-der-welt-direction-gaerten-to-kienbergpark"
        )
        self.assertEqual(
            [segment["direction_label"] for segment in inbound_segments],
            ["вверх к Волькенхайну", "вниз к Киенбергпарку"],
        )
        self.assertEqual(
            [(segment["from_station_id"], segment["to_station_id"]) for segment in inbound_segments],
            [
                (
                    "berlin-gaerten-der-welt-station-gaerten-der-welt",
                    "berlin-gaerten-der-welt-station-wolkenhain",
                ),
                (
                    "berlin-gaerten-der-welt-station-wolkenhain",
                    "berlin-gaerten-der-welt-station-kienbergpark",
                ),
            ],
        )

        video = self.storage.get_media_asset("berlin-gaerten-der-welt-demo-video-kienbergpark-to-gaerten")
        self.assertIsNotNone(video)
        assert video is not None
        self.assertEqual(video["kind"], "video")
        self.assertEqual(video["coordinate_source"], "manual")
        self.assertIn("будущий UI", video["geo_note"])
        self.assertEqual(
            video["route_direction_id"],
            "berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten",
        )

        self.storage.seed_demo_objects()
        self.assertEqual(len(self.storage.list_object_stations("berlin-gaerten-der-welt")), 3)
        self.assertEqual(len(self.storage.list_route_directions("berlin-gaerten-der-welt")), 2)
        self.assertEqual(
            len(
                self.storage.connection.execute(
                    """
                    SELECT id
                    FROM route_segments
                    WHERE transport_object_id = 'berlin-gaerten-der-welt'
                    """
                ).fetchall()
            ),
            4,
        )

    def test_gaerten_der_welt_object_mode_hotspots_wait_for_engineering_point_schema(self) -> None:
        self.storage.seed_demo_objects()

        tables = {
            row[0]
            for row in self.storage.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        self.assertNotIn("engineering_points", tables)
        self.assertNotIn("EngineeringPoint", tables)

        seed_text = DEMO_SEED.read_text(encoding="utf-8")
        self.assertIn("TODO(object-mode)", seed_text)
        self.assertIn("EngineeringPoint/hotspot seed", seed_text)
        self.assertIn("не геодезические инженерные точки", seed_text)

    def test_visit_status_update_does_not_change_operational_status(self) -> None:
        self.storage.seed_demo_objects()

        before = self.storage.get_object("berlin-gaerten-der-welt")
        self.assertIsNotNone(before)
        assert before is not None
        self.storage.update_object_status("berlin-gaerten-der-welt", "favorite")
        after = self.storage.get_object("berlin-gaerten-der-welt")
        self.assertIsNotNone(after)
        assert after is not None

        self.assertEqual(after["visit_status_id"], "favorite")
        self.assertEqual(after["operational_status"], before["operational_status"])
        self.assertEqual(after["status_checked_at"], before["status_checked_at"])
        self.assertEqual(after["status_source_url"], before["status_source_url"])

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
            updated = self.storage.update_object_status("moscow-vorobyovy-gory-cable-car", status_id)
            self.assertEqual(updated["visit_status_id"], status_id)
            self.assertEqual(
                self.storage.get_object("moscow-vorobyovy-gory-cable-car")["visit_status_id"],
                status_id,
            )

        self.storage.close()
        self.storage = SQLiteStorage(self.database_path)
        self.storage.migrate()

        restored = self.storage.get_object("moscow-vorobyovy-gory-cable-car")
        self.assertIsNotNone(restored)
        self.assertEqual(restored["visit_status_id"], "favorite")

    def test_visit_crud_and_cascade_delete(self) -> None:
        self.storage.seed_demo_objects()
        before_status = self.storage.get_object("moscow-vorobyovy-gory-cable-car")
        self.assertIsNotNone(before_status)
        assert before_status is not None

        self.storage.upsert_visit(
            {
                "id": "visit-vorobyovy-2026",
                "transport_object_id": "moscow-vorobyovy-gory-cable-car",
                "visited_on": "2026-05-30",
                "title": "Семейная поездка",
                "notes": "Проверка журнала посещений.",
                "impression_rating": 5,
            }
        )
        visit = self.storage.get_visit("visit-vorobyovy-2026")
        self.assertEqual(visit["impression_rating"], 5)
        self.assertEqual(len(self.storage.list_visits("moscow-vorobyovy-gory-cable-car")), 1)
        after_visit = self.storage.get_object("moscow-vorobyovy-gory-cable-car")
        self.assertEqual(after_visit["visit_status_id"], before_status["visit_status_id"])
        self.assertEqual(after_visit["operational_status"], before_status["operational_status"])

        self.storage.close()
        self.storage = SQLiteStorage(self.database_path)
        self.storage.migrate()

        restored_visits = self.storage.list_visits("moscow-vorobyovy-gory-cable-car")
        self.assertEqual(len(restored_visits), 1)
        self.assertEqual(restored_visits[0]["title"], "Семейная поездка")
        restored_object = self.storage.get_object("moscow-vorobyovy-gory-cable-car")
        self.assertEqual(restored_object["visit_status_id"], before_status["visit_status_id"])
        self.assertEqual(restored_object["operational_status"], before_status["operational_status"])

        self.storage.upsert_visit(
            {
                "id": "visit-vorobyovy-2026",
                "transport_object_id": "moscow-vorobyovy-gory-cable-car",
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
                "transport_object_id": "moscow-vorobyovy-gory-cable-car",
                "visited_on": "2026-05-30",
            }
        )
        self.storage.delete_object("moscow-vorobyovy-gory-cable-car")
        self.assertEqual(self.storage.list_visits("moscow-vorobyovy-gory-cable-car"), [])

    def test_media_asset_photo_crud_and_object_listing(self) -> None:
        self.storage.seed_demo_objects()

        created = self.storage.upsert_media_asset(
            MediaAsset(
                id="photo-vorobyovy-mvp",
                transport_object_id="moscow-vorobyovy-gory-cable-car",
                kind="photo",
                local_path="media/moscow-vorobyovy-gory-cable-car/photo-vorobyovy-mvp.jpg",
                caption="Фото MVP: запись без копирования файла.",
                latitude=55.7103,
                longitude=37.5517,
                coordinate_source="manual",
                geo_note="Точка вручную поставлена у станции для проверки UI.",
            )
        )

        self.assertEqual(created["kind"], "photo")
        self.assertEqual(created["transport_object_id"], "moscow-vorobyovy-gory-cable-car")
        self.assertEqual(created["local_path"], "media/moscow-vorobyovy-gory-cable-car/photo-vorobyovy-mvp.jpg")
        self.assertEqual(created["coordinate_source"], "manual")
        self.assertEqual(created["geo_note"], "Точка вручную поставлена у станции для проверки UI.")
        self.assertEqual(
            self.storage.get_object("moscow-vorobyovy-gory-cable-car")["photo_count"],
            1,
        )

        photos = self.storage.list_object_photos("moscow-vorobyovy-gory-cable-car")
        self.assertEqual([photo["id"] for photo in photos], ["photo-vorobyovy-mvp"])

        self.storage.upsert_media_asset(
            {
                "id": "photo-vorobyovy-mvp",
                "transport_object_id": "moscow-vorobyovy-gory-cable-car",
                "kind": "photo",
                "local_path": "media/moscow-vorobyovy-gory-cable-car/photo-vorobyovy-mvp.jpg",
                "caption": "Обновленная подпись MVP.",
            }
        )
        self.assertEqual(
            self.storage.get_media_asset("photo-vorobyovy-mvp")["caption"],
            "Обновленная подпись MVP.",
        )

        self.storage.delete_media_asset("photo-vorobyovy-mvp")
        self.assertIsNone(self.storage.get_media_asset("photo-vorobyovy-mvp"))
        self.assertEqual(self.storage.list_object_photos("moscow-vorobyovy-gory-cable-car"), [])

    def test_ticket_crud_lists_by_object_and_visit_after_reopen(self) -> None:
        self.storage.seed_demo_objects()
        self.storage.upsert_visit(
            {
                "id": "visit-vorobyovy-ticket-2026",
                "transport_object_id": "moscow-vorobyovy-gory-cable-car",
                "visited_on": "2026-05-30",
                "title": "Поездка с билетом",
            }
        )
        self.storage.upsert_media_asset(
            MediaAsset(
                id="ticket-scan-vorobyovy-2026",
                transport_object_id="moscow-vorobyovy-gory-cable-car",
                visit_id="visit-vorobyovy-ticket-2026",
                kind="document",
                local_path="media/moscow-vorobyovy-gory-cable-car/ticket-scan-vorobyovy-2026.jpg",
                caption="Скан билета.",
            )
        )

        created = self.storage.upsert_ticket(
            Ticket(
                id="ticket-vorobyovy-2026",
                transport_object_id="moscow-vorobyovy-gory-cable-car",
                visit_id="visit-vorobyovy-ticket-2026",
                media_asset_id="ticket-scan-vorobyovy-2026",
                title="Билет на канатную дорогу",
                issued_on="2026-05-30",
                price_amount=350.0,
                price_currency="RUB",
                notes="Локальная запись без внешнего сервера.",
            )
        )

        self.assertEqual(created["transport_object_id"], "moscow-vorobyovy-gory-cable-car")
        self.assertEqual(created["visit_id"], "visit-vorobyovy-ticket-2026")
        self.assertEqual(created["media_asset_id"], "ticket-scan-vorobyovy-2026")
        self.assertEqual(created["price_currency"], "RUB")
        self.assertEqual(
            [ticket["id"] for ticket in self.storage.list_tickets(object_id="moscow-vorobyovy-gory-cable-car")],
            ["ticket-vorobyovy-2026"],
        )
        self.assertEqual(
            [ticket["id"] for ticket in self.storage.list_tickets(visit_id="visit-vorobyovy-ticket-2026")],
            ["ticket-vorobyovy-2026"],
        )

        self.storage.upsert_ticket(
            {
                "id": "ticket-vorobyovy-2026",
                "transport_object_id": "moscow-vorobyovy-gory-cable-car",
                "visit_id": "visit-vorobyovy-ticket-2026",
                "media_asset_id": "ticket-scan-vorobyovy-2026",
                "title": "Семейный билет",
                "issued_on": "2026-05-30",
                "price_amount": 700.0,
                "price_currency": "RUB",
                "notes": "Обновленная заметка.",
            }
        )
        self.assertEqual(self.storage.get_ticket("ticket-vorobyovy-2026")["title"], "Семейный билет")
        self.assertEqual(self.storage.get_object("moscow-vorobyovy-gory-cable-car")["photo_count"], 0)
        self.assertEqual(len(self.storage.list_visits("moscow-vorobyovy-gory-cable-car")), 1)

        self.storage.close()
        self.storage = SQLiteStorage(self.database_path)
        self.storage.migrate()

        restored = self.storage.list_tickets(object_id="moscow-vorobyovy-gory-cable-car")
        self.assertEqual([ticket["id"] for ticket in restored], ["ticket-vorobyovy-2026"])
        self.assertEqual(restored[0]["notes"], "Обновленная заметка.")

        self.storage.delete_visit("visit-vorobyovy-ticket-2026")
        ticket_without_visit = self.storage.get_ticket("ticket-vorobyovy-2026")
        self.assertIsNotNone(ticket_without_visit)
        assert ticket_without_visit is not None
        self.assertIsNone(ticket_without_visit["visit_id"])
        self.assertEqual(
            [ticket["id"] for ticket in self.storage.list_tickets(object_id="moscow-vorobyovy-gory-cable-car")],
            ["ticket-vorobyovy-2026"],
        )

        self.storage.delete_ticket("ticket-vorobyovy-2026")
        self.assertIsNone(self.storage.get_ticket("ticket-vorobyovy-2026"))

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
                    "transport_object_id": "moscow-vorobyovy-gory-cable-car",
                    "visited_on": "2026-05-30",
                    "impression_rating": 6,
                }
            )


if __name__ == "__main__":
    unittest.main()
