extends ScrollContainer
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
const ATLAS_SELECTED_META_TEXT_COLOR := Color("#dfc986")
const ATLAS_SHADOW_COLOR := Color(0.12, 0.08, 0.03, 0.42)
const ATLAS_META_TEXT_COLOR := Color("#52604a")
const ATLAS_TYPE_TEXT_COLOR := Color("#6e5431")
const ATLAS_ICON_INK_COLOR := Color("#2b392f")
const ATLAS_ICON_CABLE_COLOR := Color("#6e5431")
const ATLAS_ICON_VISITED_COLOR := Color("#5f8a54")
const ATLAS_ICON_PLANNED_COLOR := Color("#a98237")
const ATLAS_ICON_UNKNOWN_COLOR := Color("#7b725e")
const ATLAS_LIST_RADIUS := 6
const ATLAS_LIST_BORDER_WIDTH := 2
const LIST_ICON_SIZE := Vector2i(36, 36)
const ROW_NAME_MAX_CHARS := 30
const ROW_TYPE_MAX_CHARS := 32
const ROW_META_MAX_CHARS := 42

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
var icon_cache: Dictionary = {}
var rows_container: VBoxContainer
var row_buttons: Array[Button] = []

const TOUCH_DRAG_THRESHOLD := 18.0
const SELECTION_SUPPRESS_MSEC := 250
const TAP_SELECTION_DELAY_SEC := 0.12

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	_apply_atlas_list_style()
	_create_rows_container()
	_update_empty_state()

func _draw() -> void:
	draw_style_box(_panel_style(), Rect2(Vector2.ZERO, size))

func set_empty_state_label(label: Label) -> void:
	empty_state_label = label
	_apply_empty_state_style()
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
	_clear_rows()
	visible_object_indices.clear()
	for index in objects.size():
		var object_data := objects[index]
		if not _matches_filters(object_data):
			continue

		visible_object_indices.append(index)
		var visible_index := row_buttons.size()
		_add_row(object_data, index, visible_index)
	_update_empty_state()

func _apply_atlas_list_style() -> void:
	add_theme_stylebox_override("panel", _panel_style())

func _apply_empty_state_style() -> void:
	if empty_state_label == null:
		return
	empty_state_label.add_theme_color_override("font_color", ATLAS_META_TEXT_COLOR)
	empty_state_label.add_theme_font_size_override("font_size", 14)
	empty_state_label.add_theme_stylebox_override("normal", _empty_state_style())

func _create_rows_container() -> void:
	rows_container = VBoxContainer.new()
	rows_container.name = "Rows"
	rows_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows_container.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rows_container.add_theme_constant_override("separation", 2)
	add_child(rows_container)

func _clear_rows() -> void:
	if rows_container == null:
		return
	for child in rows_container.get_children():
		rows_container.remove_child(child)
		child.queue_free()
	row_buttons.clear()

func _add_row(object_data: Dictionary, object_index: int, visible_index: int) -> void:
	var row := Button.new()
	row.toggle_mode = true
	row.focus_mode = Control.FOCUS_NONE
	row.text = ""
	row.tooltip_text = "Открыть объект: %s" % object_data.get("name", "Без названия")
	row.custom_minimum_size = Vector2(0, 70)
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_theme_stylebox_override("normal", _row_style(visible_index, false))
	row.add_theme_stylebox_override("hover", _row_style(visible_index, false, true))
	row.add_theme_stylebox_override("pressed", _row_style(visible_index, true))
	row.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	rows_container.add_child(row)
	row_buttons.append(row)

	var row_content := HBoxContainer.new()
	row_content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row_content.set_anchors_preset(Control.PRESET_FULL_RECT)
	row_content.offset_left = 8
	row_content.offset_top = 6
	row_content.offset_right = -8
	row_content.offset_bottom = -6
	row_content.add_theme_constant_override("separation", 10)
	row.add_child(row_content)

	var icon := TextureRect.new()
	icon.texture = _object_icon_texture(object_data)
	icon.custom_minimum_size = Vector2(LIST_ICON_SIZE)
	icon.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	row_content.add_child(icon)

	var text_box := VBoxContainer.new()
	text_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	text_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text_box.add_theme_constant_override("separation", 1)
	row_content.add_child(text_box)

	var name_label := Label.new()
	name_label.text = _compact_name(str(object_data.get("name", "Без названия")))
	name_label.clip_text = true
	name_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	name_label.add_theme_font_size_override("font_size", 15)
	name_label.add_theme_color_override("font_color", ATLAS_TEXT_COLOR)
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text_box.add_child(name_label)

	var type_label := Label.new()
	type_label.text = _row_type_text(object_data)
	type_label.clip_text = true
	type_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	type_label.add_theme_font_size_override("font_size", 12)
	type_label.add_theme_color_override("font_color", ATLAS_TYPE_TEXT_COLOR)
	type_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text_box.add_child(type_label)

	var meta_label := Label.new()
	meta_label.text = _row_meta_text(object_data)
	meta_label.clip_text = true
	meta_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	meta_label.add_theme_font_size_override("font_size", 13)
	meta_label.add_theme_color_override("font_color", ATLAS_META_TEXT_COLOR)
	meta_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text_box.add_child(meta_label)

	var open_hint := Label.new()
	open_hint.text = ">"
	open_hint.tooltip_text = "Открыть карточку объекта"
	open_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	open_hint.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	open_hint.custom_minimum_size = Vector2(18, 0)
	open_hint.add_theme_font_size_override("font_size", 20)
	open_hint.add_theme_color_override("font_color", ATLAS_TYPE_TEXT_COLOR)
	row_content.add_child(open_hint)

	row.toggled.connect(func(toggled_on: bool) -> void: _sync_row_visual_state(name_label, type_label, meta_label, open_hint, toggled_on))
	row.pressed.connect(func() -> void: _on_row_pressed(object_index))

func _panel_style() -> StyleBoxFlat:
	var panel_style := StyleBoxFlat.new()
	panel_style.bg_color = ATLAS_PARCHMENT_COLOR
	panel_style.border_color = ATLAS_BORDER_COLOR
	panel_style.shadow_color = ATLAS_SHADOW_COLOR
	panel_style.shadow_size = 5
	panel_style.content_margin_left = 6.0
	panel_style.content_margin_top = 6.0
	panel_style.content_margin_right = 6.0
	panel_style.content_margin_bottom = 6.0
	panel_style.set_border_width_all(ATLAS_LIST_BORDER_WIDTH)
	panel_style.set_corner_radius_all(ATLAS_LIST_RADIUS)
	return panel_style

func _row_style(visible_index: int, selected: bool, hovered: bool = false) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = ATLAS_SELECTED_COLOR if selected else (ATLAS_PARCHMENT_ALT_COLOR if visible_index % 2 == 0 else ATLAS_PARCHMENT_COLOR)
	if hovered and not selected:
		style.bg_color = Color(0.94, 0.86, 0.61, 0.96)
	style.border_color = Color(0.23, 0.16, 0.09, 0.18) if not selected else ATLAS_BORDER_COLOR
	style.content_margin_left = 6.0
	style.content_margin_top = 4.0
	style.content_margin_right = 6.0
	style.content_margin_bottom = 4.0
	style.set_border_width_all(1 if selected else 0)
	style.set_corner_radius_all(4)
	return style

func _empty_state_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.99, 0.94, 0.78, 0.72)
	style.border_color = Color(0.23, 0.16, 0.09, 0.22)
	style.content_margin_left = 10.0
	style.content_margin_top = 10.0
	style.content_margin_right = 10.0
	style.content_margin_bottom = 10.0
	style.set_border_width_all(1)
	style.set_corner_radius_all(4)
	return style

func _sync_row_visual_state(name_label: Label, type_label: Label, meta_label: Label, open_hint: Label, selected: bool) -> void:
	name_label.add_theme_color_override("font_color", ATLAS_SELECTED_TEXT_COLOR if selected else ATLAS_TEXT_COLOR)
	type_label.add_theme_color_override("font_color", ATLAS_SELECTED_META_TEXT_COLOR if selected else ATLAS_TYPE_TEXT_COLOR)
	meta_label.add_theme_color_override("font_color", ATLAS_SELECTED_META_TEXT_COLOR if selected else ATLAS_META_TEXT_COLOR)
	open_hint.add_theme_color_override("font_color", ATLAS_SELECTED_TEXT_COLOR if selected else ATLAS_TYPE_TEXT_COLOR)

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
	for row_index in row_buttons.size():
		row_buttons[row_index].button_pressed = row_index == visible_index
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

func _location_text(object_data: Dictionary) -> String:
	var city := str(object_data.get("city", "")).strip_edges()
	if not city.is_empty():
		return city
	var region := str(object_data.get("region", "")).strip_edges()
	if not region.is_empty():
		return region
	return "Место не указано"

func _compact_name(name: String) -> String:
	var compact := name.replace("Канатная дорога ", "").replace("подвесная железная дорога", "подвесная дорога")
	return _trim_for_row(compact, ROW_NAME_MAX_CHARS)

func _row_type_text(object_data: Dictionary) -> String:
	var type_title := str(object_data.get("transport_type_title", "")).strip_edges()
	if type_title.is_empty():
		type_title = str(object_data.get("kind", "")).strip_edges()
	if type_title.is_empty():
		type_title = "тип не указан"
	return _trim_for_row(type_title, ROW_TYPE_MAX_CHARS)

func _row_meta_text(object_data: Dictionary) -> String:
	var parts := PackedStringArray([
		_location_text(object_data),
		_visit_status_text(object_data),
		_operational_status_text(object_data),
	])
	return _trim_for_row(" · ".join(parts), ROW_META_MAX_CHARS)

func _trim_for_row(text: String, max_chars: int) -> String:
	if text.length() <= max_chars:
		return text
	return "%s..." % text.substr(0, max(0, max_chars - 3)).strip_edges()

func _visit_status_text(object_data: Dictionary) -> String:
	if object_data.has("visit_status_id"):
		return SQLiteStorageAdapter.status_title(str(object_data.get("visit_status_id", "")))
	return SQLiteStorageAdapter.status_title(SQLiteStorageAdapter.STATUS_VISITED if object_data.get("visited", false) else SQLiteStorageAdapter.STATUS_NOT_VISITED)


func _operational_status_text(object_data: Dictionary) -> String:
	return SQLiteStorageAdapter.operational_status_title(str(object_data.get("operational_status", SQLiteStorageAdapter.OPERATIONAL_UNKNOWN)))

func _object_icon_texture(object_data: Dictionary) -> Texture2D:
	var kind := str(object_data.get("kind", "")).to_lower()
	var status := str(object_data.get("visit_status_id", "visited" if object_data.get("visited", false) else "not_visited"))
	var cache_key := "%s:%s" % [_icon_family(kind), status]
	if icon_cache.has(cache_key):
		return icon_cache[cache_key]

	var image := Image.create(LIST_ICON_SIZE.x, LIST_ICON_SIZE.y, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	_fill_rect(image, Rect2i(2, 2, 32, 32), Color(0.94, 0.84, 0.58, 0.94))
	_fill_rect(image, Rect2i(2, 2, 32, 2), ATLAS_BORDER_COLOR)
	_fill_rect(image, Rect2i(2, 32, 32, 2), ATLAS_BORDER_COLOR)
	_fill_rect(image, Rect2i(2, 2, 2, 32), ATLAS_BORDER_COLOR)
	_fill_rect(image, Rect2i(32, 2, 2, 32), ATLAS_BORDER_COLOR)
	_draw_transport_pictogram(image, _icon_family(kind))
	_draw_visit_badge(image, status)

	var texture := ImageTexture.create_from_image(image)
	icon_cache[cache_key] = texture
	return texture

func _icon_family(kind: String) -> String:
	if kind.contains("фуникулер"):
		return "funicular"
	if kind.contains("лифт"):
		return "elevator"
	if kind.contains("монорельс") or kind.contains("поезд"):
		return "rail"
	return "cable"

func _draw_transport_pictogram(image: Image, family: String) -> void:
	_draw_line(image, Vector2i(7, 13), Vector2i(28, 9), ATLAS_ICON_CABLE_COLOR)
	if family == "funicular":
		_fill_rect(image, Rect2i(11, 17, 14, 8), ATLAS_ICON_INK_COLOR)
		_fill_rect(image, Rect2i(13, 15, 10, 2), ATLAS_ICON_INK_COLOR)
		_fill_rect(image, Rect2i(13, 19, 3, 3), ATLAS_PARCHMENT_COLOR)
		_fill_rect(image, Rect2i(20, 19, 3, 3), ATLAS_PARCHMENT_COLOR)
		_draw_line(image, Vector2i(8, 27), Vector2i(28, 24), ATLAS_ICON_CABLE_COLOR)
	elif family == "elevator":
		_fill_rect(image, Rect2i(14, 10, 8, 17), ATLAS_ICON_INK_COLOR)
		_fill_rect(image, Rect2i(16, 13, 4, 4), ATLAS_PARCHMENT_COLOR)
		_draw_line(image, Vector2i(24, 10), Vector2i(24, 27), ATLAS_ICON_CABLE_COLOR)
	elif family == "rail":
		_fill_rect(image, Rect2i(10, 15, 17, 8), ATLAS_ICON_INK_COLOR)
		_fill_rect(image, Rect2i(13, 17, 4, 3), ATLAS_PARCHMENT_COLOR)
		_fill_rect(image, Rect2i(20, 17, 4, 3), ATLAS_PARCHMENT_COLOR)
		_draw_line(image, Vector2i(9, 27), Vector2i(28, 27), ATLAS_ICON_CABLE_COLOR)
	else:
		_fill_rect(image, Rect2i(11, 14, 14, 10), ATLAS_ICON_INK_COLOR)
		_fill_rect(image, Rect2i(14, 16, 3, 4), ATLAS_PARCHMENT_COLOR)
		_fill_rect(image, Rect2i(20, 16, 3, 4), ATLAS_PARCHMENT_COLOR)
		_draw_line(image, Vector2i(18, 11), Vector2i(18, 14), ATLAS_ICON_CABLE_COLOR)

func _draw_visit_badge(image: Image, status: String) -> void:
	var badge_color := ATLAS_ICON_VISITED_COLOR if SQLiteStorageAdapter.status_is_visited(status) else ATLAS_ICON_UNKNOWN_COLOR
	if status == SQLiteStorageAdapter.STATUS_PLANNED:
		badge_color = ATLAS_ICON_PLANNED_COLOR
	_fill_rect(image, Rect2i(24, 24, 7, 7), badge_color)
	_fill_rect(image, Rect2i(26, 26, 3, 3), ATLAS_PARCHMENT_COLOR)

func _fill_rect(image: Image, rect: Rect2i, color: Color) -> void:
	for y in range(rect.position.y, rect.position.y + rect.size.y):
		for x in range(rect.position.x, rect.position.x + rect.size.x):
			if x >= 0 and x < image.get_width() and y >= 0 and y < image.get_height():
				image.set_pixel(x, y, color)

func _draw_line(image: Image, from_point: Vector2i, to_point: Vector2i, color: Color) -> void:
	var delta := to_point - from_point
	var steps: int = maxi(abs(delta.x), abs(delta.y))
	if steps <= 0:
		image.set_pixel(from_point.x, from_point.y, color)
		return
	for step in range(steps + 1):
		var t := float(step) / float(steps)
		var point := Vector2i(roundi(lerpf(from_point.x, to_point.x, t)), roundi(lerpf(from_point.y, to_point.y, t)))
		_fill_rect(image, Rect2i(point.x, point.y, 2, 2), color)


func _update_empty_state() -> void:
	if empty_state_label == null:
		return

	var has_rows := not visible_object_indices.is_empty()
	empty_state_label.visible = not has_rows
	visible = has_rows
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

func _on_row_pressed(object_index: int) -> void:
	if visual_selection_refreshing:
		return

	selection_request_token += 1
	var request_token := selection_request_token
	await get_tree().create_timer(TAP_SELECTION_DELAY_SEC).timeout
	if request_token != selection_request_token:
		return
	if touch_is_dragging or Time.get_ticks_msec() < suppress_selection_until_msec:
		return

	object_selected.emit(object_index)
