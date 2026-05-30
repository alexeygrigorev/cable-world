extends RefCounted
class_name Achievements

const STATUS_NOT_VISITED: String = "not_visited"
const STATUS_PLANNED: String = "planned"
const STATUS_VISITED: String = "visited"
const STATUS_FAVORITE: String = "favorite"

const FUNICULAR_TYPE_IDS := {
	"funicular_classic": true,
	"funicular_water": true,
	"funicular_modern": true,
}
const CABLEWAY_TYPE_IDS := {
	"cable_gondola": true,
	"cable_aerial_tram": true,
	"cable_urban": true,
	"cable_tourist": true,
}
const SUSPENDED_TRAIN_TYPE_IDS := {
	"suspended_train": true,
}
const ACHIEVEMENT_RULES := [
	{
		"id": "first_funicular",
		"title": "Первый фуникулер",
		"description": "Засчитывается после первого посещенного фуникулера любого типа.",
		"transport_type_ids": FUNICULAR_TYPE_IDS,
	},
	{
		"id": "first_cableway",
		"title": "Первая канатная дорога",
		"description": "Засчитывается после первой посещенной канатной дороги любого типа.",
		"transport_type_ids": CABLEWAY_TYPE_IDS,
	},
	{
		"id": "first_suspended_train",
		"title": "Первый подвесной поезд",
		"description": "Засчитывается после первого посещенного объекта типа «подвесной поезд».",
		"transport_type_ids": SUSPENDED_TRAIN_TYPE_IDS,
	},
]


static func calculate(objects: Array[Dictionary]) -> Array[Dictionary]:
	var achievements: Array[Dictionary] = []
	for rule in ACHIEVEMENT_RULES:
		achievements.append(_calculate_rule(rule, objects))
	return achievements


static func status_is_visited(visit_status_id: String) -> bool:
	var normalized_status := normalized_status_id(visit_status_id)
	return normalized_status == STATUS_VISITED or normalized_status == STATUS_FAVORITE


static func normalized_status_id(visit_status_id: String) -> String:
	if visit_status_id == STATUS_PLANNED:
		return STATUS_PLANNED
	if visit_status_id == STATUS_VISITED:
		return STATUS_VISITED
	if visit_status_id == STATUS_FAVORITE:
		return STATUS_FAVORITE
	return STATUS_NOT_VISITED


static func _calculate_rule(rule: Dictionary, objects: Array[Dictionary]) -> Dictionary:
	var matched_object: Dictionary = {}
	for object_data in objects:
		if not _object_matches_rule(object_data, rule):
			continue
		matched_object = object_data
		break

	var unlocked := not matched_object.is_empty()
	var matched_name := str(matched_object.get("name", "")) if unlocked else ""
	return {
		"id": str(rule.get("id", "")),
		"title": str(rule.get("title", "")),
		"description": str(rule.get("description", "")),
		"unlocked": unlocked,
		"status_text": "Получено" if unlocked else "Еще не получено",
		"progress_text": matched_name if unlocked else "Отметьте объект как посещенный или любимый.",
		"matched_object_id": str(matched_object.get("id", "")) if unlocked else "",
	}


static func _object_matches_rule(object_data: Dictionary, rule: Dictionary) -> bool:
	var visit_status_id := str(object_data.get("visit_status_id", STATUS_NOT_VISITED))
	if not status_is_visited(visit_status_id):
		return false

	var transport_type_ids: Dictionary = rule.get("transport_type_ids", {})
	return transport_type_ids.has(str(object_data.get("transport_type_id", "")))
