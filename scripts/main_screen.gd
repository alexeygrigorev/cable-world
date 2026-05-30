extends Control
class_name MainScreen

@onready var object_list: ObjectListPanel = %ObjectList
@onready var object_card: ObjectCardPanel = %ObjectCard
@onready var type_filter_option: OptionButton = %TypeFilterOption
@onready var visit_filter_option: OptionButton = %VisitFilterOption
@onready var list_empty_state_label: Label = %ListEmptyStateLabel
@onready var journal_label: RichTextLabel = %JournalLabel
@onready var selected_object_label: Label = %SelectedObjectLabel
@onready var map_button: Button = %MapButton
@onready var list_button: Button = %ListButton
@onready var card_button: Button = %CardButton
@onready var journal_button: Button = %JournalButton
@onready var map_section: VBoxContainer = %MapSection
@onready var list_section: VBoxContainer = %ListSection
@onready var card_section: VBoxContainer = %CardSection
@onready var journal_section: VBoxContainer = %JournalSection

var objects: Array[Dictionary] = []
var journal_entries: Array[String] = []
var selected_index: int = -1
var sections: Dictionary = {}
var navigation_buttons: Dictionary = {}
var storage: SQLiteStorageAdapter = SQLiteStorageAdapter.new()
var storage_runtime_enabled: bool = false

func _ready() -> void:
	objects = _load_objects_from_local_source()
	sections = {
		"map": map_section,
		"list": list_section,
		"card": card_section,
		"journal": journal_section,
	}
	navigation_buttons = {
		"map": map_button,
		"list": list_button,
		"card": card_button,
		"journal": journal_button,
	}

	map_button.pressed.connect(func() -> void: _show_section("map"))
	list_button.pressed.connect(func() -> void: _show_section("list"))
	card_button.pressed.connect(func() -> void: _show_section("card"))
	journal_button.pressed.connect(func() -> void: _show_section("journal"))
	type_filter_option.item_selected.connect(_on_filter_changed)
	visit_filter_option.item_selected.connect(_on_filter_changed)
	object_list.set_empty_state_label(list_empty_state_label)
	object_list.set_objects(objects)
	object_list.object_selected.connect(_on_object_selected)
	object_card.status_changed.connect(_on_status_changed)

	_configure_list_filters()
	if not objects.is_empty():
		_select_object(0, false)
	_show_section("map")

func _load_objects_from_local_source() -> Array[Dictionary]:
	var open_result := storage.open()
	if open_result == OK:
		var migration_result := storage.migrate()
		var seed_result := storage.seed_demo_objects() if migration_result == OK else migration_result
		if seed_result == OK:
			var stored_objects := storage.list_objects()
			if not stored_objects.is_empty():
				storage_runtime_enabled = true
				return stored_objects
		push_warning("SQLite storage fallback: %s" % storage.last_error)
		storage.close()
	else:
		push_warning("SQLite storage unavailable: %s" % storage.last_error)

	storage_runtime_enabled = false
	return DemoCatalog.get_objects()

func _on_object_selected(index: int) -> void:
	_select_object(index, true)

func _on_filter_changed(_item_index: int) -> void:
	var type_filter := ObjectListPanel.FILTER_ALL
	if type_filter_option.selected > 0:
		type_filter = type_filter_option.get_item_text(type_filter_option.selected)

	var visit_filter := ObjectListPanel.FILTER_ALL
	if visit_filter_option.selected == 1:
		visit_filter = ObjectListPanel.FILTER_NOT_VISITED
	elif visit_filter_option.selected == 2:
		visit_filter = ObjectListPanel.FILTER_VISITED

	object_list.set_filters(type_filter, visit_filter)
	if selected_index >= 0:
		object_list.select_visual_object(selected_index)

func _on_status_changed(object_id: String, status_id: String) -> void:
	var normalized_status := SQLiteStorageAdapter.normalized_status_id(status_id)
	for index in objects.size():
		if objects[index].get("id", "") == object_id:
			if storage_runtime_enabled:
				var update_result := storage.update_object_status(object_id, normalized_status)
				if update_result != OK:
					push_warning("SQLite status update failed: %s" % storage.last_error)
			var visited := SQLiteStorageAdapter.status_is_visited(normalized_status)
			objects[index]["visited"] = visited
			objects[index]["visit_status_id"] = normalized_status
			object_list.refresh()
			_select_object(index, false)
			_add_journal_entry(objects[index], normalized_status)
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
	object_list.set_filters(ObjectListPanel.FILTER_ALL, ObjectListPanel.FILTER_ALL)

func _select_object(index: int, open_card: bool) -> void:
	if index < 0 or index >= objects.size():
		return

	selected_index = index
	object_list.select_visual_object(index)
	object_card.show_object(objects[index])
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

func _update_map_selection(object_data: Dictionary) -> void:
	var coordinates: Vector2 = object_data.get("coordinates", Vector2.ZERO)
	selected_object_label.text = "Выбранный объект: %s, %s (%.4f, %.4f)" % [
		object_data.get("name", "без названия"),
		object_data.get("region", "регион не указан"),
		coordinates.y,
		coordinates.x
	]

func _add_journal_entry(object_data: Dictionary, status_id: String) -> void:
	var status: String = "статус: %s" % SQLiteStorageAdapter.status_title(status_id)
	journal_entries.push_front("%s: %s" % [object_data.get("name", "Объект"), status])
	journal_entries = journal_entries.slice(0, 6)
	journal_label.text = "[b]Журнал[/b]\n%s" % "\n".join(journal_entries)
