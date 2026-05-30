extends Control
class_name MainScreen

const AppSettings := preload("res://scripts/app_settings.gd")
const MapPanelScript := preload("res://scripts/map_panel.gd")
const ObjectModePanelScript := preload("res://scripts/object_mode_panel.gd")
const RidePanelScript := preload("res://scripts/ride_panel.gd")
const COLLECTION_STATS_SCRIPT_PATH := "res://scripts/collection_stats.gd"
const ACHIEVEMENTS_SCRIPT_PATH := "res://scripts/achievements.gd"
const CONTENT_WIDTH_GUARD := 2.0

@onready var object_list: ObjectListPanel = %ObjectList
@onready var object_card: ObjectCardPanel = %ObjectCard
@onready var memory_panel: MemoryPanel = %MemoryPanel
@onready var object_mode_panel: ObjectModePanelScript = %ObjectModePanel
@onready var observer_panel: ObserverPanel = %ObserverPanel
@onready var map_panel: MapPanelScript = %MapPanel
@onready var ride_panel: RidePanelScript = %RidePanel
@onready var search_line_edit: LineEdit = %SearchLineEdit
@onready var type_filter_option: OptionButton = %TypeFilterOption
@onready var visit_filter_option: OptionButton = %VisitFilterOption
@onready var country_filter_option: OptionButton = %CountryFilterOption
@onready var orientation_option: OptionButton = %OrientationOption
@onready var list_empty_state_label: Label = %ListEmptyStateLabel
@onready var list_active_collection_filter_label: Label = %ListActiveCollectionFilterLabel
@onready var journal_label: RichTextLabel = %JournalLabel
@onready var selected_object_label: Label = %SelectedObjectLabel
@onready var map_button: Button = %MapButton
@onready var list_button: Button = %ListButton
@onready var card_button: Button = %CardButton
@onready var object_mode_button: Button = %ObjectModeButton
@onready var observer_button: Button = %ObserverButton
@onready var memory_button: Button = %MemoryButton
@onready var ride_button: Button = %RideButton
@onready var collection_button: Button = %CollectionButton
@onready var journal_button: Button = %JournalButton
@onready var settings_button: Button = %SettingsButton
@onready var navigation_scroll: ScrollContainer = %НавигацияПрокрутка
@onready var current_section_label: Label = %CurrentSectionLabel
@onready var map_section: VBoxContainer = %MapSection
@onready var list_section: VBoxContainer = %ListSection
@onready var card_section: VBoxContainer = %CardSection
@onready var object_mode_section: VBoxContainer = %ObjectModeSection
@onready var observer_section: VBoxContainer = %ObserverSection
@onready var memory_section: VBoxContainer = %MemorySection
@onready var ride_section: VBoxContainer = %RideSection
@onready var collection_section: VBoxContainer = %CollectionSection
@onready var journal_section: VBoxContainer = %JournalSection
@onready var settings_section: VBoxContainer = %SettingsSection
@onready var content_viewport: Control = $Отступы/Оболочка/Содержимое/ContentViewport
@onready var content_scroll: ScrollContainer = %ContentScroll
@onready var sections_container: VBoxContainer = $Отступы/Оболочка/Содержимое/ContentViewport/ContentScroll/Секции
@onready var collection_rows: VBoxContainer = %CollectionRows
@onready var collection_empty_state_label: Label = %CollectionEmptyStateLabel

var objects: Array[Dictionary] = []
var collection_stats: Dictionary = {}
var journal_entries: Array[String] = []
var selected_index: int = -1
var sections: Dictionary = {}
var navigation_buttons: Dictionary = {}
var section_titles: Dictionary = {}
var storage: SQLiteStorageAdapter = SQLiteStorageAdapter.new()
var storage_runtime_enabled: bool = false
var app_settings: RefCounted = AppSettings.new()
var collection_stats_script: Resource = null
var achievements_script: Resource = null
var orientation_option_is_refreshing: bool = false

func _ready() -> void:
	collection_stats_script = load(COLLECTION_STATS_SCRIPT_PATH) if ResourceLoader.exists(COLLECTION_STATS_SCRIPT_PATH) else null
	achievements_script = load(ACHIEVEMENTS_SCRIPT_PATH) if ResourceLoader.exists(ACHIEVEMENTS_SCRIPT_PATH) else null
	objects = _load_objects_from_local_source()
	sections = {
		"map": map_section,
		"list": list_section,
		"card": card_section,
		"object_mode": object_mode_section,
		"observer": observer_section,
		"memory": memory_section,
		"ride": ride_section,
		"collection": collection_section,
		"journal": journal_section,
		"settings": settings_section,
	}
	navigation_buttons = {
		"map": map_button,
		"list": list_button,
		"card": card_button,
		"object_mode": object_mode_button,
		"observer": observer_button,
		"memory": memory_button,
		"ride": ride_button,
		"collection": collection_button,
		"journal": journal_button,
		"settings": settings_button,
	}
	section_titles = {
		"map": "Карта",
		"list": "Список",
		"card": "Карточка",
		"object_mode": "Режим объекта",
		"observer": "Наблюдатель",
		"memory": "Воспоминание",
		"ride": "Поездка",
		"collection": "Коллекция",
		"journal": "Журнал",
		"settings": "Настройки",
	}

	map_button.pressed.connect(func() -> void: _show_section("map"))
	list_button.pressed.connect(func() -> void: _show_section("list"))
	card_button.pressed.connect(func() -> void: _show_section("card"))
	object_mode_button.pressed.connect(func() -> void: _show_section("object_mode"))
	observer_button.pressed.connect(func() -> void: _show_section("observer"))
	memory_button.pressed.connect(func() -> void: _show_section("memory"))
	ride_button.pressed.connect(func() -> void: _show_section("ride"))
	collection_button.pressed.connect(func() -> void: _show_section("collection"))
	journal_button.pressed.connect(func() -> void: _show_section("journal"))
	settings_button.pressed.connect(func() -> void: _show_section("settings"))
	orientation_option.item_selected.connect(_on_orientation_selected)
	search_line_edit.text_changed.connect(_on_search_changed)
	type_filter_option.item_selected.connect(_on_filter_changed)
	visit_filter_option.item_selected.connect(_on_filter_changed)
	country_filter_option.item_selected.connect(_on_filter_changed)
	object_list.set_empty_state_label(list_empty_state_label)
	object_list.set_objects(objects)
	object_list.object_selected.connect(_on_object_selected)
	object_card.status_changed.connect(_on_status_changed)
	object_card.photo_registration_requested.connect(_on_photo_registration_requested)
	object_card.visit_registration_requested.connect(_on_visit_registration_requested)
	object_card.object_mode_requested.connect(func() -> void: _show_section("object_mode"))
	object_card.observer_requested.connect(func() -> void: _show_section("observer"))
	memory_panel.back_requested.connect(func() -> void: _show_section("card"))
	object_mode_panel.card_requested.connect(func() -> void: _show_section("card"))
	object_mode_panel.ride_requested.connect(func() -> void: _show_section("ride"))
	observer_panel.back_requested.connect(func() -> void: _show_section("card"))
	ride_panel.card_requested.connect(func() -> void: _show_section("card"))
	map_panel.set_objects(objects)
	map_panel.object_selected.connect(_on_map_object_selected)
	content_viewport.resized.connect(_sync_content_width)

	_configure_orientation_setting()
	_configure_list_filters()
	_sync_content_width()
	_refresh_collection()
	if not objects.is_empty():
		_select_object(0, false)
	_show_section("map")

func set_collection_stats(next_stats: Dictionary) -> void:
	collection_stats = next_stats
	if collection_rows != null:
		_refresh_collection()

func _load_objects_from_local_source() -> Array[Dictionary]:
	var open_result := storage.open()
	if open_result == OK:
		var migration_result := storage.migrate()
		var seed_result := storage.seed_demo_objects() if migration_result == OK else migration_result
		if seed_result == OK:
			var stored_objects := storage.list_objects()
			if not stored_objects.is_empty():
				storage_runtime_enabled = true
				return _attach_photo_lists(stored_objects)
		push_warning("Локальное хранилище недоступно, открыт встроенный каталог: %s" % storage.last_error)
		storage.close()
	else:
		push_warning("Локальное хранилище недоступно: %s" % storage.last_error)

	storage_runtime_enabled = false
	return DemoCatalog.get_objects()

func _on_object_selected(index: int) -> void:
	_select_object(index, true)

func _on_map_object_selected(index: int) -> void:
	_select_object(index, false)

func _on_filter_changed(_item_index: int) -> void:
	var type_filter := ObjectListPanel.FILTER_ALL
	if type_filter_option.selected > 0:
		type_filter = type_filter_option.get_item_text(type_filter_option.selected)

	var country_filter := ObjectListPanel.FILTER_ALL
	if country_filter_option.selected > 0:
		country_filter = country_filter_option.get_item_text(country_filter_option.selected)

	var visit_filter := ObjectListPanel.FILTER_ALL
	if visit_filter_option.selected == 1:
		visit_filter = ObjectListPanel.FILTER_NOT_VISITED
	elif visit_filter_option.selected == 2:
		visit_filter = ObjectListPanel.FILTER_VISITED

	object_list.set_filters(type_filter, visit_filter, country_filter)
	list_active_collection_filter_label.visible = false
	if selected_index >= 0:
		object_list.select_visual_object(selected_index)

func _on_search_changed(next_text: String) -> void:
	object_list.set_search_query(next_text)
	list_active_collection_filter_label.visible = false
	if selected_index >= 0:
		object_list.select_visual_object(selected_index)

func _on_status_changed(object_id: String, status_id: String) -> void:
	var normalized_status := SQLiteStorageAdapter.normalized_status_id(status_id)
	for index in objects.size():
		if objects[index].get("id", "") == object_id:
			if storage_runtime_enabled:
				var update_result := storage.update_object_status(object_id, normalized_status)
				if update_result != OK:
					push_warning("Не удалось сохранить статус посещения: %s" % storage.last_error)
			var visited := SQLiteStorageAdapter.status_is_visited(normalized_status)
			objects[index]["visited"] = visited
			objects[index]["visit_status_id"] = normalized_status
			object_list.refresh()
			map_panel.set_objects(objects)
			_refresh_collection()
			_select_object(index, false)
			_add_journal_entry(objects[index], normalized_status)
			return

func _on_photo_registration_requested(object_id: String) -> void:
	if not storage_runtime_enabled:
		push_warning("Добавление фото сейчас недоступно: локальное хранилище не открыто.")
		return

	for index in objects.size():
		if objects[index].get("id", "") != object_id:
			continue

		var sequence := int(objects[index].get("photo_count", 0)) + 1
		var media_id := "%s-photo-%d-%d" % [
			object_id,
			int(Time.get_unix_time_from_system()),
			Time.get_ticks_msec(),
		]
		var local_path := "media/%s/%s.jpg" % [object_id, media_id]
		var caption := "Фото %d: запись без выбранного файла" % sequence
		var save_result := storage.upsert_media_asset({
			"id": media_id,
			"transport_object_id": object_id,
			"kind": SQLiteStorageAdapter.MEDIA_KIND_PHOTO,
			"local_path": local_path,
			"caption": caption,
		})
		if save_result != OK:
			push_warning("Не удалось сохранить запись о фото: %s" % storage.last_error)
			return

		objects[index]["photos"] = storage.list_object_photos(object_id)
		objects[index]["photo_count"] = objects[index]["photos"].size()
		objects[index]["tickets"] = storage.list_tickets(object_id)
		objects[index]["ticket_count"] = objects[index]["tickets"].size()
		object_list.refresh()
		_select_object(index, false)
		_add_photo_journal_entry(objects[index], caption)
		return

func _on_visit_registration_requested(object_id: String, title: String, notes: String) -> void:
	if not storage_runtime_enabled:
		push_warning("Журнал посещений сейчас недоступен: локальное хранилище не открыто.")
		return

	for index in objects.size():
		if objects[index].get("id", "") != object_id:
			continue

		var visited_at := Time.get_datetime_dict_from_system(false)
		var visited_on := "%04d-%02d-%02d %02d:%02d" % [
			int(visited_at.get("year", 0)),
			int(visited_at.get("month", 0)),
			int(visited_at.get("day", 0)),
			int(visited_at.get("hour", 0)),
			int(visited_at.get("minute", 0)),
		]
		var visit_id := "%s-visit-%d-%d" % [
			object_id,
			int(Time.get_unix_time_from_system()),
			Time.get_ticks_msec(),
		]
		var visit_title := title if not title.is_empty() else "Семейная поездка"
		var visit_notes := notes if not notes.is_empty() else "Заметка пока не добавлена."
		var save_result := storage.upsert_visit({
			"id": visit_id,
			"transport_object_id": object_id,
			"visited_on": visited_on,
			"title": visit_title,
			"notes": visit_notes,
		})
		if save_result != OK:
			push_warning("Не удалось сохранить посещение: %s" % storage.last_error)
			return

		objects[index]["visits"] = storage.list_visits(object_id)
		objects[index]["visit_count"] = objects[index]["visits"].size()
		objects[index]["tickets"] = storage.list_tickets(object_id)
		objects[index]["ticket_count"] = objects[index]["tickets"].size()
		object_list.refresh()
		_select_object(index, false)
		_add_visit_journal_entry(objects[index], visit_title, visited_on)
		return

func _exit_tree() -> void:
	storage.close()

func _configure_list_filters() -> void:
	type_filter_option.clear()
	type_filter_option.add_item("Все виды транспорта")
	for transport_type in object_list.get_transport_types():
		type_filter_option.add_item(transport_type)

	visit_filter_option.clear()
	visit_filter_option.add_item("Все объекты")
	visit_filter_option.add_item("Еще не посещали")
	visit_filter_option.add_item("Уже посещали")

	country_filter_option.clear()
	country_filter_option.add_item("Все страны")
	for country in object_list.get_countries():
		country_filter_option.add_item(country)

	search_line_edit.text = ""
	object_list.set_search_query("")
	object_list.set_filters(ObjectListPanel.FILTER_ALL, ObjectListPanel.FILTER_ALL, ObjectListPanel.FILTER_ALL)

func _refresh_collection() -> void:
	for child in collection_rows.get_children():
		collection_rows.remove_child(child)
		child.queue_free()

	var stats := collection_stats if not collection_stats.is_empty() else _calculate_collection_stats(objects)
	var countries: Array = stats.get("countries", [])
	var transport_types: Array = stats.get("transport_types", [])
	var has_rows := not countries.is_empty() or not transport_types.is_empty()
	collection_empty_state_label.visible = not has_rows
	collection_rows.visible = has_rows
	if not has_rows:
		return

	_add_achievements_group(_calculate_achievements(objects))
	_add_collection_group("Страны", countries, "country")
	_add_collection_group("Типы транспорта", transport_types, "type")

func _calculate_achievements(source_objects: Array[Dictionary]) -> Array[Dictionary]:
	if achievements_script != null and achievements_script.has_method("calculate"):
		return achievements_script.calculate(source_objects)
	return []

func _calculate_collection_stats(source_objects: Array[Dictionary]) -> Dictionary:
	if collection_stats_script != null and collection_stats_script.has_method("calculate"):
		return collection_stats_script.calculate(source_objects)

	var country_stats: Dictionary = {}
	var type_stats: Dictionary = {}
	var total_count := 0
	var visited_count := 0
	for object_data in source_objects:
		total_count += 1
		var is_visited := _is_collection_object_visited(object_data)
		if is_visited:
			visited_count += 1
		_add_collection_stat(country_stats, object_data.get("country", "Страна не указана"), object_data.get("country", "country_unknown"), is_visited)
		_add_collection_stat(type_stats, object_data.get("kind", "Тип не указан"), object_data.get("transport_type_id", "transport_type_unknown"), is_visited)

	return {
		"overall": _collection_progress("overall", "Вся коллекция", total_count, visited_count),
		"visited_count": visited_count,
		"total_count": total_count,
		"progress_percent": _collection_progress_percent(total_count, visited_count),
		"countries": _sorted_collection_stats(country_stats),
		"transport_types": _sorted_collection_stats(type_stats),
	}

func _add_collection_stat(stats: Dictionary, title_value: Variant, id_value: Variant, is_visited: bool) -> void:
	var title := str(title_value).strip_edges()
	if title.is_empty():
		title = "Не указано"
	var id := str(id_value).strip_edges()
	if id.is_empty():
		id = title
	if not stats.has(id):
		stats[id] = _collection_progress(id, title, 0, 0)

	stats[id]["total_count"] = int(stats[id].get("total_count", 0)) + 1
	if is_visited:
		stats[id]["visited_count"] = int(stats[id].get("visited_count", 0)) + 1
	stats[id]["progress_percent"] = _collection_progress_percent(
		int(stats[id].get("total_count", 0)),
		int(stats[id].get("visited_count", 0))
	)

func _collection_progress(id: String, title: String, total_count: int, visited_count: int) -> Dictionary:
	return {
		"id": id,
		"title": title,
		"total_count": total_count,
		"visited_count": visited_count,
		"progress_percent": _collection_progress_percent(total_count, visited_count),
	}

func _collection_progress_percent(total_count: int, visited_count: int) -> int:
	if total_count <= 0:
		return 0
	return int(round(float(visited_count) * 100.0 / float(total_count)))

func _sorted_collection_stats(stats: Dictionary) -> Array[Dictionary]:
	var rows: Array[Dictionary] = []
	for id in stats.keys():
		rows.append(stats[id])
	rows.sort_custom(func(left: Dictionary, right: Dictionary) -> bool:
		return str(left.get("title", "")) < str(right.get("title", ""))
	)
	return rows

func _add_collection_group(title: String, rows: Array, filter_kind: String) -> void:
	var title_label := Label.new()
	title_label.text = title
	title_label.add_theme_font_size_override("font_size", 20)
	title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	collection_rows.add_child(title_label)

	for row in rows:
		if row is Dictionary:
			_add_collection_row(row, filter_kind)

func _add_achievements_group(rows: Array[Dictionary]) -> void:
	if rows.is_empty():
		return

	var title_label := Label.new()
	title_label.text = "Достижения"
	title_label.add_theme_font_size_override("font_size", 20)
	title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	collection_rows.add_child(title_label)

	for achievement in rows:
		_add_achievement_row(achievement)

func _add_achievement_row(achievement: Dictionary) -> void:
	var unlocked := bool(achievement.get("unlocked", false))
	var status_text := str(achievement.get("status_text", "Еще не получено"))
	var title := str(achievement.get("title", "Достижение"))
	var description := str(achievement.get("description", ""))
	var progress_text := str(achievement.get("progress_text", ""))

	var row := VBoxContainer.new()
	row.add_theme_constant_override("separation", 4)
	collection_rows.add_child(row)

	var title_label := Label.new()
	title_label.text = "%s: %s" % [status_text, title]
	title_label.custom_minimum_size = Vector2(0, 36)
	title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	row.add_child(title_label)

	var detail_label := Label.new()
	detail_label.text = "%s\n%s" % [description, progress_text]
	detail_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	detail_label.modulate = Color(0.82, 0.82, 0.82, 1.0) if unlocked else Color(0.68, 0.68, 0.68, 1.0)
	row.add_child(detail_label)

func _add_collection_row(row: Dictionary, filter_kind: String) -> void:
	var title := str(row.get("title", "Не указано"))
	var total := int(row.get("total_count", row.get("total", 0)))
	var visited := int(row.get("visited_count", row.get("visited", 0)))
	var percent := float(row.get("progress_percent", 0.0 if total <= 0 else float(visited) / float(total) * 100.0))

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	collection_rows.add_child(box)

	var button := Button.new()
	button.text = "%s\n%d из %d, %d%%" % [title, visited, total, int(round(percent))]
	button.tooltip_text = "Открыть список с фильтром: %s" % title
	button.custom_minimum_size = Vector2(0, 52)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	button.pressed.connect(func() -> void: _apply_collection_filter(filter_kind, title))
	box.add_child(button)

	var progress := ProgressBar.new()
	progress.custom_minimum_size = Vector2(0, 36)
	progress.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	progress.max_value = 100.0
	progress.value = percent
	progress.tooltip_text = "Прогресс: %d%%" % int(round(percent))
	box.add_child(progress)

func _apply_collection_filter(filter_kind: String, value: String) -> void:
	var type_filter := ObjectListPanel.FILTER_ALL
	var country_filter := ObjectListPanel.FILTER_ALL
	if filter_kind == "type":
		type_filter = value
		_select_type_filter_option(value)
		_select_country_filter_option(ObjectListPanel.FILTER_ALL)
	else:
		_select_type_filter_option(ObjectListPanel.FILTER_ALL)
		country_filter = value
		_select_country_filter_option(value)

	visit_filter_option.select(0)
	search_line_edit.text = ""
	object_list.set_search_query("")
	object_list.set_filters(type_filter, ObjectListPanel.FILTER_ALL, country_filter)
	list_active_collection_filter_label.text = "Фильтр: %s\n%s" % [
		"тип транспорта" if filter_kind == "type" else "страна",
		value,
	]
	list_active_collection_filter_label.visible = true
	if selected_index >= 0:
		object_list.select_visual_object(selected_index)
	_show_section("list")

func _select_type_filter_option(value: String) -> void:
	type_filter_option.select(0)
	if value == ObjectListPanel.FILTER_ALL:
		return
	for index in type_filter_option.get_item_count():
		if type_filter_option.get_item_text(index) == value:
			type_filter_option.select(index)
			return

func _select_country_filter_option(value: String) -> void:
	country_filter_option.select(0)
	if value == ObjectListPanel.FILTER_ALL:
		return
	for index in country_filter_option.get_item_count():
		if country_filter_option.get_item_text(index) == value:
			country_filter_option.select(index)
			return

func _is_collection_object_visited(object_data: Dictionary) -> bool:
	if object_data.has("visit_status_id"):
		return SQLiteStorageAdapter.status_is_visited(str(object_data.get("visit_status_id", "")))
	return object_data.get("visited", false)

func _configure_orientation_setting() -> void:
	orientation_option.clear()
	for option in AppSettings.orientation_options():
		orientation_option.add_item(str(option.get("title", "")))
		orientation_option.set_item_metadata(orientation_option.get_item_count() - 1, option.get("id", AppSettings.ORIENTATION_SYSTEM))

	var saved_orientation: String = app_settings.load_orientation()
	_select_orientation_option(saved_orientation)
	_apply_screen_orientation(saved_orientation)

func _on_orientation_selected(index: int) -> void:
	if orientation_option_is_refreshing:
		return
	if index < 0 or index >= orientation_option.get_item_count():
		return

	var orientation_id: String = str(orientation_option.get_item_metadata(index))
	app_settings.save_orientation(orientation_id)
	_apply_screen_orientation(orientation_id)

func _select_orientation_option(orientation_id: String) -> void:
	orientation_option_is_refreshing = true
	var normalized_orientation: String = AppSettings.normalize_orientation(orientation_id)
	for index in orientation_option.get_item_count():
		if orientation_option.get_item_metadata(index) == normalized_orientation:
			orientation_option.select(index)
			break
	orientation_option_is_refreshing = false

func _apply_screen_orientation(orientation_id: String) -> void:
	if not _screen_orientation_can_change():
		return

	DisplayServer.screen_set_orientation(AppSettings.display_server_orientation(orientation_id))

func _screen_orientation_can_change() -> bool:
	return OS.has_feature("android") or OS.has_feature("ios")

func _select_object(index: int, open_card: bool) -> void:
	if index < 0 or index >= objects.size():
		return

	selected_index = index
	object_list.select_visual_object(index)
	if storage_runtime_enabled:
		_ensure_route_details(index)
	object_card.show_object(objects[index], storage_runtime_enabled)
	memory_panel.show_object(objects[index])
	object_mode_panel.show_object(objects[index])
	observer_panel.show_object(objects[index])
	ride_panel.show_object(objects[index])
	map_panel.select_object(index)
	_update_map_selection(objects[index])
	if open_card:
		_show_section("card")

func _show_section(section_name: String) -> void:
	for key in sections:
		var section: Control = sections[key]
		section.visible = key == section_name

	for key in navigation_buttons:
		var button: Button = navigation_buttons[key]
		button.button_pressed = key == section_name

	var title: String = section_titles.get(section_name, section_name)
	current_section_label.text = "Раздел: %s" % title
	_sync_content_width()
	_scroll_navigation_to_current(section_name)

func _sync_content_width() -> void:
	if content_viewport == null or content_scroll == null or sections_container == null:
		return
	var content_width: float = max(0.0, content_viewport.size.x - CONTENT_WIDTH_GUARD)
	content_scroll.scroll_horizontal = 0
	content_scroll.set_deferred("scroll_horizontal", 0)
	sections_container.custom_minimum_size.x = content_width
	for key in sections:
		var section: Control = sections[key]
		section.custom_minimum_size.x = content_width

func _scroll_navigation_to_current(section_name: String) -> void:
	if navigation_scroll == null or not navigation_buttons.has(section_name):
		return
	var button: Button = navigation_buttons[section_name]
	if not button.visible:
		return
	var button_left := int(button.position.x)
	var button_right := int(button.position.x + button.size.x)
	var viewport_width := int(navigation_scroll.size.x)
	var target := navigation_scroll.scroll_horizontal
	if button_left < target:
		target = button_left
	elif button_right > target + viewport_width:
		target = button_right - viewport_width
	navigation_scroll.set_deferred("scroll_horizontal", max(0, target))

func _update_map_selection(object_data: Dictionary) -> void:
	selected_object_label.text = "Выбрано: %s, %s" % [
		object_data.get("name", "без названия"),
		object_data.get("region", "регион не указан"),
	]

func _add_journal_entry(object_data: Dictionary, status_id: String) -> void:
	var status: String = "статус: %s" % SQLiteStorageAdapter.status_title(status_id)
	journal_entries.push_front("%s: %s" % [object_data.get("name", "Объект"), status])
	journal_entries = journal_entries.slice(0, 6)
	journal_label.text = "[b]Журнал[/b]\n%s" % "\n".join(journal_entries)

func _add_photo_journal_entry(object_data: Dictionary, caption: String) -> void:
	journal_entries.push_front("%s: добавлена запись фото (%s)" % [object_data.get("name", "Объект"), caption])
	journal_entries = journal_entries.slice(0, 6)
	journal_label.text = "[b]Журнал[/b]\n%s" % "\n".join(journal_entries)

func _add_visit_journal_entry(object_data: Dictionary, title: String, visited_on: String) -> void:
	journal_entries.push_front("%s: посещение %s (%s)" % [object_data.get("name", "Объект"), title, visited_on])
	journal_entries = journal_entries.slice(0, 6)
	journal_label.text = "[b]Журнал[/b]\n%s" % "\n".join(journal_entries)

func _attach_photo_lists(source_objects: Array[Dictionary]) -> Array[Dictionary]:
	var objects_with_photos: Array[Dictionary] = []
	for object_data in source_objects:
		var enriched_object := object_data.duplicate(true)
		var object_id: String = enriched_object.get("id", "")
		var photos := storage.list_object_photos(object_id)
		var visits := storage.list_visits(object_id)
		var tickets := storage.list_tickets(object_id)
		enriched_object["photos"] = photos
		enriched_object["photo_count"] = photos.size()
		enriched_object["visits"] = visits
		enriched_object["visit_count"] = visits.size()
		enriched_object["tickets"] = tickets
		enriched_object["ticket_count"] = tickets.size()
		objects_with_photos.append(enriched_object)
	return objects_with_photos

func _ensure_route_details(index: int) -> void:
	if index < 0 or index >= objects.size():
		return
	if objects[index].get("route_details_loaded", false):
		return

	var enriched_object := objects[index].duplicate(true)
	var object_id: String = enriched_object.get("id", "")
	var media_assets := storage.list_media_assets(object_id)
	var videos: Array[Dictionary] = []
	for media_asset in media_assets:
		if media_asset is Dictionary and media_asset.get("kind", "") == "video":
			videos.append(media_asset)

	var stations := storage.list_object_stations(object_id)
	var directions := storage.list_route_directions(object_id)
	var route_segments_by_direction := {}
	for direction in directions:
		if direction is Dictionary:
			var direction_id := str(direction.get("id", ""))
			if not direction_id.is_empty():
				route_segments_by_direction[direction_id] = storage.list_route_segments(direction_id)

	enriched_object["videos"] = videos
	enriched_object["video_count"] = videos.size()
	enriched_object["stations"] = stations
	enriched_object["route_directions"] = directions
	enriched_object["route_segments_by_direction"] = route_segments_by_direction
	enriched_object["route_details_loaded"] = true
	objects[index] = enriched_object
