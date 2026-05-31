extends ItemList
class_name ObjectListPanel

signal object_selected(index: int)

const FILTER_ALL := "all"
const FILTER_VISITED := "visited"
const FILTER_NOT_VISITED := "not_visited"
const ATLAS_PARCHMENT_COLOR := Color(0.96, 0.90, 0.72, 0.94)
const ATLAS_PARCHMENT_ALT_COLOR := Color(0.99, 0.94, 0.78, 0.82)
const ATLAS_BORDER_COLOR := Color("#3b2a18")
const ATLAS_TEXT_COLOR := Color("#27321f")
const ATLAS_SELECTED_COLOR := Color("#31544d")
const ATLAS_SELECTED_TEXT_COLOR := Color("#f7e4b0")
const ATLAS_SHADOW_COLOR := Color(0.12, 0.08, 0.03, 0.42)
const ATLAS_LIST_RADIUS := 6
const ATLAS_LIST_BORDER_WIDTH := 2

var objects: Array[Dictionary] = []
var type_filter: String = FILTER_ALL
var visit_filter: String = FILTER_ALL
var country_filter: String = FILTER_ALL
var search_query: String = ""
var visible_object_indices: Array[int] = []
var empty_state_label: Label
var touch_start_position := Vector2.ZERO
var touch_is_dragging := false
var suppress_selection_until_msec := 0
var visual_selection_refreshing := false
var selection_request_token := 0

const TOUCH_DRAG_THRESHOLD := 18.0
const SELECTION_SUPPRESS_MSEC := 250
const TAP_SELECTION_DELAY_SEC := 0.12

func _ready() -> void:
	item_selected.connect(_on_item_selected)
	mouse_filter = Control.MOUSE_FILTER_STOP
	_apply_atlas_list_style()
	_update_empty_state()

func set_empty_state_label(label: Label) -> void:
	empty_state_label = label
	_update_empty_state()

func set_objects(next_objects: Array[Dictionary]) -> void:
	objects = next_objects
	refresh()

func set_filters(next_type_filter: String, next_visit_filter: String, next_country_filter: String = FILTER_ALL) -> void:
	type_filter = next_type_filter
	visit_filter = next_visit_filter
	country_filter = next_country_filter
	refresh()

func set_search_query(next_search_query: String) -> void:
	search_query = next_search_query.strip_edges().to_lower()
	refresh()

func get_transport_types() -> Array[String]:
	var transport_types: Array[String] = []
	for object_data in objects:
		var kind: String = object_data.get("kind", "")
		if kind != "" and not transport_types.has(kind):
			transport_types.append(kind)

	transport_types.sort()
	return transport_types

func get_countries() -> Array[String]:
	var countries: Array[String] = []
	for object_data in objects:
		var country: String = object_data.get("country", "")
		if country != "" and not countries.has(country):
			countries.append(country)

	countries.sort()
	return countries

func refresh() -> void:
	clear()
	visible_object_indices.clear()
	for index in objects.size():
		var object_data := objects[index]
		if not _matches_filters(object_data):
			continue

		visible_object_indices.append(index)
		var label := "%s\n%s · %s · %s" % [
			object_data.get("name", "Без названия"),
			object_data.get("region", "Регион не указан"),
			_visit_status_text(object_data),
			_operational_status_text(object_data)
		]
		add_item(label)
		var visible_index := get_item_count() - 1
		set_item_custom_bg_color(visible_index, ATLAS_PARCHMENT_ALT_COLOR if visible_index % 2 == 0 else ATLAS_PARCHMENT_COLOR)
		set_item_tooltip(visible_index, "Открыть объект: %s" % object_data.get("name", "Без названия"))
	_update_empty_state()

func _apply_atlas_list_style() -> void:
	fixed_icon_size = Vector2i(1, 1)
	add_theme_color_override("font_color", ATLAS_TEXT_COLOR)
	add_theme_color_override("font_selected_color", ATLAS_SELECTED_TEXT_COLOR)
	add_theme_color_override("guide_color", Color(0.23, 0.16, 0.09, 0.20))
	add_theme_font_size_override("font_size", 18)

	var panel_style := StyleBoxFlat.new()
	panel_style.bg_color = ATLAS_PARCHMENT_COLOR
	panel_style.border_color = ATLAS_BORDER_COLOR
	panel_style.shadow_color = ATLAS_SHADOW_COLOR
	panel_style.shadow_size = 5
	panel_style.content_margin_left = 8.0
	panel_style.content_margin_top = 8.0
	panel_style.content_margin_right = 8.0
	panel_style.content_margin_bottom = 8.0
	panel_style.set_border_width_all(ATLAS_LIST_BORDER_WIDTH)
	panel_style.set_corner_radius_all(ATLAS_LIST_RADIUS)
	add_theme_stylebox_override("panel", panel_style)

	var selected_style := StyleBoxFlat.new()
	selected_style.bg_color = ATLAS_SELECTED_COLOR
	selected_style.border_color = ATLAS_BORDER_COLOR
	selected_style.set_border_width_all(ATLAS_LIST_BORDER_WIDTH)
	selected_style.set_corner_radius_all(ATLAS_LIST_RADIUS)
	add_theme_stylebox_override("selected", selected_style)
	add_theme_stylebox_override("selected_focus", selected_style)

	var cursor_style := selected_style.duplicate()
	cursor_style.bg_color = Color(0.18, 0.31, 0.28, 0.18)
	add_theme_stylebox_override("cursor", cursor_style)
	add_theme_stylebox_override("cursor_unfocused", cursor_style)

func select_object(index: int) -> void:
	if index < 0 or index >= objects.size():
		return

	select_visual_object(index)
	object_selected.emit(index)

func select_visual_object(index: int) -> void:
	var visible_index := visible_object_indices.find(index)
	if visible_index == -1:
		return

	visual_selection_refreshing = true
	select(visible_index)
	visual_selection_refreshing = false

func _matches_filters(object_data: Dictionary) -> bool:
	if type_filter != FILTER_ALL and object_data.get("kind", "") != type_filter:
		return false
	if country_filter != FILTER_ALL and object_data.get("country", "") != country_filter:
		return false
	if not search_query.is_empty() and not _matches_search(object_data):
		return false

	var is_visited := _is_object_visited(object_data)
	if visit_filter == FILTER_VISITED and not is_visited:
		return false
	if visit_filter == FILTER_NOT_VISITED and is_visited:
		return false

	return true

func _matches_search(object_data: Dictionary) -> bool:
	var searchable_parts := PackedStringArray([
		str(object_data.get("name", "")),
		str(object_data.get("title", "")),
		str(object_data.get("region", "")),
		str(object_data.get("country", "")),
	])
	var searchable_text := " ".join(searchable_parts).to_lower()
	return searchable_text.contains(search_query)

func _is_object_visited(object_data: Dictionary) -> bool:
	if object_data.has("visit_status_id"):
		return SQLiteStorageAdapter.status_is_visited(str(object_data.get("visit_status_id", "")))
	return object_data.get("visited", false)

func _visit_status_text(object_data: Dictionary) -> String:
	if object_data.has("visit_status_id"):
		return SQLiteStorageAdapter.status_title(str(object_data.get("visit_status_id", "")))
	return SQLiteStorageAdapter.status_title(SQLiteStorageAdapter.STATUS_VISITED if object_data.get("visited", false) else SQLiteStorageAdapter.STATUS_NOT_VISITED)


func _operational_status_text(object_data: Dictionary) -> String:
	return "работа: %s" % SQLiteStorageAdapter.operational_status_title(str(object_data.get("operational_status", SQLiteStorageAdapter.OPERATIONAL_UNKNOWN)))


func _update_empty_state() -> void:
	if empty_state_label == null:
		return

	empty_state_label.visible = get_item_count() == 0
	visible = get_item_count() > 0
	if objects.is_empty():
		empty_state_label.text = "Пока нет объектов. Когда список появится, здесь можно будет выбрать место для семейной поездки."
	else:
		empty_state_label.text = "По этому поиску и фильтрам ничего не нашлось. Попробуйте изменить запрос, страну, тип или статус."

func _gui_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		if event.pressed:
			touch_start_position = event.position
			touch_is_dragging = false
		else:
			if touch_is_dragging:
				suppress_selection_until_msec = Time.get_ticks_msec() + SELECTION_SUPPRESS_MSEC
			touch_is_dragging = false
	elif event is InputEventScreenDrag:
		if event.position.distance_to(touch_start_position) >= TOUCH_DRAG_THRESHOLD:
			touch_is_dragging = true
			suppress_selection_until_msec = Time.get_ticks_msec() + SELECTION_SUPPRESS_MSEC
	elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		if event.relative.length() >= TOUCH_DRAG_THRESHOLD:
			touch_is_dragging = true
			suppress_selection_until_msec = Time.get_ticks_msec() + SELECTION_SUPPRESS_MSEC

func _on_item_selected(index: int) -> void:
	if index < 0 or index >= visible_object_indices.size():
		return
	if visual_selection_refreshing:
		return

	selection_request_token += 1
	var request_token := selection_request_token
	await get_tree().create_timer(TAP_SELECTION_DELAY_SEC).timeout
	if request_token != selection_request_token:
		return
	if touch_is_dragging or Time.get_ticks_msec() < suppress_selection_until_msec:
		return

	object_selected.emit(visible_object_indices[index])
