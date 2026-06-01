extends SceneTree

const MapPanelScript: GDScript = preload("res://scripts/map_panel.gd")
const OUTPUT_DIR := "assets/map/review"
const VIEWPORT_SIZE := Vector2i(1280, 900)
const FRAME_DELAY := 4

const REVIEW_SCENES := [
	{
		"id": "godot_berlin_cluster",
		"title": "Godot Berlin Cluster",
		"description": "Runtime crop focused on the Berlin multi-symbol city cluster glyph.",
		"feedback_target": "Check whether Berlin reads as a city cluster, not just a thin TV tower.",
		"focus": Vector2(13.4050, 52.5200),
	},
	{
		"id": "godot_north_cities",
		"title": "Godot Hamburg Rostock Berlin",
		"description": "Runtime crop for Hamburg, Rostock and Berlin cluster glyphs.",
		"feedback_target": "Check Hamburg/Rostock/Berlin recognizability and coastal placement.",
		"focus": Vector2(10.95, 53.90),
	},
	{
		"id": "godot_rhine_main_cities",
		"title": "Godot Köln Frankfurt",
		"description": "Runtime crop for Köln and Frankfurt cluster glyphs.",
		"feedback_target": "Check whether Köln and Frankfurt have comparable visual weight and stay legible over terrain.",
		"focus": Vector2(7.82, 50.55),
	},
	{
		"id": "godot_munich_stuttgart",
		"title": "Godot München Stuttgart",
		"description": "Runtime crop for München and Stuttgart cluster glyphs.",
		"feedback_target": "Check whether München and Stuttgart are visible without the labels drifting away or clipping.",
		"focus": Vector2(10.45, 48.30),
	},
]

const REVIEW_ZOOMS := [
	{"label": "050", "zoom": 0.5},
	{"label": "100", "zoom": 1.0},
	{"label": "150", "zoom": 1.5},
	{"label": "200", "zoom": 2.0},
]

func _init() -> void:
	call_deferred("_capture_all")


func _capture_all() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))

	var exit_code := OK
	for scene_data in REVIEW_SCENES:
		var scene_error := await _capture_scene(scene_data)
		if scene_error != OK:
			exit_code = scene_error
			break
	_write_manifest()

	quit(exit_code)


func _capture_scene(scene_data: Dictionary) -> Error:
	var scene_dir := "%s/%s" % [OUTPUT_DIR, scene_data["id"]]
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(scene_dir))
	_write_review_metadata(scene_dir, scene_data)

	var viewport := SubViewport.new()
	viewport.size = VIEWPORT_SIZE
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)

	var layer: MapPanel.OfflineMapLayer = MapPanelScript.OfflineMapLayer.new()
	layer.size = Vector2(VIEWPORT_SIZE)
	layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.geo_bounds = _germany_bounds()
	layer.map_scope = "germany"
	viewport.add_child(layer)

	var label_layer: MapPanel.OfflineMapLayer = MapPanelScript.OfflineMapLayer.new()
	label_layer.size = Vector2(VIEWPORT_SIZE)
	label_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	label_layer.geo_bounds = _germany_bounds()
	label_layer.map_scope = "germany"
	label_layer.draw_map_background = false
	label_layer.draw_city_labels = true
	label_layer.draw_terrain_labels = true
	viewport.add_child(label_layer)

	await _wait_frames(FRAME_DELAY)

	var focus := Vector2(scene_data["focus"])
	for zoom_data in REVIEW_ZOOMS:
		var zoom_value := float(zoom_data["zoom"])
		_focus_layer_pair(layer, label_layer, focus, zoom_value)
		await _wait_frames(FRAME_DELAY)

		var image := viewport.get_texture().get_image()
		if image == null:
			push_error("Failed to read Godot map review image for %s %s." % [scene_data["id"], zoom_data["label"]])
			await _cleanup(viewport, layer, label_layer)
			return ERR_CANT_CREATE

		var output_path := "%s/%s_preview_%s.png" % [scene_dir, scene_data["id"], zoom_data["label"]]
		var error := image.save_png(output_path)
		if error != OK:
			push_error("Failed to save Godot map review screenshot %s: %s" % [output_path, error])
			await _cleanup(viewport, layer, label_layer)
			return error
		print("Wrote %s" % output_path)

	await _cleanup(viewport, layer, label_layer)
	return OK


func _write_manifest() -> void:
	var tabs := [
		{
			"id": "city_cluster_glyphs",
			"title": "City Cluster Glyphs",
			"description": "Current multi-symbol city cluster glyph sheet for the first 8 German cities.",
		}
	]
	for scene_data in REVIEW_SCENES:
		tabs.append({
			"id": scene_data["id"],
			"title": scene_data["title"],
			"description": scene_data.get("description", "Godot runtime review scene."),
		})
	var manifest := {
		"schema": "cable-world.map-review-previews.v1",
		"source": "map_review_app/capture_map_review_scenes.gd",
		"review_goal": "current_city_cluster_runtime_review",
		"zooms": [50, 100, 150, 200],
		"viewport_size_px": [VIEWPORT_SIZE.x, VIEWPORT_SIZE.y],
		"tabs": tabs,
	}
	var path := "%s/manifest.json" % OUTPUT_DIR
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("Failed to write review manifest %s." % path)
		return
	file.store_string(JSON.stringify(manifest, "\t"))
	file.store_string("\n")


func _write_review_metadata(scene_dir: String, scene_data: Dictionary) -> void:
	var metadata := {
		"schema": "cable-world.map-review-set.v1",
		"id": scene_data["id"],
		"title": scene_data["title"],
		"description": scene_data.get("description", "Godot runtime review scene."),
		"feedbackTarget": scene_data.get("feedback_target", "Review this current Godot runtime map scene."),
		"order": ["050", "100", "150", "200"],
		"captureScript": "map_review_app/capture_map_review_scenes.gd",
	}
	var path := "%s/review.yml" % scene_dir
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("Failed to write review metadata %s." % path)
		return
	file.store_string(JSON.stringify(metadata, "\t"))
	file.store_string("\n")


func _focus_layer_pair(
	layer: MapPanel.OfflineMapLayer,
	label_layer: MapPanel.OfflineMapLayer,
	coordinates: Vector2,
	zoom_value: float
) -> void:
	var zoom: float = clamp(zoom_value, 0.5, 2.0)
	var map_point: Vector2 = MapPanel.OfflineMapLayer._project_coordinates(
		coordinates,
		_germany_bounds(),
		layer.map_base_size()
	)
	var pan_offset: Vector2 = Vector2(VIEWPORT_SIZE) * 0.5 - map_point * zoom
	layer.pan_offset = pan_offset
	layer.zoom = zoom
	layer.queue_redraw()
	label_layer.pan_offset = pan_offset
	label_layer.zoom = zoom
	label_layer.queue_redraw()


func _wait_frames(count: int) -> void:
	for _index in count:
		await process_frame


func _cleanup(
	viewport: SubViewport,
	layer: MapPanel.OfflineMapLayer,
	label_layer: MapPanel.OfflineMapLayer
) -> void:
	viewport.remove_child(label_layer)
	label_layer.free()
	viewport.remove_child(layer)
	layer.free()
	root.remove_child(viewport)
	viewport.free()
	await process_frame
	await process_frame


func _germany_bounds() -> Dictionary:
	return {
		"min_longitude": 4.5,
		"max_longitude": 16.8,
		"min_latitude": 43.2,
		"max_latitude": 55.8,
	}
