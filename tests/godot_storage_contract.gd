extends SceneTree

const TEST_DATABASE_ENV: String = "MIR_TROSSOV_STORAGE_CONTRACT_DB"
const SQLiteStorageAdapterScript: GDScript = preload("res://scripts/storage/sqlite_storage_adapter.gd")

var failed: bool = false


func _init() -> void:
	var test_database_path := _test_database_path()
	var database_absolute_path := _database_absolute_path(test_database_path)
	_remove_database_files(database_absolute_path)

	var storage: RefCounted = SQLiteStorageAdapterScript.new()
	_expect(storage.is_runtime_available(), "SQLite runtime class must be available in Godot.")
	_expect_ok(storage.open(test_database_path), storage, "open")
	_expect(FileAccess.file_exists(test_database_path), "SQLite database file must be created.")
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

	_expect_ok(storage.open(test_database_path), storage, "reopen")
	_expect_ok(storage.migrate(), storage, "repeat migrate")
	_expect_ok(storage.seed_demo_objects(), storage, "repeat seed")
	visited_object = storage.get_object("berlin-gaerten-der-welt")
	_expect(visited_object.get("visit_status_id", "") == "favorite", "Favorite status must persist after reopen and repeat seed.")
	_expect(visited_object.get("operational_status", "") == initial_operational_status, "Operational status must persist after visit status changes and repeat seed.")
	_expect(visited_object.get("visited", false), "Favorite status must remain compatible with the visited field.")
	var gaerten_stations: Array[Dictionary] = storage.list_object_stations("berlin-gaerten-der-welt")
	_expect(gaerten_stations.size() == 3, "Gärten der Welt demo seed must expose three stations.")
	_expect(gaerten_stations[0].get("title", "") == "Киенбергпарк", "Station labels must be Russian display text.")
	var gaerten_directions: Array[Dictionary] = storage.list_route_directions("berlin-gaerten-der-welt")
	_expect(gaerten_directions.size() == 2, "Gärten der Welt demo seed must expose two travel directions.")
	_expect(gaerten_directions[0].get("direction_label", "") == "от Киенбергпарка к Садам мира", "Route direction must expose a Russian direction label.")
	var gaerten_segments: Array[Dictionary] = storage.list_route_segments("berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten")
	_expect(gaerten_segments.size() == 2, "Outbound direction must expose route segments for future UI.")
	_expect(gaerten_segments[0].get("direction_label", "") == "вверх к Волькенхайну", "Route segment must expose an up/down Russian label.")
	var demo_video: Dictionary = storage.get_media_asset("berlin-gaerten-der-welt-demo-video-kienbergpark-to-gaerten")
	_expect(demo_video.get("coordinate_source", "") == "manual", "Demo route video must expose manual coordinate source.")
	_expect(demo_video.get("route_direction_id", "") == "berlin-gaerten-der-welt-direction-kienbergpark-to-gaerten", "Demo route video must reference a route direction.")

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
		"transport_object_id": "moscow-vorobyovy-gory-cable-car",
		"visited_on": "2026-05-30 12:30",
		"title": "Контрактное посещение",
		"notes": "Проверка visit CRUD.",
		"impression_rating": 5,
	}), storage, "upsert_visit")
	_expect(storage.get_visit("godot-contract-visit").get("impression_rating", 0) == 5, "Visit CRUD must read inserted visit.")
	_expect(storage.list_visits("moscow-vorobyovy-gory-cable-car").size() >= 1, "Visit CRUD must list object visits.")
	var object_before_visit: Dictionary = storage.get_object("moscow-vorobyovy-gory-cable-car")
	storage.close()
	_expect_ok(storage.open(test_database_path), storage, "reopen after visit")
	_expect_ok(storage.migrate(), storage, "migrate after visit")
	_expect(storage.get_visit("godot-contract-visit").get("title", "") == "Контрактное посещение", "Visit CRUD must persist after reopen.")
	var object_after_visit: Dictionary = storage.get_object("moscow-vorobyovy-gory-cable-car")
	_expect(object_after_visit.get("visit_status_id", "") == object_before_visit.get("visit_status_id", ""), "Visit records must not alter family visit status.")
	_expect(object_after_visit.get("operational_status", "") == object_before_visit.get("operational_status", ""), "Visit records must not alter operational status.")
	_expect_ok(storage.delete_visit("godot-contract-visit"), storage, "delete_visit")
	_expect(storage.get_visit("godot-contract-visit").is_empty(), "Visit CRUD must delete inserted visit.")

	_expect_ok(storage.upsert_media_asset({
		"id": "godot-contract-photo",
		"transport_object_id": "moscow-vorobyovy-gory-cable-car",
		"kind": "photo",
		"local_path": "media/moscow-vorobyovy-gory-cable-car/godot-contract-photo.jpg",
		"caption": "Фото MVP: запись без копирования файла.",
		"latitude": 55.7103,
		"longitude": 37.5517,
		"coordinate_source": "manual",
		"geo_note": "Точка вручную поставлена у станции для проверки UI.",
	}), storage, "upsert_media_asset")
	_expect(storage.get_media_asset("godot-contract-photo").get("kind", "") == "photo", "MediaAsset CRUD must read inserted photo.")
	_expect(storage.get_media_asset("godot-contract-photo").get("coordinate_source", "") == "manual", "MediaAsset CRUD must preserve coordinate source.")
	_expect(storage.list_object_photos("moscow-vorobyovy-gory-cable-car").size() == 1, "MediaAsset CRUD must list object photos.")
	var object_with_photo: Dictionary = storage.get_object("moscow-vorobyovy-gory-cable-car")
	_expect(int(object_with_photo.get("photo_count", 0)) == 1, "TransportObject must expose photo_count from MediaAsset records.")
	_expect_ok(storage.delete_media_asset("godot-contract-photo"), storage, "delete_media_asset")
	_expect(storage.get_media_asset("godot-contract-photo").is_empty(), "MediaAsset CRUD must delete inserted photo.")

	_expect_ok(storage.upsert_visit({
		"id": "godot-contract-ticket-visit",
		"transport_object_id": "moscow-vorobyovy-gory-cable-car",
		"visited_on": "2026-05-30",
		"title": "Посещение с билетом",
	}), storage, "upsert_visit for ticket")
	_expect_ok(storage.upsert_media_asset({
		"id": "godot-contract-ticket-scan",
		"transport_object_id": "moscow-vorobyovy-gory-cable-car",
		"visit_id": "godot-contract-ticket-visit",
		"kind": "document",
		"local_path": "media/moscow-vorobyovy-gory-cable-car/godot-contract-ticket-scan.jpg",
		"caption": "Скан билета.",
	}), storage, "upsert_media_asset for ticket")
	_expect_ok(storage.upsert_ticket({
		"id": "godot-contract-ticket",
		"transport_object_id": "moscow-vorobyovy-gory-cable-car",
		"visit_id": "godot-contract-ticket-visit",
		"media_asset_id": "godot-contract-ticket-scan",
		"title": "Контрактный билет",
		"issued_on": "2026-05-30",
		"price_amount": 350.0,
		"price_currency": "RUB",
		"notes": "Локальная запись билета.",
	}), storage, "upsert_ticket")
	_expect(storage.get_ticket("godot-contract-ticket").get("title", "") == "Контрактный билет", "Ticket CRUD must read inserted ticket.")
	_expect(storage.list_tickets("moscow-vorobyovy-gory-cable-car").size() == 1, "Ticket CRUD must list object tickets.")
	_expect(storage.list_tickets("", "godot-contract-ticket-visit").size() == 1, "Ticket CRUD must list visit tickets.")
	_expect_ok(storage.upsert_ticket({
		"id": "godot-contract-ticket",
		"transport_object_id": "moscow-vorobyovy-gory-cable-car",
		"visit_id": "godot-contract-ticket-visit",
		"media_asset_id": "godot-contract-ticket-scan",
		"title": "Обновленный контрактный билет",
		"issued_on": "2026-05-30",
		"price_amount": 700.0,
		"price_currency": "RUB",
		"notes": "Обновленная локальная запись.",
	}), storage, "update_ticket")
	_expect(storage.get_ticket("godot-contract-ticket").get("title", "") == "Обновленный контрактный билет", "Ticket CRUD must update an existing ticket.")
	_expect_ok(storage.delete_visit("godot-contract-ticket-visit"), storage, "delete ticket visit")
	_expect(storage.get_ticket("godot-contract-ticket").has("visit_id") and storage.get_ticket("godot-contract-ticket").get("visit_id") == null, "Deleting a visit must keep the object ticket and clear visit_id.")
	_expect_ok(storage.delete_ticket("godot-contract-ticket"), storage, "delete_ticket")
	_expect(storage.get_ticket("godot-contract-ticket").is_empty(), "Ticket CRUD must delete inserted ticket.")
	_expect(storage.get_object("moscow-vorobyovy-gory-cable-car").get("photo_count", 0) == 0, "Ticket document must not change object photo_count.")

	storage.close()
	_remove_database_files(database_absolute_path)
	if failed:
		quit(1)
		return
	print("Godot SQLite storage contract passed.")
	quit(0)


func _test_database_path() -> String:
	var env_database_path := OS.get_environment(TEST_DATABASE_ENV)
	if not env_database_path.is_empty():
		return env_database_path
	return "user://storage-contract-test-%s.sqlite3" % OS.get_process_id()


func _database_absolute_path(database_path: String) -> String:
	if database_path.begins_with("user://") or database_path.begins_with("res://"):
		return ProjectSettings.globalize_path(database_path)
	return database_path


func _remove_database_files(database_absolute_path: String) -> void:
	for path in [
		database_absolute_path,
		"%s-wal" % database_absolute_path,
		"%s-shm" % database_absolute_path,
		"%s-journal" % database_absolute_path,
	]:
		if FileAccess.file_exists(path):
			var remove_error := DirAccess.remove_absolute(path)
			_expect(remove_error == OK or remove_error == ERR_FILE_NOT_FOUND, "Could not remove SQLite test file: %s" % path)


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
