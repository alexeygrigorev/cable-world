extends RefCounted

const MainScene: PackedScene = preload("res://scenes/Main.tscn")
const ObjectListPanelScript: GDScript = preload("res://scripts/object_list_panel.gd")


func test_main_scene_map_list_toggle_runtime() -> Array[String]:
	var failures: Array[String] = []
	var tree := Engine.get_main_loop() as SceneTree
	var screen: MainScreen = MainScene.instantiate()
	tree.root.add_child(screen)

	_expect(screen.map_section.visible, "Main scene must start on the fullscreen map section.", failures)
	_expect(not screen.list_section.visible, "List section must be hidden while the map is active.", failures)
	_expect(not screen.navigation_area.visible, "Map-first chrome must hide the main navigation area.", failures)
	_expect(not screen.app_title_label.visible, "Map-first chrome must hide the app title.", failures)
	_expect(screen.map_list_toggle_button != null, "Map screen must create a compact map/list toggle button.", failures)
	if screen.map_list_toggle_button != null:
		_expect(screen.map_list_toggle_button.visible, "Map/list toggle must be visible on the map.", failures)
		_expect(screen.map_list_toggle_button.icon != null, "Map/list toggle must use a pictogram icon at runtime.", failures)
		screen.map_list_toggle_button.emit_signal("pressed")

	_expect(not screen.map_section.visible, "Map section must hide after pressing the map/list toggle.", failures)
	_expect(screen.list_section.visible, "Map/list toggle must open the list section at runtime.", failures)
	_expect(screen.navigation_area.visible, "List mode must restore the navigation area.", failures)
	_expect(screen.app_title_label.visible, "List mode must restore the app title.", failures)
	_expect(not screen.map_list_toggle_button.visible, "Map/list toggle must hide outside the map.", failures)
	_expect(screen.current_section_label.text == "Раздел: Список", "Current section label must track the runtime list transition.", failures)

	tree.root.remove_child(screen)
	screen.free()
	return failures


func test_object_list_filtering_and_selection_runtime() -> Array[String]:
	var failures: Array[String] = []
	var panel: ObjectListPanel = ObjectListPanelScript.new()
	var empty_state := Label.new()
	var selected_indices: Array[int] = []
	panel._ready()
	panel.set_empty_state_label(empty_state)
	panel.object_selected.connect(func(index: int) -> void: selected_indices.append(index))
	panel.set_objects([
		{
			"id": "berlin-garden-cable",
			"name": "Канатная дорога в садах мира Берлина",
			"kind": "городская канатная дорога",
			"city": "Берлин",
			"country": "Германия",
			"visit_status_id": "visited",
			"operational_status": "active_seasonal",
		},
		{
			"id": "lisbon-bica",
			"name": "Фуникулер Бика",
			"kind": "фуникулер",
			"city": "Лиссабон",
			"country": "Португалия",
			"visit_status_id": "planned",
			"operational_status": "active",
		},
		{
			"id": "wuppertal-schwebebahn",
			"name": "Вуппертальская подвесная дорога",
			"kind": "подвесной поезд",
			"city": "Вупперталь",
			"country": "Германия",
			"visit_status_id": "not_visited",
			"operational_status": "active",
		},
	])

	_expect_int_array(panel.visible_object_indices, [0, 1, 2], "Object list must show all rows before filters.", failures)
	_expect(panel.row_buttons.size() == 3, "Object list must create runtime row buttons for visible objects.", failures)
	_expect(not empty_state.visible, "Empty state must stay hidden when rows are visible.", failures)

	panel.set_search_query("берлин")
	_expect_int_array(panel.visible_object_indices, [0], "Search must filter visible object indices at runtime.", failures)

	panel.set_search_query("")
	panel.set_filters(ObjectListPanel.FILTER_ALL, ObjectListPanel.FILTER_NOT_VISITED, "Германия")
	_expect_int_array(panel.visible_object_indices, [2], "Country and visit filters must compose at runtime.", failures)
	_expect(panel.row_buttons.size() == 1, "Filtered list must rebuild runtime rows.", failures)

	panel.select_object(2)
	_expect_int_array(selected_indices, [2], "Selecting a visible list object must emit its source object index.", failures)
	_expect(panel.row_buttons.size() == 1 and panel.row_buttons[0].button_pressed, "Selecting an object must mark the visible row pressed.", failures)

	panel.set_search_query("does-not-exist")
	_expect(panel.visible_object_indices.is_empty(), "Unmatched search must produce no visible indices.", failures)
	_expect(empty_state.visible, "Empty state must become visible when filters hide every object.", failures)
	_expect(empty_state.text.contains("ничего не нашлось"), "Filtered empty state must explain that no search/filter rows matched.", failures)

	empty_state.free()
	panel.free()
	return failures


func _expect(condition: bool, message: String, failures: Array[String]) -> void:
	if not condition:
		failures.append(message)


func _expect_int_array(actual: Array[int], expected: Array[int], message: String, failures: Array[String]) -> void:
	if actual.size() != expected.size():
		failures.append("%s Expected %s, got %s." % [message, str(expected), str(actual)])
		return
	for index in expected.size():
		if actual[index] != expected[index]:
			failures.append("%s Expected %s, got %s." % [message, str(expected), str(actual)])
			return
