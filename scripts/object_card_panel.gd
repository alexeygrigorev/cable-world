extends PanelContainer
class_name ObjectCardPanel

signal status_changed(object_id: String, status_id: String)
signal photo_registration_requested(object_id: String)

var current_object: Dictionary = {}
var title_label: Label
var type_label: Label
var location_label: Label
var coordinates_label: Label
var status_label: Label
var operational_status_label: Label
var status_option: OptionButton
var description_label: Label
var notes_label: Label
var technical_label: Label
var photos_label: Label
var photos_hint_label: Label
var add_photo_button: Button
var videos_label: Label
var tickets_label: Label
var visits_label: Label
var status_option_is_refreshing: bool = false

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
	operational_status_label = _add_text_label(rows)
	status_option = OptionButton.new()
	_configure_status_option()
	status_option.item_selected.connect(_on_status_selected)
	rows.add_child(status_option)

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
	photos_hint_label = _add_text_label(rows)
	add_photo_button = Button.new()
	add_photo_button.text = "Добавить запись о фото"
	add_photo_button.tooltip_text = "Сейчас сохраняется подпись к фотографии. Выбор настоящего файла появится следующим шагом."
	add_photo_button.pressed.connect(_on_add_photo_pressed)
	rows.add_child(add_photo_button)
	videos_label = _add_text_label(rows)
	tickets_label = _add_text_label(rows)
	visits_label = _add_text_label(rows)

	show_empty_state()

func show_empty_state() -> void:
	current_object = {}
	title_label.text = "Объект не выбран"
	type_label.text = "Тип транспорта: не указано"
	location_label.text = "Место: не указано"
	coordinates_label.text = "Координаты: не указаны"
	status_label.text = "Статус посещения: не указано"
	operational_status_label.text = "Работа объекта: статус неизвестен"
	description_label.text = "Описание: выберите объект из списка."
	notes_label.text = "Семейные заметки: пока нет"
	technical_label.text = _technical_text({})
	photos_label.text = "Фотографии: пока нет"
	photos_hint_label.text = "Фотографии пока не добавлены."
	add_photo_button.disabled = true
	videos_label.text = "Видео: пока нет"
	tickets_label.text = "Билеты: пока нет"
	visits_label.text = "Посещения: пока нет"
	status_option.disabled = true
	_select_status_option(SQLiteStorageAdapter.STATUS_NOT_VISITED)

func show_object(object_data: Dictionary, can_register_photo: bool = false) -> void:
	current_object = object_data
	title_label.text = object_data.get("name", "Без названия")
	type_label.text = "Тип транспорта: %s" % _value_text(object_data.get("kind", ""))
	location_label.text = _location_text(object_data)
	coordinates_label.text = _coordinates_text(object_data)
	status_label.text = "Статус посещения: %s" % _visit_status_text(object_data)
	operational_status_label.text = _operational_status_text(object_data)
	description_label.text = _field_text("Описание", object_data.get("description", ""), "пока нет")
	notes_label.text = _field_text("Семейные заметки", object_data.get("notes", ""), "пока нет")
	technical_label.text = _technical_text(object_data)
	photos_label.text = _photo_collection_text(object_data)
	photos_hint_label.text = _photo_hint_text(can_register_photo)
	add_photo_button.disabled = not can_register_photo
	videos_label.text = _collection_status("Видео", object_data, "videos", "video_count", "пока нет добавленных видео")
	tickets_label.text = _collection_status("Билеты", object_data, "tickets", "ticket_count", "пока нет сохраненных билетов")
	visits_label.text = _visits_status(object_data)
	status_option.disabled = false
	_select_status_option(_object_status_id(object_data))

func _configure_status_option() -> void:
	status_option.clear()
	for status_id in SQLiteStorageAdapter.status_ids():
		status_option.add_item(SQLiteStorageAdapter.status_title(status_id))
		status_option.set_item_metadata(status_option.get_item_count() - 1, status_id)

func _on_status_selected(index: int) -> void:
	if current_object.is_empty():
		return
	if status_option_is_refreshing:
		return
	if index < 0 or index >= status_option.get_item_count():
		return

	var status_id := str(status_option.get_item_metadata(index))
	status_changed.emit(current_object.get("id", ""), status_id)

func _on_add_photo_pressed() -> void:
	if current_object.is_empty():
		return
	photo_registration_requested.emit(current_object.get("id", ""))

func _select_status_option(status_id: String) -> void:
	status_option_is_refreshing = true
	var normalized_status := SQLiteStorageAdapter.normalized_status_id(status_id)
	for index in status_option.get_item_count():
		if status_option.get_item_metadata(index) == normalized_status:
			status_option.select(index)
			break
	status_option_is_refreshing = false

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
	return SQLiteStorageAdapter.status_title(_object_status_id(object_data))


func _operational_status_text(object_data: Dictionary) -> String:
	var status := SQLiteStorageAdapter.operational_status_title(str(object_data.get("operational_status", SQLiteStorageAdapter.OPERATIONAL_UNKNOWN)))
	var lines: Array[String] = ["Работа объекта: %s" % status]
	var checked_at := str(object_data.get("status_checked_at", "")).strip_edges()
	if not checked_at.is_empty():
		lines.append("Проверено: %s" % checked_at)
	var note := str(object_data.get("status_note", "")).strip_edges()
	if not note.is_empty():
		lines.append("Примечание: %s" % note)
	var source_url := str(object_data.get("status_source_url", "")).strip_edges()
	if not source_url.is_empty():
		lines.append("Источник: %s" % source_url)

	var text := lines[0]
	for index in range(1, lines.size()):
		text += "\n%s" % lines[index]
	return text


func _object_status_id(object_data: Dictionary) -> String:
	if object_data.has("visit_status_id"):
		return SQLiteStorageAdapter.normalized_status_id(str(object_data.get("visit_status_id", "")))
	return SQLiteStorageAdapter.STATUS_VISITED if object_data.get("visited", false) else SQLiteStorageAdapter.STATUS_NOT_VISITED

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

func _photo_collection_text(object_data: Dictionary) -> String:
	if object_data.has("photos") and object_data.get("photos") is Array:
		var photos: Array = object_data.get("photos")
		if not photos.is_empty():
			var rows: Array[String] = ["Фотографии: %d" % photos.size()]
			for index in photos.size():
				var item = photos[index]
				if item is Dictionary:
					var photo: Dictionary = item
					var caption := _value_text(photo.get("caption", ""), "без подписи")
					rows.append("- Фото %d: %s" % [index + 1, caption])
			return "\n".join(rows)
	return _collection_status("Фотографии", object_data, "photos", "photo_count", "пока нет добавленных фотографий")

func _photo_hint_text(can_register_photo: bool) -> String:
	if can_register_photo:
		return "Сейчас добавляется только запись о фотографии. Выбор настоящего файла появится следующим шагом."
	return "Добавление фото сейчас недоступно: локальное хранилище не открыто."

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
