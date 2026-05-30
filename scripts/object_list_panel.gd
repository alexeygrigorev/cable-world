extends ItemList
class_name ObjectListPanel

signal object_selected(index: int)

var objects: Array[Dictionary] = []

func _ready() -> void:
	item_selected.connect(_on_item_selected)

func refresh() -> void:
	clear()
	for object_data in objects:
		var mark := "✓ " if object_data.get("visited", false) else ""
		var label := "%s%s — %s" % [
			mark,
			object_data.get("name", "Без названия"),
			object_data.get("region", "Регион не указан")
		]
		add_item(label)

func select_object(index: int) -> void:
	if index < 0 or index >= get_item_count():
		return

	select_visual_object(index)
	object_selected.emit(index)

func select_visual_object(index: int) -> void:
	if index < 0 or index >= get_item_count():
		return

	select(index)

func _on_item_selected(index: int) -> void:
	object_selected.emit(index)
