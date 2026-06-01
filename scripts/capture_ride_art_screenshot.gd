extends SceneTree

const RideGameViewScript: GDScript = preload("res://scripts/ride_game_view.gd")


func _init() -> void:
	call_deferred("_capture")


func _capture() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(390, 320)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)

	var view: RideGameView = RideGameViewScript.new()
	view.size = Vector2(390, 260)
	view.set_process(false)
	viewport.add_child(view)
	view.setup_route(_ride_object(), _direction(), _segments(), 0)

	await process_frame
	await process_frame
	await process_frame

	var image := viewport.get_texture().get_image()
	var output_path := "tmp/ride-art-issue-92.png"
	var error := image.save_png(output_path)
	if error != OK:
		push_error("Failed to save ride screenshot: %s" % error)
	quit(error)


func _ride_object() -> Dictionary:
	return {
		"id": "runtime-test-route",
		"name": "Тестовая канатная дорога",
		"stations": [
			{
				"id": "lower",
				"title": "Долинная станция",
				"latitude": 47.0,
				"longitude": 11.0,
			},
			{
				"id": "upper",
				"title": "Горная станция",
				"latitude": 47.2,
				"longitude": 11.4,
			},
		],
		"route_directions": [_direction()],
		"route_segments_by_direction": {
			"up": _segments(),
		},
	}


func _direction() -> Dictionary:
	return {
		"id": "up",
		"title": "Вверх",
		"from_station_id": "lower",
		"to_station_id": "upper",
		"direction_label": "подъем",
	}


func _segments() -> Array:
	return [
		{
			"id": "lower-upper",
			"from_station_id": "lower",
			"to_station_id": "upper",
			"direction_label": "подъем",
			"note": "тестовый отрезок",
		},
	]
