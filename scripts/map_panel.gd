extends PanelContainer
class_name MapPanel

signal object_selected(index: int)

const MARKER_SIZE := Vector2(44.0, 36.0)
const MAP_PADDING := 18.0

var objects: Array[Dictionary] = []
var selected_index: int = -1
var marker_buttons: Array[Button] = []
var map_layer: Control
var summary_label: Label
var selected_label: Label

func _ready() -> void:
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 18)
	margin.add_theme_constant_override("margin_top", 18)
	margin.add_theme_constant_override("margin_right", 18)
	margin.add_theme_constant_override("margin_bottom", 18)
	add_child(margin)

	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 8)
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.size_flags_vertical = Control.SIZE_EXPAND_FILL
	margin.add_child(rows)

	summary_label = Label.new()
	summary_label.text = "Общая карта объектов"
	summary_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(summary_label)

	var hint_label := Label.new()
	hint_label.text = "Локальная схема без сети: каждая точка показывает один объект."
	hint_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(hint_label)

	map_layer = Control.new()
	map_layer.name = "ТочкиОбъектов"
	map_layer.custom_minimum_size = Vector2(0.0, 220.0)
	map_layer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	map_layer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	map_layer.clip_contents = true
	map_layer.resized.connect(_position_markers)
	rows.add_child(map_layer)

	selected_label = Label.new()
	selected_label.text = "Выбранная точка: пока не выбрана"
	selected_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(selected_label)

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
		marker.tooltip_text = "Выбрать объект: %s" % objects[index].get("name", "без названия")
		marker.set_meta("object_index", index)
		marker.pressed.connect(_on_marker_pressed.bind(index))
		map_layer.add_child(marker)
		marker_buttons.append(marker)

	_update_summary_label()
	_refresh_marker_styles()
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

	for marker in marker_buttons:
		var index := int(marker.get_meta("object_index", -1))
		if index < 0 or index >= objects.size():
			continue

		var coordinates := _object_coordinates(objects[index])
		var x_ratio := (coordinates.x - float(bounds["min_longitude"])) / longitude_span
		var y_ratio := (float(bounds["max_latitude"]) - coordinates.y) / latitude_span
		marker.position = Vector2(
			MAP_PADDING + x_ratio * usable_width,
			MAP_PADDING + y_ratio * usable_height
		)

func _refresh_marker_styles() -> void:
	for marker in marker_buttons:
		var index := int(marker.get_meta("object_index", -1))
		var is_selected := index == selected_index
		marker.button_pressed = is_selected
		marker.text = "✓" if is_selected else str(index + 1)
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

	summary_label.text = "Общая карта объектов: %d точек" % marker_buttons.size()

func _update_selection_label() -> void:
	if selected_label == null:
		return

	if selected_index < 0 or selected_index >= objects.size():
		selected_label.text = "Выбранная точка: пока не выбрана"
		return

	var object_data := objects[selected_index]
	var coordinates := _object_coordinates(object_data)
	selected_label.text = "Выбранная точка: %s, %s (%.4f, %.4f)" % [
		object_data.get("name", "без названия"),
		object_data.get("region", "регион не указан"),
		coordinates.y,
		coordinates.x
	]

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
