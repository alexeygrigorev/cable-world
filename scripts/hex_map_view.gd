extends Control
class_name HexMapView

# Renders the shared hex map model (the web editor's hex_map.json) inside the
# game, mirroring the passes in map_editor/src/main.js render():
#   1. land hex fill + thin edges
#   2. country borders (between land hexes of different countries)
#   3. massif sprites (placed by world-pixel bounds)
#   4. forest glyph bundles
#   5. city sprites + labels
#
# Camera (pan_offset, zoom, geo_bounds) is driven by MapPanel so the hex map
# lines up pixel-for-pixel with the interactive object markers drawn on top.

const SQRT3 := 1.7320508075688772
const NB := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, -1), Vector2i(-1, 1)]

const COL_SEA := Color("315f6d")
const COL_LAND_DE := Color("9da05a")
const COL_LAND_OTHER := Color("8f9150")
const COL_EDGE := Color(0.157, 0.129, 0.071, 0.07)   # rgba(40,33,18,0.07)
const COL_OUTLINE := Color(0.275, 0.235, 0.157, 0.55) # rgba(70,60,40,0.55)
const COL_LABEL_FILL := Color("f6df9b")
const COL_LABEL_STROKE := Color(0.110, 0.071, 0.031, 0.9)
const COL_TREE := Color("4e7a3f")

const LABEL_FONT_PATH := "res://assets/fonts/LiberationSerif-BoldItalic.ttf"
const CITY_LABEL_FONT_SCALE := 0.72
const CITY_LABEL_OUTLINE_SCALE := 0.17
const FIXED_MAP_SCALE := 0.64

# terrain glyph set, varied per hex by a stable hash (matches main.js FOREST_GLYPHS)
const FOREST_GLYPHS := [
	"forest_pine_single_v1.png",
	"forest_mixed_single_v1.png",
	"forest_broadleaf_single_v1.png",
	"forest_dark_conifer_single_v1.png",
	"forest_pine_bundle_3_v1.png",
	"forest_mixed_bundle_3_v1.png",
	"forest_broadleaf_bundle_3_v1.png",
	"forest_rocky_bundle_3_v1.png",
	"forest_pine_bundle_7_v1.png",
	"forest_mixed_bundle_7_v1.png",
	"forest_broadleaf_bundle_7_v1.png",
	"forest_sparse_edge_bundle_7_v1.png",
]

# camera, pushed in by MapPanel (same values its OfflineMapLayer uses)
var pan_offset := Vector2.ZERO
var zoom := 1.0
var geo_bounds: Dictionary = {}

var model: HexMapModel = null
var _label_font: Font = null

# precomputed, world-pixel geometry (rebuilt only when the model changes)
var _hex_centers := PackedVector2Array()
var _hex_colors := PackedColorArray()
var _border_segments := PackedVector2Array()   # pairs: [a, b, a, b, ...]
var _unit_hex := PackedVector2Array()           # 6 corner offsets (unit radius)

# Cached screen-space triangle geometry, rebuilt only when the camera changes.
var _geom_key := ""
var _fill_pts := PackedVector2Array()
var _fill_cols := PackedColorArray()
var _fill_idx := PackedInt32Array()
var _edge_pts := PackedVector2Array()
var _edge_cols := PackedColorArray()
var _edge_idx := PackedInt32Array()
var _bord_pts := PackedVector2Array()
var _bord_cols := PackedColorArray()
var _bord_idx := PackedInt32Array()

func _init() -> void:
	for i in 6:
		var a := deg_to_rad(60.0 * i - 30.0)
		_unit_hex.append(Vector2(cos(a), sin(a)))

func set_model(next_model: HexMapModel) -> void:
	model = next_model
	_geom_key = ""
	_rebuild_cache()
	queue_redraw()

# --- geometry cache ----------------------------------------------------------
func _rebuild_cache() -> void:
	_hex_centers = PackedVector2Array()
	_hex_colors = PackedColorArray()
	_border_segments = PackedVector2Array()
	if model == null or not model.loaded:
		return

	for key in model.hexes:
		var cell: Dictionary = model.hexes[key]
		_hex_centers.append(model.hex_world_key(key))
		_hex_colors.append(_cell_color(cell))

	var apothem := model.hex_size * SQRT3 / 2.0
	var half := model.hex_size / 2.0
	for key in model.hexes:
		var cell: Dictionary = model.hexes[key]
		var parts: PackedStringArray = str(key).split(",")
		var q := int(parts[0])
		var r := int(parts[1])
		var country: Variant = cell.get("country")
		var here := model.hex_world(q, r)
		for nb in NB:
			var nkey := "%d,%d" % [q + nb.x, r + nb.y]
			if not model.hexes.has(nkey):
				continue
			if model.hexes[nkey].get("country") == country:
				continue
			if nkey < key:        # draw each shared border once
				continue
			var n := model.hex_world(q + nb.x, r + nb.y)
			var u := (n - here)
			var ln := u.length()
			if ln == 0.0:
				continue
			u /= ln
			var mid := here + u * apothem
			var perp := Vector2(-u.y, u.x)
			_border_segments.append(mid + perp * half)
			_border_segments.append(mid - perp * half)

func _cell_color(cell: Dictionary) -> Color:
	return COL_LAND_DE if str(cell.get("country", "")) == "DE" else COL_LAND_OTHER

# --- camera ------------------------------------------------------------------
func _map_base_size() -> Vector2:
	if size.x <= 0.0 or size.y <= 0.0 or geo_bounds.is_empty():
		return size
	var aspect := _projected_aspect()
	var va := size.x / size.y
	if va > aspect:
		return Vector2(size.x, size.x / aspect)
	return Vector2(size.y * aspect, size.y)

func _projected_aspect() -> float:
	var lon_span: float = max(0.000001, deg_to_rad(float(geo_bounds["max_longitude"]) - float(geo_bounds["min_longitude"])))
	var merc_span: float = max(0.000001, _mercator_y(float(geo_bounds["max_latitude"])) - _mercator_y(float(geo_bounds["min_latitude"])))
	return lon_span / merc_span

static func _mercator_y(latitude: float) -> float:
	var lat: float = clamp(latitude, -85.0, 85.0)
	return log(tan(PI / 4.0 + deg_to_rad(lat) / 2.0))

# uniform world-px -> screen scale. 100% is fixed and viewport-independent:
# resizing the control changes how much map is visible, not the map scale.
func _scale_factor() -> float:
	return FIXED_MAP_SCALE * zoom

func _w2s(world: Vector2, k: float) -> Vector2:
	return pan_offset + (world - model.focus_origin) * k

# --- draw --------------------------------------------------------------------
func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), COL_SEA, true)
	if model == null or not model.loaded:
		return

	var k := _scale_factor()
	if k <= 0.0:
		return
	var s := model.hex_size * k        # on-screen hex radius (editor's s*sc)
	var object_s := model.hex_size * k

	# visible world-pixel rectangle (+ margin), for culling
	var object_world_s := object_s / k
	var margin: float = max(model.hex_size * 2.0, object_world_s * 14.0)
	var w_tl := model.focus_origin + (Vector2.ZERO - pan_offset) / k
	var w_br := model.focus_origin + (size - pan_offset) / k
	var view_rect := Rect2(w_tl, w_br - w_tl).abs().grow(margin)

	# Rebuild hex/edge/border triangle geometry only when the camera changes; at
	# idle it's reused so _draw stays cheap. On web the GDScript build (not the
	# GPU) is the bottleneck, and 2D line primitives (draw_line/draw_multiline)
	# are ~50x slower than triangles, so everything is built as triangle soups.
	var key := "%d|%d|%d|%d|%d" % [
		int(round(pan_offset.x)), int(round(pan_offset.y)),
		int(round(k * 1000.0)), int(size.x), int(size.y)]
	if key != _geom_key:
		_geom_key = key
		_rebuild_screen_geometry(k, s, view_rect)

	var ci := get_canvas_item()
	if not _fill_pts.is_empty():
		RenderingServer.canvas_item_add_triangle_array(ci, _fill_idx, _fill_pts, _fill_cols)
	if not _edge_pts.is_empty():
		RenderingServer.canvas_item_add_triangle_array(ci, _edge_idx, _edge_pts, _edge_cols)
	if not _bord_pts.is_empty():
		RenderingServer.canvas_item_add_triangle_array(ci, _bord_idx, _bord_pts, _bord_cols)

	_draw_massifs(k, object_s, view_rect)
	_draw_forests(k, object_s, view_rect)
	_draw_cities(k, object_s, view_rect)

func _rebuild_screen_geometry(k: float, s: float, view_rect: Rect2) -> void:
	_fill_pts = PackedVector2Array()
	_fill_cols = PackedColorArray()
	_fill_idx = PackedInt32Array()
	_edge_pts = PackedVector2Array()
	_edge_cols = PackedColorArray()
	_edge_idx = PackedInt32Array()
	_bord_pts = PackedVector2Array()
	_bord_cols = PackedColorArray()
	_bord_idx = PackedInt32Array()

	var edge_hw: float = max(0.35, s * 0.012) * 0.5
	for i in _hex_centers.size():
		var c: Vector2 = _hex_centers[i]
		if not view_rect.has_point(c):
			continue
		var cs := _w2s(c, k)
		var col: Color = _hex_colors[i]
		var base := _fill_pts.size()
		_fill_pts.append(cs)
		_fill_cols.append(col)
		for j in 6:
			_fill_pts.append(cs + _unit_hex[j] * s)
			_fill_cols.append(col)
		for j in 6:
			_fill_idx.append(base)
			_fill_idx.append(base + 1 + j)
			_fill_idx.append(base + 1 + ((j + 1) % 6))
			_append_quad(_edge_pts, _edge_cols, _edge_idx, _fill_pts[base + 1 + j], _fill_pts[base + 1 + ((j + 1) % 6)], edge_hw, COL_EDGE)

	var hw: float = max(1.0, s * 0.08) * 0.5
	var bi := 0
	while bi < _border_segments.size():
		var a: Vector2 = _border_segments[bi]
		var b: Vector2 = _border_segments[bi + 1]
		bi += 2
		if not view_rect.has_point(a) and not view_rect.has_point(b):
			continue
		_append_quad(_bord_pts, _bord_cols, _bord_idx, _w2s(a, k), _w2s(b, k), hw, COL_OUTLINE)

# add a segment a-b of half-width hw as two triangles (a fast stand-in for a line)
func _append_quad(pts: PackedVector2Array, cols: PackedColorArray, idx: PackedInt32Array, a: Vector2, b: Vector2, hw: float, color: Color) -> void:
	var d := b - a
	var ln := d.length()
	if ln < 0.0001:
		return
	var n := Vector2(-d.y, d.x) / ln * hw
	var base := pts.size()
	pts.append(a + n)
	pts.append(b + n)
	pts.append(b - n)
	pts.append(a - n)
	for _j in 4:
		cols.append(color)
	idx.append(base); idx.append(base + 1); idx.append(base + 2)
	idx.append(base); idx.append(base + 2); idx.append(base + 3)

func _draw_massifs(k: float, object_s: float, view_rect: Rect2) -> void:
	for f in model.features:
		if str(f.get("glyph", "")) != "massif":
			continue
		var image := str(f.get("image", ""))
		if image.is_empty():
			continue
		var meta: Dictionary = model.glyphs.get(str(f.get("glyph_ref", "")), {})
		var bounds: Array = meta.get("bounds_offset_hex", [])
		if bounds.size() < 4:
			continue
		var anchor_world := model.hex_world_key(str(f.get("anchor", "0,0"))) + Vector2(-model.hex_size * SQRT3 * 0.5, model.hex_size * 0.75)
		if not view_rect.has_point(anchor_world):
			continue
		var tex := model.texture(image)
		if tex == null:
			continue
		var anchor_screen := _w2s(anchor_world, k)
		var x0 := float(bounds[0]) * object_s
		var y0 := float(bounds[1]) * object_s
		var x1 := float(bounds[2]) * object_s
		var y1 := float(bounds[3]) * object_s
		draw_texture_rect(tex, Rect2(anchor_screen + Vector2(x0, y0), Vector2(x1 - x0, y1 - y0)), false)

# Forest glyphs are batched per texture (one textured triangle array per glyph
# variant) instead of one draw_texture_rect per cell — on web GL the per-draw-call
# cost dominates, and forests are by far the most numerous sprites.
func _draw_forests(k: float, s: float, view_rect: Rect2) -> void:
	var by_tex := {}        # texture RID -> batch dict
	var rid_tex := {}       # texture RID -> Texture2D (kept alive)
	var h := s * 1.9
	for f in model.features:
		if str(f.get("glyph", "")) != "forest":
			continue
		for key in f.get("cells", []):
			var c := model.hex_world_key(str(key))
			if not view_rect.has_point(c):
				continue
			var cs := _w2s(c, k)
			var tex := model.texture(_variant(str(key), FOREST_GLYPHS))
			if tex == null:
				_draw_tree(cs, s)
				continue
			var rid := tex.get_rid()
			var batch: Dictionary = by_tex.get(rid, {})
			if batch.is_empty():
				batch = {"pts": PackedVector2Array(), "uvs": PackedVector2Array(), "cols": PackedColorArray(), "idx": PackedInt32Array()}
				by_tex[rid] = batch
				rid_tex[rid] = tex
			var w := h * (float(tex.get_width()) / float(tex.get_height()))
			_append_textured_quad(batch, Rect2(cs.x - w * 0.5, cs.y - h * 0.5, w, h))
	for rid in by_tex:
		var b: Dictionary = by_tex[rid]
		RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), b["idx"], b["pts"], b["cols"], b["uvs"], PackedInt32Array(), PackedFloat32Array(), rid)

func _append_textured_quad(batch: Dictionary, rect: Rect2) -> void:
	var pts: PackedVector2Array = batch["pts"]
	var uvs: PackedVector2Array = batch["uvs"]
	var cols: PackedColorArray = batch["cols"]
	var idx: PackedInt32Array = batch["idx"]
	var base := pts.size()
	pts.append(rect.position)
	pts.append(Vector2(rect.end.x, rect.position.y))
	pts.append(rect.end)
	pts.append(Vector2(rect.position.x, rect.end.y))
	uvs.append(Vector2(0, 0)); uvs.append(Vector2(1, 0)); uvs.append(Vector2(1, 1)); uvs.append(Vector2(0, 1))
	for _j in 4:
		cols.append(Color.WHITE)
	idx.append(base); idx.append(base + 1); idx.append(base + 2)
	idx.append(base); idx.append(base + 2); idx.append(base + 3)

func _draw_cities(k: float, s: float, view_rect: Rect2) -> void:
	var show_labels := s > 13.0
	# south-over-north: sort by screen y so nearer (lower) cities draw on top
	var cities := []
	for f in model.features:
		if str(f.get("glyph", "")) != "city":
			continue
		var c := model.hex_world_key(str(f.get("anchor", "0,0")))
		if not view_rect.has_point(c):
			continue
		cities.append({"f": f, "pos": _w2s(c, k)})
	cities.sort_custom(func(a, b): return a["pos"].y < b["pos"].y)

	for entry in cities:
		_draw_city(entry["f"], entry["pos"], s, show_labels)

func _draw_city(f: Dictionary, pos: Vector2, s: float, show_label: bool) -> void:
	var capital := str(f.get("kind", "")) == "capital"
	var icon := str(f.get("icon", ""))
	var tex := model.texture("city_%s.png" % icon) if not icon.is_empty() else null
	var bottom := pos.y
	if tex != null:
		var h := s * (5.0 if capital else 4.0)
		var w := h * (float(tex.get_width()) / float(tex.get_height()))
		draw_texture_rect(tex, Rect2(pos.x - w * 0.5, pos.y - h * 0.70, w, h), false)
		bottom = pos.y + h * 0.30
	else:
		var rad := s * (0.5 if capital else 0.38)
		draw_circle(pos, rad, Color("c0392b") if capital else Color("34495e"))
		bottom = pos.y + rad
	var label := str(f.get("label", ""))
	if show_label and not label.is_empty():
		_draw_city_label(label, pos.x, bottom - s * 0.55, s)

func _draw_city_label(text: String, center_x: float, top_y: float, s: float) -> void:
	var font := _get_font()
	var fs: int = int(clamp(round(s * CITY_LABEL_FONT_SCALE), 9.0, 32.0))
	var ci := get_canvas_item()
	var tw := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, fs).x
	var origin := Vector2(round(center_x - tw * 0.5), round(top_y + fs))
	# A single clean outline (like the editor's canvas strokeText) instead of a
	# few offset black copies that read as a doubled label.
	var outline: int = max(2, int(round(s * CITY_LABEL_OUTLINE_SCALE)))
	font.draw_string_outline(ci, origin, text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, fs, outline, COL_LABEL_STROKE)
	font.draw_string(ci, origin, text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, fs, COL_LABEL_FILL)

# --- sprites / fallbacks -----------------------------------------------------
func _draw_sprite(tex: Texture2D, center: Vector2, h: float, base_anchor: bool) -> void:
	var w := h * (float(tex.get_width()) / float(tex.get_height()))
	var top := center.y - h * 0.78 if base_anchor else center.y - h * 0.5
	draw_texture_rect(tex, Rect2(center.x - w * 0.5, top, w, h), false)

func _draw_tree(c: Vector2, s: float) -> void:
	var pts := PackedVector2Array([
		c + Vector2(0, -s * 0.55), c + Vector2(s * 0.4, s * 0.3), c + Vector2(-s * 0.4, s * 0.3)])
	draw_colored_polygon(pts, COL_TREE)
	draw_rect(Rect2(c.x - s * 0.06, c.y + s * 0.3, s * 0.12, s * 0.22), Color("6a4a2a"), true)

func _get_font() -> Font:
	if _label_font == null:
		if ResourceLoader.exists(LABEL_FONT_PATH):
			_label_font = load(LABEL_FONT_PATH)
		else:
			_label_font = ThemeDB.fallback_font
	return _label_font

# --- stable per-hex glyph variant (FNV-1a, matches main.js) -------------------
func _variant(key: String, arr: Array) -> String:
	return arr[_hash_key(key) % arr.size()]

func _hash_key(s: String) -> int:
	var h := 2166136261
	for i in s.length():
		h = (h ^ s.unicode_at(i)) & 0xFFFFFFFF
		h = (h * 16777619) & 0xFFFFFFFF
	return h
