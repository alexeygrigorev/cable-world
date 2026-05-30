extends RefCounted
class_name CollectionStats

const STATUS_NOT_VISITED: String = "not_visited"
const STATUS_PLANNED: String = "planned"
const STATUS_VISITED: String = "visited"
const STATUS_FAVORITE: String = "favorite"

const COUNTRY_IDS_BY_TITLE := {
	"Россия": "ru",
	"Германия": "de",
}


static func calculate(objects: Array[Dictionary]) -> Dictionary:
	var countries_by_id: Dictionary = {}
	var transport_types_by_id: Dictionary = {}
	var total_count := 0
	var visited_count := 0

	for object_data in objects:
		total_count += 1
		var is_visited := status_is_visited(str(object_data.get("visit_status_id", STATUS_NOT_VISITED)))
		if is_visited:
			visited_count += 1

		var country_title := str(object_data.get("country", "Страна не указана"))
		var country_id := country_id_for_title(country_title)
		_add_to_group(countries_by_id, country_id, country_title, is_visited)

		var type_id := normalized_transport_type_id(str(object_data.get("transport_type_id", "")))
		var type_title := str(object_data.get("transport_type_title", object_data.get("kind", type_id)))
		_add_to_group(transport_types_by_id, type_id, type_title, is_visited)

	return {
		"overall": progress("overall", "Вся коллекция", total_count, visited_count),
		"visited_count": visited_count,
		"total_count": total_count,
		"progress_percent": progress_percent(total_count, visited_count),
		"countries": _sorted_groups(countries_by_id),
		"transport_types": _sorted_groups(transport_types_by_id),
	}


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


static func progress(id: String, title: String, total_count: int, visited_count: int) -> Dictionary:
	return {
		"id": id,
		"title": title,
		"total_count": total_count,
		"visited_count": visited_count,
		"progress_percent": progress_percent(total_count, visited_count),
	}


static func progress_percent(total_count: int, visited_count: int) -> int:
	if total_count <= 0:
		return 0
	return int(round(float(visited_count) * 100.0 / float(total_count)))


static func country_id_for_title(country_title: String) -> String:
	if COUNTRY_IDS_BY_TITLE.has(country_title):
		return COUNTRY_IDS_BY_TITLE[country_title]
	return "country_unknown"


static func normalized_transport_type_id(transport_type_id: String) -> String:
	if transport_type_id.is_empty():
		return "transport_type_unknown"
	return transport_type_id


static func _add_to_group(groups_by_id: Dictionary, id: String, title: String, is_visited: bool) -> void:
	if not groups_by_id.has(id):
		groups_by_id[id] = progress(id, title, 0, 0)

	var group: Dictionary = groups_by_id[id]
	group["total_count"] = int(group.get("total_count", 0)) + 1
	if is_visited:
		group["visited_count"] = int(group.get("visited_count", 0)) + 1
	group["progress_percent"] = progress_percent(int(group["total_count"]), int(group["visited_count"]))
	groups_by_id[id] = group


static func _sorted_groups(groups_by_id: Dictionary) -> Array[Dictionary]:
	var groups: Array[Dictionary] = []
	for group_id in groups_by_id.keys():
		groups.append(groups_by_id[group_id])
	groups.sort_custom(_compare_groups)
	return groups


static func _compare_groups(left: Dictionary, right: Dictionary) -> bool:
	var left_title := str(left.get("title", ""))
	var right_title := str(right.get("title", ""))
	if left_title == right_title:
		return str(left.get("id", "")) < str(right.get("id", ""))
	return left_title < right_title
