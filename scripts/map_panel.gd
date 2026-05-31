extends PanelContainer
class_name MapPanel

signal object_selected(index: int)

class OfflineMapLayer:
	extends Control

	var pan_offset := Vector2.ZERO
	var zoom := 1.0
	var geo_bounds: Dictionary = {}
	var map_scope := "germany"
	var reserved_label_rects: Array[Rect2] = []
	var draw_map_background := true
	var draw_city_labels := true
	var draw_terrain_labels := true
	var _germany_texture: Texture2D = null
	var _city_icon_textures: Dictionary = {}
	const LANDMARK_EDGE_MARGIN := 96.0
	const LANDMARK_VIEWPORT_MARGIN := 6.0
	const OVERLAY_CONTROL_SAFE_WIDTH := 242.0
	const OVERLAY_CONTROL_SAFE_HEIGHT := 78.0
	const SECONDARY_CITY_LABEL_ZOOM := 1.20
	const LANDMARK_VIEWPORT_REFERENCE_WIDTH := 390.0
	const LANDMARK_VIEWPORT_SCALE_MIN := 0.92
	const LANDMARK_VIEWPORT_SCALE_MAX := 1.30
	const CITY_LABELS := [
		{"name": "Hamburg", "coordinates": Vector2(9.9937, 53.5511), "kind": "city", "icon": "hamburg"},
		{"name": "Berlin", "coordinates": Vector2(13.4050, 52.5200), "kind": "capital", "icon": "berlin"},
		{"name": "Rostock", "coordinates": Vector2(12.0991, 54.0924), "kind": "city", "icon": "rostock"},
		{"name": "Köln", "coordinates": Vector2(6.9603, 50.9375), "kind": "city", "icon": "cologne"},
		{"name": "München", "coordinates": Vector2(11.5820, 48.1351), "kind": "city", "icon": "munich"},
		{"name": "Dresden", "coordinates": Vector2(13.7373, 51.0504), "kind": "city", "icon": "dresden"},
		{"name": "Stuttgart", "coordinates": Vector2(9.1829, 48.7758), "kind": "city", "icon": "stuttgart"},
		{"name": "Hannover", "coordinates": Vector2(9.7320, 52.3759), "kind": "town", "icon": ""},
		{"name": "Bremen", "coordinates": Vector2(8.8017, 53.0793), "kind": "town", "icon": ""},
		{"name": "Kiel", "coordinates": Vector2(10.1228, 54.3233), "kind": "town", "icon": ""},
		{"name": "Lübeck", "coordinates": Vector2(10.6866, 53.8655), "kind": "town", "icon": ""},
		{"name": "Düsseldorf", "coordinates": Vector2(6.7735, 51.2277), "kind": "town", "icon": "duesseldorf"},
		{"name": "Dortmund", "coordinates": Vector2(7.4653, 51.5136), "kind": "town", "icon": "dortmund"},
		{"name": "Essen", "coordinates": Vector2(7.0116, 51.4556), "kind": "town", "icon": ""},
		{"name": "Frankfurt", "coordinates": Vector2(8.6821, 50.1109), "kind": "town", "icon": "frankfurt"},
		{"name": "Leipzig", "coordinates": Vector2(12.3731, 51.3397), "kind": "town", "icon": ""},
		{"name": "Magdeburg", "coordinates": Vector2(11.6276, 52.1205), "kind": "town", "icon": ""},
		{"name": "Wolfsburg", "coordinates": Vector2(10.7865, 52.4227), "kind": "town", "icon": ""},
		{"name": "Kassel", "coordinates": Vector2(9.4797, 51.3127), "kind": "town", "icon": ""},
		{"name": "Erfurt", "coordinates": Vector2(11.0299, 50.9848), "kind": "town", "icon": ""},
		{"name": "Nürnberg", "coordinates": Vector2(11.0767, 49.4521), "kind": "town", "icon": ""},
		{"name": "Regensburg", "coordinates": Vector2(12.1016, 49.0134), "kind": "town", "icon": ""},
		{"name": "Augsburg", "coordinates": Vector2(10.8978, 48.3705), "kind": "town", "icon": ""},
		{"name": "Freiburg", "coordinates": Vector2(7.8421, 47.9990), "kind": "town", "icon": ""},
		{"name": "Saarbrücken", "coordinates": Vector2(6.9969, 49.2402), "kind": "town", "icon": ""},
	]
	const TERRAIN_LABELS := [
		{"name": "Harz", "coordinates": Vector2(10.56, 51.80)},
		{"name": "Zugspitze", "coordinates": Vector2(10.99, 47.43)},
		{"name": "Alpen", "coordinates": Vector2(11.70, 47.12)},
		{"name": "Müritz", "coordinates": Vector2(12.75, 53.43)},
		{"name": "Rügen", "coordinates": Vector2(13.38, 54.45)},
	]

	func _draw() -> void:
		if draw_map_background:
			var rect := Rect2(Vector2.ZERO, size)
			draw_rect(rect, Color("#c8dce8"))
			_draw_land_mass()
			if _germany_texture == null:
				_draw_graticule()
		if draw_city_labels or draw_terrain_labels:
			_draw_landmark_labels()

	func _map_point(point: Vector2) -> Vector2:
		return pan_offset + point * zoom

	func map_base_size() -> Vector2:
		return _map_base_size_for_viewport(size, geo_bounds)

	func _draw_graticule() -> void:
		if geo_bounds.is_empty():
			return

		var min_lon: float = floor(float(geo_bounds["min_longitude"]) / 10.0) * 10.0
		var max_lon: float = ceil(float(geo_bounds["max_longitude"]) / 10.0) * 10.0
		var min_lat: float = floor(float(geo_bounds["min_latitude"]) / 5.0) * 5.0
		var max_lat: float = ceil(float(geo_bounds["max_latitude"]) / 5.0) * 5.0

		var lon: float = min_lon
		while lon <= max_lon:
			var start: Vector2 = _geo_to_screen(Vector2(lon, float(geo_bounds["min_latitude"])))
			var finish: Vector2 = _geo_to_screen(Vector2(lon, float(geo_bounds["max_latitude"])))
			draw_line(start, finish, Color(0.62, 0.69, 0.65, 0.38), 1.0, true)
			lon += 10.0

		var lat: float = min_lat
		while lat <= max_lat:
			var start: Vector2 = _geo_to_screen(Vector2(float(geo_bounds["min_longitude"]), lat))
			var finish: Vector2 = _geo_to_screen(Vector2(float(geo_bounds["max_longitude"]), lat))
			draw_line(start, finish, Color(0.62, 0.69, 0.65, 0.38), 1.0, true)
			lat += 5.0

	func _draw_scale_bar() -> void:
		var bar_origin := Vector2(14.0, max(34.0, size.y - 28.0))
		var bar_width: float = clamp(size.x * 0.26 / max(zoom, 0.01), 54.0, 110.0) * zoom
		draw_line(bar_origin, bar_origin + Vector2(bar_width, 0.0), Color("#263b36"), 3.0, true)
		draw_line(bar_origin, bar_origin + Vector2(0.0, -6.0), Color("#263b36"), 2.0, true)
		draw_line(bar_origin + Vector2(bar_width, 0.0), bar_origin + Vector2(bar_width, -6.0), Color("#263b36"), 2.0, true)
		draw_string(get_theme_default_font(), bar_origin + Vector2(0.0, -8.0), "масштаб", HORIZONTAL_ALIGNMENT_LEFT, -1.0, 10, Color("#263b36"))

	func _draw_land_mass() -> void:
		if geo_bounds.is_empty() or size.x <= 0.0 or size.y <= 0.0:
			return
		if map_scope != "germany":
			return
		if _germany_texture == null:
			_germany_texture = load("res://assets/map/germany_styled.png")
		if _germany_texture == null:
			return
		var tex_rect := Rect2(_map_point(Vector2.ZERO), map_base_size() * zoom)
		draw_texture_rect(_germany_texture, tex_rect, false)
		draw_rect(tex_rect, Color(0.93, 0.82, 0.55, 0.10), true)

	func _draw_landmark_labels() -> void:
		var font := get_theme_default_font()
		var occupied_rects: Array[Rect2] = reserved_label_rects.duplicate()
		if draw_city_labels:
			for label_data in CITY_LABELS:
				_draw_city_label(font, label_data, occupied_rects)
		if draw_terrain_labels:
			for label_data in TERRAIN_LABELS:
				_draw_terrain_label(font, label_data, occupied_rects)

	func _draw_city_label(font: Font, label_data: Dictionary, occupied_rects: Array[Rect2]) -> void:
		var position := _geo_to_screen(label_data["coordinates"])
		if not _screen_point_near_viewport(position, LANDMARK_EDGE_MARGIN):
			return
		var is_capital := str(label_data.get("kind", "")) == "capital"
		var is_town := str(label_data.get("kind", "")) == "town"
		if is_town and zoom < SECONDARY_CITY_LABEL_ZOOM:
			return
		var label_size := 18 if is_capital else (12 if is_town else 15)
		var icon_rect := _city_icon_rect(label_data, position)
		var label_rect := Rect2()
		if icon_rect.size != Vector2.ZERO:
			var label_baseline_y := icon_rect.position.y + icon_rect.size.y + 4.0 * zoom
			label_rect = _centered_label_rect(font, str(label_data["name"]), icon_rect.get_center().x, label_baseline_y, label_size)
		else:
			label_rect = _centered_label_rect(font, str(label_data["name"]), position.x, position.y + 12.0 * zoom, label_size)
		var occupied_rect := label_rect if icon_rect.size == Vector2.ZERO else icon_rect.merge(label_rect)
		if is_town and _rect_overlaps_any(occupied_rect, occupied_rects):
			return
		if icon_rect.size != Vector2.ZERO:
			_draw_city_icon(label_data, icon_rect)
		_draw_label_text(font, str(label_data["name"]), label_rect.position + Vector2(0.0, label_rect.size.y), label_size, Color("#f6df9b"), Color(0.11, 0.07, 0.03, 0.90))
		occupied_rects.append(occupied_rect)

	func _city_icon_rect(label_data: Dictionary, position: Vector2) -> Rect2:
		var icon_id := str(label_data.get("icon", ""))
		if icon_id.is_empty():
			return Rect2()
		var texture: Texture2D = _city_icon_texture(icon_id)
		if texture == null:
			return Rect2()
		var icon_size: float = clamp(54.0 * _landmark_visual_scale(), 46.0, 88.0)
		var icon_rect := Rect2(
			position + Vector2(-icon_size * 0.5, -icon_size - 9.0 * zoom),
			Vector2(icon_size, icon_size)
		)
		return icon_rect

	func _draw_city_icon(label_data: Dictionary, icon_rect: Rect2) -> void:
		var texture: Texture2D = _city_icon_texture(str(label_data.get("icon", "")))
		if texture != null:
			draw_texture_rect(texture, icon_rect, false)

	func _city_icon_texture(icon_id: String) -> Texture2D:
		if not _city_icon_textures.has(icon_id):
			var path := "res://assets/sprites/city_landmarks/outlined/city_%s.png" % icon_id
			_city_icon_textures[icon_id] = load(path) if ResourceLoader.exists(path) else null
		return _city_icon_textures.get(icon_id, null)

	func _draw_terrain_label(font: Font, label_data: Dictionary, occupied_rects: Array[Rect2]) -> void:
		var position := _geo_to_screen(label_data["coordinates"])
		if not _screen_point_near_viewport(position, LANDMARK_EDGE_MARGIN):
			return
		var text_pos := position + Vector2(7.0, -5.0) * zoom
		var label_rect := _left_label_rect(font, str(label_data["name"]), text_pos, 14)
		if _rect_overlaps_any(label_rect, occupied_rects):
			return
		_draw_label_text(font, str(label_data["name"]), text_pos, 14, Color("#efe2bd"), Color(0.12, 0.08, 0.04, 0.78))
		occupied_rects.append(label_rect)

	func _screen_point_near_viewport(position: Vector2, margin: float) -> bool:
		return position.x >= -margin \
			and position.x <= size.x + margin \
			and position.y >= -margin \
			and position.y <= size.y + margin

	func _clamp_landmark_rect(rect: Rect2) -> Rect2:
		var clamped_position := rect.position
		clamped_position.x = clamp(
			clamped_position.x,
			LANDMARK_VIEWPORT_MARGIN,
			max(LANDMARK_VIEWPORT_MARGIN, size.x - rect.size.x - LANDMARK_VIEWPORT_MARGIN)
		)
		clamped_position.y = clamp(
			clamped_position.y,
			LANDMARK_VIEWPORT_MARGIN,
			max(LANDMARK_VIEWPORT_MARGIN, size.y - rect.size.y - LANDMARK_VIEWPORT_MARGIN)
		)
		var clamped_rect := Rect2(clamped_position, rect.size)
		var overlay_rect := _top_right_overlay_rect()
		if clamped_rect.intersects(overlay_rect, true):
			var left_position := overlay_rect.position.x - rect.size.x - LANDMARK_VIEWPORT_MARGIN
			if left_position >= LANDMARK_VIEWPORT_MARGIN:
				clamped_rect.position.x = left_position
			else:
				clamped_rect.position.y = overlay_rect.end.y + LANDMARK_VIEWPORT_MARGIN
		return clamped_rect

	func _top_right_overlay_rect() -> Rect2:
		return Rect2(
			Vector2(max(0.0, size.x - OVERLAY_CONTROL_SAFE_WIDTH), 0.0),
			Vector2(OVERLAY_CONTROL_SAFE_WIDTH, OVERLAY_CONTROL_SAFE_HEIGHT)
		)

	func _rect_overlaps_any(rect: Rect2, occupied_rects: Array[Rect2]) -> bool:
		var padded_rect := rect.grow(3.0)
		for occupied_rect in occupied_rects:
			if padded_rect.intersects(occupied_rect.grow(3.0), true):
				return true
		return false

	func _landmark_visual_scale() -> float:
		var viewport_width: float = max(1.0, size.x)
		var viewport_scale: float = clamp(sqrt(viewport_width / LANDMARK_VIEWPORT_REFERENCE_WIDTH), LANDMARK_VIEWPORT_SCALE_MIN, LANDMARK_VIEWPORT_SCALE_MAX)
		return sqrt(max(zoom, 0.75)) * viewport_scale

	func _draw_label_text(font: Font, text: String, position: Vector2, font_size: int, text_color: Color, shadow_color: Color) -> void:
		var scaled_size := int(clamp(float(font_size) * sqrt(max(zoom, 0.65)), 12.0, 24.0))
		var shadow_offset := Vector2(1.7, 1.7)
		draw_string(font, position + Vector2(-1.3, 0.0), text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, scaled_size, shadow_color)
		draw_string(font, position + Vector2(1.3, 0.0), text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, scaled_size, shadow_color)
		draw_string(font, position + Vector2(0.0, -1.3), text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, scaled_size, shadow_color)
		draw_string(font, position + Vector2(0.0, 1.3), text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, scaled_size, shadow_color)
		draw_string(font, position + shadow_offset, text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, scaled_size, shadow_color)
		draw_string(font, position, text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, scaled_size, text_color)

	func _centered_label_rect(font: Font, text: String, center_x: float, baseline_y: float, font_size: int) -> Rect2:
		var scaled_size := int(clamp(float(font_size) * sqrt(max(zoom, 0.65)), 12.0, 24.0))
		var text_size := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, scaled_size)
		var position := Vector2(center_x - text_size.x * 0.5, baseline_y)
		return Rect2(position - Vector2(0.0, float(scaled_size)), text_size + Vector2(0.0, float(scaled_size)))

	func _left_label_rect(font: Font, text: String, baseline_position: Vector2, font_size: int) -> Rect2:
		var scaled_size := int(clamp(float(font_size) * sqrt(max(zoom, 0.65)), 12.0, 24.0))
		var text_size := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, scaled_size)
		return Rect2(baseline_position - Vector2(0.0, float(scaled_size)), text_size + Vector2(0.0, float(scaled_size)))

	func _draw_centered_label_text(font: Font, text: String, center_x: float, baseline_y: float, font_size: int, text_color: Color, shadow_color: Color) -> void:
		var label_rect := _centered_label_rect(font, text, center_x, baseline_y, font_size)
		var position := label_rect.position + Vector2(0.0, label_rect.size.y)
		_draw_label_text(font, text, position, font_size, text_color, shadow_color)

	func _geo_to_screen(coordinates: Vector2) -> Vector2:
		return _map_point(_project_coordinates(coordinates, geo_bounds, map_base_size()))

	static func _map_base_size_for_viewport(viewport_size: Vector2, bounds: Dictionary) -> Vector2:
		if viewport_size.x <= 0.0 or viewport_size.y <= 0.0 or bounds.is_empty():
			return viewport_size

		var aspect := _projected_aspect(bounds)
		var viewport_aspect := viewport_size.x / viewport_size.y
		if viewport_aspect > aspect:
			return Vector2(viewport_size.x, viewport_size.x / aspect)
		return Vector2(viewport_size.y * aspect, viewport_size.y)

	static func _projected_aspect(bounds: Dictionary) -> float:
		var min_longitude: float = float(bounds["min_longitude"])
		var max_longitude: float = float(bounds["max_longitude"])
		var min_latitude: float = float(bounds["min_latitude"])
		var max_latitude: float = float(bounds["max_latitude"])
		var longitude_span: float = max(0.000001, deg_to_rad(max_longitude - min_longitude))
		var min_mercator_y: float = _mercator_y(min_latitude)
		var max_mercator_y: float = _mercator_y(max_latitude)
		var mercator_span: float = max(0.000001, max_mercator_y - min_mercator_y)
		return longitude_span / mercator_span

	static func _project_coordinates(coordinates: Vector2, bounds: Dictionary, map_size: Vector2) -> Vector2:
		if bounds.is_empty():
			return Vector2.ZERO

		var min_longitude: float = float(bounds["min_longitude"])
		var max_longitude: float = float(bounds["max_longitude"])
		var min_latitude: float = float(bounds["min_latitude"])
		var max_latitude: float = float(bounds["max_latitude"])
		var longitude_span: float = max(0.000001, max_longitude - min_longitude)
		var min_mercator_y: float = _mercator_y(min_latitude)
		var max_mercator_y: float = _mercator_y(max_latitude)
		var mercator_span: float = max(0.000001, max_mercator_y - min_mercator_y)
		var x_ratio: float = (coordinates.x - min_longitude) / longitude_span
		var y_ratio: float = (max_mercator_y - _mercator_y(coordinates.y)) / mercator_span
		return Vector2(x_ratio * map_size.x, y_ratio * map_size.y)

	static func _mercator_y(latitude: float) -> float:
		var clamped_latitude: float = clamp(latitude, -85.0, 85.0)
		var radians: float = deg_to_rad(clamped_latitude)
		return log(tan(PI / 4.0 + radians / 2.0))

const MARKER_SIZE := Vector2(44.0, 44.0)
const ICON_MARKER_SIZE := Vector2(52.0, 52.0)
const MARKER_ZOOM_SIZE_MIN := 48.0
const MARKER_ZOOM_SIZE_MAX := 78.0
const CLUSTER_MARKER_ZOOM_SIZE_MAX := 70.0
const ICON_VIEWPORT_REFERENCE_WIDTH := 390.0
const ICON_VIEWPORT_SCALE_MIN := 0.92
const ICON_VIEWPORT_SCALE_MAX := 1.30
const MAP_MIN_HEIGHT := 360.0
const MAP_VIEW_HEIGHT := 720.0
const MAP_LANDSCAPE_MIN_HEIGHT := 320.0
const MAP_PADDING := 24.0
const MARKER_SPREAD_DISTANCE := 58.0
const MARKER_SPREAD_STEP := 42.0
const MARKER_LOCAL_CLUSTER_DISTANCE := 44.0
const MARKER_LOCAL_CLUSTER_RADIUS := 28.0
const OBJECT_CLUSTER_ZOOM_THRESHOLD := 1.45
const OBJECT_CLUSTER_SCREEN_DISTANCE := 118.0
const SELECTED_NAME_LIMIT := 42
const MAP_FILTER_ALL := "all"
const MAP_FILTER_VISITED := "visited"
const MAP_FILTER_NOT_VISITED := "not_visited"
const MAP_SCOPE_GERMANY := "germany"
const MAP_SCOPE_ALL := "all"
const GERMANY_INITIAL_FOCUS_COORDINATES := Vector2(10.70, 51.45)
const TRANSPORT_TYPE_ICON := {
	"cable_gondola": "icon_cable_gondola",
	"cable_aerial_tram": "icon_aerial_tram",
	"cable_urban": "icon_cable_gondola",
	"cable_tourist": "icon_cable_gondola",
	"funicular_classic": "icon_funicular",
	"funicular_water": "icon_funicular",
	"funicular_modern": "icon_funicular",
	"rail_cog": "icon_cog_railway",
	"rail_mountain": "icon_cog_railway",
	"rail_suspended": "icon_suspended_monorail",
	"elevator_vertical": "icon_elevator",
	"elevator_inclined": "icon_elevator",
	"elevator_panoramic": "icon_elevator",
	"suspended_train": "icon_suspended_monorail",
	"monorail": "icon_suspended_monorail",
	"suspended_ferry": "icon_suspended_monorail",
	"escalator_unusual": "icon_station",
	"special_transport_system": "icon_station",
	"unique_engineering_object": "icon_station",
}
const MIN_ZOOM := 0.5
const MAX_ZOOM := 1.5
const ZOOM_STEP := 1.25
const DEFAULT_ZOOM := 1.10
const DEFAULT_LANDSCAPE_ZOOM := 1.0
const MAP_CONTROL_SIZE := Vector2(48.0, 48.0)
const FIT_CONTROL_SIZE := Vector2(48.0, 48.0)
const PAN_LIMIT_PADDING := 72.0
const PAN_DRAG_SCALE := 0.22
const DRAG_TAP_SUPPRESS_DISTANCE := 10.0

var objects: Array[Dictionary] = []
var selected_index: int = -1
var marker_buttons: Array[Button] = []
var pan_offset := Vector2.ZERO
var zoom := 1.0
var map_filter := MAP_FILTER_ALL
var map_scope := MAP_SCOPE_GERMANY
var map_layer: Control
var map_label_layer: Control
var map_content: Control
var empty_state_label: Label
var summary_label: Label
var zoom_controls: HBoxContainer
var zoom_percent_label: Label
var filter_controls: HBoxContainer
var filter_buttons: Dictionary = {}
var dragging := false
var drag_distance := 0.0
var suppress_next_marker_press := false
var active_touch_index := -1
var last_touch_positions: Dictionary = {}
var marker_icons: Dictionary = {}
var map_view_initialized := false

func _ready() -> void:
	custom_minimum_size.y = max(custom_minimum_size.y, MAP_MIN_HEIGHT)
	var panel_style := StyleBoxFlat.new()
	panel_style.bg_color = Color(1.0, 1.0, 1.0, 0.0)
	panel_style.border_color = Color(1.0, 1.0, 1.0, 0.0)
	panel_style.set_border_width_all(0)
	panel_style.set_corner_radius_all(0)
	add_theme_stylebox_override("panel", panel_style)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 0)
	margin.add_theme_constant_override("margin_top", 0)
	margin.add_theme_constant_override("margin_right", 0)
	margin.add_theme_constant_override("margin_bottom", 0)
	add_child(margin)

	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 4)
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.size_flags_vertical = Control.SIZE_EXPAND_FILL
	margin.add_child(rows)

	summary_label = Label.new()
	summary_label.text = "Карта объектов"
	summary_label.add_theme_color_override("font_color", Color("#24332f"))
	summary_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	summary_label.visible = false

	map_layer = OfflineMapLayer.new()
	map_layer.name = "ТочкиОбъектов"
	map_layer.set("draw_city_labels", false)
	map_layer.set("draw_terrain_labels", true)
	map_layer.custom_minimum_size = Vector2(0.0, MAP_VIEW_HEIGHT)
	map_layer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	map_layer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	map_layer.clip_contents = true
	map_layer.mouse_filter = Control.MOUSE_FILTER_STOP
	map_layer.gui_input.connect(_on_map_layer_gui_input)
	map_layer.resized.connect(_on_map_layer_resized)
	rows.add_child(map_layer)
	resized.connect(_sync_map_canvas_height)

	map_content = Control.new()
	map_content.name = "ПодвижнаяКарта"
	map_content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	map_layer.add_child(map_content)

	map_label_layer = OfflineMapLayer.new()
	map_label_layer.name = "ПодписиГородов"
	map_label_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	map_label_layer.set("draw_map_background", false)
	map_label_layer.set("draw_city_labels", true)
	map_label_layer.set("draw_terrain_labels", false)
	map_label_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	map_layer.add_child(map_label_layer)

	empty_state_label = Label.new()
	empty_state_label.text = "Нет точек с координатами"
	empty_state_label.add_theme_color_override("font_color", Color("#24332f"))
	empty_state_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	empty_state_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	empty_state_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	empty_state_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	map_layer.add_child(empty_state_label)

	var toolbar := HBoxContainer.new()
	toolbar.name = "ПанельИнструментов"
	toolbar.visible = false
	toolbar.add_theme_constant_override("separation", 6)
	toolbar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_child(toolbar)

	filter_controls = HBoxContainer.new()
	filter_controls.name = "ФильтрКарты"
	filter_controls.add_theme_constant_override("separation", 6)
	toolbar.add_child(filter_controls)
	_add_filter_button(filter_controls, "Все", MAP_FILTER_ALL)
	_add_filter_button(filter_controls, "✓", MAP_FILTER_VISITED)
	_add_filter_button(filter_controls, "○", MAP_FILTER_NOT_VISITED)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	toolbar.add_child(spacer)

	zoom_controls = HBoxContainer.new()
	zoom_controls.name = "МасштабКарты"
	zoom_controls.add_theme_constant_override("separation", 6)
	zoom_controls.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	zoom_controls.offset_left = -228.0
	zoom_controls.offset_top = 12.0
	zoom_controls.offset_right = -12.0
	zoom_controls.offset_bottom = 60.0
	map_layer.add_child(zoom_controls)
	_add_zoom_percent_label(zoom_controls)
	_add_zoom_button(zoom_controls, "-", 1.0 / ZOOM_STEP)
	_add_zoom_button(zoom_controls, "+", ZOOM_STEP)
	_add_fit_button(zoom_controls)

	_refresh_markers()
	call_deferred("_sync_map_canvas_height")
	call_deferred("_reset_map_view")

func set_objects(next_objects: Array[Dictionary]) -> void:
	objects = next_objects
	map_scope = MAP_SCOPE_GERMANY if _has_germany_object() else MAP_SCOPE_ALL
	if is_node_ready():
		_refresh_markers()

func select_object(index: int) -> void:
	selected_index = index if index >= 0 and index < objects.size() else -1
	if is_node_ready():
		_refresh_marker_styles()

func set_map_filter(next_filter: String) -> void:
	if next_filter == MAP_FILTER_VISITED:
		map_filter = MAP_FILTER_VISITED
	elif next_filter == MAP_FILTER_NOT_VISITED:
		map_filter = MAP_FILTER_NOT_VISITED
	else:
		map_filter = MAP_FILTER_ALL

	if is_node_ready():
		_refresh_filter_buttons()
		_refresh_marker_styles()
		_update_summary_label()
		_update_empty_state()

func _refresh_markers() -> void:
	if map_layer == null:
		return

	for marker in marker_buttons:
		marker.queue_free()
	marker_buttons.clear()

	for index in objects.size():
		if not _has_coordinates(objects[index]):
			continue

		var marker := Button.new()
		marker.name = "Маркер%d" % (index + 1)
		marker.custom_minimum_size = ICON_MARKER_SIZE
		marker.size = ICON_MARKER_SIZE
		marker.toggle_mode = true
		marker.focus_mode = Control.FOCUS_ALL
		marker.mouse_filter = Control.MOUSE_FILTER_PASS
		marker.add_theme_font_size_override("font_size", 18)
		marker.icon = _icon_for_object(objects[index])
		marker.expand_icon = true
		marker.tooltip_text = "Выбрать объект: %s" % objects[index].get("name", "без названия")
		marker.set_meta("object_index", index)
		marker.gui_input.connect(_on_marker_gui_input)
		marker.pressed.connect(_on_marker_pressed.bind(index))
		map_content.add_child(marker)
		marker_buttons.append(marker)

	_refresh_filter_buttons()
	_refresh_marker_styles()
	_update_summary_label()
	_update_empty_state()
	_update_map_reference_data()
	_position_markers()

func _sync_map_canvas_height() -> void:
	if map_layer == null:
		return

	var target_height := MAP_VIEW_HEIGHT
	if size.y > 0.0:
		var available_height: float = max(1.0, size.y)
		if size.x > size.y:
			target_height = max(MAP_LANDSCAPE_MIN_HEIGHT, available_height)
		else:
			target_height = max(MAP_LANDSCAPE_MIN_HEIGHT, available_height)
	map_layer.custom_minimum_size.y = target_height
	custom_minimum_size.y = target_height

func _on_map_layer_resized() -> void:
	map_layer.queue_redraw()
	if map_content != null:
		map_content.size = map_layer.size
	if map_label_layer != null:
		map_label_layer.size = map_layer.size
	if empty_state_label != null:
		empty_state_label.size = map_layer.size
	_update_map_reference_data()
	if not map_view_initialized:
		_reset_map_view()
	else:
		_apply_map_transform()
	_position_markers()

func _position_markers() -> void:
	if map_layer == null:
		return

	var bounds := _active_coordinate_bounds()
	if bounds.is_empty():
		return

	var clusters := _marker_clusters(bounds)
	var base_positions: Array[Vector2] = []
	var reserved_rects: Array[Rect2] = []

	for marker_number in marker_buttons.size():
		var marker := marker_buttons[marker_number]
		var index := int(marker.get_meta("object_index", -1))
		if index < 0 or index >= objects.size():
			continue

		marker.set_meta("cluster_indices", PackedInt32Array([index]))
		marker.set_meta("cluster_center", Vector2.ZERO)
		marker.set_meta("is_cluster_marker", false)
		marker.visible = _object_matches_filter(objects[index])
		marker.button_pressed = index == selected_index
		marker.text = ""
		marker.add_theme_font_size_override("font_size", 20)
		marker.add_theme_color_override("font_color", Color("#ffffff") if index == selected_index else Color("#10231f"))
		marker.add_theme_color_override("font_pressed_color", Color("#ffffff"))
		var is_cluster_marker := clusters.has(index)
		var marker_size := _marker_visual_size(is_cluster_marker)
		_apply_marker_visual_size(marker, marker_size)
		_apply_marker_style(marker, index == selected_index)
		marker.tooltip_text = "%s: %s" % [
			"Выбранный объект" if index == selected_index else "Выбрать объект",
			objects[index].get("name", "без названия")
		]
		var coordinates := _object_coordinates(objects[index])
		var layer := map_layer as OfflineMapLayer
		var map_size := layer.map_base_size()
		var base_position := OfflineMapLayer._project_coordinates(coordinates, bounds, map_size)
		if clusters.has(index):
			var cluster: Dictionary = clusters[index]
			var cluster_indices: PackedInt32Array = cluster["indices"]
			var is_representative := int(cluster_indices[0]) == index
			marker.visible = is_representative and _object_matches_filter(objects[index])
			if not is_representative:
				continue
			base_position = cluster["center"]
			marker.set_meta("cluster_indices", cluster_indices)
			marker.set_meta("cluster_center", base_position)
			marker.set_meta("is_cluster_marker", cluster_indices.size() > 1)
			marker_size = _marker_visual_size(cluster_indices.size() > 1)
			_apply_marker_visual_size(marker, marker_size)
			_apply_cluster_marker_style(marker, cluster_indices)

		if not _coordinates_inside_bounds(coordinates, bounds):
			marker.position = _map_point_to_screen(base_position, marker_size)
			if marker.visible:
				reserved_rects.append(Rect2(marker.position, marker.size).grow(6.0))
			continue
		var local_position := _local_cluster_marker_position(base_position, base_positions)
		var clamped_position := Vector2(
			clamp(local_position.x, MAP_PADDING, max(MAP_PADDING, map_size.x - MAP_PADDING)),
			clamp(local_position.y, MAP_PADDING, max(MAP_PADDING, map_size.y - MAP_PADDING))
		)
		marker.position = _map_point_to_screen(clamped_position, marker_size)
		base_positions.append(base_position)
		if marker.visible:
			reserved_rects.append(Rect2(marker.position, marker.size).grow(6.0))
	_update_reserved_label_rects(reserved_rects)

func _update_reserved_label_rects(rects: Array[Rect2]) -> void:
	if map_layer == null:
		return
	var layer := map_layer as OfflineMapLayer
	layer.reserved_label_rects = rects
	layer.queue_redraw()
	if map_label_layer != null:
		map_label_layer.queue_redraw()

func _marker_clusters(bounds: Dictionary) -> Dictionary:
	var result := {}
	if zoom >= OBJECT_CLUSTER_ZOOM_THRESHOLD:
		return result
	if map_layer == null:
		return result

	var layer := map_layer as OfflineMapLayer
	var map_size := layer.map_base_size()
	var cluster_list: Array[Dictionary] = []
	for marker in marker_buttons:
		var index := int(marker.get_meta("object_index", -1))
		if index < 0 or index >= objects.size():
			continue
		if not _object_matches_filter(objects[index]):
			continue
		var coordinates := _object_coordinates(objects[index])
		if not _coordinates_inside_bounds(coordinates, bounds):
			continue
		var base_position := OfflineMapLayer._project_coordinates(coordinates, bounds, map_size)
		var cluster: Dictionary = _nearest_cluster(cluster_list, base_position)
		if cluster.is_empty():
			cluster_list.append({
				"indices": PackedInt32Array([index]),
				"center": base_position,
			})
		else:
			var indices: PackedInt32Array = cluster["indices"]
			var old_count := indices.size()
			indices.append(index)
			cluster["indices"] = indices
			cluster["center"] = (Vector2(cluster["center"]) * float(old_count) + base_position) / float(old_count + 1)

	for cluster in cluster_list:
		var indices: PackedInt32Array = cluster["indices"]
		if indices.size() <= 1:
			continue
		for index in indices:
			result[int(index)] = cluster
	return result

func _nearest_cluster(cluster_list: Array[Dictionary], position: Vector2) -> Dictionary:
	for cluster in cluster_list:
		var distance: float = position.distance_to(Vector2(cluster["center"])) * zoom
		if distance <= OBJECT_CLUSTER_SCREEN_DISTANCE:
			return cluster
	return {}

func _refresh_marker_styles() -> void:
	for marker in marker_buttons:
		var index := int(marker.get_meta("object_index", -1))
		marker.visible = _object_matches_filter(objects[index]) if index >= 0 and index < objects.size() else false
		var is_selected := index == selected_index
		marker.set_meta("is_cluster_marker", false)
		marker.button_pressed = is_selected
		marker.text = ""
		marker.add_theme_font_size_override("font_size", 20)
		marker.add_theme_color_override("font_color", Color("#ffffff") if is_selected else Color("#10231f"))
		marker.add_theme_color_override("font_pressed_color", Color("#ffffff"))
		_apply_marker_style(marker, is_selected)
		marker.tooltip_text = "%s: %s" % [
			"Выбранный объект" if is_selected else "Выбрать объект",
			objects[index].get("name", "без названия") if index >= 0 and index < objects.size() else "без названия"
		]
	_position_markers()

func _update_summary_label() -> void:
	if summary_label == null:
		return

	if objects.is_empty():
		summary_label.text = "Карта объектов: пока нет точек"
		return

	var visible_count := _visible_marker_count()
	summary_label.text = "Карта объектов: %d из %d точек" % [visible_count, marker_buttons.size()]

func _update_empty_state() -> void:
	if empty_state_label == null:
		return

	empty_state_label.visible = marker_buttons.is_empty() or _visible_marker_count() == 0
	empty_state_label.text = "Нет точек с координатами" if marker_buttons.is_empty() else "Нет точек для выбранного фильтра"
	empty_state_label.size = map_layer.size if map_layer != null else Vector2.ZERO

func _spread_marker_position(base_position: Vector2, placed_positions: Array[Vector2], map_size: Vector2) -> Vector2:
	if _is_clear_marker_position(base_position, placed_positions):
		return base_position

	var max_position := Vector2(
		max(MAP_PADDING, map_size.x - MAP_PADDING),
		max(MAP_PADDING, map_size.y - MAP_PADDING)
	)
	for attempt in 32:
		var angle: float = TAU * float(attempt % 8) / 8.0
		var ring: float = 1.0 + floor(float(attempt) / 8.0)
		var candidate: Vector2 = base_position + Vector2(cos(angle), sin(angle)) * MARKER_SPREAD_STEP * ring
		candidate = Vector2(
			clamp(candidate.x, MAP_PADDING, max_position.x),
			clamp(candidate.y, MAP_PADDING, max_position.y)
		)
		if _is_clear_marker_position(candidate, placed_positions):
			return candidate

	return base_position

func _is_clear_marker_position(position: Vector2, placed_positions: Array[Vector2]) -> bool:
	for placed_position in placed_positions:
		if position.distance_to(placed_position) < MARKER_SPREAD_DISTANCE:
			return false
	return true

func _local_cluster_marker_position(base_position: Vector2, base_positions: Array[Vector2]) -> Vector2:
	var nearby_count := 0
	for placed_position in base_positions:
		if base_position.distance_to(placed_position) < MARKER_LOCAL_CLUSTER_DISTANCE:
			nearby_count += 1
	if nearby_count == 0:
		return base_position
	var angle := TAU * float(nearby_count - 1) / 6.0
	return base_position + Vector2(cos(angle), sin(angle)) * MARKER_LOCAL_CLUSTER_RADIUS

func _add_filter_button(parent: Container, title: String, filter_id: String) -> void:
	var button := Button.new()
	button.text = title
	button.toggle_mode = true
	button.focus_mode = Control.FOCUS_ALL
	button.custom_minimum_size = Vector2(52.0, 48.0)
	button.size = Vector2(52.0, 48.0)
	button.set_meta("map_filter", filter_id)
	if filter_id == MAP_FILTER_VISITED:
		button.tooltip_text = "Показать посещенные"
	elif filter_id == MAP_FILTER_NOT_VISITED:
		button.tooltip_text = "Показать непосещенные"
	else:
		button.tooltip_text = "Показать все точки"
	button.add_theme_font_size_override("font_size", 18)
	_apply_map_control_style(button)
	button.pressed.connect(set_map_filter.bind(filter_id))
	parent.add_child(button)
	filter_buttons[filter_id] = button

func _add_zoom_button(parent: Container, title: String, factor: float) -> void:
	var tooltip := "Приблизить карту" if factor > 1.0 else "Отдалить карту"
	_add_map_control_button(parent, title, tooltip, MAP_CONTROL_SIZE, func() -> void: _zoom_at(map_layer.size * 0.5, factor))

func _add_zoom_percent_label(parent: Container) -> void:
	zoom_percent_label = Label.new()
	zoom_percent_label.text = "100%"
	zoom_percent_label.tooltip_text = "Текущий масштаб карты"
	zoom_percent_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	zoom_percent_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	zoom_percent_label.custom_minimum_size = Vector2(62.0, 48.0)
	zoom_percent_label.add_theme_font_size_override("font_size", 15)
	zoom_percent_label.add_theme_color_override("font_color", Color("#27321f"))
	var label_style := StyleBoxFlat.new()
	label_style.bg_color = Color(0.96, 0.90, 0.72, 0.94)
	label_style.border_color = Color("#3b2a18")
	label_style.shadow_color = Color(0.12, 0.08, 0.03, 0.42)
	label_style.shadow_size = 5
	label_style.set_border_width_all(2)
	label_style.set_corner_radius_all(6)
	zoom_percent_label.add_theme_stylebox_override("normal", label_style)
	parent.add_child(zoom_percent_label)

func _add_fit_button(parent: Container) -> void:
	_add_map_control_button(parent, "⤢", "Вписать все точки на экран", FIT_CONTROL_SIZE, _reset_map_view)

func _add_map_control_button(parent: Container, title: String, tooltip: String, minimum_size: Vector2, on_pressed: Callable) -> void:
	var button := Button.new()
	button.text = title
	button.tooltip_text = tooltip
	button.custom_minimum_size = minimum_size
	button.size = minimum_size
	button.add_theme_font_size_override("font_size", 24 if title.length() <= 2 else 18)
	button.add_theme_color_override("font_color", Color("#27321f"))
	button.add_theme_color_override("font_hover_color", Color("#11170e"))
	button.add_theme_color_override("font_pressed_color", Color("#11170e"))
	button.add_theme_color_override("font_disabled_color", Color("#52604a"))
	_apply_map_control_style(button)
	button.pressed.connect(on_pressed)
	parent.add_child(button)

func _apply_map_control_style(button: Button) -> void:
	var normal_style := StyleBoxFlat.new()
	normal_style.bg_color = Color(0.96, 0.90, 0.72, 0.94)
	normal_style.border_color = Color("#3b2a18")
	normal_style.shadow_color = Color(0.12, 0.08, 0.03, 0.42)
	normal_style.shadow_size = 5
	normal_style.set_border_width_all(2)
	normal_style.set_corner_radius_all(6)
	button.add_theme_stylebox_override("normal", normal_style)
	button.add_theme_stylebox_override("pressed", normal_style)
	button.add_theme_stylebox_override("hover", normal_style)

func _refresh_filter_buttons() -> void:
	for filter_id in filter_buttons:
		var button: Button = filter_buttons[filter_id]
		button.button_pressed = filter_id == map_filter

func _on_map_layer_gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		_handle_mouse_button(event)
	elif event is InputEventMouseMotion:
		_handle_mouse_motion(event)
	elif event is InputEventScreenTouch:
		_handle_screen_touch(event)
	elif event is InputEventScreenDrag:
		_handle_screen_drag(event)
	elif event is InputEventMagnifyGesture:
		_zoom_at(event.position, event.factor)
		accept_event()

func _handle_mouse_button(event: InputEventMouseButton) -> void:
	if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
		_zoom_at(event.position, ZOOM_STEP)
		accept_event()
	elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
		_zoom_at(event.position, 1.0 / ZOOM_STEP)
		accept_event()
	elif event.button_index == MOUSE_BUTTON_LEFT:
		dragging = event.pressed
		drag_distance = 0.0
		accept_event()

func _handle_mouse_motion(event: InputEventMouseMotion) -> void:
	if dragging or bool(event.button_mask & MOUSE_BUTTON_MASK_LEFT):
		_pan_by(_pan_delta_from_mouse_motion(event))
		drag_distance += event.screen_relative.length()
		if drag_distance >= DRAG_TAP_SUPPRESS_DISTANCE:
			suppress_next_marker_press = true
		_apply_map_transform()
		accept_event()

func _handle_screen_touch(event: InputEventScreenTouch) -> void:
	if event.pressed:
		last_touch_positions[event.index] = event.position
		drag_distance = 0.0
		if active_touch_index == -1:
			active_touch_index = event.index
	else:
		last_touch_positions.erase(event.index)
		if active_touch_index == event.index:
			active_touch_index = -1 if last_touch_positions.is_empty() else int(last_touch_positions.keys()[0])
	accept_event()

func _handle_screen_drag(event: InputEventScreenDrag) -> void:
	if last_touch_positions.size() >= 2:
		var previous_distance := _touch_distance_with(event.index, event.position - event.relative)
		var current_distance := _touch_distance_with(event.index, event.position)
		if previous_distance > 0.0 and current_distance > 0.0:
			_zoom_at(event.position, current_distance / previous_distance)
	else:
		_pan_by(_pan_delta_from_screen_drag(event))
		drag_distance += event.screen_relative.length()
		if drag_distance >= DRAG_TAP_SUPPRESS_DISTANCE:
			suppress_next_marker_press = true
		_apply_map_transform()
	last_touch_positions[event.index] = event.position
	accept_event()

func _touch_distance_with(index: int, position: Vector2) -> float:
	for touch_index in last_touch_positions:
		if int(touch_index) != index:
			var other_position: Vector2 = last_touch_positions[touch_index]
			return position.distance_to(other_position)
	return 0.0

func _pan_by(screen_delta: Vector2) -> void:
	pan_offset += screen_delta * PAN_DRAG_SCALE

func _pan_delta_from_mouse_motion(event: InputEventMouseMotion) -> Vector2:
	return event.screen_relative

func _pan_delta_from_screen_drag(event: InputEventScreenDrag) -> Vector2:
	return event.screen_relative

func _zoom_at(pivot: Vector2, factor: float) -> void:
	var previous_zoom := zoom
	zoom = clamp(zoom * factor, MIN_ZOOM, MAX_ZOOM)
	if is_equal_approx(previous_zoom, zoom):
		_update_zoom_percent_label()
		return

	var scale_factor := zoom / previous_zoom
	pan_offset = pivot - (pivot - pan_offset) * scale_factor
	_apply_map_transform()

func _reset_map_view() -> void:
	_update_map_reference_data()
	zoom = _default_zoom()
	pan_offset = _default_pan_offset()
	map_view_initialized = true
	_apply_map_transform()

func _default_zoom() -> float:
	if map_layer != null and map_layer.size.x > map_layer.size.y:
		return DEFAULT_LANDSCAPE_ZOOM
	return DEFAULT_ZOOM

func _apply_map_transform() -> void:
	if map_layer != null:
		_clamp_pan_offset()
		_sync_offline_layer_transform(map_layer)
	if map_label_layer != null:
		_sync_offline_layer_transform(map_label_layer)
	_update_zoom_percent_label()
	_position_markers()

func _sync_offline_layer_transform(layer_control: Control) -> void:
	layer_control.set("pan_offset", pan_offset)
	layer_control.set("zoom", zoom)
	layer_control.queue_redraw()

func _update_zoom_percent_label() -> void:
	if zoom_percent_label == null:
		return
	zoom_percent_label.text = "%d%%" % int(round(zoom * 100.0))

func _clamp_pan_offset() -> void:
	if map_layer == null:
		return

	var viewport_size := map_layer.size
	if viewport_size.x <= 0.0 or viewport_size.y <= 0.0:
		return

	var layer := map_layer as OfflineMapLayer
	var scaled_size := layer.map_base_size() * zoom
	if scaled_size.x <= viewport_size.x:
		pan_offset.x = (viewport_size.x - scaled_size.x) * 0.5
	else:
		pan_offset.x = clamp(pan_offset.x, viewport_size.x - scaled_size.x - PAN_LIMIT_PADDING, PAN_LIMIT_PADDING)

	if scaled_size.y <= viewport_size.y:
		pan_offset.y = (viewport_size.y - scaled_size.y) * 0.5
	else:
		pan_offset.y = clamp(pan_offset.y, viewport_size.y - scaled_size.y - PAN_LIMIT_PADDING, PAN_LIMIT_PADDING)

func _map_point_to_screen(point: Vector2, marker_size: Vector2 = ICON_MARKER_SIZE) -> Vector2:
	return pan_offset + point * zoom - marker_size * 0.5

func _marker_visual_size(is_cluster_marker: bool = false) -> Vector2:
	var max_size: float = CLUSTER_MARKER_ZOOM_SIZE_MAX if is_cluster_marker else MARKER_ZOOM_SIZE_MAX
	var size_value: float = clamp(ICON_MARKER_SIZE.x * _map_visual_scale(), MARKER_ZOOM_SIZE_MIN, max_size)
	return Vector2(size_value, size_value)

func _map_visual_scale() -> float:
	var viewport_width := ICON_VIEWPORT_REFERENCE_WIDTH
	if map_layer != null and map_layer.size.x > 0.0:
		viewport_width = map_layer.size.x
	var viewport_scale: float = clamp(sqrt(viewport_width / ICON_VIEWPORT_REFERENCE_WIDTH), ICON_VIEWPORT_SCALE_MIN, ICON_VIEWPORT_SCALE_MAX)
	return sqrt(max(zoom, 0.75)) * viewport_scale

func _apply_marker_visual_size(marker: Button, marker_size: Vector2) -> void:
	marker.custom_minimum_size = marker_size
	marker.size = marker_size

func _default_pan_offset() -> Vector2:
	if map_layer == null:
		return Vector2.ZERO
	var layer := map_layer as OfflineMapLayer
	return map_layer.size * 0.5 - _initial_focus_map_point(layer) * zoom

func _initial_focus_map_point(layer: OfflineMapLayer) -> Vector2:
	if map_scope == MAP_SCOPE_GERMANY:
		return OfflineMapLayer._project_coordinates(GERMANY_INITIAL_FOCUS_COORDINATES, _active_coordinate_bounds(), layer.map_base_size())

	var bounds := _active_coordinate_bounds()
	if bounds.is_empty():
		return layer.map_base_size() * 0.5

	var has_any := false
	var min_position := Vector2.ZERO
	var max_position := Vector2.ZERO
	for object_data in objects:
		if not _has_coordinates(object_data) or not _object_visible_in_scope(object_data):
			continue
		var coordinates := _object_coordinates(object_data)
		if not _coordinates_inside_bounds(coordinates, bounds):
			continue
		var position := OfflineMapLayer._project_coordinates(coordinates, bounds, layer.map_base_size())
		if not has_any:
			min_position = position
			max_position = position
			has_any = true
			continue
		min_position.x = min(min_position.x, position.x)
		min_position.y = min(min_position.y, position.y)
		max_position.x = max(max_position.x, position.x)
		max_position.y = max(max_position.y, position.y)

	if not has_any:
		return layer.map_base_size() * 0.5
	return (min_position + max_position) * 0.5

func _visible_marker_count() -> int:
	var count := 0
	for marker in marker_buttons:
		if marker.visible:
			count += 1
	return count

func _object_matches_filter(object_data: Dictionary) -> bool:
	if not _object_visible_in_scope(object_data):
		return false
	if map_filter == MAP_FILTER_ALL:
		return true
	var is_visited := _is_object_visited(object_data)
	if map_filter == MAP_FILTER_VISITED:
		return is_visited
	return not is_visited

func _object_visible_in_scope(object_data: Dictionary) -> bool:
	if map_scope != MAP_SCOPE_GERMANY:
		return true
	return _is_germany_object(object_data)

func _is_object_visited(object_data: Dictionary) -> bool:
	if object_data.has("visit_status_id"):
		var status_id := str(object_data.get("visit_status_id", ""))
		return status_id == "visited" or status_id == "favorite"
	return object_data.get("visited", false)

func _compact_text(text: String, max_length: int) -> String:
	var normalized := text.strip_edges().replace("\n", " ")
	if normalized.length() <= max_length:
		return normalized
	return normalized.substr(0, max(0, max_length - 1)).strip_edges() + "…"

func _icon_for_object(object_data: Dictionary) -> Texture2D:
	var icon_id := _icon_id_for_object(object_data)
	return _marker_icon_texture(icon_id)

func _marker_icon_texture(icon_id: String) -> Texture2D:
	if not marker_icons.has(icon_id):
		var path := "res://assets/sprites/outlined/%s.png" % icon_id
		marker_icons[icon_id] = load(path) if ResourceLoader.exists(path) else null
	var texture: Texture2D = marker_icons.get(icon_id, null)
	return texture

func _icon_id_for_object(object_data: Dictionary) -> String:
	var transport_type_id := str(object_data.get("transport_type_id", ""))
	return TRANSPORT_TYPE_ICON.get(transport_type_id, "icon_station")

func _apply_marker_style(marker: Button, is_selected: bool) -> void:
	marker.icon = _icon_for_object(objects[int(marker.get_meta("object_index", -1))]) if int(marker.get_meta("object_index", -1)) >= 0 else null
	marker.expand_icon = true
	var normal_style := StyleBoxFlat.new()
	normal_style.bg_color = Color(0.0, 0.0, 0.0, 0.0)
	normal_style.border_color = Color(0.0, 0.0, 0.0, 0.0)
	normal_style.shadow_color = Color(0.0, 0.0, 0.0, 0.0)
	normal_style.shadow_size = 0
	normal_style.set_border_width_all(0)
	normal_style.set_corner_radius_all(0)
	marker.add_theme_stylebox_override("normal", normal_style)

	var hover_style := normal_style.duplicate()
	hover_style.bg_color = Color(1.0, 0.86, 0.34, 0.08)
	marker.add_theme_stylebox_override("hover", hover_style)
	marker.add_theme_stylebox_override("pressed", normal_style)
	marker.add_theme_stylebox_override("focus", normal_style)

func _apply_cluster_marker_style(marker: Button, cluster_indices: PackedInt32Array) -> void:
	marker.icon = _marker_icon_texture("icon_station")
	marker.expand_icon = true
	marker.text = ""
	marker.add_theme_font_size_override("font_size", 15)
	marker.add_theme_color_override("font_color", Color("#f7e4b0"))
	marker.add_theme_color_override("font_pressed_color", Color("#f7e4b0"))
	var normal_style := StyleBoxFlat.new()
	normal_style.bg_color = Color(0.0, 0.0, 0.0, 0.0)
	normal_style.border_color = Color(0.0, 0.0, 0.0, 0.0)
	normal_style.shadow_color = Color(0.0, 0.0, 0.0, 0.0)
	normal_style.shadow_size = 0
	normal_style.set_border_width_all(0)
	normal_style.set_corner_radius_all(0)
	marker.add_theme_stylebox_override("normal", normal_style)
	var hover_style := normal_style.duplicate()
	hover_style.bg_color = Color(1.0, 0.84, 0.32, 0.08)
	marker.add_theme_stylebox_override("hover", hover_style)
	marker.add_theme_stylebox_override("pressed", normal_style)
	marker.add_theme_stylebox_override("focus", normal_style)
	marker.tooltip_text = "Группа объектов: %s" % _cluster_tooltip(cluster_indices)

func _cluster_tooltip(cluster_indices: PackedInt32Array) -> String:
	var names: Array[String] = []
	for index in cluster_indices:
		if int(index) >= 0 and int(index) < objects.size():
			names.append(str(objects[int(index)].get("name", "без названия")))
	return ", ".join(names)

func _coordinate_bounds() -> Dictionary:
	var has_any_coordinates := false
	var min_longitude := 0.0
	var max_longitude := 0.0
	var min_latitude := 0.0
	var max_latitude := 0.0

	for object_data in objects:
		if not _has_coordinates(object_data):
			continue

		var coordinates := _object_coordinates(object_data)
		if not has_any_coordinates:
			min_longitude = coordinates.x
			max_longitude = coordinates.x
			min_latitude = coordinates.y
			max_latitude = coordinates.y
			has_any_coordinates = true
			continue

		min_longitude = min(min_longitude, coordinates.x)
		max_longitude = max(max_longitude, coordinates.x)
		min_latitude = min(min_latitude, coordinates.y)
		max_latitude = max(max_latitude, coordinates.y)

	if not has_any_coordinates:
		return {}

	var longitude_padding: float = max(2.0, (max_longitude - min_longitude) * 0.08)
	var latitude_padding: float = max(1.0, (max_latitude - min_latitude) * 0.12)
	return {
		"min_longitude": min_longitude - longitude_padding,
		"max_longitude": max_longitude + longitude_padding,
		"min_latitude": clamp(min_latitude - latitude_padding, -85.0, 85.0),
		"max_latitude": clamp(max_latitude + latitude_padding, -85.0, 85.0),
	}

func _active_coordinate_bounds() -> Dictionary:
	if map_scope == MAP_SCOPE_GERMANY:
		return {
			"min_longitude": 4.5,
			"max_longitude": 16.8,
			"min_latitude": 43.2,
			"max_latitude": 55.8,
		}
	return _coordinate_bounds()

func _coordinate_bounds_for_objects(source_objects: Array) -> Dictionary:
	var has_any_coordinates := false
	var min_longitude := 0.0
	var max_longitude := 0.0
	var min_latitude := 0.0
	var max_latitude := 0.0
	for object_data in source_objects:
		if not _has_coordinates(object_data):
			continue
		var coordinates := _object_coordinates(object_data)
		if not has_any_coordinates:
			min_longitude = coordinates.x
			max_longitude = coordinates.x
			min_latitude = coordinates.y
			max_latitude = coordinates.y
			has_any_coordinates = true
			continue
		min_longitude = min(min_longitude, coordinates.x)
		max_longitude = max(max_longitude, coordinates.x)
		min_latitude = min(min_latitude, coordinates.y)
		max_latitude = max(max_latitude, coordinates.y)
	if not has_any_coordinates:
		return {}
	var longitude_padding: float = max(2.0, (max_longitude - min_longitude) * 0.08)
	var latitude_padding: float = max(1.0, (max_latitude - min_latitude) * 0.12)
	return {
		"min_longitude": min_longitude - longitude_padding,
		"max_longitude": max_longitude + longitude_padding,
		"min_latitude": clamp(min_latitude - latitude_padding, -85.0, 85.0),
		"max_latitude": clamp(max_latitude + latitude_padding, -85.0, 85.0),
	}

func _germany_objects() -> Array[Dictionary]:
	var matching_objects: Array[Dictionary] = []
	for object_data in objects:
		if _is_germany_object(object_data):
			matching_objects.append(object_data)
	return matching_objects

func _has_germany_object() -> bool:
	for object_data in objects:
		if _is_germany_object(object_data):
			return true
	return false

func _is_germany_object(object_data: Dictionary) -> bool:
	for key in object_data:
		if not (object_data[key] is String):
			continue
		var value := str(object_data[key]).to_lower()
		if value.contains("германия") or value.contains("deutschland") or value.contains("germany"):
			return true
	return false

func _coordinates_inside_bounds(coordinates: Vector2, bounds: Dictionary) -> bool:
	return coordinates.x >= float(bounds["min_longitude"]) \
		and coordinates.x <= float(bounds["max_longitude"]) \
		and coordinates.y >= float(bounds["min_latitude"]) \
		and coordinates.y <= float(bounds["max_latitude"])

func _update_map_reference_data() -> void:
	if map_layer == null:
		return

	var layer := map_layer as OfflineMapLayer
	layer.geo_bounds = _active_coordinate_bounds()
	layer.map_scope = map_scope
	layer.queue_redraw()
	if map_label_layer != null:
		var label_layer := map_label_layer as OfflineMapLayer
		label_layer.geo_bounds = _active_coordinate_bounds()
		label_layer.map_scope = map_scope
		label_layer.queue_redraw()

func _has_coordinates(object_data: Dictionary) -> bool:
	if object_data.has("coordinates") and object_data.get("coordinates") is Vector2:
		return true
	return object_data.has("latitude") and object_data.has("longitude")

func _object_coordinates(object_data: Dictionary) -> Vector2:
	if object_data.has("coordinates") and object_data.get("coordinates") is Vector2:
		return object_data.get("coordinates")
	return Vector2(float(object_data.get("longitude", 0.0)), float(object_data.get("latitude", 0.0)))

func _on_marker_pressed(index: int) -> void:
	if suppress_next_marker_press:
		suppress_next_marker_press = false
		return
	if index < 0 or index >= objects.size():
		return
	var marker := _marker_for_object_index(index)
	if marker != null and bool(marker.get_meta("is_cluster_marker", false)):
		_focus_cluster(marker)
		return

	object_selected.emit(index)

func _marker_for_object_index(index: int) -> Button:
	for marker in marker_buttons:
		if int(marker.get_meta("object_index", -1)) == index:
			return marker
	return null

func _focus_cluster(marker: Button) -> void:
	if map_layer == null:
		return
	var center := Vector2(marker.get_meta("cluster_center", Vector2.ZERO))
	if center == Vector2.ZERO:
		return
	var target_zoom: float = min(MAX_ZOOM, max(OBJECT_CLUSTER_ZOOM_THRESHOLD + 0.25, zoom * ZOOM_STEP))
	zoom = target_zoom
	pan_offset = map_layer.size * 0.5 - center * zoom
	_apply_map_transform()

func _on_marker_gui_input(event: InputEvent) -> void:
	if event is InputEventScreenDrag:
		suppress_next_marker_press = true
		_pan_by(_pan_delta_from_screen_drag(event))
		drag_distance += event.screen_relative.length()
		_apply_map_transform()
		accept_event()
	elif event is InputEventMouseMotion and bool(event.button_mask & MOUSE_BUTTON_MASK_LEFT):
		suppress_next_marker_press = true
		_pan_by(_pan_delta_from_mouse_motion(event))
		drag_distance += event.screen_relative.length()
		_apply_map_transform()
		accept_event()
