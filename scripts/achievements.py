from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scripts.collection_stats import STATUS_NOT_VISITED, status_is_visited


FUNICULAR_TYPE_IDS = {
    "funicular_classic",
    "funicular_water",
    "funicular_modern",
}
CABLEWAY_TYPE_IDS = {
    "cable_gondola",
    "cable_aerial_tram",
    "cable_urban",
    "cable_tourist",
}
SUSPENDED_TRAIN_TYPE_IDS = {
    "suspended_train",
}


@dataclass(frozen=True)
class AchievementRule:
    id: str
    title: str
    description: str
    transport_type_ids: set[str]


ACHIEVEMENT_RULES = [
    AchievementRule(
        id="first_funicular",
        title="Первый фуникулер",
        description="Засчитывается после первого посещенного фуникулера любого типа.",
        transport_type_ids=FUNICULAR_TYPE_IDS,
    ),
    AchievementRule(
        id="first_cableway",
        title="Первая канатная дорога",
        description="Засчитывается после первой посещенной канатной дороги любого типа.",
        transport_type_ids=CABLEWAY_TYPE_IDS,
    ),
    AchievementRule(
        id="first_suspended_train",
        title="Первый подвесной поезд",
        description="Засчитывается после первого посещенного объекта типа «подвесной поезд».",
        transport_type_ids=SUSPENDED_TRAIN_TYPE_IDS,
    ),
]


def calculate_achievements(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_calculate_rule(rule, objects) for rule in ACHIEVEMENT_RULES]


def _calculate_rule(rule: AchievementRule, objects: list[dict[str, Any]]) -> dict[str, Any]:
    matched_object: dict[str, Any] | None = None

    for object_data in objects:
        if not _object_matches_rule(object_data, rule):
            continue
        matched_object = object_data
        break

    unlocked = matched_object is not None
    matched_name = str(matched_object.get("name", "")) if matched_object else ""

    return {
        "id": rule.id,
        "title": rule.title,
        "description": rule.description,
        "unlocked": unlocked,
        "status_text": "Получено" if unlocked else "Еще не получено",
        "progress_text": matched_name if unlocked else "Отметьте объект как посещенный или любимый.",
        "matched_object_id": str(matched_object.get("id", "")) if matched_object else "",
    }


def _object_matches_rule(object_data: dict[str, Any], rule: AchievementRule) -> bool:
    visit_status_id = str(object_data.get("visit_status_id", STATUS_NOT_VISITED))
    if not status_is_visited(visit_status_id):
        return False
    return str(object_data.get("transport_type_id", "")) in rule.transport_type_ids
