extends Control
class_name RideGameView

signal ride_state_changed(state: Dictionary)

const BASE_SPEED := 0.18
const PASSENGER_CAPACITY := 4
const LOWER_STATION_RATIO := 0.10
const UPPER_STATION_RATIO := 0.90

var current_object: Dictionary = {}
var current_direction: Dictionary = {}
var current_segments: Array = []
var current_segment_index: int = 0
var active_segment: Dictionary = {}
var lower_station: Dictionary = {}
var upper_station: Dictionary = {}
var lower_station_title: String = "нижняя станция"
var upper_station_title: String = "верхняя станция"
var progress: float = 0.0
var speed_multiplier: float = 1.0
var passengers_waiting: int = PASSENGER_CAPACITY
var passengers_onboard: int = 0
var delivered_passengers: int = 0
var ride_finished: bool = false
var smoothness_score: int = 100
var _last_speed_multiplier: float = 1.0


func _ready() -> void:
	custom_minimum_size = Vector2(0, 260)
	set_process(true)


func setup_route(object_data: Dictionary, direction: Dictionary, segments: Array, segment_index: int) -> void:
	current_object = object_data
	current_direction = direction
	current_segments = segments
	current_segment_index = clampi(segment_index, 0, max(0, segments.size() - 1))
	active_segment = {}
	if not current_segments.is_empty() and current_segments[current_segment_index] is Dictionary:
		active_segment = current_segments[current_segment_index]

	lower_station = _station_for_segment_end("from_station_id")
	upper_station = _station_for_segment_end("to_station_id")
	lower_station_title = _station_title(lower_station, "нижняя станция")
	upper_station_title = _station_title(upper_station, "верхняя станция")
	reset_ride()


func clear_route() -> void:
	current_object = {}
	current_direction = {}
	current_segments = []
	active_segment = {}
	lower_station = {}
	upper_station = {}
	lower_station_title = "нижняя станция"
	upper_station_title = "верхняя станция"
	progress = 0.0
	passengers_waiting = 0
	passengers_onboard = 0
	delivered_passengers = 0
	ride_finished = false
	smoothness_score = 100
	queue_redraw()
	_emit_state()


func reset_ride() -> void:
	progress = 0.0
	speed_multiplier = 1.0
	_last_speed_multiplier = speed_multiplier
	passengers_waiting = PASSENGER_CAPACITY if not active_segment.is_empty() else 0
	passengers_onboard = 0
	delivered_passengers = 0
	ride_finished = false
	smoothness_score = 100
	_board_lower_station()
	queue_redraw()
	_emit_state()


func set_speed_multiplier(value: float) -> void:
	var next_speed := clampf(value, 0.5, 2.0)
	var speed_delta := absf(next_speed - _last_speed_multiplier)
	if speed_delta > 0.01:
		smoothness_score = maxi(0, smoothness_score - int(round(speed_delta * 12.0)))
	speed_multiplier = next_speed
	_last_speed_multiplier = speed_multiplier
	_emit_state()


func advance_ride(delta: float) -> void:
	if active_segment.is_empty() or ride_finished:
		return
	progress = minf(1.0, progress + maxf(0.0, delta) * BASE_SPEED * speed_multiplier)
	if progress >= 1.0:
		_leave_upper_station()
	queue_redraw()
	_emit_state()


func _process(delta: float) -> void:
	advance_ride(delta)


func _board_lower_station() -> void:
	var boarding_count := mini(passengers_waiting, PASSENGER_CAPACITY)
	passengers_waiting -= boarding_count
	passengers_onboard += boarding_count


func _leave_upper_station() -> void:
	delivered_passengers += passengers_onboard
	passengers_onboard = 0
	ride_finished = true
	progress = 1.0


func state_snapshot() -> Dictionary:
	return {
		"lower_station_title": lower_station_title,
		"upper_station_title": upper_station_title,
		"progress": progress,
		"speed_multiplier": speed_multiplier,
		"passengers_waiting": passengers_waiting,
		"passengers_onboard": passengers_onboard,
		"delivered_passengers": delivered_passengers,
		"ride_finished": ride_finished,
		"smoothness_score": smoothness_score,
	}


func _emit_state() -> void:
	ride_state_changed.emit(state_snapshot())


func _draw() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	_draw_background(rect)
	if active_segment.is_empty():
		_draw_empty_state(rect)
		return

	var lower_point := _lower_station_point(rect)
	var upper_point := _upper_station_point(rect)
	var cabin_point := lower_point.lerp(upper_point, progress)

	_draw_mountains(rect)
	_draw_trees(rect)
	_draw_stations(lower_point, upper_point)
	_draw_cable(lower_point, upper_point)
	_draw_cabin(cabin_point)
	_draw_hud(rect)


func _draw_background(rect: Rect2) -> void:
	draw_rect(rect, Color("#a9d2e5"), true)
	var ground_y := rect.size.y * 0.76
	draw_rect(Rect2(Vector2(0, ground_y), Vector2(rect.size.x, rect.size.y - ground_y)), Color("#6d8b48"), true)
	draw_line(Vector2(0, ground_y), Vector2(rect.size.x, ground_y), Color("#31452d"), 3.0)


func _draw_mountains(rect: Rect2) -> void:
	var base_y := rect.size.y * 0.76
	var peaks := PackedVector2Array([
		Vector2(rect.size.x * 0.02, base_y),
		Vector2(rect.size.x * 0.18, rect.size.y * 0.36),
		Vector2(rect.size.x * 0.34, base_y),
		Vector2(rect.size.x * 0.47, rect.size.y * 0.44),
		Vector2(rect.size.x * 0.63, base_y),
		Vector2(rect.size.x * 0.78, rect.size.y * 0.31),
		Vector2(rect.size.x * 0.98, base_y),
	])
	draw_colored_polygon(peaks, Color("#7b8b68"))
	draw_polyline(peaks, Color("#394632"), 3.0, true)
	draw_line(Vector2(rect.size.x * 0.14, rect.size.y * 0.48), Vector2(rect.size.x * 0.18, rect.size.y * 0.36), Color("#e6dcc4"), 5.0)
	draw_line(Vector2(rect.size.x * 0.73, rect.size.y * 0.43), Vector2(rect.size.x * 0.78, rect.size.y * 0.31), Color("#e6dcc4"), 5.0)


func _draw_trees(rect: Rect2) -> void:
	var ground_y := rect.size.y * 0.76
	for index in 7:
		var x := rect.size.x * (0.08 + float(index) * 0.13)
		var trunk_bottom := Vector2(x, ground_y + 14.0)
		draw_line(trunk_bottom - Vector2(0, 6), trunk_bottom, Color("#4d3322"), 5.0)
		draw_circle(trunk_bottom - Vector2(0, 24), 17.0, Color("#2f6738"))
		draw_circle(trunk_bottom - Vector2(11, 16), 12.0, Color("#24552f"))
		draw_circle(trunk_bottom + Vector2(11, -16), 12.0, Color("#3c7a3c"))


func _draw_stations(lower_point: Vector2, upper_point: Vector2) -> void:
	_draw_station_house(lower_point, lower_station_title, false)
	_draw_station_house(upper_point, upper_station_title, true)


func _draw_station_house(anchor: Vector2, title: String, elevated: bool) -> void:
	var width := 68.0
	var height := 44.0
	var base := anchor + Vector2(-width * 0.5, 12.0 if elevated else 18.0)
	var body := Rect2(base, Vector2(width, height))
	var roof := PackedVector2Array([
		body.position + Vector2(-6, 4),
		body.position + Vector2(width * 0.5, -18),
		body.position + Vector2(width + 6, 4),
	])
	draw_colored_polygon(roof, Color("#7f3d2c"))
	draw_rect(body, Color("#d0b074"), true)
	draw_rect(body, Color("#3d2a1e"), false, 2.0)
	draw_rect(Rect2(body.position + Vector2(width * 0.42, height * 0.42), Vector2(12, 22)), Color("#5b3826"), true)
	var font := get_theme_default_font()
	var label_width := 120.0
	var label_x := clampf(anchor.x - label_width * 0.5, 8.0, maxf(8.0, size.x - label_width - 8.0))
	draw_multiline_string(font, Vector2(label_x, body.position.y + height + 8.0), title, HORIZONTAL_ALIGNMENT_CENTER, label_width, 14, 2, Color("#1f251c"))


func _draw_cable(lower_point: Vector2, upper_point: Vector2) -> void:
	draw_line(lower_point, upper_point, Color("#27302c"), 6.0, true)
	draw_line(lower_point, upper_point, Color("#d9c482"), 2.0, true)


func _draw_cabin(cabin_point: Vector2) -> void:
	draw_line(cabin_point + Vector2(0, -18), cabin_point + Vector2(0, 4), Color("#202522"), 3.0)
	var body := Rect2(cabin_point + Vector2(-22, 4), Vector2(44, 32))
	draw_rect(body, Color("#b44332"), true)
	draw_rect(body, Color("#261f1c"), false, 3.0)
	draw_rect(Rect2(body.position + Vector2(7, 7), Vector2(12, 10)), Color("#dbe9ef"), true)
	draw_rect(Rect2(body.position + Vector2(25, 7), Vector2(12, 10)), Color("#dbe9ef"), true)
	draw_circle(body.position + Vector2(10, 39), 4.0, Color("#1b1a18"))
	draw_circle(body.position + Vector2(34, 39), 4.0, Color("#1b1a18"))


func _draw_hud(rect: Rect2) -> void:
	var font := get_theme_default_font()
	var text := "x%.2f · %d/%d · %d%%" % [speed_multiplier, delivered_passengers, PASSENGER_CAPACITY, smoothness_score]
	var panel := Rect2(Vector2(10, 10), Vector2(178, 30))
	draw_rect(panel, Color(0.09, 0.11, 0.09, 0.72), true)
	draw_string(font, panel.position + Vector2(10, 21), text, HORIZONTAL_ALIGNMENT_LEFT, panel.size.x - 20, 15, Color("#f4e2b4"))


func _draw_empty_state(rect: Rect2) -> void:
	var font := get_theme_default_font()
	draw_multiline_string(font, Vector2(18, rect.size.y * 0.42), "Маршрут появится после выбора объекта.", HORIZONTAL_ALIGNMENT_CENTER, rect.size.x - 36, 18, 2, Color("#1f251c"))


func _lower_station_point(rect: Rect2) -> Vector2:
	return Vector2(rect.size.x * LOWER_STATION_RATIO, rect.size.y * 0.62)


func _upper_station_point(rect: Rect2) -> Vector2:
	return Vector2(rect.size.x * UPPER_STATION_RATIO, rect.size.y * 0.30)


func _station_for_segment_end(key: String) -> Dictionary:
	var station_id := str(active_segment.get(key, ""))
	for item in _array_field(current_object, "stations"):
		if item is Dictionary:
			var station: Dictionary = item
			if str(station.get("id", "")) == station_id:
				return station
	return {}


func _station_title(station: Dictionary, fallback: String) -> String:
	return _value_text(station.get("title", ""), fallback)


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
