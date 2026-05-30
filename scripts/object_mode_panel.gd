extends PanelContainer
class_name ObjectModePanel

signal card_requested
signal ride_requested

class ObjectModeSchemeView:
	extends Control

	var current_object: Dictionary = {}
	var selected_direction_id: String = ""
	var selected_station_id: String = ""

	func _ready() -> void:
		custom_minimum_size = Vector2(0, 280)
		size_flags_horizontal = Control.SIZE_EXPAND_FILL

	func show_object(object_data: Dictionary, direction_id: String, station_id: String) -> void:
		current_object = object_data
		selected_direction_id = direction_id
		selected_station_id = station_id
		queue_redraw()

	func clear_scheme() -> void:
		current_object = {}
		selected_direction_id = ""
		selected_station_id = ""
		queue_redraw()

	func _draw() -> void:
		var drawing_rect := Rect2(Vector2(8, 8), size - Vector2(16, 16))
		draw_rect(drawing_rect, Color(0.08, 0.10, 0.11, 1.0), true)
		draw_rect(drawing_rect, Color(0.34, 0.39, 0.42, 1.0), false, 2.0)

		var stations := _stations()
		if stations.is_empty():
			_draw_center_text("Для этого объекта пока нет станций схемы.", drawing_rect)
			return

		var route_rect := drawing_rect.grow_individual(-28.0, -44.0, -28.0, -82.0)
		var station_points := _station_points(stations, route_rect)
		_draw_route(station_points)
		_draw_stations(stations, station_points, drawing_rect)

	func _draw_route(station_points: Dictionary) -> void:
		var segments := _selected_segments()
		if segments.is_empty():
			var previous_point := Vector2.ZERO
			var has_previous := false
			for item in _stations():
				if not (item is Dictionary):
					continue
				var station: Dictionary = item
				var station_id := str(station.get("id", ""))
				if not station_points.has(station_id):
					continue
				var point: Vector2 = station_points[station_id]
				if has_previous:
					draw_line(previous_point, point, Color(0.92, 0.66, 0.22, 1.0), 5.0, true)
				previous_point = point
				has_previous = true
			return

		for item in segments:
			if not (item is Dictionary):
				continue
			var segment: Dictionary = item
			var from_id := str(segment.get("from_station_id", ""))
			var to_id := str(segment.get("to_station_id", ""))
			if station_points.has(from_id) and station_points.has(to_id):
				draw_line(station_points[from_id], station_points[to_id], Color(0.33, 0.37, 0.38, 1.0), 11.0, true)
				draw_line(station_points[from_id], station_points[to_id], Color(0.92, 0.66, 0.22, 1.0), 6.0, true)

	func _draw_stations(stations: Array, station_points: Dictionary, drawing_rect: Rect2) -> void:
		var font := get_theme_default_font()
		var font_size := 17
		var label_width: float = min(124.0, max(88.0, drawing_rect.size.x - 36.0))
		for index in stations.size():
			if not (stations[index] is Dictionary):
				continue
			var station: Dictionary = stations[index]
			var station_id := str(station.get("id", ""))
			if not station_points.has(station_id):
				continue

			var point: Vector2 = station_points[station_id]
			var selected := station_id == selected_station_id
			var radius := 16.0 if selected else 12.0
			draw_circle(point, radius + 5.0, Color(0.02, 0.03, 0.03, 0.86))
			draw_circle(point, radius, Color(0.19, 0.57, 0.45, 1.0) if selected else Color(0.91, 0.92, 0.88, 1.0))
			draw_arc(point, radius + 5.0, 0.0, TAU, 48, Color(0.95, 0.73, 0.31, 1.0), 2.0, true)
			draw_string(font, point + Vector2(-4.5, 5.5), str(index + 1), HORIZONTAL_ALIGNMENT_CENTER, 16.0, font_size, Color(0.02, 0.03, 0.03, 1.0))

			var title := _value_text(station.get("title", ""), "станция")
			var label_position := point + Vector2(label_width * -0.5, 25.0)
			if point.y > drawing_rect.position.y + drawing_rect.size.y * 0.58:
				label_position.y = point.y - 58.0
			label_position.x = clampf(label_position.x, drawing_rect.position.x + 8.0, drawing_rect.end.x - label_width - 8.0)
			label_position.y = clampf(label_position.y, drawing_rect.position.y + 12.0, drawing_rect.end.y - 50.0)
			draw_multiline_string(font, label_position, title, HORIZONTAL_ALIGNMENT_CENTER, label_width, font_size, 2, Color(0.94, 0.95, 0.91, 1.0))

	func _draw_center_text(text: String, drawing_rect: Rect2) -> void:
		var font := get_theme_default_font()
		var font_size := 18
		var position := drawing_rect.position + Vector2(12.0, max(36.0, drawing_rect.size.y * 0.5 - 28.0))
		draw_multiline_string(font, position, text, HORIZONTAL_ALIGNMENT_CENTER, drawing_rect.size.x - 24.0, font_size, -1, Color(0.94, 0.95, 0.91, 1.0))

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
			var latitude := float(station.get("latitude", 0.0))
			var longitude := float(station.get("longitude", 0.0))
			min_lat = min(min_lat, latitude)
			max_lat = max(max_lat, latitude)
			min_lon = min(min_lon, longitude)
			max_lon = max(max_lon, longitude)

		if has_coordinates and max_lat > min_lat and max_lon > min_lon:
			for item in stations:
				if not (item is Dictionary):
					continue
				var station: Dictionary = item
				var station_id := str(station.get("id", ""))
				var x := inverse_lerp(min_lon, max_lon, float(station.get("longitude", 0.0)))
				var y := 1.0 - inverse_lerp(min_lat, max_lat, float(station.get("latitude", 0.0)))
				points[station_id] = drawing_rect.position + Vector2(drawing_rect.size.x * x, drawing_rect.size.y * y)
			return points

		var count: int = max(1, stations.size() - 1)
		for index in stations.size():
			if not (stations[index] is Dictionary):
				continue
			var station: Dictionary = stations[index]
			var station_id := str(station.get("id", ""))
			var x := float(index) / float(count)
			var y := 0.52 - sin(float(index) * 0.85) * 0.16
			points[station_id] = drawing_rect.position + Vector2(drawing_rect.size.x * x, drawing_rect.size.y * y)
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

var current_object: Dictionary = {}
var selected_direction_id: String = ""
var selected_station_id: String = ""
var direction_option_is_refreshing: bool = false
var back_button: Button
var ride_button: Button
var title_label: Label
var summary_label: Label
var empty_state_label: Label
var direction_option: OptionButton
var scheme_view: ObjectModeSchemeView
var station_buttons: GridContainer
var segment_label: Label

func _ready() -> void:
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_top", 12)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_bottom", 12)
	margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	add_child(margin)

	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 10)
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	margin.add_child(rows)

	back_button = Button.new()
	back_button.text = "К карточке"
	back_button.custom_minimum_size = Vector2(0, 56)
	back_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	back_button.pressed.connect(func() -> void: card_requested.emit())
	rows.add_child(back_button)

	title_label = Label.new()
	title_label.text = "Режим объекта"
	title_label.add_theme_font_size_override("font_size", 24)
	title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_child(title_label)

	summary_label = _add_text_label(rows, 18)
	empty_state_label = _add_text_label(rows, 18)

	scheme_view = ObjectModeSchemeView.new()
	scheme_view.custom_minimum_size = Vector2(0, 280)
	scheme_view.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_child(scheme_view)

	direction_option = OptionButton.new()
	direction_option.custom_minimum_size = Vector2(0, 52)
	direction_option.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	direction_option.item_selected.connect(_on_direction_selected)
	rows.add_child(direction_option)

	ride_button = Button.new()
	ride_button.text = "Открыть поездку"
	ride_button.custom_minimum_size = Vector2(0, 56)
	ride_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ride_button.pressed.connect(func() -> void: ride_requested.emit())
	rows.add_child(ride_button)

	var station_title := Label.new()
	station_title.text = "Станции и точки"
	station_title.add_theme_font_size_override("font_size", 20)
	station_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(station_title)

	station_buttons = GridContainer.new()
	station_buttons.columns = 1
	station_buttons.add_theme_constant_override("h_separation", 8)
	station_buttons.add_theme_constant_override("v_separation", 8)
	station_buttons.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_child(station_buttons)

	segment_label = _add_text_label(rows, 18)

	show_empty_state()

func show_empty_state() -> void:
	current_object = {}
	selected_direction_id = ""
	selected_station_id = ""
	title_label.text = "Режим объекта"
	summary_label.text = "Объект не выбран"
	empty_state_label.text = "Выберите объект, чтобы открыть детальную схему."
	empty_state_label.visible = true
	direction_option.clear()
	direction_option.disabled = true
	_clear_station_buttons()
	segment_label.text = "Для этого объекта пока нет направления поездки."
	back_button.disabled = true
	ride_button.disabled = true
	scheme_view.clear_scheme()

func show_object(object_data: Dictionary) -> void:
	current_object = object_data
	var stations := _stations()
	var directions := _directions()
	if selected_station_id.is_empty() or not _has_station(selected_station_id):
		selected_station_id = str(stations[0].get("id", "")) if not stations.is_empty() else ""
	if selected_direction_id.is_empty() or not _has_direction(selected_direction_id):
		selected_direction_id = str(directions[0].get("id", "")) if not directions.is_empty() else ""

	title_label.text = "Режим объекта: %s" % _value_text(object_data.get("name", ""), "объект без названия")
	summary_label.text = "Станции: %d\nНаправления: %d\nВыбрано: %s" % [
		stations.size(),
		directions.size(),
		_station_title(selected_station_id),
	]
	empty_state_label.visible = stations.is_empty() or directions.is_empty()
	empty_state_label.text = _empty_state_text()
	back_button.disabled = false
	ride_button.disabled = false
	_configure_direction_option()
	_refresh_station_buttons()
	_refresh_segment_label()
	_refresh_scheme()

func _configure_direction_option() -> void:
	var directions := _directions()
	direction_option_is_refreshing = true
	direction_option.clear()
	for index in directions.size():
		var direction: Dictionary = directions[index]
		direction_option.add_item(_direction_title(direction))
		direction_option.set_item_metadata(index, str(direction.get("id", "")))
		if str(direction.get("id", "")) == selected_direction_id:
			direction_option.select(index)
	direction_option.disabled = directions.is_empty()
	direction_option_is_refreshing = false

func _refresh_station_buttons() -> void:
	_clear_station_buttons()
	for item in _stations():
		if not (item is Dictionary):
			continue
		var station: Dictionary = item
		var station_id := str(station.get("id", ""))
		var button := Button.new()
		button.text = _value_text(station.get("title", ""), "станция")
		button.tooltip_text = "Открыть точку: %s" % button.text
		button.custom_minimum_size = Vector2(0, 56)
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		button.toggle_mode = true
		button.button_pressed = station_id == selected_station_id
		button.pressed.connect(func() -> void: _select_station(station_id))
		station_buttons.add_child(button)

func _refresh_segment_label() -> void:
	var segments := _selected_segments()
	if _directions().is_empty():
		segment_label.text = "Для этого объекта пока нет направления поездки."
		return
	if segments.is_empty():
		segment_label.text = "Для этого направления пока нет отрезков маршрута."
		return

	var rows: Array[String] = ["Отрезки маршрута:"]
	for item in segments:
		if not (item is Dictionary):
			continue
		var segment: Dictionary = item
		rows.append("- %s → %s: %s" % [
			_station_title(str(segment.get("from_station_id", ""))),
			_station_title(str(segment.get("to_station_id", ""))),
			_value_text(segment.get("direction_label", ""), "подпись пока не указана"),
		])
	segment_label.text = "\n".join(rows)

func _refresh_scheme() -> void:
	scheme_view.show_object(current_object, selected_direction_id, selected_station_id)

func _clear_station_buttons() -> void:
	for child in station_buttons.get_children():
		station_buttons.remove_child(child)
		child.queue_free()

func _on_direction_selected(index: int) -> void:
	if direction_option_is_refreshing:
		return
	if index < 0 or index >= direction_option.get_item_count():
		return
	selected_direction_id = str(direction_option.get_item_metadata(index))
	_refresh_segment_label()
	_refresh_scheme()

func _select_station(station_id: String) -> void:
	selected_station_id = station_id
	show_object(current_object)

func _empty_state_text() -> String:
	if _stations().is_empty():
		return "Для этого объекта пока нет станций схемы."
	if _directions().is_empty():
		return "Для этого объекта пока нет направления поездки."
	return ""

func _selected_segments() -> Array:
	var route_segments_by_direction: Dictionary = current_object.get("route_segments_by_direction", {})
	if route_segments_by_direction.has(selected_direction_id) and route_segments_by_direction[selected_direction_id] is Array:
		return route_segments_by_direction[selected_direction_id]
	return []

func _stations() -> Array:
	if current_object.has("stations") and current_object.get("stations") is Array:
		return current_object.get("stations")
	return []

func _directions() -> Array:
	if current_object.has("route_directions") and current_object.get("route_directions") is Array:
		return current_object.get("route_directions")
	return []

func _has_station(station_id: String) -> bool:
	for item in _stations():
		if item is Dictionary and str(item.get("id", "")) == station_id:
			return true
	return false

func _has_direction(direction_id: String) -> bool:
	for item in _directions():
		if item is Dictionary and str(item.get("id", "")) == direction_id:
			return true
	return false

func _station_title(station_id: String) -> String:
	for item in _stations():
		if item is Dictionary and str(item.get("id", "")) == station_id:
			var station: Dictionary = item
			return _value_text(station.get("title", ""), "станция")
	return "станция не выбрана"

func _direction_title(direction: Dictionary) -> String:
	var title := str(direction.get("title", "")).strip_edges()
	if not title.is_empty():
		return title.replace("->", "→")
	return "%s → %s" % [
		_station_title(str(direction.get("from_station_id", ""))),
		_station_title(str(direction.get("to_station_id", ""))),
	]

func _add_text_label(rows: VBoxContainer, font_size: int) -> Label:
	var label := Label.new()
	label.add_theme_font_size_override("font_size", font_size)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_child(label)
	return label

func _value_text(value: Variant, empty_text: String) -> String:
	if value == null:
		return empty_text
	if value is String and value.strip_edges().is_empty():
		return empty_text
	return str(value)
