extends Control
class_name ObserverSchemeView

const MODE_LINE := "line"
const MODE_STATIONS := "stations"

var current_object: Dictionary = {}
var selected_station_id: String = ""
var selected_direction_id: String = ""
var view_mode: String = MODE_LINE


func _ready() -> void:
	custom_minimum_size = Vector2(0, 280)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL


func show_object(object_data: Dictionary, station_id: String, direction_id: String, mode: String) -> void:
	current_object = object_data
	selected_station_id = station_id
	selected_direction_id = direction_id
	view_mode = mode
	queue_redraw()


func _draw() -> void:
	var stations := _stations()
	var drawing_rect := Rect2(Vector2(8, 8), size - Vector2(16, 16))
	draw_rect(drawing_rect, Color(0.09, 0.11, 0.13, 1.0), true)
	draw_rect(drawing_rect, Color(0.42, 0.48, 0.54, 1.0), false, 2.0)

	if stations.is_empty():
		_draw_center_text("Для наблюдения пока нет схемы маршрута.", drawing_rect)
		return

	var station_points := _station_points(stations, _route_rect(drawing_rect))
	_draw_route_lines(station_points)
	_draw_stations(stations, station_points, drawing_rect)
	_draw_observer_marker(station_points)


func _draw_center_text(text: String, drawing_rect: Rect2) -> void:
	var font := get_theme_default_font()
	var font_size := 18
	var text_size := font.get_string_size(text, HORIZONTAL_ALIGNMENT_CENTER, drawing_rect.size.x - 24.0, font_size)
	var position := drawing_rect.position + Vector2(12.0, max(36.0, drawing_rect.size.y * 0.5 - text_size.y * 0.5))
	draw_multiline_string(font, position, text, HORIZONTAL_ALIGNMENT_CENTER, drawing_rect.size.x - 24.0, font_size, -1, Color(0.92, 0.93, 0.90, 1.0))


func _draw_route_lines(station_points: Dictionary) -> void:
	var segments := _selected_segments()
	if segments.is_empty():
		var last_point := Vector2.ZERO
		var has_last := false
		for station in _stations():
			var station_id := str(station.get("id", ""))
			if not station_points.has(station_id):
				continue
			var point: Vector2 = station_points[station_id]
			if has_last:
				draw_line(last_point, point, Color(0.95, 0.69, 0.24, 1.0), 5.0, true)
			last_point = point
			has_last = true
		return

	for item in segments:
		if not (item is Dictionary):
			continue
		var segment: Dictionary = item
		var from_id := str(segment.get("from_station_id", ""))
		var to_id := str(segment.get("to_station_id", ""))
		if station_points.has(from_id) and station_points.has(to_id):
			draw_line(station_points[from_id], station_points[to_id], Color(0.95, 0.69, 0.24, 1.0), 6.0, true)
			if view_mode == MODE_STATIONS:
				draw_line(station_points[from_id] + Vector2(0, 9), station_points[to_id] + Vector2(0, 9), Color(0.35, 0.63, 0.82, 1.0), 2.0, true)


func _draw_stations(stations: Array, station_points: Dictionary, drawing_rect: Rect2) -> void:
	var font := get_theme_default_font()
	var font_size := 18
	var label_width: float = min(132.0, max(84.0, drawing_rect.size.x - 36.0))
	for item in stations:
		if not (item is Dictionary):
			continue
		var station: Dictionary = item
		var station_id := str(station.get("id", ""))
		if not station_points.has(station_id):
			continue
		var point: Vector2 = station_points[station_id]
		var is_selected := station_id == selected_station_id
		var radius := 15.0 if is_selected else 11.0
		draw_circle(point, radius + 4.0, Color(0.05, 0.06, 0.07, 0.9))
		draw_circle(point, radius, Color(0.18, 0.55, 0.44, 1.0) if is_selected else Color(0.92, 0.93, 0.90, 1.0))
		draw_arc(point, radius + 4.0, 0.0, TAU, 48, Color(0.95, 0.69, 0.24, 1.0), 2.0, true)
		var title := _value_text(station.get("title", ""), "станция")
		var label_pos := point + Vector2(label_width * -0.5, 24.0)
		label_pos.x = clampf(label_pos.x, drawing_rect.position.x + 8.0, drawing_rect.end.x - label_width - 8.0)
		label_pos.y = min(label_pos.y, drawing_rect.end.y - 46.0)
		draw_multiline_string(font, label_pos, title, HORIZONTAL_ALIGNMENT_CENTER, label_width, font_size, 2, Color(0.92, 0.93, 0.90, 1.0))


func _route_rect(drawing_rect: Rect2) -> Rect2:
	var horizontal_padding: float = min(56.0, max(30.0, drawing_rect.size.x * 0.16))
	var top_padding: float = 58.0
	var bottom_padding: float = 78.0
	return drawing_rect.grow_individual(-horizontal_padding, -top_padding, -horizontal_padding, -bottom_padding)


func _draw_observer_marker(station_points: Dictionary) -> void:
	if selected_station_id.is_empty() or not station_points.has(selected_station_id):
		return
	var point: Vector2 = station_points[selected_station_id]
	var cabin_rect := Rect2(point + Vector2(-18.0, -48.0), Vector2(36.0, 26.0))
	draw_line(point + Vector2(0.0, -20.0), point + Vector2(0.0, -36.0), Color(0.95, 0.69, 0.24, 1.0), 3.0, true)
	draw_rect(cabin_rect, Color(0.35, 0.63, 0.82, 1.0), true)
	draw_rect(cabin_rect, Color(0.92, 0.93, 0.90, 1.0), false, 2.0)


func _station_points(stations: Array, drawing_rect: Rect2) -> Dictionary:
	var points := {}
	var has_coordinates := true
	var min_lat := INF
	var max_lat := -INF
	var min_lon := INF
	var max_lon := -INF
	for item in stations:
		if not (item is Dictionary):
			continue
		var station: Dictionary = item
		if not station.has("latitude") or not station.has("longitude"):
			has_coordinates = false
			break
		var lat := float(station.get("latitude", 0.0))
		var lon := float(station.get("longitude", 0.0))
		min_lat = min(min_lat, lat)
		max_lat = max(max_lat, lat)
		min_lon = min(min_lon, lon)
		max_lon = max(max_lon, lon)

	if has_coordinates and max_lat > min_lat and max_lon > min_lon:
		for item in stations:
			var station: Dictionary = item
			var station_id := str(station.get("id", ""))
			var x := inverse_lerp(min_lon, max_lon, float(station.get("longitude", 0.0)))
			var y := 1.0 - inverse_lerp(min_lat, max_lat, float(station.get("latitude", 0.0)))
			points[station_id] = drawing_rect.position + Vector2(drawing_rect.size.x * x, drawing_rect.size.y * y)
		return points

	var count: int = max(1, stations.size() - 1)
	for index in stations.size():
		var station: Dictionary = stations[index]
		var station_id := str(station.get("id", ""))
		var x: float = float(index) / float(count)
		var wave: float = sin(float(index) * 0.9) * 0.14
		points[station_id] = drawing_rect.position + Vector2(drawing_rect.size.x * x, drawing_rect.size.y * (0.5 + wave))
	return points


func _selected_segments() -> Array:
	var route_segments_by_direction: Dictionary = current_object.get("route_segments_by_direction", {})
	if route_segments_by_direction.has(selected_direction_id) and route_segments_by_direction[selected_direction_id] is Array:
		return route_segments_by_direction[selected_direction_id]
	return []


func _stations() -> Array:
	if current_object.has("stations") and current_object.get("stations") is Array:
		return current_object.get("stations")
	return []


func _value_text(value: Variant, empty_text: String) -> String:
	if value == null:
		return empty_text
	if value is String and value.strip_edges().is_empty():
		return empty_text
	return str(value)
