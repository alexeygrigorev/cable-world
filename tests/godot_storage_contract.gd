extends SceneTree

const TEST_DATABASE_PATH: String = "user://storage-contract-test.sqlite3"
const SQLiteStorageAdapterScript: GDScript = preload("res://scripts/storage/sqlite_storage_adapter.gd")

var failed: bool = false


func _init() -> void:
	var database_absolute_path := ProjectSettings.globalize_path(TEST_DATABASE_PATH)
	if FileAccess.file_exists(TEST_DATABASE_PATH):
		DirAccess.remove_absolute(database_absolute_path)

	var storage: RefCounted = SQLiteStorageAdapterScript.new()
	_expect(storage.is_runtime_available(), "SQLite runtime class must be available in Godot.")
	_expect_ok(storage.open(TEST_DATABASE_PATH), storage, "open")
	_expect(FileAccess.file_exists(TEST_DATABASE_PATH), "SQLite database file must be created.")
	_expect_ok(storage.migrate(), storage, "migrate")
	_expect_ok(storage.seed_demo_objects(), storage, "seed")
	_expect(storage.list_objects().size() >= 3, "Demo seed must create transport objects.")
	var initial_operational_status: String = storage.get_object("berlin-gaerten-der-welt").get("operational_status", "")
	_expect(initial_operational_status == "active_seasonal", "Demo seed must set an operational status separately from visit status.")

	for status_id in ["not_visited", "planned", "visited", "favorite"]:
		_expect_ok(storage.update_object_status("berlin-gaerten-der-welt", status_id), storage, "update_object_status")
		var status_object: Dictionary = storage.get_object("berlin-gaerten-der-welt")
		_expect(status_object.get("visit_status_id", "") == status_id, "Visit status must transition to %s." % status_id)
		_expect(status_object.get("operational_status", "") == initial_operational_status, "Visit status changes must not alter operational status.")
	var visited_object: Dictionary = storage.get_object("berlin-gaerten-der-welt")
	_expect(visited_object.get("visited", false), "Favorite status must be treated as visited in the open database.")
	storage.close()

	_expect_ok(storage.open(TEST_DATABASE_PATH), storage, "reopen")
	_expect_ok(storage.migrate(), storage, "repeat migrate")
	_expect_ok(storage.seed_demo_objects(), storage, "repeat seed")
	visited_object = storage.get_object("berlin-gaerten-der-welt")
	_expect(visited_object.get("visit_status_id", "") == "favorite", "Favorite status must persist after reopen and repeat seed.")
	_expect(visited_object.get("operational_status", "") == initial_operational_status, "Operational status must persist after visit status changes and repeat seed.")
	_expect(visited_object.get("visited", false), "Favorite status must remain compatible with the visited field.")

	_expect_ok(storage.upsert_object({
		"id": "godot-contract-lift",
		"title": "Тестовый лифт",
		"transport_type_id": "elevator_vertical",
		"visit_status_id": "planned",
		"country": "Россия",
		"region": "Тестовый регион",
		"city": "Тестовый город",
		"latitude": 55.0,
		"longitude": 37.0,
		"description": "Проверка runtime CRUD.",
		"notes": "Создано headless-тестом.",
		"operational_status": "temporarily_closed_planned",
		"status_checked_at": "2026-05-30",
		"status_source_url": "https://example.test/status",
		"status_note": "Плановая проверка контрактного объекта.",
	}), storage, "upsert_object")
	_expect(storage.get_object("godot-contract-lift").get("name", "") == "Тестовый лифт", "Object CRUD must read inserted object.")
	_expect(storage.get_object("godot-contract-lift").get("operational_status", "") == "temporarily_closed_planned", "Object CRUD must map operational status.")
	_expect_ok(storage.delete_object("godot-contract-lift"), storage, "delete_object")
	_expect(storage.get_object("godot-contract-lift").is_empty(), "Object CRUD must delete inserted object.")

	_expect_ok(storage.upsert_visit({
		"id": "godot-contract-visit",
		"transport_object_id": "vorobyovy-gory",
		"visited_on": "2026-05-30",
		"title": "Контрактное посещение",
		"notes": "Проверка visit CRUD.",
		"impression_rating": 5,
	}), storage, "upsert_visit")
	_expect(storage.get_visit("godot-contract-visit").get("impression_rating", 0) == 5, "Visit CRUD must read inserted visit.")
	_expect(storage.list_visits("vorobyovy-gory").size() >= 1, "Visit CRUD must list object visits.")
	_expect_ok(storage.delete_visit("godot-contract-visit"), storage, "delete_visit")
	_expect(storage.get_visit("godot-contract-visit").is_empty(), "Visit CRUD must delete inserted visit.")

	_expect_ok(storage.upsert_media_asset({
		"id": "godot-contract-photo",
		"transport_object_id": "vorobyovy-gory",
		"kind": "photo",
		"local_path": "media/vorobyovy-gory/godot-contract-photo.jpg",
		"caption": "Фото MVP: запись без копирования файла.",
	}), storage, "upsert_media_asset")
	_expect(storage.get_media_asset("godot-contract-photo").get("kind", "") == "photo", "MediaAsset CRUD must read inserted photo.")
	_expect(storage.list_object_photos("vorobyovy-gory").size() == 1, "MediaAsset CRUD must list object photos.")
	var object_with_photo: Dictionary = storage.get_object("vorobyovy-gory")
	_expect(int(object_with_photo.get("photo_count", 0)) == 1, "TransportObject must expose photo_count from MediaAsset records.")
	_expect_ok(storage.delete_media_asset("godot-contract-photo"), storage, "delete_media_asset")
	_expect(storage.get_media_asset("godot-contract-photo").is_empty(), "MediaAsset CRUD must delete inserted photo.")

	storage.close()
	DirAccess.remove_absolute(database_absolute_path)
	if failed:
		quit(1)
		return
	print("Godot SQLite storage contract passed.")
	quit(0)


func _expect(condition: bool, message: String) -> void:
	if condition:
		return
	push_error(message)
	failed = true


func _expect_ok(result: int, storage: RefCounted, action: String) -> void:
	if result == OK:
		return
	push_error("%s failed: %s" % [action, storage.last_error])
	failed = true
