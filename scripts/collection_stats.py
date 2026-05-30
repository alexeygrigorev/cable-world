from __future__ import annotations

from dataclasses import dataclass
from typing import Any


STATUS_NOT_VISITED = "not_visited"
STATUS_PLANNED = "planned"
STATUS_VISITED = "visited"
STATUS_FAVORITE = "favorite"

COUNTRY_IDS_BY_TITLE = {
    "Россия": "ru",
    "Германия": "de",
}


@dataclass(frozen=True)
class ProgressStats:
    id: str
    title: str
    total_count: int
    visited_count: int
    progress_percent: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "total_count": self.total_count,
            "visited_count": self.visited_count,
            "progress_percent": self.progress_percent,
        }


def calculate_collection_stats(objects: list[dict[str, Any]]) -> dict[str, Any]:
    countries_by_id: dict[str, dict[str, Any]] = {}
    transport_types_by_id: dict[str, dict[str, Any]] = {}
    total_count = 0
    visited_count = 0

    for object_data in objects:
        total_count += 1
        is_visited = status_is_visited(str(object_data.get("visit_status_id", STATUS_NOT_VISITED)))
        if is_visited:
            visited_count += 1

        country_title = str(object_data.get("country") or "Страна не указана")
        _add_to_group(countries_by_id, country_id_for_title(country_title), country_title, is_visited)

        type_id = normalized_transport_type_id(str(object_data.get("transport_type_id") or ""))
        type_title = str(object_data.get("transport_type_title") or object_data.get("kind") or type_id)
        _add_to_group(transport_types_by_id, type_id, type_title, is_visited)

    return {
        "overall": progress("overall", "Вся коллекция", total_count, visited_count).as_dict(),
        "visited_count": visited_count,
        "total_count": total_count,
        "progress_percent": progress_percent(total_count, visited_count),
        "countries": _sorted_groups(countries_by_id),
        "transport_types": _sorted_groups(transport_types_by_id),
    }


def status_is_visited(visit_status_id: str) -> bool:
    return normalized_status_id(visit_status_id) in {STATUS_VISITED, STATUS_FAVORITE}


def normalized_status_id(visit_status_id: str) -> str:
    if visit_status_id in {STATUS_PLANNED, STATUS_VISITED, STATUS_FAVORITE}:
        return visit_status_id
    return STATUS_NOT_VISITED


def progress(id: str, title: str, total_count: int, visited_count: int) -> ProgressStats:
    return ProgressStats(
        id=id,
        title=title,
        total_count=total_count,
        visited_count=visited_count,
        progress_percent=progress_percent(total_count, visited_count),
    )


def progress_percent(total_count: int, visited_count: int) -> int:
    if total_count <= 0:
        return 0
    return int((visited_count * 100 / total_count) + 0.5)


def country_id_for_title(country_title: str) -> str:
    return COUNTRY_IDS_BY_TITLE.get(country_title, "country_unknown")


def normalized_transport_type_id(transport_type_id: str) -> str:
    return transport_type_id or "transport_type_unknown"


def _add_to_group(
    groups_by_id: dict[str, dict[str, Any]],
    id: str,
    title: str,
    is_visited: bool,
) -> None:
    group = groups_by_id.setdefault(id, progress(id, title, 0, 0).as_dict())
    group["total_count"] += 1
    if is_visited:
        group["visited_count"] += 1
    group["progress_percent"] = progress_percent(group["total_count"], group["visited_count"])


def _sorted_groups(groups_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(groups_by_id.values(), key=lambda group: (group["title"], group["id"]))
