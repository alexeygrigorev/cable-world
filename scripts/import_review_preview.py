from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_REVIEW_STATES = {"candidate", "approved", "rejected"}
ALLOWED_TRANSPORT_TYPE_IDS = {
    "cable_gondola",
    "cable_aerial_tram",
    "cable_urban",
    "cable_tourist",
    "funicular_classic",
    "funicular_water",
    "funicular_modern",
    "rail_cog",
    "rail_mountain",
    "rail_suspended",
    "elevator_vertical",
    "elevator_inclined",
    "elevator_panoramic",
    "suspended_train",
    "monorail",
    "suspended_ferry",
    "escalator_unusual",
    "special_transport_system",
    "unique_engineering_object",
}
ALLOWED_OPERATIONAL_STATUSES = {
    "active",
    "active_seasonal",
    "temporarily_closed_planned",
    "temporarily_closed_unplanned",
    "closed",
    "historical",
    "unknown",
}


class ReviewPreviewError(ValueError):
    pass


def load_staging_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("records", "candidates"):
            if key in payload:
                records = payload[key]
                if isinstance(records, list):
                    return records
                raise ReviewPreviewError(f"staging JSON поле {key} должно быть массивом")
        return [payload]
    raise ReviewPreviewError(
        "staging JSON должен быть одиночной записью, массивом записей, "
        "объектом с records или объектом с candidates"
    )


def approved_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    approved: list[dict[str, Any]] = []
    for record in records:
        state = str(record.get("review", {}).get("state", ""))
        if state not in ALLOWED_REVIEW_STATES:
            raise ReviewPreviewError(f"{record.get('id', '<без id>')}: неизвестный review.state")
        if state == "approved":
            validate_approved_record(record)
            approved.append(record)
    return approved


def validate_approved_record(record: dict[str, Any]) -> None:
    record_id = str(record.get("id", "<без id>"))
    localized_ru = record.get("localized", {}).get("ru", {})
    title = str(localized_ru.get("title", "")).strip()
    description = str(localized_ru.get("description", "")).strip()
    transport_type_id = str(record.get("transport_type_id", ""))
    operational_status = str(record.get("operational_status", "unknown"))
    operator = str(record.get("operator", "")).strip()
    source_urls = record.get("source_urls", [])

    if not title or not _has_cyrillic(title):
        raise ReviewPreviewError(f"{record_id}: нужен русский localized.ru.title")
    if not description or not _has_cyrillic(description):
        raise ReviewPreviewError(f"{record_id}: нужен русский localized.ru.description")
    if transport_type_id not in ALLOWED_TRANSPORT_TYPE_IDS:
        raise ReviewPreviewError(f"{record_id}: неизвестный transport_type_id")
    if not _coordinate_in_range(record.get("latitude"), -90.0, 90.0):
        raise ReviewPreviewError(f"{record_id}: некорректная latitude")
    if not _coordinate_in_range(record.get("longitude"), -180.0, 180.0):
        raise ReviewPreviewError(f"{record_id}: некорректная longitude")
    if not operator:
        raise ReviewPreviewError(f"{record_id}: нужен оператор")
    if not isinstance(source_urls, list) or not any(_is_url(url) for url in source_urls):
        raise ReviewPreviewError(f"{record_id}: нужен хотя бы один источник")
    if operational_status not in ALLOWED_OPERATIONAL_STATUSES:
        raise ReviewPreviewError(f"{record_id}: неизвестный operational_status")

    if operational_status != "unknown":
        status_source_url = str(record.get("status_source_url", "")).strip()
        status_checked_at = str(record.get("status_checked_at", "")).strip()
        status_note = str(record.get("status_note", "")).strip()
        if not _is_url(status_source_url) or not status_checked_at or not status_note:
            raise ReviewPreviewError(
                f"{record_id}: для operational_status нужен свежий официальный источник"
            )


def build_preview_json(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [transport_object_payload(record) for record in approved_records(records)]


def transport_object_payload(record: dict[str, Any]) -> dict[str, Any]:
    localized_ru = record["localized"]["ru"]
    return {
        "id": record["id"],
        "title": localized_ru["title"],
        "transport_type_id": record["transport_type_id"],
        "visit_status_id": record.get("visit_status_id", "not_visited"),
        "country": record["country"],
        "region": record.get("region", ""),
        "city": record.get("city", ""),
        "latitude": record["latitude"],
        "longitude": record["longitude"],
        "description": localized_ru["description"],
        "notes": record.get("notes", ""),
        "opened_year": record.get("opened_year"),
        "operator": record.get("operator"),
        "manufacturer": record.get("manufacturer"),
        "operational_status": record.get("operational_status", "unknown"),
        "status_checked_at": record.get("status_checked_at", ""),
        "status_source_url": record.get("status_source_url", ""),
        "status_note": record.get("status_note", ""),
    }


def build_preview_sql(records: list[dict[str, Any]]) -> str:
    objects = build_preview_json(records)
    if not objects:
        return "-- Нет approved-записей для preview seed.\n"

    rows = ",\n".join(_sql_row(obj) for obj in objects)
    return (
        "INSERT INTO transport_objects (\n"
        "    id, title, transport_type_id, visit_status_id, country, region, city,\n"
        "    latitude, longitude, description, notes, opened_year, operator, manufacturer,\n"
        "    operational_status, status_checked_at, status_source_url, status_note,\n"
        "    created_at, updated_at\n"
        ") VALUES\n"
        f"{rows}\n"
        "ON CONFLICT(id) DO UPDATE SET\n"
        "    title = excluded.title,\n"
        "    transport_type_id = excluded.transport_type_id,\n"
        "    country = excluded.country,\n"
        "    region = excluded.region,\n"
        "    city = excluded.city,\n"
        "    latitude = excluded.latitude,\n"
        "    longitude = excluded.longitude,\n"
        "    description = excluded.description,\n"
        "    notes = excluded.notes,\n"
        "    opened_year = excluded.opened_year,\n"
        "    operator = excluded.operator,\n"
        "    manufacturer = excluded.manufacturer,\n"
        "    operational_status = excluded.operational_status,\n"
        "    status_checked_at = excluded.status_checked_at,\n"
        "    status_source_url = excluded.status_source_url,\n"
        "    status_note = excluded.status_note,\n"
        "    updated_at = excluded.updated_at;\n"
    )


def _sql_row(obj: dict[str, Any]) -> str:
    values = [
        _sql_value(obj["id"]),
        _sql_value(obj["title"]),
        _sql_value(obj["transport_type_id"]),
        _sql_value(obj["visit_status_id"]),
        _sql_value(obj["country"]),
        _sql_value(obj["region"]),
        _sql_value(obj["city"]),
        _sql_value(obj["latitude"]),
        _sql_value(obj["longitude"]),
        _sql_value(obj["description"]),
        _sql_value(obj["notes"]),
        _sql_value(obj["opened_year"]),
        _sql_value(obj["operator"]),
        _sql_value(obj["manufacturer"]),
        _sql_value(obj["operational_status"]),
        _sql_value(obj["status_checked_at"]),
        _sql_value(obj["status_source_url"]),
        _sql_value(obj["status_note"]),
        "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')",
        "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')",
    ]
    return "(" + ", ".join(values) + ")"


def _sql_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int | float):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def _coordinate_in_range(value: Any, minimum: float, maximum: float) -> bool:
    if isinstance(value, bool):
        return False
    try:
        coordinate = float(value)
    except (TypeError, ValueError):
        return False
    return minimum <= coordinate <= maximum


def _has_cyrillic(value: str) -> bool:
    return any("А" <= char <= "я" or char in "Ёё" for char in value)


def _is_url(value: Any) -> bool:
    text = str(value).strip()
    return text.startswith("https://") or text.startswith("http://")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Генерирует preview JSON/SQL только из approved staging-записей."
    )
    parser.add_argument("input", type=Path, help="Путь к staging JSON")
    parser.add_argument("--json-out", type=Path, help="Куда записать preview JSON")
    parser.add_argument("--sql-out", type=Path, help="Куда записать preview SQL")
    args = parser.parse_args()

    records = load_staging_records(args.input)
    preview_json = build_preview_json(records)
    preview_sql = build_preview_sql(records)

    if args.json_out:
        args.json_out.write_text(
            json.dumps(preview_json, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.sql_out:
        args.sql_out.write_text(preview_sql, encoding="utf-8")
    if not args.json_out and not args.sql_out:
        print(json.dumps({"objects": preview_json, "sql": preview_sql}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
