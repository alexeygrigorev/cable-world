extends ItemList
class_name ObjectListPanel

signal object_selected(index: int)

const FILTER_ALL := "all"
const FILTER_VISITED := "visited"
const FILTER_NOT_VISITED := "not_visited"

var objects: Array[Dictionary] = []
var type_filter: String = FILTER_ALL
var visit_filter: String = FILTER_ALL
var visible_object_indices: Array[int] = []
var empty_state_label: Label

func _ready() -> void:
	item_selected.connect(_on_item_selected)
	_update_empty_state()

func set_empty_state_label(label: Label) -> void:
	empty_state_label = label
	_update_empty_state()

func set_objects(next_objects: Array[Dictionary]) -> void:
	objects = next_objects
	refresh()

func set_filters(next_type_filter: String, next_visit_filter: String) -> void:
	type_filter = next_type_filter
	visit_filter = next_visit_filter
	refresh()

func get_transport_types() -> Array[String]:
	var transport_types: Array[String] = []
	for object_data in objects:
		var kind: String = object_data.get("kind", "")
		if kind != "" and not transport_types.has(kind):
			transport_types.append(kind)

	transport_types.sort()
	return transport_types

func refresh() -> void:
	clear()
	visible_object_indices.clear()
	for index in objects.size():
		var object_data := objects[index]
		if not _matches_filters(object_data):
			continue

		visible_object_indices.append(index)
		var mark := "✓ " if object_data.get("visited", false) else ""
		var label := "%s%s — %s" % [
			mark,
			object_data.get("name", "Без названия"),
			object_data.get("region", "Регион не указан")
		]
		add_item(label)
	_update_empty_state()

func select_object(index: int) -> void:
	if index < 0 or index >= objects.size():
		return

	select_visual_object(index)
	object_selected.emit(index)

func select_visual_object(index: int) -> void:
	var visible_index := visible_object_indices.find(index)
	if visible_index == -1:
		return

	select(visible_index)

func _matches_filters(object_data: Dictionary) -> bool:
	if type_filter != FILTER_ALL and object_data.get("kind", "") != type_filter:
		return false

	var is_visited: bool = object_data.get("visited", false)
	if visit_filter == FILTER_VISITED and not is_visited:
		return false
	if visit_filter == FILTER_NOT_VISITED and is_visited:
		return false

	return true

func _update_empty_state() -> void:
	if empty_state_label == null:
		return

	empty_state_label.visible = get_item_count() == 0
	visible = get_item_count() > 0
	if objects.is_empty():
		empty_state_label.text = "Пока нет объектов. Когда список появится, здесь можно будет выбрать место для семейной поездки."
	else:
		empty_state_label.text = "По таким фильтрам ничего не нашлось. Попробуйте выбрать другой тип или статус посещения."

func _on_item_selected(index: int) -> void:
	if index < 0 or index >= visible_object_indices.size():
		return

	object_selected.emit(visible_object_indices[index])
