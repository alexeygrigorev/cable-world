extends SceneTree

const MainScene: PackedScene = preload("res://scenes/Main.tscn")
const OUTPUT_DIR := "tmp/ui-review"
const TEST_DATABASE_ENV := "MIR_TROSSOV_DATABASE_PATH"
const TEST_DATABASE_PATH := "user://ui-review-screenshots.sqlite3"

const SCENARIOS := [
	{
		"name": "mobile-390x844-map",
		"size": Vector2i(390, 844),
		"section": "map",
	},
	{
		"name": "mobile-390x844-list",
		"size": Vector2i(390, 844),
		"section": "list",
	},
	{
		"name": "landscape-844x390-map",
		"size": Vector2i(844, 390),
		"section": "map",
	},
	{
		"name": "landscape-844x390-list",
		"size": Vector2i(844, 390),
		"section": "list",
	},
]


func _init() -> void:
	call_deferred("_capture_all")


func _capture_all() -> void:
	OS.set_environment(TEST_DATABASE_ENV, TEST_DATABASE_PATH)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT_DIR))

	var exit_code := OK
	for scenario in SCENARIOS:
		var error := await _capture_scenario(scenario)
		if error != OK:
			exit_code = error
			break

	OS.unset_environment(TEST_DATABASE_ENV)
	quit(exit_code)


func _capture_scenario(scenario: Dictionary) -> Error:
	var viewport := SubViewport.new()
	viewport.size = scenario["size"]
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)

	var screen: MainScreen = MainScene.instantiate()
	screen.size = Vector2(scenario["size"])
	viewport.add_child(screen)

	await process_frame
	await process_frame

	if scenario["section"] == "list":
		screen._show_section("list")
		await process_frame
		await process_frame

	var image := viewport.get_texture().get_image()
	if image == null:
		push_error("Failed to read UI review viewport image for %s." % scenario["name"])
		return ERR_CANT_CREATE
	var output_path := "%s/%s.png" % [OUTPUT_DIR, scenario["name"]]
	var error := image.save_png(output_path)

	viewport.remove_child(screen)
	screen.free()
	root.remove_child(viewport)
	viewport.free()

	if error != OK:
		push_error("Failed to save UI review screenshot %s: %s" % [output_path, error])
	return error
