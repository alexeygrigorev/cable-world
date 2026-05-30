extends PanelContainer
class_name MemoryPanel

signal back_requested

var current_object: Dictionary = {}
var title_label: Label
var visit_label: Label
var note_label: Label
var rating_label: Label
var photos_label: Label
var tickets_label: Label
var back_button: Button


func _ready() -> void:
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 18)
	margin.add_theme_constant_override("margin_top", 18)
	margin.add_theme_constant_override("margin_right", 18)
	margin.add_theme_constant_override("margin_bottom", 18)
	add_child(margin)

	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 12)
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	margin.add_child(rows)

	back_button = Button.new()
	back_button.text = "Вернуться к карточке"
	back_button.custom_minimum_size = Vector2(0, 52)
	back_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	back_button.pressed.connect(func() -> void: back_requested.emit())
	rows.add_child(back_button)

	title_label = Label.new()
	title_label.add_theme_font_size_override("font_size", 24)
	title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(title_label)

	_add_section_title(rows, "Поездка")
	visit_label = _add_text_label(rows)
	note_label = _add_text_label(rows)
	rating_label = _add_text_label(rows)

	_add_section_title(rows, "Фотографии")
	photos_label = _add_text_label(rows)

	_add_section_title(rows, "Билеты")
	tickets_label = _add_text_label(rows)

	show_empty_state()


func show_empty_state() -> void:
	current_object = {}
	title_label.text = "Воспоминание"
	visit_label.text = "Выберите объект, чтобы увидеть историю поездки."
	note_label.text = "Заметка: пока нет"
	rating_label.text = "Оценка: пока нет"
	photos_label.text = "Фотографии: выберите объект, чтобы увидеть снимки."
	tickets_label.text = "Билеты: выберите объект, чтобы увидеть билеты."
	back_button.disabled = true


func show_object(object_data: Dictionary) -> void:
	current_object = object_data
	title_label.text = "Воспоминание: %s" % _value_text(object_data.get("name", ""), "объект без названия")
	back_button.disabled = false

	var visits := _array_field(object_data, "visits")
	if visits.is_empty():
		visit_label.text = "Посещений пока нет. Когда вы сохраните поездку, здесь появятся дата, заметка и оценка."
		note_label.text = "Заметка: пока нет"
		rating_label.text = "Оценка: пока нет"
	else:
		var visit := _latest_visit(visits)
		visit_label.text = "Дата посещения: %s" % _value_text(visit.get("visited_on", ""), "дата не указана")
		var notes := str(visit.get("notes", "")).strip_edges()
		note_label.text = "Заметка: %s" % ("пока нет" if notes.is_empty() else notes)
		rating_label.text = "Оценка: %s" % _rating_text(visit.get("impression_rating", null))

	photos_label.text = _photos_text(object_data)
	tickets_label.text = _tickets_text(object_data)


func _add_section_title(rows: VBoxContainer, text: String) -> void:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 20)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(label)


func _add_text_label(rows: VBoxContainer) -> Label:
	var label := Label.new()
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.custom_minimum_size = Vector2(0, 32)
	rows.add_child(label)
	return label


func _array_field(object_data: Dictionary, key: String) -> Array:
	if object_data.has(key) and object_data.get(key) is Array:
		return object_data.get(key)
	return []


func _latest_visit(visits: Array) -> Dictionary:
	var latest: Dictionary = {}
	for item in visits:
		if not (item is Dictionary):
			continue
		var visit: Dictionary = item
		if latest.is_empty() or str(visit.get("visited_on", "")) >= str(latest.get("visited_on", "")):
			latest = visit
	return latest


func _photos_text(object_data: Dictionary) -> String:
	var photos := _array_field(object_data, "photos")
	if photos.is_empty():
		return "Фотографии: пока нет добавленных снимков."

	var rows: Array[String] = ["Фотографии: %d" % photos.size()]
	for index in photos.size():
		var item = photos[index]
		if item is Dictionary:
			var photo: Dictionary = item
			rows.append("%d. %s" % [index + 1, _value_text(photo.get("caption", ""), "снимок без подписи")])
	return "\n".join(rows)


func _tickets_text(object_data: Dictionary) -> String:
	var tickets := _array_field(object_data, "tickets")
	if tickets.is_empty():
		return "Билеты: пока нет сохраненных билетов."

	var rows: Array[String] = ["Билеты: %d" % tickets.size()]
	for index in tickets.size():
		var item = tickets[index]
		if item is Dictionary:
			var ticket: Dictionary = item
			var line := "%d. %s" % [index + 1, _value_text(ticket.get("title", ""), "билет без названия")]
			var issued_on := str(ticket.get("issued_on", "")).strip_edges()
			if not issued_on.is_empty():
				line += "\n   Дата билета: %s" % issued_on
			var notes := str(ticket.get("notes", "")).strip_edges()
			if not notes.is_empty():
				line += "\n   Заметка: %s" % notes
			rows.append(line)
	return "\n".join(rows)


func _rating_text(value: Variant) -> String:
	if value == null:
		return "пока нет"
	var rating := int(value)
	if rating <= 0:
		return "пока нет"
	return "%d из 5" % rating


func _value_text(value: Variant, empty_text: String) -> String:
	if value == null:
		return empty_text
	if value is String and value.strip_edges().is_empty():
		return empty_text
	return str(value)
