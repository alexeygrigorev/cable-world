from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any


STORAGE_DIR = Path(__file__).resolve().parent
MIGRATIONS_DIR = STORAGE_DIR / "migrations"
SEEDS_DIR = STORAGE_DIR / "seeds"


class SQLiteStorage:
    """Small SQLite contract used by tests until Godot gets a SQLite runtime plugin."""

    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self.database_path = database_path
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        self.connection.close()

    def migrate(self) -> None:
        applied = self._applied_migrations()
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = path.stem
            if version in applied:
                continue
            self.connection.executescript(path.read_text(encoding="utf-8"))
        self.connection.commit()

    def seed_demo_objects(self) -> None:
        self.connection.executescript((SEEDS_DIR / "demo_objects.sql").read_text(encoding="utf-8"))
        self.connection.commit()

    def list_objects(self) -> list[dict[str, Any]]:
        return self._query_all(
            """
            SELECT id, title, transport_type_id, visit_status_id, country, region, city,
                   latitude, longitude, description, notes, opened_year, operator,
                   manufacturer, created_at, updated_at
            FROM transport_objects
            ORDER BY title
            """
        )

    def get_object(self, object_id: str) -> dict[str, Any] | None:
        return self._query_one(
            """
            SELECT id, title, transport_type_id, visit_status_id, country, region, city,
                   latitude, longitude, description, notes, opened_year, operator,
                   manufacturer, created_at, updated_at
            FROM transport_objects
            WHERE id = ?
            """,
            (object_id,),
        )

    def upsert_object(self, data: dict[str, Any]) -> dict[str, Any]:
        required = {
            "id",
            "title",
            "transport_type_id",
            "visit_status_id",
            "country",
            "latitude",
            "longitude",
        }
        missing = sorted(required - set(data))
        if missing:
            raise ValueError(f"Missing transport object fields: {', '.join(missing)}")

        now = self._now()
        existing = self.get_object(data["id"])
        created_at = data.get("created_at") or (existing["created_at"] if existing else now)
        updated_at = data.get("updated_at") or now

        self.connection.execute(
            """
            INSERT INTO transport_objects (
                id, title, transport_type_id, visit_status_id, country, region, city,
                latitude, longitude, description, notes, opened_year, operator,
                manufacturer, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                transport_type_id = excluded.transport_type_id,
                visit_status_id = excluded.visit_status_id,
                country = excluded.country,
                region = excluded.region,
                city = excluded.city,
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                description = excluded.description,
                notes = excluded.notes,
                opened_year = excluded.opened_year,
                operator = excluded.operator,
                manufacturer = excluded.manufacturer,
                updated_at = excluded.updated_at
            """,
            (
                data["id"],
                data["title"],
                data["transport_type_id"],
                data["visit_status_id"],
                data["country"],
                data.get("region"),
                data.get("city"),
                data["latitude"],
                data["longitude"],
                data.get("description", ""),
                data.get("notes", ""),
                data.get("opened_year"),
                data.get("operator"),
                data.get("manufacturer"),
                created_at,
                updated_at,
            ),
        )
        self.connection.commit()
        obj = self.get_object(data["id"])
        assert obj is not None
        return obj

    def update_object_status(self, object_id: str, visit_status_id: str) -> dict[str, Any]:
        self.connection.execute(
            """
            UPDATE transport_objects
            SET visit_status_id = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE id = ?
            """,
            (visit_status_id, object_id),
        )
        self.connection.commit()
        obj = self.get_object(object_id)
        if obj is None:
            raise KeyError(object_id)
        return obj

    def delete_object(self, object_id: str) -> None:
        self.connection.execute("DELETE FROM transport_objects WHERE id = ?", (object_id,))
        self.connection.commit()

    def list_visits(self, object_id: str | None = None) -> list[dict[str, Any]]:
        if object_id is None:
            return self._query_all(
                """
                SELECT id, transport_object_id, visited_on, title, notes,
                       impression_rating, created_at, updated_at
                FROM visits
                ORDER BY visited_on, id
                """
            )
        return self._query_all(
            """
            SELECT id, transport_object_id, visited_on, title, notes,
                   impression_rating, created_at, updated_at
            FROM visits
            WHERE transport_object_id = ?
            ORDER BY visited_on, id
            """,
            (object_id,),
        )

    def get_visit(self, visit_id: str) -> dict[str, Any] | None:
        return self._query_one(
            """
            SELECT id, transport_object_id, visited_on, title, notes,
                   impression_rating, created_at, updated_at
            FROM visits
            WHERE id = ?
            """,
            (visit_id,),
        )

    def upsert_visit(self, data: dict[str, Any]) -> dict[str, Any]:
        required = {"id", "transport_object_id", "visited_on"}
        missing = sorted(required - set(data))
        if missing:
            raise ValueError(f"Missing visit fields: {', '.join(missing)}")

        now = self._now()
        existing = self.get_visit(data["id"])
        created_at = data.get("created_at") or (existing["created_at"] if existing else now)
        updated_at = data.get("updated_at") or now

        self.connection.execute(
            """
            INSERT INTO visits (
                id, transport_object_id, visited_on, title, notes,
                impression_rating, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                transport_object_id = excluded.transport_object_id,
                visited_on = excluded.visited_on,
                title = excluded.title,
                notes = excluded.notes,
                impression_rating = excluded.impression_rating,
                updated_at = excluded.updated_at
            """,
            (
                data["id"],
                data["transport_object_id"],
                data["visited_on"],
                data.get("title", ""),
                data.get("notes", ""),
                data.get("impression_rating"),
                created_at,
                updated_at,
            ),
        )
        self.connection.commit()
        visit = self.get_visit(data["id"])
        assert visit is not None
        return visit

    def delete_visit(self, visit_id: str) -> None:
        self.connection.execute("DELETE FROM visits WHERE id = ?", (visit_id,))
        self.connection.commit()

    def _applied_migrations(self) -> set[str]:
        exists = self.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
        ).fetchone()
        if exists is None:
            return set()
        rows = self.connection.execute("SELECT version FROM schema_migrations").fetchall()
        return {row["version"] for row in rows}

    def _query_one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        row = self.connection.execute(query, params).fetchone()
        return None if row is None else dict(row)

    def _query_all(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute(query, params).fetchall()]

    def _now(self) -> str:
        return self.connection.execute("SELECT strftime('%Y-%m-%dT%H:%M:%fZ', 'now')").fetchone()[0]
