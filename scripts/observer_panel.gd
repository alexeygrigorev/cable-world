extends PanelContainer
class_name ObserverPanel

signal back_requested

const MODE_LINE := "line"
const MODE_STATIONS := "stations"

var current_object: Dictionary = {}
var selected_station_id: String = ""
var selected_direction_id: String = ""
var view_mode: String = MODE_LINE
var title_label: Label
var summary_label: Label
var scheme_view: ObserverSchemeView
var mode_button: Button
var direction_button: Button
var station_buttons: GridContainer
var back_button: Button


func _ready() -> void:
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_top", 12)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_bottom", 12)
	margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	add_child(margin)

	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 12)
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	margin.add_child(rows)

	back_button = Button.new()
	back_button.text = "К карточке объекта"
	back_button.custom_minimum_size = Vector2(0, 56)
	back_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	back_button.pressed.connect(func() -> void: back_requested.emit())
	rows.add_child(back_button)

	title_label = Label.new()
	title_label.text = "Наблюдатель"
	title_label.add_theme_font_size_override("font_size", 24)
	title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_child(title_label)

	summary_label = Label.new()
	summary_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	summary_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_child(summary_label)

	scheme_view = ObserverSchemeView.new()
	scheme_view.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scheme_view.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rows.add_child(scheme_view)

	var controls := GridContainer.new()
	controls.columns = 1
	controls.add_theme_constant_override("h_separation", 8)
	controls.add_theme_constant_override("v_separation", 8)
	controls.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_child(controls)

	mode_button = Button.new()
	mode_button.text = "Вид: линия"
	mode_button.custom_minimum_size = Vector2(0, 56)
	mode_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	mode_button.pressed.connect(_on_mode_pressed)
	controls.add_child(mode_button)

	direction_button = Button.new()
	direction_button.text = "Сменить направление"
	direction_button.custom_minimum_size = Vector2(0, 56)
	direction_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	direction_button.pressed.connect(_on_direction_pressed)
	controls.add_child(direction_button)

	var station_title := Label.new()
	station_title.text = "Точка наблюдения"
	station_title.add_theme_font_size_override("font_size", 20)
	station_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	station_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_child(station_title)

	station_buttons = GridContainer.new()
	station_buttons.columns = 1
	station_buttons.add_theme_constant_override("h_separation", 8)
	station_buttons.add_theme_constant_override("v_separation", 8)
	station_buttons.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_child(station_buttons)

	show_empty_state()


func show_empty_state() -> void:
	current_object = {}
	selected_station_id = ""
	selected_direction_id = ""
	view_mode = MODE_LINE
	title_label.text = "Наблюдатель"
	summary_label.text = "Выберите объект с детальной схемой маршрута, чтобы посмотреть его со стороны."
	back_button.disabled = true
	mode_button.disabled = true
	direction_button.disabled = true
	_clear_station_buttons()
	scheme_view.show_object(current_object, selected_station_id, selected_direction_id, view_mode)


func show_object(object_data: Dictionary) -> void:
	current_object = object_data
	var stations := _stations()
	var directions := _directions()
	if selected_station_id.is_empty() or not _has_station(selected_station_id):
		selected_station_id = str(stations[0].get("id", "")) if not stations.is_empty() else ""
	if selected_direction_id.is_empty() or not _has_direction(selected_direction_id):
		selected_direction_id = str(directions[0].get("id", "")) if not directions.is_empty() else ""

	title_label.text = "Наблюдатель: %s" % _value_text(object_data.get("name", ""), "объект без названия")
	back_button.disabled = false
	mode_button.disabled = stations.is_empty()
	direction_button.disabled = directions.size() < 2
	_refresh_summary()
	_refresh_station_buttons()
	_refresh_scheme()


func _refresh_summary() -> void:
	var stations := _stations()
	var directions := _directions()
	if stations.is_empty() or directions.is_empty():
		summary_label.text = "Для наблюдения пока нет схемы маршрута. Вернитесь к карточке объекта."
		return

	summary_label.text = "Станции: %d\nМаршрут: %s\nОтрезки: %s\nТочка наблюдения: %s" % [
		stations.size(),
		_direction_title(selected_direction_id),
		_segment_labels_text(),
		_station_title(selected_station_id),
	]


func _refresh_scheme() -> void:
	mode_button.text = "Вид: станции" if view_mode == MODE_STATIONS else "Вид: линия"
	scheme_view.show_object(current_object, selected_station_id, selected_direction_id, view_mode)


func _refresh_station_buttons() -> void:
	_clear_station_buttons()
	for item in _stations():
		if not (item is Dictionary):
			continue
		var station: Dictionary = item
		var station_id := str(station.get("id", ""))
		var button := Button.new()
		button.text = _value_text(station.get("title", ""), "станция")
		button.tooltip_text = "Выбрать точку наблюдения: %s" % button.text
		button.custom_minimum_size = Vector2(0, 56)
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		button.toggle_mode = true
		button.button_pressed = station_id == selected_station_id
		button.pressed.connect(func() -> void: _select_station(station_id))
		station_buttons.add_child(button)


func _clear_station_buttons() -> void:
	for child in station_buttons.get_children():
		station_buttons.remove_child(child)
		child.queue_free()


func _select_station(station_id: String) -> void:
	selected_station_id = station_id
	_refresh_summary()
	_refresh_station_buttons()
	_refresh_scheme()


func _on_mode_pressed() -> void:
	view_mode = MODE_STATIONS if view_mode == MODE_LINE else MODE_LINE
	_refresh_scheme()


func _on_direction_pressed() -> void:
	var directions := _directions()
	if directions.size() < 2:
		return

	var current_index := 0
	for index in directions.size():
		var direction: Dictionary = directions[index]
		if str(direction.get("id", "")) == selected_direction_id:
			current_index = index
			break
	var next_direction: Dictionary = directions[(current_index + 1) % directions.size()]
	selected_direction_id = str(next_direction.get("id", ""))
	_refresh_summary()
	_refresh_scheme()


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


func _direction_title(direction_id: String) -> String:
	for item in _directions():
		if item is Dictionary and str(item.get("id", "")) == direction_id:
			var direction: Dictionary = item
			return _value_text(direction.get("direction_label", ""), "направление не указано")
	return "направление не выбрано"


func _segment_labels_text() -> String:
	var segments_by_direction: Dictionary = current_object.get("route_segments_by_direction", {})
	if not segments_by_direction.has(selected_direction_id) or not (segments_by_direction[selected_direction_id] is Array):
		return "отрезки пока не указаны"

	var labels: Array[String] = []
	for item in segments_by_direction[selected_direction_id]:
		if not (item is Dictionary):
			continue
		var segment: Dictionary = item
		labels.append(_value_text(segment.get("direction_label", ""), "отрезок без подписи"))
	if labels.is_empty():
		return "отрезки пока не указаны"
	return " · ".join(labels)


func _value_text(value: Variant, empty_text: String) -> String:
	if value == null:
		return empty_text
	if value is String and value.strip_edges().is_empty():
		return empty_text
	return str(value)
