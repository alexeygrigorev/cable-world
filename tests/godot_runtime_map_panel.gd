extends RefCounted

const MapPanelScript: GDScript = preload("res://scripts/map_panel.gd")


func test_mouse_drag_moves_map_one_to_one() -> Array[String]:
	var failures: Array[String] = []
	var panel: Variant = MapPanelScript.new()
	panel.pan_offset = Vector2(10.0, 20.0)
	panel.dragging = true

	var event := InputEventMouseMotion.new()
	event.relative = Vector2(37.0, -19.0)
	event.button_mask = MOUSE_BUTTON_MASK_LEFT
	panel._handle_mouse_motion(event)

	_expect_vector_close(panel.pan_offset, Vector2(47.0, 1.0), "Mouse drag must pan the map 1:1.", failures)
	panel.free()
	return failures


func test_touch_drag_is_calmer_than_mouse_drag() -> Array[String]:
	var failures: Array[String] = []
	var panel: Variant = MapPanelScript.new()
	panel.pan_offset = Vector2(-12.0, 8.0)

	var touch := InputEventScreenTouch.new()
	touch.index = 0
	touch.position = Vector2(100.0, 120.0)
	touch.pressed = true
	panel._handle_screen_touch(touch)

	var drag := InputEventScreenDrag.new()
	drag.index = 0
	drag.position = Vector2(136.0, 98.0)
	drag.relative = Vector2(36.0, -22.0)
	panel._handle_screen_drag(drag)

	_expect_vector_close(panel.pan_offset, Vector2(0.24, 0.52), "Touch drag must be damped so finger movement does not outrun the map.", failures)
	panel.free()
	return failures


func test_pinch_gesture_does_not_change_zoom() -> Array[String]:
	var failures: Array[String] = []
	var panel: Variant = MapPanelScript.new()
	panel.zoom = 1.25

	var event := InputEventMagnifyGesture.new()
	event.factor = 1.8
	panel._on_map_layer_gui_input(event)

	_expect_float_close(panel.zoom, 1.25, "Magnify/pinch gesture must not change map zoom.", failures)
	panel.free()
	return failures


func test_zoom_buttons_step_by_25_percent_with_bounds() -> Array[String]:
	var failures: Array[String] = []
	var panel: Variant = _ready_map_panel()
	panel.zoom = 1.0
	panel.pan_offset = Vector2.ZERO
	panel._apply_map_transform()

	var zoom_in := _zoom_button(panel, "+")
	var zoom_out := _zoom_button(panel, "-")
	if zoom_in == null or zoom_out == null:
		_cleanup_panel(panel)
		return ["MapPanel zoom controls must expose + and - buttons."]

	var expected_zoom_in := [1.25, 1.5, 1.75, 2.0, 2.0]
	for expected in expected_zoom_in:
		zoom_in.emit_signal("pressed")
		_expect_float_close(panel.zoom, float(expected), "Zoom + button must step by 25% and stop at 200%.", failures)

	var expected_zoom_out := [1.75, 1.5, 1.25, 1.0, 0.75, 0.5, 0.5]
	for expected in expected_zoom_out:
		zoom_out.emit_signal("pressed")
		_expect_float_close(panel.zoom, float(expected), "Zoom - button must step by 25% and stop at 50%.", failures)

	_expect(panel.zoom_percent_label.text == "50%", "Zoom percent label must reflect the clamped zoom.", failures)
	_cleanup_panel(panel)
	return failures


func test_marker_label_and_map_layers_share_transform() -> Array[String]:
	var failures: Array[String] = []
	var panel: Variant = _ready_map_panel()
	var coordinates := Vector2(13.4050, 52.5200)
	var objects: Array[Dictionary] = [
		{
			"name": "Berlin test object",
			"country": "Germany",
			"coordinates": coordinates,
			"transport_type_id": "special_transport_system",
			"visit_status_id": "planned",
		},
	]
	panel.objects = objects
	var marker := Button.new()
	marker.set_meta("object_index", 0)
	marker.set_meta("style_key", "single:0:false:icon_station")
	panel.map_content.add_child(marker)
	panel.marker_buttons.append(marker)
	panel._update_map_reference_data()

	panel.zoom = 1.5
	panel.pan_offset = Vector2(42.0, -31.0)
	panel._apply_map_transform()
	_expect_layer_transform_matches(panel, failures)
	_expect_marker_tracks_label_position(panel, coordinates, failures)

	panel.zoom = 0.75
	panel.pan_offset = Vector2(-18.0, 64.0)
	panel._apply_map_transform()
	_expect_layer_transform_matches(panel, failures)
	_expect_marker_tracks_label_position(panel, coordinates, failures)

	_cleanup_panel(panel)
	return failures


func test_marker_spread_keeps_dense_markers_apart_without_jitter() -> Array[String]:
	var failures: Array[String] = []
	var panel: Variant = MapPanelScript.new()
	var map_size := Vector2(600.0, 600.0)
	var placed: Array[Vector2] = [Vector2(300.0, 300.0)]

	var first: Vector2 = panel._spread_marker_position(Vector2(308.0, 304.0), placed, map_size)
	var second: Vector2 = panel._spread_marker_position(Vector2(308.0, 304.0), placed, map_size)

	_expect_vector_close(first, second, "Marker spread must be deterministic so pan/zoom does not jitter markers.", failures)
	_expect(first.distance_to(placed[0]) >= 64.0, "Dense marker spread must keep marker centers at least the anti-clutter distance apart.", failures)
	_expect(first.x >= 24.0 and first.x <= 576.0, "Spread marker must stay inside horizontal map padding.", failures)
	_expect(first.y >= 24.0 and first.y <= 576.0, "Spread marker must stay inside vertical map padding.", failures)
	panel.free()
	return failures


func _ready_map_panel() -> Variant:
	var panel: Variant = MapPanelScript.new()
	panel.map_layer = MapPanelScript.OfflineMapLayer.new()
	panel.map_label_layer = MapPanelScript.OfflineMapLayer.new()
	panel.map_content = Control.new()
	panel.zoom_controls = HBoxContainer.new()
	panel.map_layer.size = Vector2(800.0, 600.0)
	panel.map_label_layer.size = Vector2(800.0, 600.0)
	panel.map_content.size = Vector2(800.0, 600.0)
	panel._add_zoom_percent_label(panel.zoom_controls)
	panel._add_zoom_button(panel.zoom_controls, "-", -0.25)
	panel._add_zoom_button(panel.zoom_controls, "+", 0.25)
	panel._update_map_reference_data()
	return panel


func _cleanup_panel(panel: Variant) -> void:
	panel.marker_buttons.clear()
	panel.zoom_controls.free()
	panel.map_content.free()
	panel.map_label_layer.free()
	panel.map_layer.free()
	panel.free()


func _zoom_button(panel: Variant, text: String) -> Button:
	for child in panel.zoom_controls.get_children():
		if child is Button and child.text == text:
			return child
	return null


func _expect_layer_transform_matches(panel: Variant, failures: Array[String]) -> void:
	_expect_vector_close(panel.map_layer.get("pan_offset"), panel.pan_offset, "Map background layer must use MapPanel pan_offset.", failures)
	_expect_vector_close(panel.map_label_layer.get("pan_offset"), panel.pan_offset, "Label layer must use MapPanel pan_offset.", failures)
	_expect_float_close(float(panel.map_layer.get("zoom")), panel.zoom, "Map background layer must use MapPanel zoom.", failures)
	_expect_float_close(float(panel.map_label_layer.get("zoom")), panel.zoom, "Label layer must use MapPanel zoom.", failures)


func _expect_marker_tracks_label_position(panel: Variant, coordinates: Vector2, failures: Array[String]) -> void:
	if panel.marker_buttons.is_empty():
		failures.append("MapPanel must create a marker for the test object.")
		return
	var marker: Button = panel.marker_buttons[0]
	var label_screen_position: Vector2 = panel.map_label_layer._geo_to_screen(coordinates)
	var map_screen_position: Vector2 = panel.map_layer._geo_to_screen(coordinates)
	var marker_base_position: Vector2 = MapPanelScript.OfflineMapLayer._project_coordinates(
		coordinates,
		panel._active_coordinate_bounds(),
		panel.map_layer.map_base_size()
	)
	var expected_marker_position: Vector2 = panel._map_point_to_screen(marker_base_position, panel._marker_visual_size(false))
	_expect_vector_close(map_screen_position, label_screen_position, "Map and label layers must project coordinates identically.", failures)
	_expect_vector_close(marker.position, expected_marker_position, "Marker must use the same pan/zoom projection as map labels.", failures, 1.0)


func _expect(condition: bool, message: String, failures: Array[String]) -> void:
	if not condition:
		failures.append(message)


func _expect_float_close(actual: float, expected: float, message: String, failures: Array[String], tolerance: float = 0.001) -> void:
	if abs(actual - expected) > tolerance:
		failures.append("%s Expected %.3f, got %.3f." % [message, expected, actual])


func _expect_vector_close(actual: Vector2, expected: Vector2, message: String, failures: Array[String], tolerance: float = 0.001) -> void:
	if actual.distance_to(expected) > tolerance:
		failures.append("%s Expected %s, got %s." % [message, str(expected), str(actual)])
