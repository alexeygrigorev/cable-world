extends SceneTree

const TEST_SCRIPT_PATHS: Array[String] = [
	"res://tests/godot_runtime_smoke.gd",
	"res://tests/godot_runtime_map_panel.gd",
	"res://tests/godot_runtime_app_shell.gd",
]
const TEST_SCRIPTS_ENV: String = "MIR_TROSSOV_GODOT_RUNTIME_TEST_SCRIPTS"

var failed_count: int = 0
var passed_count: int = 0


func _init() -> void:
	call_deferred("_run_all_tests")


func _run_all_tests() -> void:
	for test_script_path in _test_script_paths():
		_run_test_script(test_script_path)

	await process_frame

	if failed_count > 0:
		push_error("Godot runtime tests failed: %d failed, %d passed." % [failed_count, passed_count])
		quit(1)
		return

	print("Godot runtime tests passed: %d checks." % passed_count)
	quit(0)


func _test_script_paths() -> Array[String]:
	var env_paths := OS.get_environment(TEST_SCRIPTS_ENV)
	if env_paths.is_empty():
		return TEST_SCRIPT_PATHS

	var paths: Array[String] = []
	for raw_path in env_paths.split(",", false):
		var test_script_path := raw_path.strip_edges()
		if not test_script_path.is_empty():
			paths.append(test_script_path)
	return paths


func _run_test_script(test_script_path: String) -> void:
	var test_script := load(test_script_path)
	if test_script == null:
		_fail("%s: could not load test script." % test_script_path)
		return

	var test_instance: Object = test_script.new()
	if test_instance == null:
		_fail("%s: could not instantiate test script." % test_script_path)
		return

	var method_names := _test_method_names(test_instance)
	if method_names.is_empty():
		_fail("%s: no test_* methods found." % test_script_path)
		return

	for method_name in method_names:
		var result: Variant = test_instance.call(method_name)
		_record_result(test_script_path, String(method_name), result)


func _test_method_names(test_instance: Object) -> Array[StringName]:
	var method_names: Array[StringName] = []
	for method in test_instance.get_method_list():
		var method_name: StringName = method.get("name", &"")
		if String(method_name).begins_with("test_"):
			method_names.append(method_name)
	method_names.sort()
	return method_names


func _record_result(test_script_path: String, method_name: String, result: Variant) -> void:
	if result is bool:
		if result:
			_pass(test_script_path, method_name)
		else:
			_fail("%s:%s returned false." % [test_script_path, method_name])
		return

	if result is String:
		if String(result).is_empty():
			_pass(test_script_path, method_name)
		else:
			_fail("%s:%s\n%s" % [test_script_path, method_name, result])
		return

	if result is Array:
		var failures: Array = result
		if failures.is_empty():
			_pass(test_script_path, method_name)
		else:
			var failure_lines := PackedStringArray()
			for failure in failures:
				failure_lines.append(str(failure))
			_fail("%s:%s\n%s" % [test_script_path, method_name, "\n".join(failure_lines)])
		return

	if result == null:
		_pass(test_script_path, method_name)
		return

	_fail("%s:%s returned unsupported result type %s." % [test_script_path, method_name, type_string(typeof(result))])


func _pass(test_script_path: String, method_name: String) -> void:
	passed_count += 1
	print("PASS %s:%s" % [test_script_path, method_name])


func _fail(message: String) -> void:
	failed_count += 1
	push_error(message)
