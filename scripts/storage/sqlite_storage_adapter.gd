extends RefCounted
class_name SQLiteStorageAdapter

const DATABASE_PATH: String = "user://mir-trossov.sqlite3"
const MIGRATIONS_PATH: String = "res://scripts/storage/migrations"
const DEMO_SEED_PATH: String = "res://scripts/storage/seeds/demo_objects.sql"
const STATUS_NOT_VISITED: String = "not_visited"
const STATUS_PLANNED: String = "planned"
const STATUS_VISITED: String = "visited"
const STATUS_FAVORITE: String = "favorite"

var last_error: String = ""
var database: Object = null


func is_runtime_available() -> bool:
	return ClassDB.class_exists("SQLite")


func open(database_path: String = DATABASE_PATH) -> int:
	if not is_runtime_available():
		last_error = "SQLite runtime is unavailable on this platform."
		return ERR_UNAVAILABLE

	close()
	database = ClassDB.instantiate("SQLite")
	if database == null:
		last_error = "SQLite runtime class exists, but instance creation failed."
		return ERR_UNAVAILABLE

	database.set("path", database_path)
	database.set("foreign_keys", true)
	database.set("verbosity_level", 0)
	if not database.call("open_db"):
		last_error = _database_error()
		database = null
		return ERR_CANT_OPEN

	last_error = ""
	return OK


func close() -> void:
	if database != null:
		database.call("close_db")
		database = null


func migrate() -> int:
	if database == null:
		last_error = "SQLite database is not open."
		return ERR_UNCONFIGURED

	var migrations_dir := DirAccess.open(MIGRATIONS_PATH)
	if migrations_dir == null:
		last_error = "Cannot open migrations directory: %s" % MIGRATIONS_PATH
		return ERR_FILE_CANT_OPEN

	var migration_files: Array[String] = []
	migrations_dir.list_dir_begin()
	var file_name := migrations_dir.get_next()
	while file_name != "":
		if not migrations_dir.current_is_dir() and file_name.ends_with(".sql"):
			migration_files.append(file_name)
		file_name = migrations_dir.get_next()
	migrations_dir.list_dir_end()
	migration_files.sort()

	for migration_file in migration_files:
		var version := migration_file.get_basename()
		if _is_migration_applied(version):
			continue
		var migration_sql := _read_text("%s/%s" % [MIGRATIONS_PATH, migration_file])
		if migration_sql.is_empty() and not last_error.is_empty():
			return ERR_FILE_CANT_READ
		var migration_result := _execute(migration_sql)
		if migration_result != OK:
			return migration_result

	last_error = ""
	return OK


func seed_demo_objects() -> int:
	if database == null:
		last_error = "SQLite database is not open."
		return ERR_UNCONFIGURED

	var seed_sql := _read_text(DEMO_SEED_PATH)
	if seed_sql.is_empty() and not last_error.is_empty():
		return ERR_FILE_CANT_READ
	return _execute(seed_sql)


func list_objects() -> Array[Dictionary]:
	var rows := _query("""
		SELECT transport_objects.id,
		       transport_objects.title,
		       transport_objects.transport_type_id,
		       transport_objects.visit_status_id,
		       transport_types.title AS transport_type_title,
		       transport_objects.country,
		       transport_objects.region,
		       transport_objects.city,
		       transport_objects.latitude,
		       transport_objects.longitude,
		       transport_objects.description,
		       transport_objects.notes,
		       transport_objects.opened_year,
		       transport_objects.operator,
		       transport_objects.manufacturer,
		       transport_objects.created_at,
		       transport_objects.updated_at
		FROM transport_objects
		JOIN transport_types ON transport_types.id = transport_objects.transport_type_id
		ORDER BY transport_objects.title
	""")
	var objects: Array[Dictionary] = []
	for row in rows:
		objects.append(_row_to_app_object(row))
	return objects


func get_object(object_id: String) -> Dictionary:
	var rows := _query("""
		SELECT transport_objects.id,
		       transport_objects.title,
		       transport_objects.transport_type_id,
		       transport_objects.visit_status_id,
		       transport_types.title AS transport_type_title,
		       transport_objects.country,
		       transport_objects.region,
		       transport_objects.city,
		       transport_objects.latitude,
		       transport_objects.longitude,
		       transport_objects.description,
		       transport_objects.notes,
		       transport_objects.opened_year,
		       transport_objects.operator,
		       transport_objects.manufacturer,
		       transport_objects.created_at,
		       transport_objects.updated_at
		FROM transport_objects
		JOIN transport_types ON transport_types.id = transport_objects.transport_type_id
		WHERE transport_objects.id = ?
	""", [object_id])
	return {} if rows.is_empty() else _row_to_app_object(rows[0])


func upsert_object(data: Dictionary) -> int:
	var existing := get_object(data.get("id", ""))
	var now := _now()
	var created_at: String = data.get("created_at", existing.get("created_at", now))
	var updated_at: String = data.get("updated_at", now)
	return _execute_with_bindings("""
		INSERT INTO transport_objects (
			id, title, transport_type_id, visit_status_id, country, region, city,
			latitude, longitude, description, notes, opened_year, operator,
			manufacturer, created_at, updated_at
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(id) DO UPDATE SET
			title = excluded.title,
			transport_type_id = excluded.transport_type_id,
			visit_status_id = excluded.visit_status_id,
			country = excluded.country,
			region = excluded.region,
			city = excluded.city,
			latitude = excluded.latitude,
			longitude = excluded.longitude,
			description = excluded.description,
			notes = excluded.notes,
			opened_year = excluded.opened_year,
			operator = excluded.operator,
			manufacturer = excluded.manufacturer,
			updated_at = excluded.updated_at
	""", [
		data.get("id", ""),
		data.get("title", ""),
		data.get("transport_type_id", ""),
		data.get("visit_status_id", STATUS_NOT_VISITED),
		data.get("country", ""),
		data.get("region", null),
		data.get("city", null),
		data.get("latitude", 0.0),
		data.get("longitude", 0.0),
		data.get("description", ""),
		data.get("notes", ""),
		data.get("opened_year", null),
		data.get("operator", null),
		data.get("manufacturer", null),
		created_at,
		updated_at,
	])


func update_object_visited(object_id: String, visited: bool) -> int:
	return update_object_status(object_id, STATUS_VISITED if visited else STATUS_NOT_VISITED)


func update_object_status(object_id: String, visit_status_id: String) -> int:
	return _execute_with_bindings("""
		UPDATE transport_objects
		SET visit_status_id = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
		WHERE id = ?
	""", [normalized_status_id(visit_status_id), object_id])


static func normalized_status_id(visit_status_id: String) -> String:
	if visit_status_id == STATUS_NOT_VISITED:
		return STATUS_NOT_VISITED
	if visit_status_id == STATUS_PLANNED:
		return STATUS_PLANNED
	if visit_status_id == STATUS_VISITED:
		return STATUS_VISITED
	if visit_status_id == STATUS_FAVORITE:
		return STATUS_FAVORITE
	return STATUS_NOT_VISITED


static func status_is_visited(visit_status_id: String) -> bool:
	var normalized_status := normalized_status_id(visit_status_id)
	return normalized_status == STATUS_VISITED or normalized_status == STATUS_FAVORITE


static func status_title(visit_status_id: String) -> String:
	var normalized_status := normalized_status_id(visit_status_id)
	if normalized_status == STATUS_PLANNED:
		return "запланирован"
	if normalized_status == STATUS_VISITED:
		return "посещен"
	if normalized_status == STATUS_FAVORITE:
		return "любимый"
	return "не посещен"


static func status_ids() -> Array[String]:
	var ids: Array[String] = [
		STATUS_NOT_VISITED,
		STATUS_PLANNED,
		STATUS_VISITED,
		STATUS_FAVORITE,
	]
	return ids


func delete_object(object_id: String) -> int:
	return _execute_with_bindings("DELETE FROM transport_objects WHERE id = ?", [object_id])


func list_visits(object_id: String = "") -> Array[Dictionary]:
	if object_id.is_empty():
		return _query("""
			SELECT id, transport_object_id, visited_on, title, notes,
			       impression_rating, created_at, updated_at
			FROM visits
			ORDER BY visited_on, id
		""")
	return _query("""
		SELECT id, transport_object_id, visited_on, title, notes,
		       impression_rating, created_at, updated_at
		FROM visits
		WHERE transport_object_id = ?
		ORDER BY visited_on, id
	""", [object_id])


func get_visit(visit_id: String) -> Dictionary:
	var rows := _query("""
		SELECT id, transport_object_id, visited_on, title, notes,
		       impression_rating, created_at, updated_at
		FROM visits
		WHERE id = ?
	""", [visit_id])
	return {} if rows.is_empty() else rows[0]


func upsert_visit(data: Dictionary) -> int:
	var existing := get_visit(data.get("id", ""))
	var now := _now()
	var created_at: String = data.get("created_at", existing.get("created_at", now))
	var updated_at: String = data.get("updated_at", now)
	return _execute_with_bindings("""
		INSERT INTO visits (
			id, transport_object_id, visited_on, title, notes,
			impression_rating, created_at, updated_at
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(id) DO UPDATE SET
			transport_object_id = excluded.transport_object_id,
			visited_on = excluded.visited_on,
			title = excluded.title,
			notes = excluded.notes,
			impression_rating = excluded.impression_rating,
			updated_at = excluded.updated_at
	""", [
		data.get("id", ""),
		data.get("transport_object_id", ""),
		data.get("visited_on", ""),
		data.get("title", ""),
		data.get("notes", ""),
		data.get("impression_rating", null),
		created_at,
		updated_at,
	])


func delete_visit(visit_id: String) -> int:
	return _execute_with_bindings("DELETE FROM visits WHERE id = ?", [visit_id])


func _execute(sql: String) -> int:
	if database == null:
		last_error = "SQLite database is not open."
		return ERR_UNCONFIGURED
	if not database.call("query", sql):
		last_error = _database_error()
		return FAILED
	last_error = ""
	return OK


func _execute_with_bindings(sql: String, bindings: Array) -> int:
	if database == null:
		last_error = "SQLite database is not open."
		return ERR_UNCONFIGURED
	if not database.call("query_with_bindings", sql, bindings):
		last_error = _database_error()
		return FAILED
	last_error = ""
	return OK


func _query(sql: String, bindings: Array = []) -> Array[Dictionary]:
	var result := OK
	if bindings.is_empty():
		result = _execute(sql)
	else:
		result = _execute_with_bindings(sql, bindings)
	if result != OK:
		return []

	var rows: Array[Dictionary] = []
	for row in database.get("query_result"):
		rows.append(row)
	return rows


func _is_migration_applied(version: String) -> bool:
	var tables := _query("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'")
	if tables.is_empty():
		return false
	var rows := _query("SELECT version FROM schema_migrations WHERE version = ?", [version])
	return not rows.is_empty()


func _read_text(path: String) -> String:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		last_error = "Cannot read %s: %s" % [path, error_string(FileAccess.get_open_error())]
		return ""
	last_error = ""
	return file.get_as_text()


func _database_error() -> String:
	if database == null:
		return "SQLite database is not open."
	var message: String = database.get("error_message")
	return "SQLite query failed." if message.is_empty() else message


func _row_to_app_object(row: Dictionary) -> Dictionary:
	var latitude := float(row.get("latitude", 0.0))
	var longitude := float(row.get("longitude", 0.0))
	return {
		"id": row.get("id", ""),
		"name": row.get("title", ""),
		"kind": row.get("transport_type_title", row.get("transport_type_id", "")),
		"region": row.get("region", row.get("country", "")),
		"coordinates": Vector2(longitude, latitude),
		"description": row.get("description", ""),
		"visited": status_is_visited(str(row.get("visit_status_id", STATUS_NOT_VISITED))),
		"notes": row.get("notes", ""),
		"transport_type_id": row.get("transport_type_id", ""),
		"visit_status_id": row.get("visit_status_id", STATUS_NOT_VISITED),
		"country": row.get("country", ""),
		"city": row.get("city", ""),
		"latitude": latitude,
		"longitude": longitude,
		"opened_year": row.get("opened_year", null),
		"operator": row.get("operator", null),
		"manufacturer": row.get("manufacturer", null),
		"created_at": row.get("created_at", ""),
		"updated_at": row.get("updated_at", ""),
	}


func _now() -> String:
	var rows := _query("SELECT strftime('%Y-%m-%dT%H:%M:%fZ', 'now') AS now")
	return "" if rows.is_empty() else rows[0].get("now", "")
