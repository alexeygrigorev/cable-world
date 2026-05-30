extends PanelContainer
class_name ObjectCardPanel

signal visit_toggled(object_id: String, visited: bool)

var current_object: Dictionary = {}
var title_label: Label
var meta_label: Label
var description_label: Label
var notes_label: Label
var visit_button: Button
var attachment_label: Label

func _ready() -> void:
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 18)
	margin.add_theme_constant_override("margin_top", 18)
	margin.add_theme_constant_override("margin_right", 18)
	margin.add_theme_constant_override("margin_bottom", 18)
	add_child(margin)

	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 10)
	margin.add_child(rows)

	title_label = Label.new()
	title_label.add_theme_font_size_override("font_size", 24)
	title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(title_label)

	meta_label = Label.new()
	meta_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(meta_label)

	description_label = Label.new()
	description_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(description_label)

	notes_label = Label.new()
	notes_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(notes_label)

	attachment_label = Label.new()
	attachment_label.text = "Фото и билеты: раздел появится после подключения локального хранилища."
	attachment_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(attachment_label)

	visit_button = Button.new()
	visit_button.pressed.connect(_on_visit_pressed)
	rows.add_child(visit_button)

	show_empty_state()

func show_empty_state() -> void:
	current_object = {}
	title_label.text = "Выберите объект"
	meta_label.text = "Список слева содержит первые демо-объекты."
	description_label.text = ""
	notes_label.text = ""
	visit_button.text = "Отметить посещение"
	visit_button.disabled = true

func show_object(object_data: Dictionary) -> void:
	current_object = object_data
	var coordinates: Vector2 = object_data.get("coordinates", Vector2.ZERO)
	title_label.text = object_data.get("name", "Без названия")
	meta_label.text = "%s · %s · %.4f, %.4f" % [
		object_data.get("kind", "тип не указан"),
		object_data.get("region", "регион не указан"),
		coordinates.y,
		coordinates.x
	]
	description_label.text = object_data.get("description", "Описание пока не добавлено.")
	notes_label.text = "Семейные заметки: %s" % object_data.get("notes", "пока пусто")
	visit_button.disabled = false
	visit_button.text = "Снять отметку посещения" if object_data.get("visited", false) else "Отметить как посещенное"

func _on_visit_pressed() -> void:
	if current_object.is_empty():
		return

	var current_visited: bool = current_object.get("visited", false)
	var next_visited: bool = not current_visited
	visit_toggled.emit(current_object.get("id", ""), next_visited)
