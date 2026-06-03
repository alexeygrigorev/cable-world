extends RefCounted
class_name HexMapModel

# Shared map model: the SAME hex_map.json that the web map editor edits.
# The editor writes this file (map_editor/src/data/hex_map.json); the game reads
# it here so the editor and the game render one map. Edit in the editor -> the
# file changes -> the game picks it up (live in dev via mtime polling, baked into
# the build at export time).
#
# Coordinate system mirrors map_editor/src/main.js exactly:
#   - pointy-top axial hexes (q, r) in Web Mercator "world pixels"
#     world.x = hex_size * sqrt(3) * (q + r/2)
#     world.y = hex_size * 1.5 * r
#   - focus.origin / focus.size define the Germany box (same geo_bounds the game
#     already uses) so hexes line up pixel-for-pixel with the game's markers.

const SQRT3 := 1.7320508075688772
# Canonical, single source of truth shared with the web editor.
const CANONICAL_PATH := "res://map_editor/src/data/hex_map.json"
# Shared map UI config (zoom range etc), read by BOTH the editor and the game.
const CONFIG_PATH := "res://map_editor/src/data/map_config.json"

# Zoom settings shared with the editor. Defaults match map_config.json so the
# game still works if the file is missing.
static func load_zoom_config() -> Dictionary:
	var cfg := {"min": 0.25, "max": 3.0, "step": 0.25, "default": 1.0}
	if not FileAccess.file_exists(CONFIG_PATH):
		return cfg
	var file := FileAccess.open(CONFIG_PATH, FileAccess.READ)
	if file == null:
		return cfg
	var data: Variant = JSON.parse_string(file.get_as_text())
	file.close()
	if typeof(data) == TYPE_DICTIONARY and data.has("zoom"):
		var z: Dictionary = data["zoom"]
		for key in cfg:
			if z.has(key):
				cfg[key] = float(z[key])
	return cfg

# Asset search dirs, in priority order — mirrors map_editor/vite.config.js
# ASSET_DIRS. A bare filename ("austrian_alps_massif.png", "city_berlin.png",
# "forest_pine_single_v1.png") resolves to the first dir that has it, so assets
# can be moved between these folders without breaking references.
const ASSET_DIRS := [
	"res://assets/sprites/transport_glow/",
	"res://assets/sprites/",
	"res://assets/sprites/city_landmark_clusters_hi_res/outlined/",
	"res://assets/map/glyphs/",
	"res://assets/map/massifs/",
	"res://assets/map/hex_terrain/generated_2026_06_01/forests/",
	"res://assets/map/hex_terrain/generated_2026_06_01/wooded_mountains/",
	"res://assets/map/hex_terrain/generated_2026_06_01/german_mountains/",
	"res://assets/map/hex_terrain/generated_2026_06_01/alps/",
]

var loaded := false
var source_path := CANONICAL_PATH
var grid := {}
var view := {}
var focus := {}
var hexes := {}        # "q,r" -> {country, terrain, center:[lon,lat]}
var features := []     # Array of feature dicts (forest/massif/city/transport)
var glyphs := {}        # glyph_ref -> shared glyph metadata
var hex_size := 37.5071
var focus_origin := Vector2.ZERO
var focus_size := Vector2.ONE
var view_origin := Vector2.ZERO   # top-left of the populated (Europe) extent, world px
var view_size := Vector2.ONE      # size of the populated extent, world px
var world_size := 65536.0         # Web Mercator world span in px (grid.world_size_px)
var _mtime := 0

var _tex_cache := {}   # filename -> Texture2D (or null when missing)

func load_from(path: String = CANONICAL_PATH) -> bool:
	source_path = path
	if not FileAccess.file_exists(path):
		push_warning("HexMapModel: file not found: %s" % path)
		loaded = false
		return false
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_warning("HexMapModel: cannot open %s" % path)
		return false
	var text := file.get_as_text()
	file.close()
	var data: Variant = JSON.parse_string(text)
	if typeof(data) != TYPE_DICTIONARY:
		push_warning("HexMapModel: parse failed for %s" % path)
		return false
	grid = data.get("grid", {})
	view = data.get("view", {})
	focus = data.get("focus", {})
	hexes = data.get("hexes", {})
	features = data.get("features", [])
	glyphs = data.get("glyphs", {})
	hex_size = float(grid.get("hex_size_px", 37.5071))
	world_size = float(grid.get("world_size_px", 65536.0))
	var fo: Array = focus.get("origin", [0.0, 0.0])
	var fs: Array = focus.get("size", [1.0, 1.0])
	focus_origin = Vector2(float(fo[0]), float(fo[1]))
	focus_size = Vector2(max(0.0001, float(fs[0])), max(0.0001, float(fs[1])))
	var vo: Array = view.get("origin", [focus_origin.x, focus_origin.y])
	var vs: Array = view.get("size", [focus_size.x, focus_size.y])
	view_origin = Vector2(float(vo[0]), float(vo[1]))
	view_size = Vector2(max(0.0001, float(vs[0])), max(0.0001, float(vs[1])))
	loaded = true
	_mtime = _modified_time(path)
	return true

# --- live reload (dev) -------------------------------------------------------
func file_changed() -> bool:
	return loaded and _modified_time(source_path) != _mtime

static func _modified_time(path: String) -> int:
	# res:// maps to a real file in the editor/dev; in an exported build the file
	# lives in the PCK and this just returns a stable value (we don't poll there).
	return int(FileAccess.get_modified_time(path))

# --- hex math (matches map_editor/src/main.js) -------------------------------
func hex_world(q: float, r: float) -> Vector2:
	return Vector2(hex_size * SQRT3 * (q + r / 2.0), hex_size * 1.5 * r)

func hex_world_key(key: String) -> Vector2:
	var parts := key.split(",")
	return hex_world(float(parts[0]), float(parts[1]))

# Web Mercator lon/lat -> world pixels, the SAME space hex centers live in. Lets
# the game place geo-coordinate markers in the hex map's coordinate system.
func geo_to_world(lon: float, lat: float) -> Vector2:
	var x := (lon + 180.0) / 360.0 * world_size
	var clamped: float = clamp(lat, -85.05112878, 85.05112878)
	var y := world_size * 0.5 - world_size / (2.0 * PI) * log(tan(PI / 4.0 + deg_to_rad(clamped) / 2.0))
	return Vector2(x, y)

# geo_bounds the game's projection expects, taken from the model's focus box so
# the two coordinate systems are guaranteed to agree.
func geo_bounds_dict() -> Dictionary:
	var gb: Array = focus.get("geo_bounds", [4.5, 43.2, 16.8, 55.8])
	return {
		"min_longitude": float(gb[0]),
		"min_latitude": float(gb[1]),
		"max_longitude": float(gb[2]),
		"max_latitude": float(gb[3]),
	}

# --- asset resolver ----------------------------------------------------------
func texture(name: String) -> Texture2D:
	if name.is_empty():
		return null
	if _tex_cache.has(name):
		return _tex_cache[name]
	var found: Texture2D = null
	for dir in ASSET_DIRS:
		var p: String = dir + name
		if ResourceLoader.exists(p):
			found = load(p)
			break
	_tex_cache[name] = found
	return found
