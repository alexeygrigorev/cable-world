extends PanelContainer
class_name RidePanel

signal card_requested

var current_object: Dictionary = {}
var selected_direction_index: int = 0
var selected_segment_index: int = 0
var card_button: Button
var object_label: Label
var empty_state_label: Label
var direction_option: OptionButton
var ride_game_view: RideGameView
var route_view: RideRouteView
var speed_label: Label
var passenger_label: Label
var score_label: Label
var slower_button: Button
var faster_button: Button
var reset_ride_button: Button
var speed_slider: HSlider
var progress_label: Label
var segment_label: Label
var direction_label: Label
var note_label: Label
var previous_button: Button
var next_button: Button
var direction_option_is_refreshing: bool = false


func _ready() -> void:
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 18)
	margin.add_theme_constant_override("margin_top", 18)
	margin.add_theme_constant_override("margin_right", 18)
	margin.add_theme_constant_override("margin_bottom", 18)
	add_child(margin)

	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 12)
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	margin.add_child(rows)

	card_button = Button.new()
	card_button.text = "К карточке"
	card_button.custom_minimum_size = Vector2(0, 56)
	card_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card_button.pressed.connect(func() -> void: card_requested.emit())
	rows.add_child(card_button)

	var title_label := Label.new()
	title_label.text = "Поездка"
	title_label.add_theme_font_size_override("font_size", 26)
	title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(title_label)

	object_label = _add_text_label(rows, 20)
	empty_state_label = _add_text_label(rows, 20)

	direction_option = OptionButton.new()
	direction_option.custom_minimum_size = Vector2(0, 52)
	direction_option.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	direction_option.item_selected.connect(_on_direction_selected)
	rows.add_child(direction_option)

	ride_game_view = RideGameView.new()
	ride_game_view.custom_minimum_size = Vector2(0, 260)
	ride_game_view.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ride_game_view.ride_state_changed.connect(_on_ride_state_changed)
	rows.add_child(ride_game_view)

	var speed_controls := GridContainer.new()
	speed_controls.columns = 3
	speed_controls.add_theme_constant_override("h_separation", 8)
	speed_controls.add_theme_constant_override("v_separation", 8)
	rows.add_child(speed_controls)

	slower_button = Button.new()
	slower_button.text = "−"
	slower_button.tooltip_text = "Сделать ход тише"
	slower_button.custom_minimum_size = Vector2(64, 56)
	slower_button.pressed.connect(func() -> void: _change_speed(-0.25))
	speed_controls.add_child(slower_button)

	speed_slider = HSlider.new()
	speed_slider.min_value = 0.5
	speed_slider.max_value = 2.0
	speed_slider.step = 0.25
	speed_slider.value = 1.0
	speed_slider.custom_minimum_size = Vector2(0, 56)
	speed_slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	speed_slider.value_changed.connect(_on_speed_slider_changed)
	speed_controls.add_child(speed_slider)

	faster_button = Button.new()
	faster_button.text = "+"
	faster_button.tooltip_text = "Ускорить кабинку"
	faster_button.custom_minimum_size = Vector2(64, 56)
	faster_button.pressed.connect(func() -> void: _change_speed(0.25))
	speed_controls.add_child(faster_button)

	reset_ride_button = Button.new()
	reset_ride_button.text = "Начать заново"
	reset_ride_button.custom_minimum_size = Vector2(0, 56)
	reset_ride_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	reset_ride_button.pressed.connect(_on_reset_ride_pressed)
	rows.add_child(reset_ride_button)

	speed_label = _add_text_label(rows, 18)
	passenger_label = _add_text_label(rows, 18)
	score_label = _add_text_label(rows, 18)

	var controls := GridContainer.new()
	controls.columns = 2
	controls.add_theme_constant_override("h_separation", 8)
	controls.add_theme_constant_override("v_separation", 8)
	rows.add_child(controls)

	previous_button = Button.new()
	previous_button.text = "Назад"
	previous_button.custom_minimum_size = Vector2(0, 56)
	previous_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	previous_button.pressed.connect(_on_previous_pressed)
	controls.add_child(previous_button)

	next_button = Button.new()
	next_button.text = "Дальше"
	next_button.custom_minimum_size = Vector2(0, 56)
	next_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	next_button.pressed.connect(_on_next_pressed)
	controls.add_child(next_button)

	route_view = RideRouteView.new()
	route_view.custom_minimum_size = Vector2(0, 170)
	route_view.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_child(route_view)

	progress_label = _add_text_label(rows, 20)
	segment_label = _add_text_label(rows, 24)
	direction_label = _add_text_label(rows, 20)
	note_label = _add_text_label(rows, 18)

	show_empty_state()


func show_empty_state() -> void:
	current_object = {}
	selected_direction_index = 0
	selected_segment_index = 0
	object_label.text = "Объект не выбран"
	empty_state_label.text = "Выберите объект с маршрутом, чтобы открыть поездку."
	direction_option.clear()
	direction_option.disabled = true
	progress_label.text = "Шаг: маршрут не выбран"
	segment_label.text = "Откуда → куда: маршрут не выбран"
	direction_label.text = "Направление: маршрут не выбран"
	note_label.text = "Подробности маршрута появятся после выбора объекта."
	ride_game_view.clear_route()
	route_view.clear_route()
	_set_game_controls_disabled(true)
	previous_button.disabled = true
	next_button.disabled = true
	card_button.disabled = true


func show_object(object_data: Dictionary) -> void:
	current_object = object_data
	selected_direction_index = 0
	selected_segment_index = 0
	object_label.text = _value_text(object_data.get("name", ""), "объект без названия")
	card_button.disabled = false
	_configure_direction_option()
	_update_route_view()


func _configure_direction_option() -> void:
	var directions := _directions()
	direction_option_is_refreshing = true
	direction_option.clear()
	for index in directions.size():
		var direction: Dictionary = directions[index]
		direction_option.add_item(_direction_title(direction))
		direction_option.set_item_metadata(index, index)
	direction_option.disabled = directions.is_empty()
	if not directions.is_empty():
		direction_option.select(0)
	direction_option_is_refreshing = false


func _on_direction_selected(index: int) -> void:
	if direction_option_is_refreshing:
		return
	selected_direction_index = max(0, index)
	selected_segment_index = 0
	_update_route_view()


func _on_previous_pressed() -> void:
	if selected_segment_index > 0:
		selected_segment_index -= 1
	_update_route_view()


func _on_next_pressed() -> void:
	var segments := _segments_for_selected_direction()
	if selected_segment_index < segments.size() - 1:
		selected_segment_index += 1
	_update_route_view()


func _update_route_view() -> void:
	var directions := _directions()
	if directions.is_empty():
		empty_state_label.text = "Для этого объекта маршрут поездки пока не добавлен."
		empty_state_label.visible = true
		progress_label.text = "Шаг: нет данных маршрута"
		segment_label.text = "Откуда → куда: нет данных маршрута"
		direction_label.text = "Направление: нет данных маршрута"
		note_label.text = "Откройте карточку объекта, чтобы посмотреть общую информацию."
		ride_game_view.clear_route()
		route_view.clear_route()
		_set_game_controls_disabled(true)
		previous_button.disabled = true
		next_button.disabled = true
		return

	empty_state_label.visible = false
	selected_direction_index = clampi(selected_direction_index, 0, directions.size() - 1)
	var direction: Dictionary = directions[selected_direction_index]
	var segments := _segments_for_direction(direction)
	if segments.is_empty():
		progress_label.text = "Шаг: маршрут без отрезков"
		segment_label.text = _direction_from_to_text(direction)
		direction_label.text = "Направление: %s" % _value_text(direction.get("direction_label", ""), "подпись пока не указана")
		note_label.text = _value_text(direction.get("note", ""), "Подробности этого направления пока не добавлены.")
		ride_game_view.clear_route()
		route_view.show_route(current_object, direction, segments, selected_segment_index)
		_set_game_controls_disabled(true)
		previous_button.disabled = true
		next_button.disabled = true
		return

	selected_segment_index = clampi(selected_segment_index, 0, segments.size() - 1)
	var segment: Dictionary = segments[selected_segment_index]
	progress_label.text = "Шаг %d из %d" % [selected_segment_index + 1, segments.size()]
	segment_label.text = "%s → %s" % [
		_station_title(str(segment.get("from_station_id", ""))),
		_station_title(str(segment.get("to_station_id", ""))),
	]
	direction_label.text = "Направление: %s" % _value_text(segment.get("direction_label", ""), _value_text(direction.get("direction_label", ""), "подпись пока не указана"))
	note_label.text = _value_text(segment.get("note", ""), "Подробности этого отрезка пока не добавлены.")
	ride_game_view.setup_route(current_object, direction, segments, selected_segment_index)
	route_view.show_route(current_object, direction, segments, selected_segment_index)
	_set_game_controls_disabled(false)
	previous_button.disabled = selected_segment_index <= 0
	next_button.disabled = selected_segment_index >= segments.size() - 1


func _change_speed(delta: float) -> void:
	speed_slider.value = clampf(float(speed_slider.value) + delta, float(speed_slider.min_value), float(speed_slider.max_value))
	ride_game_view.set_speed_multiplier(float(speed_slider.value))


func _on_speed_slider_changed(value: float) -> void:
	ride_game_view.set_speed_multiplier(value)


func _on_reset_ride_pressed() -> void:
	ride_game_view.reset_ride()
	speed_slider.value = ride_game_view.speed_multiplier


func _on_ride_state_changed(state: Dictionary) -> void:
	var speed := float(state.get("speed_multiplier", 1.0))
	var delivered := int(state.get("delivered_passengers", 0))
	var onboard := int(state.get("passengers_onboard", 0))
	var waiting := int(state.get("passengers_waiting", 0))
	var smoothness := int(state.get("smoothness_score", 100))
	var is_finished := bool(state.get("ride_finished", false))
	speed_label.text = "Скорость: x%.2f" % speed
	passenger_label.text = "Пассажиры: в кабинке %d, ждут %d, доставлено %d" % [onboard, waiting, delivered]
	score_label.text = "Итог: плавность %d, доставлено %d" % [smoothness, delivered] if is_finished else "Итог появится на верхней станции."


func _set_game_controls_disabled(disabled: bool) -> void:
	slower_button.disabled = disabled
	faster_button.disabled = disabled
	speed_slider.editable = not disabled
	reset_ride_button.disabled = disabled
	if disabled:
		speed_label.text = "Скорость: маршрут не выбран"
		passenger_label.text = "Пассажиры: маршрут не выбран"
		score_label.text = "Итог появится после поездки."


func _directions() -> Array:
	return _array_field(current_object, "route_directions")


func _segments_for_selected_direction() -> Array:
	var directions := _directions()
	if directions.is_empty():
		return []
	selected_direction_index = clampi(selected_direction_index, 0, directions.size() - 1)
	return _segments_for_direction(directions[selected_direction_index])


func _segments_for_direction(direction: Dictionary) -> Array:
	var direction_id := str(direction.get("id", ""))
	var segments_by_direction: Dictionary = current_object.get("route_segments_by_direction", {})
	if segments_by_direction.has(direction_id) and segments_by_direction[direction_id] is Array:
		return segments_by_direction[direction_id]
	return []


func _direction_title(direction: Dictionary) -> String:
	var title := str(direction.get("title", "")).strip_edges()
	if not title.is_empty():
		return title.replace("->", "→")
	return _direction_from_to_text(direction)


func _direction_from_to_text(direction: Dictionary) -> String:
	return "%s → %s" % [
		_station_title(str(direction.get("from_station_id", ""))),
		_station_title(str(direction.get("to_station_id", ""))),
	]


func _station_title(station_id: String) -> String:
	for item in _array_field(current_object, "stations"):
		if item is Dictionary:
			var station: Dictionary = item
			if str(station.get("id", "")) == station_id:
				return _value_text(station.get("title", ""), "станция без названия")
	return "станция не указана"


func _array_field(object_data: Dictionary, key: String) -> Array:
	if object_data.has(key) and object_data.get(key) is Array:
		return object_data.get(key)
	return []


func _add_text_label(rows: VBoxContainer, font_size: int) -> Label:
	var label := Label.new()
	label.add_theme_font_size_override("font_size", font_size)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.custom_minimum_size = Vector2(0, 32)
	rows.add_child(label)
	return label


func _value_text(value: Variant, empty_text: String) -> String:
	if value == null:
		return empty_text
	if value is String and value.strip_edges().is_empty():
		return empty_text
	return str(value)
