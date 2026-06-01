extends Control
class_name MainScreen

const AppSettings := preload("res://scripts/app_settings.gd")
const MapPanelScript := preload("res://scripts/map_panel.gd")
const ObjectModePanelScript := preload("res://scripts/object_mode_panel.gd")
const RidePanelScript := preload("res://scripts/ride_panel.gd")
const COLLECTION_STATS_SCRIPT_PATH := "res://scripts/collection_stats.gd"
const ACHIEVEMENTS_SCRIPT_PATH := "res://scripts/achievements.gd"
const CONTENT_WIDTH_GUARD := 2.0
const ATLAS_CONTROL_BG := Color(0.96, 0.90, 0.72, 0.94)
const ATLAS_CONTROL_BORDER := Color("#3b2a18")
const ATLAS_CONTROL_INK := Color("#27321f")
const ATLAS_CONTROL_ACCENT := Color("#31544d")
const ATLAS_CONTROL_SHADOW := Color(0.12, 0.08, 0.03, 0.42)
const ATLAS_LIST_BACKDROP := preload("res://assets/map/germany_styled.png")
const ATLAS_ICON_PARCHMENT := Color("#f2e5bd")
const ATLAS_ICON_PARCHMENT_DARK := Color("#d7c06f")
const ATLAS_ICON_GREEN := Color("#8fb18a")
const ATLAS_ICON_BLUE := Color("#c7d6da")
const ATLAS_ICON_RED := Color("#c46335")
const MAP_LIST_ICON_SIZE := Vector2i(40, 40)
const MAP_LIST_TOGGLE_SIZE := Vector2(60.0, 60.0)
const MAP_LIST_TOGGLE_MARGIN := Vector2(14.0, 14.0)
const MAP_RIDE_BUTTON_SIZE := Vector2(152.0, 56.0)
const MAP_RIDE_BUTTON_MARGIN := Vector2(14.0, 84.0)
const LIST_MAP_RETURN_SIZE := Vector2(132.0, 52.0)
const LIST_LEDGER_MAX_WIDTH := 920.0
const LIST_LEDGER_MIN_WIDTH := 320.0

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
@onready var list_content: VBoxContainer = $Отступы/Оболочка/Содержимое/ContentViewport/ContentScroll/Секции/ListSection/ListSafeArea/ListContent
@onready var list_safe_area: MarginContainer = %ListSafeArea
@onready var list_title_label: Label = $Отступы/Оболочка/Содержимое/ContentViewport/ContentScroll/Секции/ListSection/ListSafeArea/ListContent/СписокЗаголовок
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
@onready var root_margins: MarginContainer = $Отступы
@onready var app_title_label: Label = $Отступы/Оболочка/Заголовок
@onready var app_subtitle_label: Label = $Отступы/Оболочка/Подзаголовок
@onready var navigation_area: Control = $Отступы/Оболочка/НавигацияОбласть
@onready var navigation_scroll: ScrollContainer = %НавигацияПрокрутка
@onready var current_section_label: Label = %CurrentSectionLabel
@onready var map_section: VBoxContainer = %MapSection
@onready var map_title_label: Label = $Отступы/Оболочка/Содержимое/ContentViewport/ContentScroll/Секции/MapSection/КартаЗаголовок
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
@onready var content_panel: PanelContainer = $Отступы/Оболочка/Содержимое
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
var map_list_toggle_button: Button = null
var map_ride_button: Button = null
var list_map_return_button: Button = null
var list_backdrop: TextureRect = null
var list_ledger_header: HBoxContainer = null
var list_ledger_title_stack: VBoxContainer = null
var list_ledger_subtitle_label: Label = null
var active_section_name := ""
var map_return_state: Dictionary = {}
var ride_return_section_name := "card"

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
	ride_button.pressed.connect(func() -> void: _open_ride_from_context(active_section_name))
	collection_button.pressed.connect(func() -> void: _show_section("collection"))
	journal_button.pressed.connect(func() -> void: _show_section("journal"))
	settings_button.pressed.connect(func() -> void: _show_section("settings"))
	orientation_option.item_selected.connect(_on_orientation_selected)
	search_line_edit.text_changed.connect(_on_search_changed)
	type_filter_option.item_selected.connect(_on_filter_changed)
	visit_filter_option.item_selected.connect(_on_filter_changed)
	country_filter_option.item_selected.connect(_on_filter_changed)
	_apply_map_list_button_icons()
	_apply_atlas_list_screen_style()
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
	object_mode_panel.ride_requested.connect(func() -> void: _open_ride_from_context("object_mode"))
	observer_panel.back_requested.connect(func() -> void: _show_section("card"))
	ride_panel.back_requested.connect(_on_ride_back_requested)
	map_panel.set_objects(objects)
	map_panel.object_selected.connect(_on_map_object_selected)
	content_viewport.resized.connect(_sync_content_width)
	_create_map_list_toggle()
	_create_map_ride_button()
	_create_list_backdrop()
	_create_list_map_return_button()
	_create_list_ledger_header()

	_configure_orientation_setting()
	_configure_list_filters()
	_sync_content_width()
	_refresh_collection()
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
	storage_runtime_enabled = false

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
	_update_map_ride_button()
	if open_card:
		_show_section("card")

func _open_ride_from_context(return_section_name: String) -> void:
	if return_section_name.is_empty() or return_section_name == "ride":
		return_section_name = "card"
	if return_section_name == "map":
		_capture_map_return_state()
	ride_return_section_name = return_section_name
	ride_panel.set_back_button_text(_ride_back_button_text(return_section_name))
	_show_section("ride")

func _on_ride_back_requested() -> void:
	_show_section(ride_return_section_name)

func _show_section(section_name: String) -> void:
	if active_section_name == "map" and section_name != "map":
		_capture_map_return_state()

	for key in sections:
		var section: Control = sections[key]
		section.visible = key == section_name

	for key in navigation_buttons:
		var button: Button = navigation_buttons[key]
		button.button_pressed = key == section_name

	active_section_name = section_name
	var title: String = section_titles.get(section_name, section_name)
	current_section_label.text = "Раздел: %s" % title
	_apply_map_focus_chrome(section_name == "map")
	_sync_content_width()
	_sync_content_width_after_layout()
	_scroll_navigation_to_current(section_name)
	if section_name == "map":
		_restore_map_return_state()
		call_deferred("_restore_map_return_state_after_layout")

func _capture_map_return_state() -> void:
	if map_panel == null:
		return
	map_return_state = map_panel.get_navigation_state()

func _restore_map_return_state() -> void:
	if map_panel == null or map_return_state.is_empty():
		return
	map_panel.restore_navigation_state(map_return_state)

func _restore_map_return_state_after_layout() -> void:
	if not is_inside_tree():
		return
	await get_tree().process_frame
	_restore_map_return_state()

func _create_map_list_toggle() -> void:
	map_list_toggle_button = Button.new()
	map_list_toggle_button.name = "MapListToggle"
	map_list_toggle_button.text = ""
	map_list_toggle_button.icon = _make_map_list_icon("list")
	map_list_toggle_button.expand_icon = false
	map_list_toggle_button.tooltip_text = "Открыть список объектов"
	map_list_toggle_button.custom_minimum_size = MAP_LIST_TOGGLE_SIZE
	map_list_toggle_button.size = MAP_LIST_TOGGLE_SIZE
	map_list_toggle_button.anchor_left = 0.0
	map_list_toggle_button.anchor_right = 0.0
	map_list_toggle_button.offset_left = MAP_LIST_TOGGLE_MARGIN.x
	map_list_toggle_button.offset_right = MAP_LIST_TOGGLE_MARGIN.x + MAP_LIST_TOGGLE_SIZE.x
	map_list_toggle_button.offset_top = MAP_LIST_TOGGLE_MARGIN.y
	map_list_toggle_button.offset_bottom = MAP_LIST_TOGGLE_MARGIN.y + MAP_LIST_TOGGLE_SIZE.y
	map_list_toggle_button.z_index = 90
	_apply_atlas_toggle_button_style(map_list_toggle_button, true)
	map_list_toggle_button.pressed.connect(func() -> void: _show_section("list"))
	add_child(map_list_toggle_button)

func _create_map_ride_button() -> void:
	map_ride_button = Button.new()
	map_ride_button.name = "MapRideButton"
	map_ride_button.text = "Поездка"
	map_ride_button.tooltip_text = "Открыть поездку для выбранного объекта"
	map_ride_button.custom_minimum_size = MAP_RIDE_BUTTON_SIZE
	map_ride_button.size = MAP_RIDE_BUTTON_SIZE
	map_ride_button.anchor_left = 0.0
	map_ride_button.anchor_right = 0.0
	map_ride_button.offset_left = MAP_RIDE_BUTTON_MARGIN.x
	map_ride_button.offset_right = MAP_RIDE_BUTTON_MARGIN.x + MAP_RIDE_BUTTON_SIZE.x
	map_ride_button.offset_top = MAP_RIDE_BUTTON_MARGIN.y
	map_ride_button.offset_bottom = MAP_RIDE_BUTTON_MARGIN.y + MAP_RIDE_BUTTON_SIZE.y
	map_ride_button.z_index = 90
	_apply_atlas_toggle_button_style(map_ride_button, false)
	map_ride_button.pressed.connect(func() -> void: _open_ride_from_context("map"))
	add_child(map_ride_button)
	_update_map_ride_button()

func _create_list_map_return_button() -> void:
	list_map_return_button = Button.new()
	list_map_return_button.name = "ListMapReturn"
	list_map_return_button.text = "Карта"
	list_map_return_button.icon = _make_map_list_icon("map")
	list_map_return_button.expand_icon = false
	list_map_return_button.tooltip_text = "Вернуться к карте объектов"
	list_map_return_button.custom_minimum_size = LIST_MAP_RETURN_SIZE
	list_map_return_button.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_apply_atlas_toggle_button_style(list_map_return_button, false)
	list_map_return_button.pressed.connect(func() -> void: _show_section("map"))

func _create_list_backdrop() -> void:
	list_backdrop = TextureRect.new()
	list_backdrop.name = "ListAtlasBackdrop"
	list_backdrop.texture = ATLAS_LIST_BACKDROP
	list_backdrop.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	list_backdrop.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	list_backdrop.set_anchors_preset(Control.PRESET_FULL_RECT)
	list_backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	list_backdrop.modulate = Color(0.86, 0.77, 0.56, 0.42)
	list_backdrop.visible = false
	list_backdrop.z_index = -20
	add_child(list_backdrop)
	move_child(list_backdrop, 0)

func _create_list_ledger_header() -> void:
	if list_content == null or list_title_label == null or list_map_return_button == null:
		return

	list_ledger_header = HBoxContainer.new()
	list_ledger_header.name = "ListLedgerHeader"
	list_ledger_header.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list_ledger_header.alignment = BoxContainer.ALIGNMENT_BEGIN
	list_ledger_header.add_theme_constant_override("separation", 10)

	list_ledger_title_stack = VBoxContainer.new()
	list_ledger_title_stack.name = "ListLedgerTitleStack"
	list_ledger_title_stack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list_ledger_title_stack.add_theme_constant_override("separation", 1)

	list_ledger_subtitle_label = Label.new()
	list_ledger_subtitle_label.name = "ListLedgerSubtitle"
	list_ledger_subtitle_label.text = "Реестр маршрутов, станций и семейных отметок"
	list_ledger_subtitle_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	list_ledger_subtitle_label.add_theme_color_override("font_color", Color("#6e5431"))
	list_ledger_subtitle_label.add_theme_font_size_override("font_size", 13)

	list_content.add_child(list_ledger_header)
	list_content.move_child(list_ledger_header, 0)
	list_ledger_header.add_child(list_map_return_button)
	list_ledger_header.add_child(list_ledger_title_stack)

	list_title_label.get_parent().remove_child(list_title_label)
	list_ledger_title_stack.add_child(list_title_label)
	list_ledger_title_stack.add_child(list_ledger_subtitle_label)

func _update_map_ride_button() -> void:
	if map_ride_button == null:
		return
	map_ride_button.visible = active_section_name == "map" and selected_index >= 0
	if selected_index < 0 or selected_index >= objects.size():
		map_ride_button.disabled = true
		map_ride_button.tooltip_text = "Выберите объект на карте"
		return
	var object_data := objects[selected_index]
	var has_route := _object_has_playable_route(object_data)
	map_ride_button.disabled = false
	map_ride_button.tooltip_text = "Открыть поездку" if has_route else "Открыть пустое состояние поездки: маршрут пока не добавлен"

func _object_has_playable_route(object_data: Dictionary) -> bool:
	if not object_data.has("route_directions") or not (object_data.get("route_directions") is Array):
		return false
	var directions: Array = object_data.get("route_directions")
	var route_segments_by_direction: Dictionary = object_data.get("route_segments_by_direction", {})
	for direction in directions:
		if not (direction is Dictionary):
			continue
		var direction_id := str(direction.get("id", ""))
		if route_segments_by_direction.has(direction_id) and route_segments_by_direction[direction_id] is Array:
			var segments: Array = route_segments_by_direction[direction_id]
			if not segments.is_empty():
				return true
	return false

func _ride_back_button_text(return_section_name: String) -> String:
	if return_section_name == "map":
		return "К карте"
	if return_section_name == "object_mode":
		return "К объекту"
	return "К карточке"

func _apply_map_list_button_icons() -> void:
	map_button.icon = _make_map_list_icon("map")
	map_button.expand_icon = false
	map_button.tooltip_text = "Открыть карту объектов"
	list_button.icon = _make_map_list_icon("list")
	list_button.expand_icon = false
	list_button.tooltip_text = "Открыть компактный список объектов"

func _apply_atlas_toggle_button_style(button: Button, icon_only: bool) -> void:
	button.add_theme_color_override("icon_normal_color", Color.WHITE)
	button.add_theme_color_override("icon_hover_color", Color.WHITE)
	button.add_theme_color_override("icon_pressed_color", Color.WHITE)
	button.add_theme_color_override("font_color", ATLAS_CONTROL_INK)
	button.add_theme_color_override("font_hover_color", Color("#11170e"))
	button.add_theme_color_override("font_pressed_color", Color("#11170e"))
	button.add_theme_font_size_override("font_size", 18)
	var margin := 10.0 if icon_only else 8.0
	button.add_theme_stylebox_override("normal", _atlas_toggle_style(ATLAS_CONTROL_BG, margin))
	button.add_theme_stylebox_override("hover", _atlas_toggle_style(Color(0.98, 0.92, 0.76, 0.98), margin))
	button.add_theme_stylebox_override("pressed", _atlas_toggle_style(Color(0.86, 0.76, 0.55, 0.98), margin))

func _atlas_toggle_style(bg_color: Color, content_margin: float) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = bg_color
	style.border_color = ATLAS_CONTROL_BORDER
	style.shadow_color = ATLAS_CONTROL_SHADOW
	style.shadow_size = 5
	style.set_border_width_all(2)
	style.set_corner_radius_all(6)
	style.content_margin_left = content_margin
	style.content_margin_top = content_margin
	style.content_margin_right = content_margin
	style.content_margin_bottom = content_margin
	return style

func _apply_atlas_list_screen_style() -> void:
	map_title_label.add_theme_color_override("font_color", ATLAS_CONTROL_INK)
	if list_safe_area != null:
		list_safe_area.add_theme_constant_override("margin_left", 14)
		list_safe_area.add_theme_constant_override("margin_top", 14)
		list_safe_area.add_theme_constant_override("margin_right", 14)
		list_safe_area.add_theme_constant_override("margin_bottom", 14)
	if list_title_label != null:
		list_title_label.add_theme_color_override("font_color", ATLAS_CONTROL_INK)
		list_title_label.add_theme_font_size_override("font_size", 22)
		list_title_label.add_theme_stylebox_override("normal", StyleBoxEmpty.new())
		list_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT

	list_active_collection_filter_label.add_theme_color_override("font_color", Color("#6e5431"))
	list_active_collection_filter_label.add_theme_font_size_override("font_size", 14)
	list_active_collection_filter_label.add_theme_stylebox_override("normal", _atlas_list_meta_style())
	_apply_atlas_search_style(search_line_edit)
	for option in [country_filter_option, type_filter_option, visit_filter_option]:
		_apply_atlas_filter_style(option)

func _apply_atlas_search_style(line_edit: LineEdit) -> void:
	line_edit.add_theme_color_override("font_color", ATLAS_CONTROL_INK)
	line_edit.add_theme_color_override("font_placeholder_color", Color(0.39, 0.30, 0.18, 0.76))
	line_edit.add_theme_font_size_override("font_size", 16)
	line_edit.add_theme_stylebox_override("normal", _atlas_field_style(ATLAS_CONTROL_BG))
	line_edit.add_theme_stylebox_override("focus", _atlas_field_style(Color(0.99, 0.94, 0.78, 0.98), true))
	line_edit.add_theme_stylebox_override("read_only", _atlas_field_style(Color(0.90, 0.84, 0.66, 0.90)))

func _apply_atlas_filter_style(option: OptionButton) -> void:
	option.add_theme_color_override("font_color", ATLAS_CONTROL_INK)
	option.add_theme_color_override("font_hover_color", Color("#11170e"))
	option.add_theme_color_override("font_pressed_color", Color("#11170e"))
	option.add_theme_font_size_override("font_size", 15)
	option.add_theme_stylebox_override("normal", _atlas_field_style(ATLAS_CONTROL_BG))
	option.add_theme_stylebox_override("hover", _atlas_field_style(Color(0.98, 0.92, 0.76, 0.98), true))
	option.add_theme_stylebox_override("pressed", _atlas_field_style(Color(0.86, 0.76, 0.55, 0.98), true))
	option.add_theme_stylebox_override("focus", _atlas_field_style(Color(0.98, 0.92, 0.76, 0.98), true))

func _atlas_field_style(bg_color: Color, highlighted: bool = false) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = bg_color
	style.border_color = ATLAS_CONTROL_BORDER if highlighted else Color(0.23, 0.16, 0.09, 0.46)
	style.shadow_color = Color(0.12, 0.08, 0.03, 0.18)
	style.shadow_size = 2
	style.content_margin_left = 12.0
	style.content_margin_top = 8.0
	style.content_margin_right = 12.0
	style.content_margin_bottom = 8.0
	style.set_border_width_all(2 if highlighted else 1)
	style.set_corner_radius_all(5)
	return style

func _atlas_list_header_style() -> StyleBoxFlat:
	var style := _atlas_field_style(Color(0.86, 0.76, 0.55, 0.96), true)
	style.content_margin_top = 6.0
	style.content_margin_bottom = 6.0
	return style

func _atlas_list_meta_style() -> StyleBoxFlat:
	var style := _atlas_field_style(Color(0.99, 0.94, 0.78, 0.72))
	style.content_margin_top = 6.0
	style.content_margin_bottom = 6.0
	return style

func _make_map_list_icon(kind: String) -> Texture2D:
	var image := Image.create(MAP_LIST_ICON_SIZE.x, MAP_LIST_ICON_SIZE.y, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	if kind == "map":
		_draw_map_icon(image)
	else:
		_draw_list_icon(image)
	return ImageTexture.create_from_image(image)

func _draw_map_icon(image: Image) -> void:
	_fill_icon_rect(image, Rect2i(4, 8, 9, 24), ATLAS_ICON_PARCHMENT_DARK)
	_fill_icon_rect(image, Rect2i(14, 6, 10, 24), ATLAS_ICON_GREEN)
	_fill_icon_rect(image, Rect2i(25, 9, 9, 24), ATLAS_ICON_BLUE)
	_draw_icon_line(image, Vector2i(13, 8), Vector2i(13, 32), ATLAS_CONTROL_BORDER)
	_draw_icon_line(image, Vector2i(24, 6), Vector2i(24, 31), ATLAS_CONTROL_BORDER)
	_draw_icon_line(image, Vector2i(7, 28), Vector2i(16, 20), ATLAS_CONTROL_ACCENT)
	_draw_icon_line(image, Vector2i(16, 20), Vector2i(28, 24), ATLAS_CONTROL_ACCENT)
	_draw_icon_pin(image, Vector2i(20, 16), Color("#7f3f2a"))
	_draw_compass_arrow(image, Vector2i(30, 12))

func _draw_list_icon(image: Image) -> void:
	_draw_folded_map_badge(image, Rect2i(4, 8, 17, 22))
	_fill_icon_rect(image, Rect2i(18, 6, 17, 27), ATLAS_ICON_PARCHMENT_DARK)
	_fill_icon_rect(image, Rect2i(21, 5, 15, 27), ATLAS_ICON_PARCHMENT)
	_draw_icon_outline_rect(image, Rect2i(21, 5, 15, 27), ATLAS_CONTROL_BORDER)
	_draw_icon_line(image, Vector2i(23, 10), Vector2i(34, 10), Color("#b68b4a"))
	for row in range(3):
		var y := 15 + row * 6
		_draw_object_row_icon(image, Vector2i(25, y), row)
		_fill_icon_rect(image, Rect2i(29, y - 1, 5, 2), ATLAS_CONTROL_INK)
		_fill_icon_rect(image, Rect2i(29, y + 2, 4, 1), Color("#6e5431"))
	_draw_return_chevron(image, Vector2i(18, 32), false)

func _draw_folded_map_badge(image: Image, rect: Rect2i) -> void:
	_fill_icon_rect(image, rect, ATLAS_ICON_PARCHMENT_DARK)
	_fill_icon_rect(image, Rect2i(rect.position.x + 1, rect.position.y - 1, 6, rect.size.y), ATLAS_ICON_GREEN)
	_fill_icon_rect(image, Rect2i(rect.position.x + 7, rect.position.y, 5, rect.size.y - 2), ATLAS_ICON_PARCHMENT)
	_fill_icon_rect(image, Rect2i(rect.position.x + 12, rect.position.y - 1, 6, rect.size.y), ATLAS_ICON_BLUE)
	_draw_icon_line(image, rect.position + Vector2i(7, 0), rect.position + Vector2i(7, rect.size.y - 1), ATLAS_CONTROL_BORDER)
	_draw_icon_line(image, rect.position + Vector2i(12, -1), rect.position + Vector2i(12, rect.size.y - 2), ATLAS_CONTROL_BORDER)
	_draw_icon_line(image, rect.position + Vector2i(2, rect.size.y - 5), rect.position + Vector2i(8, rect.size.y - 11), ATLAS_CONTROL_ACCENT)
	_draw_icon_line(image, rect.position + Vector2i(8, rect.size.y - 11), rect.position + Vector2i(15, rect.size.y - 7), ATLAS_CONTROL_ACCENT)
	_draw_icon_pin(image, rect.position + Vector2i(10, 8), Color("#7f3f2a"))

func _draw_object_row_icon(image: Image, center: Vector2i, row: int) -> void:
	var color := ATLAS_CONTROL_ACCENT
	if row == 1:
		color = Color("#7f3f2a")
	elif row == 2:
		color = Color("#5e6c88")
	_fill_icon_rect(image, Rect2i(center.x - 2, center.y - 2, 5, 5), color)
	_fill_icon_rect(image, Rect2i(center.x - 1, center.y - 1, 3, 3), ATLAS_ICON_PARCHMENT)

func _draw_compass_arrow(image: Image, center: Vector2i) -> void:
	_draw_icon_line(image, center + Vector2i(-4, 4), center + Vector2i(3, -4), ATLAS_CONTROL_BORDER)
	_draw_icon_line(image, center + Vector2i(3, -4), center + Vector2i(2, 2), ATLAS_CONTROL_BORDER)
	_fill_icon_rect(image, Rect2i(center.x + 1, center.y - 6, 3, 3), ATLAS_ICON_RED)

func _draw_return_chevron(image: Image, center: Vector2i, points_left: bool) -> void:
	var direction := -1 if points_left else 1
	_draw_icon_line(image, center + Vector2i(-direction * 4, -4), center + Vector2i(direction * 3, 0), ATLAS_CONTROL_BORDER)
	_draw_icon_line(image, center + Vector2i(direction * 3, 0), center + Vector2i(-direction * 4, 4), ATLAS_CONTROL_BORDER)

func _draw_icon_outline_rect(image: Image, rect: Rect2i, color: Color) -> void:
	_draw_icon_line(image, rect.position, rect.position + Vector2i(rect.size.x - 1, 0), color)
	_draw_icon_line(image, rect.position + Vector2i(rect.size.x - 1, 0), rect.position + rect.size - Vector2i(1, 1), color)
	_draw_icon_line(image, rect.position + rect.size - Vector2i(1, 1), rect.position + Vector2i(0, rect.size.y - 1), color)
	_draw_icon_line(image, rect.position + Vector2i(0, rect.size.y - 1), rect.position, color)

func _draw_icon_pin(image: Image, center: Vector2i, color: Color) -> void:
	_fill_icon_rect(image, Rect2i(center.x - 2, center.y - 2, 5, 5), color)
	_fill_icon_rect(image, Rect2i(center.x - 1, center.y + 3, 3, 2), color)
	_fill_icon_rect(image, Rect2i(center.x, center.y + 5, 1, 2), color)
	_fill_icon_rect(image, Rect2i(center.x - 1, center.y - 1, 3, 3), Color("#f2e5bd"))

func _fill_icon_rect(image: Image, rect: Rect2i, color: Color) -> void:
	for y in range(rect.position.y, rect.position.y + rect.size.y):
		for x in range(rect.position.x, rect.position.x + rect.size.x):
			if x >= 0 and x < image.get_width() and y >= 0 and y < image.get_height():
				image.set_pixel(x, y, color)

func _draw_icon_line(image: Image, from_point: Vector2i, to_point: Vector2i, color: Color) -> void:
	var delta := to_point - from_point
	var steps: int = maxi(abs(delta.x), abs(delta.y))
	if steps <= 0:
		image.set_pixel(from_point.x, from_point.y, color)
		return
	for step in range(steps + 1):
		var t := float(step) / float(steps)
		var point := Vector2i(roundi(lerpf(from_point.x, to_point.x, t)), roundi(lerpf(from_point.y, to_point.y, t)))
		_fill_icon_rect(image, Rect2i(point.x, point.y, 2, 2), color)

func _apply_map_focus_chrome(is_map: bool) -> void:
	var is_list := active_section_name == "list"
	var hide_primary_chrome := is_map or is_list
	app_title_label.visible = not hide_primary_chrome
	app_subtitle_label.visible = not hide_primary_chrome
	navigation_area.visible = not hide_primary_chrome
	current_section_label.visible = false
	map_title_label.visible = false
	selected_object_label.visible = false
	if map_list_toggle_button != null:
		map_list_toggle_button.visible = is_map
	if list_backdrop != null:
		list_backdrop.visible = is_list
	_update_map_ride_button()
	if list_map_return_button != null:
		list_map_return_button.visible = is_list

	var margin := 0 if hide_primary_chrome else 12
	root_margins.add_theme_constant_override("margin_left", margin)
	root_margins.add_theme_constant_override("margin_top", margin)
	root_margins.add_theme_constant_override("margin_right", margin)
	root_margins.add_theme_constant_override("margin_bottom", margin)
	map_section.add_theme_constant_override("separation", 0 if is_map else 10)

	var panel_style := StyleBoxFlat.new()
	if is_map:
		panel_style.bg_color = Color(1.0, 1.0, 1.0, 0.0)
		panel_style.border_color = Color(1.0, 1.0, 1.0, 0.0)
	elif is_list:
		panel_style.bg_color = Color(0.92, 0.82, 0.58, 0.66)
		panel_style.border_color = Color(0.23, 0.16, 0.09, 0.0)
	else:
		panel_style.bg_color = Color("#f7f3e7")
		panel_style.border_color = Color("#6f7d67")
	panel_style.set_border_width_all(0 if hide_primary_chrome else 2)
	panel_style.set_corner_radius_all(0 if hide_primary_chrome else 8)
	content_panel.add_theme_stylebox_override("panel", panel_style)

func _sync_content_width() -> void:
	if content_viewport == null or content_scroll == null or sections_container == null:
		return
	var content_width: float = max(0.0, content_viewport.size.x - CONTENT_WIDTH_GUARD)
	_reset_content_horizontal_scroll()
	sections_container.custom_minimum_size.x = content_width
	for key in sections:
		var section: Control = sections[key]
		section.custom_minimum_size.x = content_width
	_sync_list_ledger_width(content_width)

func _sync_list_ledger_width(content_width: float) -> void:
	if list_safe_area == null:
		return
	var ledger_width: float = min(max(LIST_LEDGER_MIN_WIDTH, content_width), LIST_LEDGER_MAX_WIDTH)
	list_safe_area.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	list_safe_area.custom_minimum_size.x = ledger_width
	if list_content != null:
		list_content.custom_minimum_size.x = max(0.0, ledger_width - 28.0)

func _sync_content_width_after_layout() -> void:
	call_deferred("_sync_content_width")
	call_deferred("_reset_content_horizontal_scroll")
	if not is_inside_tree():
		return
	await get_tree().process_frame
	_sync_content_width()
	_reset_content_horizontal_scroll()
	await get_tree().process_frame
	_reset_content_horizontal_scroll()

func _reset_content_horizontal_scroll() -> void:
	if content_scroll == null:
		return
	if content_viewport != null:
		content_viewport.position.x = 0.0
		content_viewport.set_deferred("position", Vector2(0.0, content_viewport.position.y))
	content_scroll.position.x = 0.0
	content_scroll.set_deferred("position", Vector2(0.0, content_scroll.position.y))
	content_scroll.scroll_horizontal = 0
	content_scroll.set_deferred("scroll_horizontal", 0)
	if sections_container != null:
		sections_container.position.x = 0.0
		sections_container.set_deferred("position", Vector2(0.0, sections_container.position.y))
	for key in sections:
		var section: Control = sections[key]
		section.position.x = 0.0
		section.set_deferred("position", Vector2(0.0, section.position.y))

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
