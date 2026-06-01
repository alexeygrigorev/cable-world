extends RefCounted

const MainScene: PackedScene = preload("res://scenes/Main.tscn")
const ObjectListPanelScript: GDScript = preload("res://scripts/object_list_panel.gd")
const TEST_DATABASE_ENV := "MIR_TROSSOV_DATABASE_PATH"
const TEST_DATABASE_PATH := "user://godot-runtime-app-shell.sqlite3"


func test_main_scene_map_list_toggle_runtime() -> Array[String]:
	var failures: Array[String] = []
	var tree := Engine.get_main_loop() as SceneTree
	OS.set_environment(TEST_DATABASE_ENV, TEST_DATABASE_PATH)
	var screen: MainScreen = MainScene.instantiate()
	screen.visible = false
	tree.root.add_child(screen)

	_expect(screen.map_section.visible, "Main scene must start on the fullscreen map section.", failures)
	_expect(not screen.list_section.visible, "List section must be hidden while the map is active.", failures)
	_expect(not screen.navigation_area.visible, "Map-first chrome must hide the main navigation area.", failures)
	_expect(not screen.app_title_label.visible, "Map-first chrome must hide the app title.", failures)
	_expect(screen.map_list_toggle_button != null, "Map screen must create a compact map/list toggle button.", failures)
	_expect(screen.list_map_return_button != null, "List mode must create a matching return-to-map button.", failures)
	var selected_before := -1
	var map_selected_before := -1
	var pan_before := Vector2.ZERO
	var zoom_before := 1.0
	if screen.map_list_toggle_button != null:
		_expect(screen.map_list_toggle_button.visible, "Map/list toggle must be visible on the map.", failures)
		_expect(screen.map_list_toggle_button.icon != null, "Map/list toggle must use a pictogram icon at runtime.", failures)
		_expect(screen.map_list_toggle_button.text == "", "Map/list toggle must stay icon-only on the map.", failures)
		_expect(screen.map_list_toggle_button.icon.get_width() == 40 and screen.map_list_toggle_button.icon.get_height() == 40, "Map/list toggle pictogram must use the dedicated 40px atlas icon.", failures)
		_expect(screen.map_list_toggle_button.anchor_left == 0.0 and screen.map_list_toggle_button.anchor_right == 0.0, "Map/list toggle must live in its own top-left map corner.", failures)
		_expect(screen.map_list_toggle_button.offset_left >= 12.0, "Map/list toggle must keep atlas-map margin from the left edge.", failures)
		_expect(screen.map_list_toggle_button.offset_right <= 84.0, "Map/list toggle must stay away from top-right zoom controls.", failures)
		_expect(screen.map_list_toggle_button.custom_minimum_size.x >= 60.0 and screen.map_list_toggle_button.custom_minimum_size.y >= 60.0, "Map/list toggle must remain a readable touch target.", failures)
		if screen.map_panel != null and screen.map_panel.zoom_controls != null:
			var toggle_rect: Rect2 = screen.map_list_toggle_button.get_global_rect().grow(8.0)
			var zoom_rect: Rect2 = screen.map_panel.zoom_controls.get_global_rect().grow(8.0)
			_expect(not toggle_rect.intersects(zoom_rect, true), "Map/list toggle must not visually merge with zoom controls.", failures)
		var routed_index := _first_routed_object_index(screen)
		_expect(routed_index >= 0, "Runtime catalog must include at least one ride-capable object.", failures)
		screen._select_object(max(0, routed_index), false)
		screen.map_panel.pan_offset = Vector2(37.0, -24.0)
		screen.map_panel.zoom = 1.5
		selected_before = screen.selected_index
		map_selected_before = screen.map_panel.selected_index
		pan_before = screen.map_panel.pan_offset
		zoom_before = screen.map_panel.zoom
		_expect(screen.map_ride_button != null, "Map selection must create a direct ride button.", failures)
		if screen.map_ride_button != null:
			_expect(screen.map_ride_button.visible, "Map ride button must appear after selecting an object on the map.", failures)
			_expect(not screen.map_ride_button.disabled, "Ride-capable map selection must allow opening the ride.", failures)
			screen.map_ride_button.emit_signal("pressed")
			_expect(screen.ride_section.visible, "Map ride button must open the ride section directly.", failures)
			_expect(screen.ride_panel.card_button.text == "К карте", "Ride back button must reflect the map return context.", failures)
			_expect(screen.ride_panel.speed_slider.editable, "Ride-capable map flow must open playable controls.", failures)
			screen.ride_panel.back_requested.emit()
			_expect(screen.map_section.visible, "Returning from a map-started ride must restore the map.", failures)
			_expect_vector_close(screen.map_panel.pan_offset, pan_before, "Ride return must preserve the previous map pan offset.", failures)
			_expect_float_close(screen.map_panel.zoom, zoom_before, "Ride return must preserve the previous map zoom.", failures)
			_expect(screen.selected_index == selected_before, "Ride return must preserve the app shell selected object.", failures)
			_expect(screen.map_panel.selected_index == map_selected_before, "Ride return must preserve the selected map marker.", failures)

		var empty_ride_index := _first_unrouted_object_index(screen)
		if empty_ride_index >= 0 and screen.map_ride_button != null:
			screen._select_object(empty_ride_index, false)
			screen.map_ride_button.emit_signal("pressed")
			_expect(screen.ride_section.visible, "Map ride button must still open the ride section for objects without route data.", failures)
			_expect(screen.ride_panel.empty_state_label.visible, "Unrouted objects must show a clear ride empty state.", failures)
			_expect(screen.ride_panel.speed_slider.editable == false, "Unrouted ride state must disable playable controls.", failures)
			screen.ride_panel.back_requested.emit()
			selected_before = screen.selected_index
			map_selected_before = screen.map_panel.selected_index
			pan_before = screen.map_panel.pan_offset
			zoom_before = screen.map_panel.zoom
		screen.map_list_toggle_button.emit_signal("pressed")

	_expect(not screen.map_section.visible, "Map section must hide after pressing the map/list toggle.", failures)
	_expect(screen.list_section.visible, "Map/list toggle must open the list section at runtime.", failures)
	_expect(screen.navigation_area.visible, "List mode must restore the navigation area.", failures)
	_expect(screen.app_title_label.visible, "List mode must restore the app title.", failures)
	_expect(not screen.map_list_toggle_button.visible, "Map/list toggle must hide outside the map.", failures)
	_expect(screen.current_section_label.text == "Раздел: Список", "Current section label must track the runtime list transition.", failures)
	if screen.list_map_return_button != null:
		_expect(screen.list_map_return_button.visible, "List mode must expose its return-to-map atlas button.", failures)
		_expect(screen.list_map_return_button.text == "Карта", "List return button must be explicit at mobile size.", failures)
		_expect(screen.list_map_return_button.icon != null, "List return button must use the matching map pictogram.", failures)
		_expect(screen.list_map_return_button.icon.get_width() == 40 and screen.list_map_return_button.icon.get_height() == 40, "List return pictogram must use the matching 40px atlas map icon.", failures)
		_expect(screen.list_map_return_button.custom_minimum_size.x >= 120.0 and screen.list_map_return_button.custom_minimum_size.y >= 48.0, "List return button must be a readable touch target.", failures)
		screen.list_map_return_button.emit_signal("pressed")
		_expect(screen.map_section.visible, "List return button must restore the fullscreen map.", failures)
		_expect(not screen.list_section.visible, "List section must hide after returning to the map.", failures)
		_expect(screen.map_list_toggle_button.visible, "Map/list toggle must reappear after returning to the map.", failures)
		_expect(screen.current_section_label.text == "Раздел: Карта", "Current section label must track the return to map.", failures)
		_expect_vector_close(screen.map_panel.pan_offset, pan_before, "Map/list return must preserve the previous map pan offset.", failures)
		_expect_float_close(screen.map_panel.zoom, zoom_before, "Map/list return must preserve the previous map zoom.", failures)
		_expect(screen.selected_index == selected_before, "Map/list return must preserve the selected object in the app shell.", failures)
		_expect(screen.map_panel.selected_index == map_selected_before, "Map/list return must preserve the selected map marker.", failures)

	_free_screen(screen)
	OS.unset_environment(TEST_DATABASE_ENV)
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


func _first_routed_object_index(screen: MainScreen) -> int:
	for index in screen.objects.size():
		screen._ensure_route_details(index)
		if screen._object_has_playable_route(screen.objects[index]):
			return index
	return -1


func _first_unrouted_object_index(screen: MainScreen) -> int:
	for index in screen.objects.size():
		screen._ensure_route_details(index)
		if not screen._object_has_playable_route(screen.objects[index]):
			return index
	return -1


func _free_screen(screen: MainScreen) -> void:
	if screen == null:
		return
	if screen.is_inside_tree():
		screen.get_parent().remove_child(screen)
	screen.free()


func _expect_int_array(actual: Array[int], expected: Array[int], message: String, failures: Array[String]) -> void:
	if actual.size() != expected.size():
		failures.append("%s Expected %s, got %s." % [message, str(expected), str(actual)])
		return
	for index in expected.size():
		if actual[index] != expected[index]:
			failures.append("%s Expected %s, got %s." % [message, str(expected), str(actual)])
			return


func _expect_float_close(actual: float, expected: float, message: String, failures: Array[String], tolerance: float = 0.001) -> void:
	if abs(actual - expected) > tolerance:
		failures.append("%s Expected %.3f, got %.3f." % [message, expected, actual])


func _expect_vector_close(actual: Vector2, expected: Vector2, message: String, failures: Array[String], tolerance: float = 0.001) -> void:
	if actual.distance_to(expected) > tolerance:
		failures.append("%s Expected %s, got %s." % [message, str(expected), str(actual)])
