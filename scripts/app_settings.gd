extends RefCounted
class_name AppSettings

const SETTINGS_PATH := "user://settings.cfg"
const SECTION_DISPLAY := "display"
const KEY_ORIENTATION := "orientation"

const ORIENTATION_SYSTEM := "system"
const ORIENTATION_PORTRAIT := "portrait"
const ORIENTATION_LANDSCAPE := "landscape"

var config: ConfigFile = ConfigFile.new()

static func orientation_options() -> Array[Dictionary]:
	return [
		{
			"id": ORIENTATION_SYSTEM,
			"title": "Как в системе",
			"display_server_orientation": DisplayServer.SCREEN_SENSOR,
		},
		{
			"id": ORIENTATION_PORTRAIT,
			"title": "Вертикальная",
			"display_server_orientation": DisplayServer.SCREEN_PORTRAIT,
		},
		{
			"id": ORIENTATION_LANDSCAPE,
			"title": "Горизонтальная",
			"display_server_orientation": DisplayServer.SCREEN_LANDSCAPE,
		},
	]

static func normalize_orientation(orientation_id: String) -> String:
	for option in orientation_options():
		if option.get("id", "") == orientation_id:
			return orientation_id

	return ORIENTATION_SYSTEM

static func display_server_orientation(orientation_id: String) -> int:
	var normalized_orientation := normalize_orientation(orientation_id)
	for option in orientation_options():
		if option.get("id", "") == normalized_orientation:
			return int(option.get("display_server_orientation", DisplayServer.SCREEN_SENSOR))

	return DisplayServer.SCREEN_SENSOR

func load_orientation() -> String:
	var load_result := config.load(SETTINGS_PATH)
	if load_result != OK and load_result != ERR_FILE_NOT_FOUND:
		push_warning("Не удалось загрузить настройки приложения: %s" % error_string(load_result))

	var saved_orientation := str(config.get_value(SECTION_DISPLAY, KEY_ORIENTATION, ORIENTATION_SYSTEM))
	return normalize_orientation(saved_orientation)

func save_orientation(orientation_id: String) -> void:
	config.set_value(SECTION_DISPLAY, KEY_ORIENTATION, normalize_orientation(orientation_id))
	var save_result := config.save(SETTINGS_PATH)
	if save_result != OK:
		push_warning("Не удалось сохранить настройки приложения: %s" % error_string(save_result))
