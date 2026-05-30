extends Control
class_name MainScreen

@onready var object_list: ObjectListPanel = %ObjectList
@onready var object_card: ObjectCardPanel = %ObjectCard
@onready var journal_label: RichTextLabel = %JournalLabel

var objects: Array[Dictionary] = []
var journal_entries: Array[String] = []

func _ready() -> void:
	objects = DemoCatalog.get_objects()
	object_list.objects = objects
	object_list.object_selected.connect(_on_object_selected)
	object_card.visit_toggled.connect(_on_visit_toggled)

	object_list.refresh()
	if not objects.is_empty():
		object_list.select_object(0)

func _on_object_selected(index: int) -> void:
	if index < 0 or index >= objects.size():
		return

	object_card.show_object(objects[index])

func _on_visit_toggled(object_id: String, visited: bool) -> void:
	for index in objects.size():
		if objects[index].get("id", "") == object_id:
			objects[index]["visited"] = visited
			object_list.refresh()
			object_card.show_object(objects[index])
			_add_journal_entry(objects[index], visited)
			return

func _add_journal_entry(object_data: Dictionary, visited: bool) -> void:
	var status: String = "посещено" if visited else "снята отметка посещения"
	journal_entries.push_front("%s: %s" % [object_data.get("name", "Объект"), status])
	journal_entries = journal_entries.slice(0, 6)
	journal_label.text = "[b]Журнал[/b]\n%s" % "\n".join(journal_entries)
