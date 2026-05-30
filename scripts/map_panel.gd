extends PanelContainer
class_name MapPanel

signal object_selected(index: int)

class OfflineMapLayer:
	extends Control

	var pan_offset := Vector2.ZERO
	var zoom := 1.0

	func _draw() -> void:
		var rect := Rect2(Vector2.ZERO, size)
		draw_rect(rect, Color("#f8fbf4"))
		draw_rect(Rect2(_map_point(Vector2(14.0, 16.0)), Vector2(max(1.0, size.x - 44.0), max(1.0, size.y - 48.0)) * zoom), Color("#d8ead2"), false, 4.0)
		draw_line(_map_point(Vector2(22.0, size.y * 0.36)), _map_point(Vector2(size.x - 24.0, size.y * 0.42)), Color("#6fa5c9"), 8.0 * zoom, true)
		draw_line(_map_point(Vector2(size.x * 0.34, 22.0)), _map_point(Vector2(size.x * 0.46, size.y - 22.0)), Color("#87aa72"), 5.0 * zoom, true)
		draw_line(_map_point(Vector2(24.0, size.y * 0.68)), _map_point(Vector2(size.x - 24.0, size.y * 0.58)), Color("#b39145"), 5.0 * zoom, true)
		draw_circle(_map_point(Vector2(size.x * 0.68, size.y * 0.28)), 28.0 * zoom, Color("#c9df7a"))
		draw_circle(_map_point(Vector2(size.x * 0.22, size.y * 0.72)), 22.0 * zoom, Color("#b8d66d"))
		draw_rect(rect, Color("#31544d"), false, 3.0)

	func _map_point(point: Vector2) -> Vector2:
		return pan_offset + point * zoom

const MARKER_SIZE := Vector2(46.0, 38.0)
const MAP_MIN_HEIGHT := 420.0
const MAP_VIEW_HEIGHT := 270.0
const MAP_PADDING := 18.0
const MARKER_SPREAD_DISTANCE := 58.0
const MARKER_SPREAD_STEP := 42.0
const GRID_LAYOUT_MIN_MARKERS := 10
const GRID_COLUMNS := 5
const SELECTED_NAME_LIMIT := 42
const MAP_FILTER_ALL := "all"
const MAP_FILTER_VISITED := "visited"
const MAP_FILTER_NOT_VISITED := "not_visited"
const MIN_ZOOM := 0.75
const MAX_ZOOM := 2.6
const ZOOM_STEP := 1.18
const MAP_CONTROL_SIZE := Vector2(48.0, 48.0)

var objects: Array[Dictionary] = []
var selected_index: int = -1
var marker_buttons: Array[Button] = []
var pan_offset := Vector2.ZERO
var zoom := 1.0
var map_filter := MAP_FILTER_ALL
var map_layer: Control
var map_content: Control
var summary_label: Label
var selected_label: Label
var empty_state_label: Label
var zoom_controls: VBoxContainer
var filter_buttons: Dictionary = {}
var dragging := false
var active_touch_index := -1
var last_touch_positions: Dictionary = {}

func _ready() -> void:
	custom_minimum_size.y = max(custom_minimum_size.y, MAP_MIN_HEIGHT)
	var panel_style := StyleBoxFlat.new()
	panel_style.bg_color = Color("#f7f3e7")
	panel_style.border_color = Color("#6f7d67")
	panel_style.set_border_width_all(2)
	panel_style.set_corner_radius_all(8)
	add_theme_stylebox_override("panel", panel_style)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_top", 12)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_bottom", 12)
	add_child(margin)

	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 6)
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.size_flags_vertical = Control.SIZE_EXPAND_FILL
	margin.add_child(rows)

	summary_label = Label.new()
	summary_label.text = "Общая карта объектов"
	summary_label.add_theme_color_override("font_color", Color("#24332f"))
	summary_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(summary_label)

	var hint_label := Label.new()
	hint_label.text = "Локальная схема без сети: каждая точка показывает один объект."
	hint_label.add_theme_color_override("font_color", Color("#344842"))
	hint_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(hint_label)

	selected_label = Label.new()
	selected_label.text = "Выбранная точка: пока не выбрана"
	selected_label.add_theme_color_override("font_color", Color("#15211e"))
	selected_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	selected_label.custom_minimum_size = Vector2(0.0, 50.0)
	rows.add_child(selected_label)

	var filter_row := HBoxContainer.new()
	filter_row.add_theme_constant_override("separation", 6)
	rows.add_child(filter_row)
	_add_filter_button(filter_row, "Все", MAP_FILTER_ALL)
	_add_filter_button(filter_row, "Посещенные", MAP_FILTER_VISITED)
	_add_filter_button(filter_row, "Непосещенные", MAP_FILTER_NOT_VISITED)

	map_layer = OfflineMapLayer.new()
	map_layer.name = "ТочкиОбъектов"
	map_layer.custom_minimum_size = Vector2(0.0, MAP_VIEW_HEIGHT)
	map_layer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	map_layer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	map_layer.clip_contents = true
	map_layer.mouse_filter = Control.MOUSE_FILTER_STOP
	map_layer.gui_input.connect(_on_map_layer_gui_input)
	map_layer.resized.connect(_on_map_layer_resized)
	rows.add_child(map_layer)

	map_content = Control.new()
	map_content.name = "ПодвижнаяКарта"
	map_content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	map_layer.add_child(map_content)

	empty_state_label = Label.new()
	empty_state_label.text = "Нет точек с координатами"
	empty_state_label.add_theme_color_override("font_color", Color("#24332f"))
	empty_state_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	empty_state_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	empty_state_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	empty_state_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	map_layer.add_child(empty_state_label)

	zoom_controls = VBoxContainer.new()
	zoom_controls.name = "МасштабКарты"
	zoom_controls.add_theme_constant_override("separation", 8)
	zoom_controls.position = Vector2(10.0, 10.0)
	map_layer.add_child(zoom_controls)
	_add_zoom_button(zoom_controls, "+", ZOOM_STEP)
	_add_zoom_button(zoom_controls, "-", 1.0 / ZOOM_STEP)

	_refresh_markers()

func set_objects(next_objects: Array[Dictionary]) -> void:
	objects = next_objects
	if is_node_ready():
		_refresh_markers()

func select_object(index: int) -> void:
	selected_index = index if index >= 0 and index < objects.size() else -1
	if is_node_ready():
		_refresh_marker_styles()
		_update_selection_label()

func set_map_filter(next_filter: String) -> void:
	if next_filter == MAP_FILTER_VISITED:
		map_filter = MAP_FILTER_VISITED
	elif next_filter == MAP_FILTER_NOT_VISITED:
		map_filter = MAP_FILTER_NOT_VISITED
	else:
		map_filter = MAP_FILTER_ALL

	if is_node_ready():
		_refresh_filter_buttons()
		_refresh_marker_styles()
		_update_summary_label()
		_update_empty_state()
		_update_selection_label()

func _refresh_markers() -> void:
	if map_layer == null:
		return

	for marker in marker_buttons:
		marker.queue_free()
	marker_buttons.clear()

	for index in objects.size():
		if not _has_coordinates(objects[index]):
			continue

		var marker := Button.new()
		marker.name = "Маркер%d" % (index + 1)
		marker.custom_minimum_size = MARKER_SIZE
		marker.size = MARKER_SIZE
		marker.toggle_mode = true
		marker.focus_mode = Control.FOCUS_ALL
		marker.add_theme_font_size_override("font_size", 18)
		marker.tooltip_text = "Выбрать объект: %s" % objects[index].get("name", "без названия")
		marker.set_meta("object_index", index)
		marker.pressed.connect(_on_marker_pressed.bind(index))
		map_content.add_child(marker)
		marker_buttons.append(marker)

	_refresh_filter_buttons()
	_refresh_marker_styles()
	_update_summary_label()
	_update_empty_state()
	_position_markers()

func _on_map_layer_resized() -> void:
	map_layer.queue_redraw()
	if map_content != null:
		map_content.size = map_layer.size
	if empty_state_label != null:
		empty_state_label.size = map_layer.size
	if zoom_controls != null:
		zoom_controls.position = Vector2(max(10.0, map_layer.size.x - MAP_CONTROL_SIZE.x - 10.0), 10.0)
	_apply_map_transform()
	_position_markers()

func _position_markers() -> void:
	if map_layer == null:
		return

	var bounds := _coordinate_bounds()
	if bounds.is_empty():
		return

	var longitude_span: float = max(0.000001, float(bounds["max_longitude"]) - float(bounds["min_longitude"]))
	var latitude_span: float = max(0.000001, float(bounds["max_latitude"]) - float(bounds["min_latitude"]))
	var usable_width: float = max(1.0, map_layer.size.x - MARKER_SIZE.x - MAP_PADDING * 2.0)
	var usable_height: float = max(1.0, map_layer.size.y - MARKER_SIZE.y - MAP_PADDING * 2.0)
	var placed_positions: Array[Vector2] = []
	var use_grid_layout: bool = marker_buttons.size() >= GRID_LAYOUT_MIN_MARKERS

	for marker_number in marker_buttons.size():
		var marker := marker_buttons[marker_number]
		var index := int(marker.get_meta("object_index", -1))
		if index < 0 or index >= objects.size():
			continue

		var coordinates := _object_coordinates(objects[index])
		var base_position: Vector2
		if use_grid_layout:
			base_position = _grid_marker_position(marker_number, marker_buttons.size(), map_layer.size)
		else:
			var x_ratio := (coordinates.x - float(bounds["min_longitude"])) / longitude_span
			var y_ratio := (float(bounds["max_latitude"]) - coordinates.y) / latitude_span
			base_position = Vector2(
				MAP_PADDING + x_ratio * usable_width,
				MAP_PADDING + y_ratio * usable_height
			)
		var spread_position := base_position if use_grid_layout else _spread_marker_position(base_position, placed_positions, map_layer.size)
		var clamped_position := Vector2(
			clamp(spread_position.x, MAP_PADDING, max(MAP_PADDING, map_layer.size.x - MARKER_SIZE.x - MAP_PADDING)),
			clamp(spread_position.y, MAP_PADDING, max(MAP_PADDING, map_layer.size.y - MARKER_SIZE.y - MAP_PADDING))
		)
		marker.position = _map_point_to_screen(clamped_position)
		placed_positions.append(clamped_position)

func _refresh_marker_styles() -> void:
	for marker in marker_buttons:
		var index := int(marker.get_meta("object_index", -1))
		marker.visible = _object_matches_filter(objects[index]) if index >= 0 and index < objects.size() else false
		var is_selected := index == selected_index
		marker.button_pressed = is_selected
		marker.text = "✓" if is_selected else str(index + 1)
		marker.add_theme_font_size_override("font_size", 22 if is_selected else 18)
		marker.add_theme_color_override("font_color", Color("#ffffff") if is_selected else Color("#10231f"))
		marker.add_theme_color_override("font_pressed_color", Color("#ffffff"))
		_apply_marker_style(marker, is_selected)
		marker.tooltip_text = "%s: %s" % [
			"Выбранный объект" if is_selected else "Выбрать объект",
			objects[index].get("name", "без названия") if index >= 0 and index < objects.size() else "без названия"
		]

	_update_selection_label()

func _update_summary_label() -> void:
	if summary_label == null:
		return

	if objects.is_empty():
		summary_label.text = "Общая карта объектов: пока нет точек"
		return

	var visible_count := _visible_marker_count()
	var layout_text := ", сетка для читаемости" if marker_buttons.size() >= GRID_LAYOUT_MIN_MARKERS else ""
	summary_label.text = "Общая карта объектов: %d из %d точек%s" % [visible_count, marker_buttons.size(), layout_text]

func _update_empty_state() -> void:
	if empty_state_label == null:
		return

	empty_state_label.visible = marker_buttons.is_empty() or _visible_marker_count() == 0
	empty_state_label.text = "Нет точек с координатами" if marker_buttons.is_empty() else "Нет точек для выбранного фильтра"
	empty_state_label.size = map_layer.size if map_layer != null else Vector2.ZERO

func _update_selection_label() -> void:
	if selected_label == null:
		return

	if selected_index < 0 or selected_index >= objects.size():
		selected_label.text = "Выбранная точка: пока не выбрана"
		return

	if not _object_matches_filter(objects[selected_index]):
		selected_label.text = "Выбранная точка скрыта фильтром карты"
		return

	var object_data := objects[selected_index]
	var coordinates := _object_coordinates(object_data)
	selected_label.text = "Выбрано: %s\n%s · %.3f, %.3f" % [
		_compact_text(str(object_data.get("name", "без названия")), SELECTED_NAME_LIMIT),
		_compact_text(str(object_data.get("region", "регион не указан")), 32),
		coordinates.y,
		coordinates.x
	]

func _grid_marker_position(marker_number: int, total_markers: int, map_size: Vector2) -> Vector2:
	var column_count: int = min(GRID_COLUMNS, max(1, total_markers))
	var row_count: int = int(ceil(float(total_markers) / float(column_count)))
	var column: int = marker_number % column_count
	var row: int = int(marker_number / column_count)
	var usable_width: float = max(1.0, map_size.x - MARKER_SIZE.x - MAP_PADDING * 2.0)
	var usable_height: float = max(1.0, map_size.y - MARKER_SIZE.y - MAP_PADDING * 2.0)
	var x_step: float = usable_width / max(1.0, float(column_count - 1))
	var y_step: float = usable_height / max(1.0, float(row_count - 1))
	var stagger: float = 10.0 if row % 2 == 1 else 0.0
	return Vector2(
		MAP_PADDING + column * x_step + stagger,
		MAP_PADDING + row * y_step
	)

func _spread_marker_position(base_position: Vector2, placed_positions: Array[Vector2], map_size: Vector2) -> Vector2:
	if _is_clear_marker_position(base_position, placed_positions):
		return base_position

	var max_position := Vector2(
		max(MAP_PADDING, map_size.x - MARKER_SIZE.x - MAP_PADDING),
		max(MAP_PADDING, map_size.y - MARKER_SIZE.y - MAP_PADDING)
	)
	for attempt in 32:
		var angle: float = TAU * float(attempt % 8) / 8.0
		var ring: float = 1.0 + floor(float(attempt) / 8.0)
		var candidate: Vector2 = base_position + Vector2(cos(angle), sin(angle)) * MARKER_SPREAD_STEP * ring
		candidate = Vector2(
			clamp(candidate.x, MAP_PADDING, max_position.x),
			clamp(candidate.y, MAP_PADDING, max_position.y)
		)
		if _is_clear_marker_position(candidate, placed_positions):
			return candidate

	return base_position

func _is_clear_marker_position(position: Vector2, placed_positions: Array[Vector2]) -> bool:
	for placed_position in placed_positions:
		if position.distance_to(placed_position) < MARKER_SPREAD_DISTANCE:
			return false
	return true

func _add_filter_button(parent: Container, title: String, filter_id: String) -> void:
	var button := Button.new()
	button.text = title
	button.toggle_mode = true
	button.focus_mode = Control.FOCUS_ALL
	button.custom_minimum_size = Vector2(0.0, 48.0)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.set_meta("map_filter", filter_id)
	button.pressed.connect(set_map_filter.bind(filter_id))
	parent.add_child(button)
	filter_buttons[filter_id] = button

func _add_zoom_button(parent: Container, title: String, factor: float) -> void:
	var button := Button.new()
	button.text = title
	button.tooltip_text = "Приблизить карту" if factor > 1.0 else "Отдалить карту"
	button.custom_minimum_size = MAP_CONTROL_SIZE
	button.size = MAP_CONTROL_SIZE
	button.add_theme_font_size_override("font_size", 24)
	_apply_map_control_style(button)
	button.pressed.connect(func() -> void: _zoom_at(map_layer.size * 0.5, factor))
	parent.add_child(button)

func _apply_map_control_style(button: Button) -> void:
	var normal_style := StyleBoxFlat.new()
	normal_style.bg_color = Color("#ffffff")
	normal_style.border_color = Color("#31544d")
	normal_style.set_border_width_all(2)
	normal_style.set_corner_radius_all(6)
	button.add_theme_stylebox_override("normal", normal_style)
	button.add_theme_stylebox_override("pressed", normal_style)
	button.add_theme_stylebox_override("hover", normal_style)

func _refresh_filter_buttons() -> void:
	for filter_id in filter_buttons:
		var button: Button = filter_buttons[filter_id]
		button.button_pressed = filter_id == map_filter

func _on_map_layer_gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		_handle_mouse_button(event)
	elif event is InputEventMouseMotion:
		_handle_mouse_motion(event)
	elif event is InputEventScreenTouch:
		_handle_screen_touch(event)
	elif event is InputEventScreenDrag:
		_handle_screen_drag(event)
	elif event is InputEventMagnifyGesture:
		_zoom_at(event.position, event.factor)
		accept_event()

func _handle_mouse_button(event: InputEventMouseButton) -> void:
	if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
		_zoom_at(event.position, ZOOM_STEP)
		accept_event()
	elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
		_zoom_at(event.position, 1.0 / ZOOM_STEP)
		accept_event()
	elif event.button_index == MOUSE_BUTTON_LEFT:
		dragging = event.pressed
		accept_event()

func _handle_mouse_motion(event: InputEventMouseMotion) -> void:
	if dragging or bool(event.button_mask & MOUSE_BUTTON_MASK_LEFT):
		pan_offset += event.relative
		_apply_map_transform()
		accept_event()

func _handle_screen_touch(event: InputEventScreenTouch) -> void:
	if event.pressed:
		last_touch_positions[event.index] = event.position
		if active_touch_index == -1:
			active_touch_index = event.index
	else:
		last_touch_positions.erase(event.index)
		if active_touch_index == event.index:
			active_touch_index = -1 if last_touch_positions.is_empty() else int(last_touch_positions.keys()[0])
	accept_event()

func _handle_screen_drag(event: InputEventScreenDrag) -> void:
	if last_touch_positions.size() >= 2:
		var previous_distance := _touch_distance_with(event.index, event.position - event.relative)
		var current_distance := _touch_distance_with(event.index, event.position)
		if previous_distance > 0.0 and current_distance > 0.0:
			_zoom_at(event.position, current_distance / previous_distance)
	else:
		pan_offset += event.relative
		_apply_map_transform()
	last_touch_positions[event.index] = event.position
	accept_event()

func _touch_distance_with(index: int, position: Vector2) -> float:
	for touch_index in last_touch_positions:
		if int(touch_index) != index:
			var other_position: Vector2 = last_touch_positions[touch_index]
			return position.distance_to(other_position)
	return 0.0

func _zoom_at(pivot: Vector2, factor: float) -> void:
	var previous_zoom := zoom
	zoom = clamp(zoom * factor, MIN_ZOOM, MAX_ZOOM)
	if is_equal_approx(previous_zoom, zoom):
		return

	var scale_factor := zoom / previous_zoom
	pan_offset = pivot - (pivot - pan_offset) * scale_factor
	_apply_map_transform()

func _apply_map_transform() -> void:
	if map_layer != null:
		map_layer.set("pan_offset", pan_offset)
		map_layer.set("zoom", zoom)
		map_layer.queue_redraw()
	_position_markers()

func _map_point_to_screen(point: Vector2) -> Vector2:
	var marker_center := MARKER_SIZE * 0.5
	return pan_offset + (point + marker_center) * zoom - marker_center

func _visible_marker_count() -> int:
	var count := 0
	for marker in marker_buttons:
		if marker.visible:
			count += 1
	return count

func _object_matches_filter(object_data: Dictionary) -> bool:
	if map_filter == MAP_FILTER_ALL:
		return true
	var is_visited := _is_object_visited(object_data)
	if map_filter == MAP_FILTER_VISITED:
		return is_visited
	return not is_visited

func _is_object_visited(object_data: Dictionary) -> bool:
	if object_data.has("visit_status_id"):
		var status_id := str(object_data.get("visit_status_id", ""))
		return status_id == "visited" or status_id == "favorite"
	return object_data.get("visited", false)

func _compact_text(text: String, max_length: int) -> String:
	var normalized := text.strip_edges().replace("\n", " ")
	if normalized.length() <= max_length:
		return normalized
	return normalized.substr(0, max(0, max_length - 1)).strip_edges() + "…"

func _apply_marker_style(marker: Button, is_selected: bool) -> void:
	var normal_style := StyleBoxFlat.new()
	normal_style.bg_color = Color("#136f63") if is_selected else Color("#f4fff8")
	normal_style.border_color = Color("#063f39") if is_selected else Color("#31544d")
	normal_style.set_border_width_all(3 if is_selected else 2)
	normal_style.set_corner_radius_all(8)
	marker.add_theme_stylebox_override("normal", normal_style)

	var hover_style := normal_style.duplicate()
	hover_style.bg_color = Color("#0f5c52") if is_selected else Color("#dff3e6")
	marker.add_theme_stylebox_override("hover", hover_style)
	marker.add_theme_stylebox_override("pressed", normal_style)
	marker.add_theme_stylebox_override("focus", normal_style)

func _coordinate_bounds() -> Dictionary:
	var has_any_coordinates := false
	var min_longitude := 0.0
	var max_longitude := 0.0
	var min_latitude := 0.0
	var max_latitude := 0.0

	for object_data in objects:
		if not _has_coordinates(object_data):
			continue

		var coordinates := _object_coordinates(object_data)
		if not has_any_coordinates:
			min_longitude = coordinates.x
			max_longitude = coordinates.x
			min_latitude = coordinates.y
			max_latitude = coordinates.y
			has_any_coordinates = true
			continue

		min_longitude = min(min_longitude, coordinates.x)
		max_longitude = max(max_longitude, coordinates.x)
		min_latitude = min(min_latitude, coordinates.y)
		max_latitude = max(max_latitude, coordinates.y)

	if not has_any_coordinates:
		return {}

	return {
		"min_longitude": min_longitude,
		"max_longitude": max_longitude,
		"min_latitude": min_latitude,
		"max_latitude": max_latitude,
	}

func _has_coordinates(object_data: Dictionary) -> bool:
	if object_data.has("coordinates") and object_data.get("coordinates") is Vector2:
		return true
	return object_data.has("latitude") and object_data.has("longitude")

func _object_coordinates(object_data: Dictionary) -> Vector2:
	if object_data.has("coordinates") and object_data.get("coordinates") is Vector2:
		return object_data.get("coordinates")
	return Vector2(float(object_data.get("longitude", 0.0)), float(object_data.get("latitude", 0.0)))

func _on_marker_pressed(index: int) -> void:
	if index < 0 or index >= objects.size():
		return

	object_selected.emit(index)
