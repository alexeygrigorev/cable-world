extends Control
class_name RideRouteView

var current_object: Dictionary = {}
var current_direction: Dictionary = {}
var current_segments: Array = []
var current_segment_index: int = 0


func _ready() -> void:
	custom_minimum_size = Vector2(0, 170)


func show_route(object_data: Dictionary, direction: Dictionary, segments: Array, segment_index: int) -> void:
	current_object = object_data
	current_direction = direction
	current_segments = segments
	current_segment_index = segment_index
	queue_redraw()


func clear_route() -> void:
	current_object = {}
	current_direction = {}
	current_segments = []
	current_segment_index = 0
	queue_redraw()


func _draw() -> void:
	var drawing_rect := Rect2(Vector2(8, 8), size - Vector2(16, 16))
	draw_rect(drawing_rect, Color(0.08, 0.10, 0.11, 1.0), true)
	draw_rect(drawing_rect, Color(0.30, 0.34, 0.36, 1.0), false, 2.0)

	if current_segments.is_empty():
		_draw_center_text("Схема появится после выбора маршрута.", drawing_rect)
		return

	var station_points := _station_points(drawing_rect.grow(-48.0))
	_draw_route(station_points)
	_draw_current_segment(station_points)
	_draw_stations(station_points)


func _draw_route(station_points: Dictionary) -> void:
	for item in current_segments:
		if not (item is Dictionary):
			continue
		var segment: Dictionary = item
		var from_id := str(segment.get("from_station_id", ""))
		var to_id := str(segment.get("to_station_id", ""))
		if station_points.has(from_id) and station_points.has(to_id):
			draw_line(station_points[from_id], station_points[to_id], Color(0.40, 0.43, 0.43, 1.0), 10.0, true)
			draw_line(station_points[from_id], station_points[to_id], Color(0.93, 0.66, 0.22, 1.0), 5.0, true)


func _draw_current_segment(station_points: Dictionary) -> void:
	if current_segment_index < 0 or current_segment_index >= current_segments.size():
		return
	if not (current_segments[current_segment_index] is Dictionary):
		return

	var segment: Dictionary = current_segments[current_segment_index]
	var from_id := str(segment.get("from_station_id", ""))
	var to_id := str(segment.get("to_station_id", ""))
	if not station_points.has(from_id) or not station_points.has(to_id):
		return

	var from_point: Vector2 = station_points[from_id]
	var to_point: Vector2 = station_points[to_id]
	draw_line(from_point, to_point, Color(0.25, 0.65, 0.86, 1.0), 9.0, true)

	var midpoint := from_point.lerp(to_point, 0.5)
	var direction := (to_point - from_point).normalized()
	var side := Vector2(-direction.y, direction.x)
	var arrow_size := 13.0
	var arrow := PackedVector2Array([
		midpoint + direction * arrow_size,
		midpoint - direction * arrow_size * 0.75 + side * arrow_size * 0.55,
		midpoint - direction * arrow_size * 0.75 - side * arrow_size * 0.55,
	])
	draw_colored_polygon(arrow, Color(0.95, 0.93, 0.86, 1.0))


func _draw_stations(station_points: Dictionary) -> void:
	var font := get_theme_default_font()
	var font_size := 17
	var ordered_ids := _ordered_station_ids()
	for index in ordered_ids.size():
		var station_id := ordered_ids[index]
		if not station_points.has(station_id):
			continue

		var point: Vector2 = station_points[station_id]
		var station := _station_by_id(station_id)
		var title := _value_text(station.get("title", ""), "станция")
		var is_current := _station_is_on_current_segment(station_id)
		var radius := 15.0 if is_current else 12.0
		draw_circle(point, radius + 4.0, Color(0.02, 0.03, 0.03, 0.85))
		draw_circle(point, radius, Color(0.18, 0.55, 0.44, 1.0) if is_current else Color(0.91, 0.91, 0.86, 1.0))
		draw_arc(point, radius + 4.0, 0.0, TAU, 48, Color(0.95, 0.69, 0.24, 1.0), 2.0, true)
		draw_string(font, point + Vector2(-4.5, 5.5), str(index + 1), HORIZONTAL_ALIGNMENT_CENTER, 16.0, font_size, Color(0.02, 0.03, 0.03, 1.0))
		var label_y := point.y + 24.0
		if point.y > size.y * 0.58:
			label_y = point.y - 54.0
		var label_x := clampf(point.x - 58.0, 12.0, max(12.0, size.x - 128.0))
		var label_position := Vector2(label_x, label_y)
		draw_multiline_string(font, label_position, title, HORIZONTAL_ALIGNMENT_CENTER, 116.0, font_size, 2, Color(0.92, 0.93, 0.90, 1.0))


func _draw_center_text(text: String, drawing_rect: Rect2) -> void:
	var font := get_theme_default_font()
	var font_size := 18
	var text_size := font.get_string_size(text, HORIZONTAL_ALIGNMENT_CENTER, drawing_rect.size.x - 24.0, font_size)
	var position := drawing_rect.position + Vector2(12.0, max(36.0, drawing_rect.size.y * 0.5 - text_size.y * 0.5))
	draw_multiline_string(font, position, text, HORIZONTAL_ALIGNMENT_CENTER, drawing_rect.size.x - 24.0, font_size, -1, Color(0.92, 0.93, 0.90, 1.0))


func _station_points(drawing_rect: Rect2) -> Dictionary:
	var ordered_ids := _ordered_station_ids()
	var stations_with_coordinates := _stations_with_coordinates(ordered_ids)
	if stations_with_coordinates.size() == ordered_ids.size() and ordered_ids.size() > 1:
		return _coordinate_station_points(ordered_ids, stations_with_coordinates, drawing_rect)
	return _ordered_station_points(ordered_ids, drawing_rect)


func _coordinate_station_points(ordered_ids: Array[String], stations: Dictionary, drawing_rect: Rect2) -> Dictionary:
	var points := {}
	var min_lat := INF
	var max_lat := -INF
	var min_lon := INF
	var max_lon := -INF
	for station_id in ordered_ids:
		var station: Dictionary = stations[station_id]
		var lat := float(station.get("latitude", 0.0))
		var lon := float(station.get("longitude", 0.0))
		min_lat = min(min_lat, lat)
		max_lat = max(max_lat, lat)
		min_lon = min(min_lon, lon)
		max_lon = max(max_lon, lon)

	if max_lat <= min_lat or max_lon <= min_lon:
		return _ordered_station_points(ordered_ids, drawing_rect)

	for station_id in ordered_ids:
		var station: Dictionary = stations[station_id]
		var x := inverse_lerp(min_lon, max_lon, float(station.get("longitude", 0.0)))
		var y := 1.0 - inverse_lerp(min_lat, max_lat, float(station.get("latitude", 0.0)))
		points[station_id] = drawing_rect.position + Vector2(drawing_rect.size.x * x, drawing_rect.size.y * y)
	return points


func _ordered_station_points(ordered_ids: Array[String], drawing_rect: Rect2) -> Dictionary:
	var points := {}
	var count: int = max(1, ordered_ids.size() - 1)
	for index in ordered_ids.size():
		var station_id := ordered_ids[index]
		var x := float(index) / float(count)
		var y := 0.55 - sin(float(index) * 0.9) * 0.16
		points[station_id] = drawing_rect.position + Vector2(drawing_rect.size.x * x, drawing_rect.size.y * y)
	return points


func _ordered_station_ids() -> Array[String]:
	var ordered_ids: Array[String] = []
	for index in current_segments.size():
		if not (current_segments[index] is Dictionary):
			continue
		var segment: Dictionary = current_segments[index]
		var from_id := str(segment.get("from_station_id", ""))
		var to_id := str(segment.get("to_station_id", ""))
		if index == 0 and not from_id.is_empty():
			ordered_ids.append(from_id)
		if not to_id.is_empty():
			ordered_ids.append(to_id)

	if ordered_ids.is_empty():
		var from_station_id := str(current_direction.get("from_station_id", ""))
		var to_station_id := str(current_direction.get("to_station_id", ""))
		if not from_station_id.is_empty():
			ordered_ids.append(from_station_id)
		if not to_station_id.is_empty():
			ordered_ids.append(to_station_id)
	return ordered_ids


func _stations_with_coordinates(station_ids: Array[String]) -> Dictionary:
	var stations := {}
	for station_id in station_ids:
		var station := _station_by_id(station_id)
		if station.has("latitude") and station.has("longitude"):
			stations[station_id] = station
	return stations


func _station_by_id(station_id: String) -> Dictionary:
	for item in _array_field(current_object, "stations"):
		if item is Dictionary:
			var station: Dictionary = item
			if str(station.get("id", "")) == station_id:
				return station
	return {}


func _station_is_on_current_segment(station_id: String) -> bool:
	if current_segment_index < 0 or current_segment_index >= current_segments.size():
		return false
	if not (current_segments[current_segment_index] is Dictionary):
		return false
	var segment: Dictionary = current_segments[current_segment_index]
	return station_id == str(segment.get("from_station_id", "")) or station_id == str(segment.get("to_station_id", ""))


func _array_field(object_data: Dictionary, key: String) -> Array:
	if object_data.has(key) and object_data.get(key) is Array:
		return object_data.get(key)
	return []


func _value_text(value: Variant, empty_text: String) -> String:
	if value == null:
		return empty_text
	if value is String and value.strip_edges().is_empty():
		return empty_text
	return str(value)
