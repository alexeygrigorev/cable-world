extends RefCounted

const AchievementsScript: GDScript = preload("res://scripts/achievements.gd")
const CollectionStatsScript: GDScript = preload("res://scripts/collection_stats.gd")
const ObjectListPanelScript: GDScript = preload("res://scripts/object_list_panel.gd")


func test_collection_stats_and_achievements_runtime() -> Array[String]:
	var failures: Array[String] = []
	var objects: Array[Dictionary] = [
		{
			"id": "wuppertal-schwebebahn",
			"name": "Вуппертальская подвесная дорога",
			"country": "Германия",
			"transport_type_id": "suspended_train",
			"transport_type_title": "Подвесной поезд",
			"visit_status_id": "favorite",
		},
		{
			"id": "lisbon-bica",
			"name": "Фуникулер Бика",
			"country": "Португалия",
			"transport_type_id": "funicular_classic",
			"transport_type_title": "Фуникулер",
			"visit_status_id": "planned",
		},
	]

	var stats: Dictionary = CollectionStatsScript.calculate(objects)
	_expect(stats.get("total_count", 0) == 2, "CollectionStats must count all runtime objects.", failures)
	_expect(stats.get("visited_count", 0) == 1, "Favorite object must count as visited.", failures)
	_expect(stats.get("progress_percent", 0) == 50, "Progress must be rounded from visited/total.", failures)

	var achievements: Array[Dictionary] = AchievementsScript.calculate(objects)
	var suspended_train_achievement := _achievement_by_id(achievements, "first_suspended_train")
	var funicular_achievement := _achievement_by_id(achievements, "first_funicular")
	_expect(suspended_train_achievement.get("unlocked", false), "Visited suspended train must unlock its achievement.", failures)
	_expect(
		suspended_train_achievement.get("matched_object_id", "") == "wuppertal-schwebebahn",
		"Achievement must expose the matched runtime object.",
		failures
	)
	_expect(not funicular_achievement.get("unlocked", true), "Planned funicular must not unlock a visited achievement.", failures)

	return failures


func test_object_list_rows_use_compact_control_layout() -> Array[String]:
	var failures: Array[String] = []
	var panel: ObjectListPanel = ObjectListPanelScript.new()
	panel._ready()
	panel.set_objects([
		{
			"id": "berlin-garden-cable",
			"name": "Канатная дорога в садах мира Берлина",
			"kind": "городская канатная дорога",
			"city": "Берлин",
			"country": "Германия",
			"visit_status_id": "not_visited",
			"operational_status": "active_seasonal",
		},
	])

	_expect(panel.row_buttons.size() == 1, "Object list must create one control row for one visible object.", failures)
	if panel.row_buttons.size() == 1:
		var row := panel.row_buttons[0]
		_expect(row is Button, "Object list row must be a touchable Button control.", failures)
		_expect(row.get_child_count() == 1, "Object list row must own a single layout container.", failures)
		if row.get_child_count() == 1:
			var row_content := row.get_child(0)
			_expect(row_content is HBoxContainer, "Object list row content must be horizontal icon/text layout.", failures)
			_expect(row_content.get_child_count() == 2, "Object list row content must contain icon and text stack.", failures)
			if row_content.get_child_count() == 2:
				_expect(row_content.get_child(0) is TextureRect, "Object list row must render a pictogram texture.", failures)
				var text_box := row_content.get_child(1)
				_expect(text_box is VBoxContainer, "Object list text must be split into separate labels.", failures)
				_expect(text_box.get_child_count() == 2, "Object list text stack must contain name and metadata labels.", failures)
				if text_box.get_child_count() == 2:
					var name_label := text_box.get_child(0) as Label
					var meta_label := text_box.get_child(1) as Label
					_expect(name_label != null and not name_label.text.contains("\n"), "Object name must not rely on newline layout inside a single item.", failures)
					_expect(meta_label != null and meta_label.text.begins_with("Берлин · "), "Object metadata must start on its own readable city/status line.", failures)
					_expect(meta_label != null and meta_label.text.contains("работает сезонно"), "Object metadata must keep key operational status.", failures)
	panel.free()
	return failures


func _achievement_by_id(achievements: Array[Dictionary], achievement_id: String) -> Dictionary:
	for achievement in achievements:
		if achievement.get("id", "") == achievement_id:
			return achievement
	return {}


func _expect(condition: bool, message: String, failures: Array[String]) -> void:
	if not condition:
		failures.append(message)
