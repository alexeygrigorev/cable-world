extends PanelContainer
class_name ObjectCardPanel

signal visit_toggled(object_id: String, visited: bool)

var current_object: Dictionary = {}
var title_label: Label
var type_label: Label
var location_label: Label
var coordinates_label: Label
var status_label: Label
var description_label: Label
var notes_label: Label
var technical_label: Label
var photos_label: Label
var videos_label: Label
var tickets_label: Label
var visits_label: Label
var visit_button: Button

func _ready() -> void:
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 18)
	margin.add_theme_constant_override("margin_top", 18)
	margin.add_theme_constant_override("margin_right", 18)
	margin.add_theme_constant_override("margin_bottom", 18)
	add_child(margin)

	var scroll := ScrollContainer.new()
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	margin.add_child(scroll)

	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 10)
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(rows)

	title_label = Label.new()
	title_label.add_theme_font_size_override("font_size", 24)
	title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(title_label)

	_add_separator(rows)
	_add_section_title(rows, "Общая информация")
	type_label = _add_text_label(rows)
	location_label = _add_text_label(rows)
	coordinates_label = _add_text_label(rows)
	status_label = _add_text_label(rows)

	_add_separator(rows)
	_add_section_title(rows, "Описание")
	description_label = _add_text_label(rows)

	_add_separator(rows)
	_add_section_title(rows, "Семейные заметки")
	notes_label = _add_text_label(rows)

	_add_separator(rows)
	_add_section_title(rows, "Технические поля")
	technical_label = _add_text_label(rows)

	_add_separator(rows)
	_add_section_title(rows, "Материалы и история")
	photos_label = _add_text_label(rows)
	videos_label = _add_text_label(rows)
	tickets_label = _add_text_label(rows)
	visits_label = _add_text_label(rows)

	visit_button = Button.new()
	visit_button.pressed.connect(_on_visit_pressed)
	rows.add_child(visit_button)

	show_empty_state()

func show_empty_state() -> void:
	current_object = {}
	title_label.text = "Объект не выбран"
	type_label.text = "Тип транспорта: не указано"
	location_label.text = "Место: не указано"
	coordinates_label.text = "Координаты: не указаны"
	status_label.text = "Статус посещения: не указано"
	description_label.text = "Описание: выберите объект из списка."
	notes_label.text = "Семейные заметки: пока нет"
	technical_label.text = _technical_text({})
	photos_label.text = "Фотографии: пока нет"
	videos_label.text = "Видео: пока нет"
	tickets_label.text = "Билеты: пока нет"
	visits_label.text = "Посещения: пока нет"
	visit_button.text = "Отметить посещение"
	visit_button.disabled = true

func show_object(object_data: Dictionary) -> void:
	current_object = object_data
	title_label.text = object_data.get("name", "Без названия")
	type_label.text = "Тип транспорта: %s" % _value_text(object_data.get("kind", ""))
	location_label.text = _location_text(object_data)
	coordinates_label.text = _coordinates_text(object_data)
	status_label.text = "Статус посещения: %s" % _visit_status_text(object_data)
	description_label.text = _field_text("Описание", object_data.get("description", ""), "пока нет")
	notes_label.text = _field_text("Семейные заметки", object_data.get("notes", ""), "пока нет")
	technical_label.text = _technical_text(object_data)
	photos_label.text = _collection_status("Фотографии", object_data, "photos", "photo_count", "пока нет добавленных фотографий")
	videos_label.text = _collection_status("Видео", object_data, "videos", "video_count", "пока нет добавленных видео")
	tickets_label.text = _collection_status("Билеты", object_data, "tickets", "ticket_count", "пока нет сохраненных билетов")
	visits_label.text = _visits_status(object_data)
	visit_button.disabled = false
	visit_button.text = "Снять отметку посещения" if object_data.get("visited", false) else "Отметить как посещенное"

func _on_visit_pressed() -> void:
	if current_object.is_empty():
		return

	var current_visited: bool = current_object.get("visited", false)
	var next_visited: bool = not current_visited
	visit_toggled.emit(current_object.get("id", ""), next_visited)

func _add_separator(rows: VBoxContainer) -> void:
	var separator := HSeparator.new()
	rows.add_child(separator)

func _add_section_title(rows: VBoxContainer, text: String) -> void:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 16)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(label)

func _add_text_label(rows: VBoxContainer) -> Label:
	var label := Label.new()
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(label)
	return label

func _field_text(title: String, value: Variant, empty_text: String) -> String:
	return "%s: %s" % [title, _value_text(value, empty_text)]

func _value_text(value: Variant, empty_text: String = "не указано") -> String:
	if value == null:
		return empty_text
	if value is String and value.strip_edges().is_empty():
		return empty_text
	return str(value)

func _location_text(object_data: Dictionary) -> String:
	var country := _value_text(object_data.get("country", ""))
	var region := _value_text(object_data.get("region", ""))
	var city := _value_text(object_data.get("city", ""))
	return "Страна: %s\nРегион: %s\nГород: %s" % [country, region, city]

func _coordinates_text(object_data: Dictionary) -> String:
	if object_data.has("coordinates") and object_data.get("coordinates") is Vector2:
		var coordinates: Vector2 = object_data.get("coordinates")
		return "Координаты: %.4f, %.4f" % [coordinates.y, coordinates.x]
	if object_data.has("latitude") and object_data.has("longitude"):
		return "Координаты: %.4f, %.4f" % [
			float(object_data.get("latitude", 0.0)),
			float(object_data.get("longitude", 0.0))
		]
	return "Координаты: не указаны"

func _visit_status_text(object_data: Dictionary) -> String:
	var status_id: String = object_data.get("visit_status_id", "")
	match status_id:
		"not_visited":
			return "не посещали"
		"planned":
			return "запланировано"
		"visited":
			return "посещено"
		"favorite":
			return "любимое место"
		_:
			return "посещено" if object_data.get("visited", false) else "не посещали"

func _technical_text(object_data: Dictionary) -> String:
	return "Год открытия: %s\nОператор: %s\nПроизводитель: %s" % [
		_year_text(object_data.get("opened_year", null)),
		_value_text(object_data.get("operator", "")),
		_value_text(object_data.get("manufacturer", ""))
	]

func _year_text(value: Variant) -> String:
	if value == null:
		return "не указано"
	if value is int and value <= 0:
		return "не указано"
	if value is float and value <= 0.0:
		return "не указано"
	if value is String and value.strip_edges().is_empty():
		return "не указано"
	return str(value)

func _collection_status(title: String, object_data: Dictionary, list_key: String, count_key: String, empty_text: String) -> String:
	var count := -1
	if object_data.has(count_key):
		count = int(object_data.get(count_key, 0))
	elif object_data.has(list_key) and object_data.get(list_key) is Array:
		var items: Array = object_data.get(list_key)
		count = items.size()

	if count > 0:
		return "%s: %d" % [title, count]
	return "%s: %s" % [title, empty_text]

func _visits_status(object_data: Dictionary) -> String:
	var count := -1
	if object_data.has("visit_count"):
		count = int(object_data.get("visit_count", 0))
	elif object_data.has("visits") and object_data.get("visits") is Array:
		var visits: Array = object_data.get("visits")
		count = visits.size()

	if count > 0:
		return "Посещения: %d" % count
	if object_data.get("visited", false):
		return "Посещения: отметка есть, подробных записей пока нет"
	return "Посещения: пока нет записей о поездках"
