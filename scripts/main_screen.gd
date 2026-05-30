extends Control
class_name MainScreen

@onready var object_list: ObjectListPanel = %ObjectList
@onready var object_card: ObjectCardPanel = %ObjectCard
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

func _ready() -> void:
	objects = DemoCatalog.get_objects()
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
	object_list.objects = objects
	object_list.object_selected.connect(_on_object_selected)
	object_card.visit_toggled.connect(_on_visit_toggled)

	object_list.refresh()
	if not objects.is_empty():
		_select_object(0, false)
	_show_section("map")

func _on_object_selected(index: int) -> void:
	_select_object(index, true)

func _on_visit_toggled(object_id: String, visited: bool) -> void:
	for index in objects.size():
		if objects[index].get("id", "") == object_id:
			objects[index]["visited"] = visited
			object_list.refresh()
			_select_object(index, false)
			_add_journal_entry(objects[index], visited)
			return

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

func _add_journal_entry(object_data: Dictionary, visited: bool) -> void:
	var status: String = "посещено" if visited else "снята отметка посещения"
	journal_entries.push_front("%s: %s" % [object_data.get("name", "Объект"), status])
	journal_entries = journal_entries.slice(0, 6)
	journal_label.text = "[b]Журнал[/b]\n%s" % "\n".join(journal_entries)
