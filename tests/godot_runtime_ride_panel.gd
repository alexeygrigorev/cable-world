extends RefCounted

const RideGameViewScript: GDScript = preload("res://scripts/ride_game_view.gd")
const RidePanelScript: GDScript = preload("res://scripts/ride_panel.gd")


func test_ride_game_view_passenger_speed_and_finish_state() -> Array[String]:
	var failures: Array[String] = []
	var view: RideGameView = RideGameViewScript.new()
	view._ready()
	view.setup_route(_ride_object(), _direction(), _segments(), 0)
	view.set_process(false)

	_expect(view.lower_station_title == "Долинная станция", "Ride view must read the lower station title from route data.", failures)
	_expect(view.upper_station_title == "Горная станция", "Ride view must read the upper station title from route data.", failures)
	_expect(view.passengers_onboard == 4, "Passengers must board at the lower station.", failures)
	_expect(view.passengers_waiting == 0, "Boarded passengers must leave the lower station queue.", failures)

	view.set_speed_multiplier(2.0)
	view.advance_ride(1.0)
	var fast_progress := view.progress
	view.reset_ride()
	view.set_speed_multiplier(0.5)
	view.advance_ride(1.0)
	_expect(fast_progress > view.progress * 2.5, "Speed multiplier must visibly affect cabin movement.", failures)

	view.advance_ride(20.0)
	_expect(view.ride_finished, "Ride must finish at the upper station.", failures)
	_expect(view.passengers_onboard == 0, "Passengers must leave the cabin at the upper station.", failures)
	_expect(view.delivered_passengers == 4, "Finished ride must count delivered passengers.", failures)
	_expect(view.smoothness_score >= 0 and view.smoothness_score <= 100, "Finished ride must expose a bounded smoothness score.", failures)

	view.free()
	return failures


func test_ride_panel_wires_playable_view_into_existing_route_flow() -> Array[String]:
	var failures: Array[String] = []
	var panel: RidePanel = RidePanelScript.new()
	panel._ready()
	panel.show_object(_ride_object())
	panel.ride_game_view.set_process(false)

	_expect(panel.ride_game_view != null, "Ride panel must create the playable side-view.", failures)
	_expect(panel.speed_slider != null and panel.speed_slider.editable, "Ride panel must expose an editable mobile speed control.", failures)
	_expect(panel.slower_button != null and not panel.slower_button.disabled, "Slower button must be enabled for route data.", failures)
	_expect(panel.faster_button != null and not panel.faster_button.disabled, "Faster button must be enabled for route data.", failures)
	_expect(panel.ride_game_view.passengers_onboard == 4, "Showing a routed object must start with boarded passengers.", failures)

	panel.speed_slider.value = 1.75
	panel._on_speed_slider_changed(1.75)
	_expect(absf(panel.ride_game_view.speed_multiplier - 1.75) < 0.01, "Panel speed slider must update ride movement speed.", failures)

	panel.ride_game_view.advance_ride(20.0)
	_expect(panel.score_label.text.contains("плавность"), "Completed ride must show smoothness in the result label.", failures)
	_expect(panel.score_label.text.contains("доставлено 4"), "Completed ride must show delivered passenger count.", failures)

	panel.free()
	return failures


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


func _expect(condition: bool, message: String, failures: Array[String]) -> void:
	if not condition:
		failures.append(message)
