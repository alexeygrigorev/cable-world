extends PanelContainer
class_name MapPanel

signal object_selected(index: int)

class OfflineMapLayer:
	extends Control

	var pan_offset := Vector2.ZERO
	var zoom := 1.0
	var geo_bounds: Dictionary = {}

	func _draw() -> void:
		var rect := Rect2(Vector2.ZERO, size)
		draw_rect(rect, Color("#dfe8e2"))
		_draw_graticule()
		_draw_scale_bar()
		draw_rect(rect, Color("#2f4b45"), false, 2.0)

	func _map_point(point: Vector2) -> Vector2:
		return pan_offset + point * zoom

	func _draw_graticule() -> void:
		if geo_bounds.is_empty():
			return

		var min_lon: float = floor(float(geo_bounds["min_longitude"]) / 10.0) * 10.0
		var max_lon: float = ceil(float(geo_bounds["max_longitude"]) / 10.0) * 10.0
		var min_lat: float = floor(float(geo_bounds["min_latitude"]) / 5.0) * 5.0
		var max_lat: float = ceil(float(geo_bounds["max_latitude"]) / 5.0) * 5.0

		var lon: float = min_lon
		while lon <= max_lon:
			var start: Vector2 = _geo_to_screen(Vector2(lon, float(geo_bounds["min_latitude"])))
			var finish: Vector2 = _geo_to_screen(Vector2(lon, float(geo_bounds["max_latitude"])))
			draw_line(start, finish, Color(0.62, 0.69, 0.65, 0.38), 1.0, true)
			lon += 10.0

		var lat: float = min_lat
		while lat <= max_lat:
			var start: Vector2 = _geo_to_screen(Vector2(float(geo_bounds["min_longitude"]), lat))
			var finish: Vector2 = _geo_to_screen(Vector2(float(geo_bounds["max_longitude"]), lat))
			draw_line(start, finish, Color(0.62, 0.69, 0.65, 0.38), 1.0, true)
			lat += 5.0

	func _draw_scale_bar() -> void:
		var bar_origin := Vector2(14.0, max(34.0, size.y - 28.0))
		var bar_width: float = clamp(size.x * 0.26 / max(zoom, 0.01), 54.0, 110.0) * zoom
		draw_line(bar_origin, bar_origin + Vector2(bar_width, 0.0), Color("#263b36"), 3.0, true)
		draw_line(bar_origin, bar_origin + Vector2(0.0, -6.0), Color("#263b36"), 2.0, true)
		draw_line(bar_origin + Vector2(bar_width, 0.0), bar_origin + Vector2(bar_width, -6.0), Color("#263b36"), 2.0, true)
		draw_string(get_theme_default_font(), bar_origin + Vector2(0.0, -8.0), "масштаб", HORIZONTAL_ALIGNMENT_LEFT, -1.0, 10, Color("#263b36"))

	func _geo_to_screen(coordinates: Vector2) -> Vector2:
		return _map_point(_project_coordinates(coordinates, geo_bounds, size))

	static func _project_coordinates(coordinates: Vector2, bounds: Dictionary, map_size: Vector2) -> Vector2:
		if bounds.is_empty():
			return Vector2.ZERO

		var marker_size := Vector2(52.0, 48.0)
		var map_padding := 24.0
		var min_longitude: float = float(bounds["min_longitude"])
		var max_longitude: float = float(bounds["max_longitude"])
		var min_latitude: float = float(bounds["min_latitude"])
		var max_latitude: float = float(bounds["max_latitude"])
		var longitude_span: float = max(0.000001, max_longitude - min_longitude)
		var min_mercator_y: float = _mercator_y(min_latitude)
		var max_mercator_y: float = _mercator_y(max_latitude)
		var mercator_span: float = max(0.000001, max_mercator_y - min_mercator_y)
		var x_ratio: float = (coordinates.x - min_longitude) / longitude_span
		var y_ratio: float = (max_mercator_y - _mercator_y(coordinates.y)) / mercator_span
		return Vector2(
			map_padding + x_ratio * max(1.0, map_size.x - marker_size.x - map_padding * 2.0),
			map_padding + y_ratio * max(1.0, map_size.y - marker_size.y - map_padding * 2.0)
		)

	static func _mercator_y(latitude: float) -> float:
		var clamped_latitude: float = clamp(latitude, -85.0, 85.0)
		var radians: float = deg_to_rad(clamped_latitude)
		return log(tan(PI / 4.0 + radians / 2.0))

const MARKER_SIZE := Vector2(52.0, 48.0)
const MAP_MIN_HEIGHT := 620.0
const MAP_VIEW_HEIGHT := 560.0
const MAP_LANDSCAPE_MIN_HEIGHT := 360.0
const MAP_PADDING := 24.0
const MARKER_SPREAD_DISTANCE := 58.0
const MARKER_SPREAD_STEP := 42.0
const SELECTED_NAME_LIMIT := 42
const MAP_FILTER_ALL := "all"
const MAP_FILTER_VISITED := "visited"
const MAP_FILTER_NOT_VISITED := "not_visited"
const MIN_ZOOM := 0.45
const MAX_ZOOM := 4.0
const ZOOM_STEP := 1.25
const MAP_CONTROL_SIZE := Vector2(64.0, 56.0)
const FIT_CONTROL_SIZE := Vector2(104.0, 56.0)
const PAN_LIMIT_PADDING := 72.0
const DRAG_TAP_SUPPRESS_DISTANCE := 10.0

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
var filter_controls: HBoxContainer
var filter_buttons: Dictionary = {}
var dragging := false
var drag_distance := 0.0
var suppress_next_marker_press := false
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
	margin.add_theme_constant_override("margin_left", 6)
	margin.add_theme_constant_override("margin_top", 6)
	margin.add_theme_constant_override("margin_right", 6)
	margin.add_theme_constant_override("margin_bottom", 6)
	add_child(margin)

	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 0)
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.size_flags_vertical = Control.SIZE_EXPAND_FILL
	margin.add_child(rows)

	summary_label = Label.new()
	summary_label.text = "Карта объектов"
	summary_label.add_theme_color_override("font_color", Color("#24332f"))
	summary_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	summary_label.visible = false

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
	resized.connect(_sync_map_canvas_height)

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

	selected_label = Label.new()
	selected_label.text = "Выбранная точка: пока не выбрана"
	selected_label.add_theme_color_override("font_color", Color("#15211e"))
	selected_label.add_theme_color_override("font_shadow_color", Color(1.0, 1.0, 1.0, 0.85))
	selected_label.add_theme_constant_override("shadow_offset_x", 1)
	selected_label.add_theme_constant_override("shadow_offset_y", 1)
	selected_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	selected_label.custom_minimum_size = Vector2(0.0, 56.0)
	selected_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	map_layer.add_child(selected_label)

	zoom_controls = VBoxContainer.new()
	zoom_controls.name = "МасштабКарты"
	zoom_controls.add_theme_constant_override("separation", 8)
	zoom_controls.position = Vector2(10.0, 10.0)
	map_layer.add_child(zoom_controls)
	_add_zoom_button(zoom_controls, "+", ZOOM_STEP)
	_add_zoom_button(zoom_controls, "-", 1.0 / ZOOM_STEP)
	_add_fit_button(zoom_controls)

	filter_controls = HBoxContainer.new()
	filter_controls.name = "ФильтрКарты"
	filter_controls.add_theme_constant_override("separation", 6)
	filter_controls.position = Vector2(10.0, 10.0)
	map_layer.add_child(filter_controls)
	_add_filter_button(filter_controls, "Все", MAP_FILTER_ALL)
	_add_filter_button(filter_controls, "✓", MAP_FILTER_VISITED)
	_add_filter_button(filter_controls, "○", MAP_FILTER_NOT_VISITED)

	_refresh_markers()
	call_deferred("_sync_map_canvas_height")

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
		marker.mouse_filter = Control.MOUSE_FILTER_PASS
		marker.add_theme_font_size_override("font_size", 18)
		marker.tooltip_text = "Выбрать объект: %s" % objects[index].get("name", "без названия")
		marker.set_meta("object_index", index)
		marker.gui_input.connect(_on_marker_gui_input)
		marker.pressed.connect(_on_marker_pressed.bind(index))
		map_content.add_child(marker)
		marker_buttons.append(marker)

	_refresh_filter_buttons()
	_refresh_marker_styles()
	_update_summary_label()
	_update_empty_state()
	_update_map_reference_data()
	_position_markers()

func _sync_map_canvas_height() -> void:
	if map_layer == null:
		return

	var target_height := MAP_VIEW_HEIGHT
	if size.y > 0.0:
		var available_height: float = max(1.0, size.y - 12.0)
		if size.x > size.y:
			target_height = max(MAP_LANDSCAPE_MIN_HEIGHT, available_height)
		else:
			target_height = max(MAP_LANDSCAPE_MIN_HEIGHT, min(MAP_VIEW_HEIGHT, available_height))
	map_layer.custom_minimum_size.y = target_height

func _on_map_layer_resized() -> void:
	map_layer.queue_redraw()
	if map_content != null:
		map_content.size = map_layer.size
	if empty_state_label != null:
		empty_state_label.size = map_layer.size
	if zoom_controls != null:
		zoom_controls.position = Vector2(max(10.0, map_layer.size.x - FIT_CONTROL_SIZE.x - 10.0), 10.0)
	if filter_controls != null:
		filter_controls.position = Vector2(10.0, 10.0)
	if selected_label != null:
		selected_label.position = Vector2(12.0, max(12.0, map_layer.size.y - 72.0))
		selected_label.size = Vector2(max(1.0, map_layer.size.x - FIT_CONTROL_SIZE.x - 34.0), 64.0)
	_update_map_reference_data()
	_apply_map_transform()
	_position_markers()

func _position_markers() -> void:
	if map_layer == null:
		return

	var bounds := _coordinate_bounds()
	if bounds.is_empty():
		return

	var placed_positions: Array[Vector2] = []

	for marker_number in marker_buttons.size():
		var marker := marker_buttons[marker_number]
		var index := int(marker.get_meta("object_index", -1))
		if index < 0 or index >= objects.size():
			continue

		var coordinates := _object_coordinates(objects[index])
		var base_position := OfflineMapLayer._project_coordinates(coordinates, bounds, map_layer.size)
		var spread_position := _spread_marker_position(base_position, placed_positions, map_layer.size)
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
		summary_label.text = "Карта объектов: пока нет точек"
		return

	var visible_count := _visible_marker_count()
	summary_label.text = "Карта объектов: %d из %d точек" % [visible_count, marker_buttons.size()]

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
	selected_label.text = "Выбрано: %s\n%s" % [
		_compact_text(str(object_data.get("name", "без названия")), SELECTED_NAME_LIMIT),
		_compact_text(str(object_data.get("region", "регион не указан")), 32),
	]

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
	button.custom_minimum_size = Vector2(52.0, 48.0)
	button.size = Vector2(52.0, 48.0)
	button.set_meta("map_filter", filter_id)
	if filter_id == MAP_FILTER_VISITED:
		button.tooltip_text = "Показать посещенные"
	elif filter_id == MAP_FILTER_NOT_VISITED:
		button.tooltip_text = "Показать непосещенные"
	else:
		button.tooltip_text = "Показать все точки"
	button.add_theme_font_size_override("font_size", 18)
	_apply_map_control_style(button)
	button.pressed.connect(set_map_filter.bind(filter_id))
	parent.add_child(button)
	filter_buttons[filter_id] = button

func _add_zoom_button(parent: Container, title: String, factor: float) -> void:
	var tooltip := "Приблизить карту" if factor > 1.0 else "Отдалить карту"
	_add_map_control_button(parent, title, tooltip, MAP_CONTROL_SIZE, func() -> void: _zoom_at(map_layer.size * 0.5, factor))

func _add_fit_button(parent: Container) -> void:
	_add_map_control_button(parent, "Вписать", "Вписать все точки на экран", FIT_CONTROL_SIZE, _reset_map_view)

func _add_map_control_button(parent: Container, title: String, tooltip: String, minimum_size: Vector2, on_pressed: Callable) -> void:
	var button := Button.new()
	button.text = title
	button.tooltip_text = tooltip
	button.custom_minimum_size = minimum_size
	button.size = minimum_size
	button.add_theme_font_size_override("font_size", 24 if title.length() <= 2 else 18)
	_apply_map_control_style(button)
	button.pressed.connect(on_pressed)
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
		drag_distance = 0.0
		accept_event()

func _handle_mouse_motion(event: InputEventMouseMotion) -> void:
	if dragging or bool(event.button_mask & MOUSE_BUTTON_MASK_LEFT):
		pan_offset += event.relative
		drag_distance += event.relative.length()
		if drag_distance >= DRAG_TAP_SUPPRESS_DISTANCE:
			suppress_next_marker_press = true
		_apply_map_transform()
		accept_event()

func _handle_screen_touch(event: InputEventScreenTouch) -> void:
	if event.pressed:
		last_touch_positions[event.index] = event.position
		drag_distance = 0.0
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
		drag_distance += event.relative.length()
		if drag_distance >= DRAG_TAP_SUPPRESS_DISTANCE:
			suppress_next_marker_press = true
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

func _reset_map_view() -> void:
	zoom = 1.0
	pan_offset = Vector2.ZERO
	_apply_map_transform()

func _apply_map_transform() -> void:
	if map_layer != null:
		_clamp_pan_offset()
		map_layer.set("pan_offset", pan_offset)
		map_layer.set("zoom", zoom)
		map_layer.queue_redraw()
	_position_markers()

func _clamp_pan_offset() -> void:
	if map_layer == null:
		return

	var viewport_size := map_layer.size
	if viewport_size.x <= 0.0 or viewport_size.y <= 0.0:
		return

	var scaled_size := viewport_size * zoom
	if scaled_size.x <= viewport_size.x:
		pan_offset.x = (viewport_size.x - scaled_size.x) * 0.5
	else:
		pan_offset.x = clamp(pan_offset.x, viewport_size.x - scaled_size.x - PAN_LIMIT_PADDING, PAN_LIMIT_PADDING)

	if scaled_size.y <= viewport_size.y:
		pan_offset.y = (viewport_size.y - scaled_size.y) * 0.5
	else:
		pan_offset.y = clamp(pan_offset.y, viewport_size.y - scaled_size.y - PAN_LIMIT_PADDING, PAN_LIMIT_PADDING)

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
	normal_style.bg_color = Color("#d64f2a") if is_selected else Color("#fff8df")
	normal_style.border_color = Color("#6a1d13") if is_selected else Color("#31544d")
	normal_style.set_border_width_all(4 if is_selected else 2)
	normal_style.set_corner_radius_all(8)
	marker.add_theme_stylebox_override("normal", normal_style)

	var hover_style := normal_style.duplicate()
	hover_style.bg_color = Color("#ba3f21") if is_selected else Color("#f1e7be")
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

	var longitude_padding: float = max(2.0, (max_longitude - min_longitude) * 0.08)
	var latitude_padding: float = max(1.0, (max_latitude - min_latitude) * 0.12)
	return {
		"min_longitude": min_longitude - longitude_padding,
		"max_longitude": max_longitude + longitude_padding,
		"min_latitude": clamp(min_latitude - latitude_padding, -85.0, 85.0),
		"max_latitude": clamp(max_latitude + latitude_padding, -85.0, 85.0),
	}

func _update_map_reference_data() -> void:
	if map_layer == null:
		return

	var layer := map_layer as OfflineMapLayer
	layer.geo_bounds = _coordinate_bounds()
	layer.queue_redraw()

func _has_coordinates(object_data: Dictionary) -> bool:
	if object_data.has("coordinates") and object_data.get("coordinates") is Vector2:
		return true
	return object_data.has("latitude") and object_data.has("longitude")

func _object_coordinates(object_data: Dictionary) -> Vector2:
	if object_data.has("coordinates") and object_data.get("coordinates") is Vector2:
		return object_data.get("coordinates")
	return Vector2(float(object_data.get("longitude", 0.0)), float(object_data.get("latitude", 0.0)))

func _on_marker_pressed(index: int) -> void:
	if suppress_next_marker_press:
		suppress_next_marker_press = false
		return
	if index < 0 or index >= objects.size():
		return

	object_selected.emit(index)

func _on_marker_gui_input(event: InputEvent) -> void:
	if event is InputEventScreenDrag:
		suppress_next_marker_press = true
	elif event is InputEventMouseMotion and bool(event.button_mask & MOUSE_BUTTON_MASK_LEFT):
		suppress_next_marker_press = true
