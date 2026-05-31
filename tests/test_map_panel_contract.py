from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MapPanelContractTest(unittest.TestCase):
    def test_map_panel_declares_local_object_marker_api(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "extends PanelContainer",
            "class_name MapPanel",
            "signal object_selected(index: int)",
            "func set_objects(next_objects: Array[Dictionary]) -> void:",
            "func select_object(index: int) -> void:",
            "Button.new()",
            "marker.pressed.connect(_on_marker_pressed.bind(index))",
            "object_selected.emit(index)",
        ]:
            self.assertIn(expected, script_text)

    def test_map_panel_uses_transport_object_coordinates_only(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")

        for expected in [
            '"coordinates"',
            "coordinates.x",
            "coordinates.y",
            '"longitude"',
            '"latitude"',
            "Vector2(float(object_data.get(\"longitude\", 0.0)), float(object_data.get(\"latitude\", 0.0)))",
        ]:
            self.assertIn(expected, script_text)

        forbidden_details = [
            "platform",
            "платформ",
            "колес",
        ]
        lowered = script_text.lower()
        for forbidden in forbidden_details:
            self.assertNotIn(forbidden, lowered)

    def test_map_panel_is_offline_and_russian(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")

        self.assertNotIn("MapLibre", script_text)
        self.assertNotIn("http://", script_text)
        self.assertNotIn("https://", script_text)
        for text in [
            "Карта объектов",
            "Выбрать объект",
            "Нет точек с координатами",
            "Вписать все точки на экран",
            "Приблизить карту",
            "Отдалить карту",
        ]:
            self.assertIn(text, script_text)

        user_strings = re.findall(r'"([^"]*[А-Яа-яЁё][^"]*)"', script_text)
        self.assertGreaterEqual(len(user_strings), 8)

    def test_mobile_map_has_visible_contract(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")

        self.assertIn("const MARKER_SIZE := Vector2(44.0, 44.0)", script_text)
        self.assertIn("const ICON_MARKER_SIZE := Vector2(52.0, 52.0)", script_text)
        self.assertIn("const MAP_MIN_HEIGHT := 360.0", script_text)
        self.assertIn("const MAP_VIEW_HEIGHT := 720.0", script_text)
        self.assertIn("const MAP_LANDSCAPE_MIN_HEIGHT := 320.0", script_text)
        self.assertIn("custom_minimum_size = Vector2(0, 720)", scene_text)
        self.assertIn('map_layer.custom_minimum_size = Vector2(0.0, MAP_VIEW_HEIGHT)', script_text)
        self.assertIn("resized.connect(_sync_map_canvas_height)", script_text)
        self.assertIn('call_deferred("_sync_map_canvas_height")', script_text)
        self.assertIn("func _sync_map_canvas_height() -> void:", script_text)
        self.assertIn("map_layer.custom_minimum_size.y = target_height", script_text)
        self.assertIn("custom_minimum_size.y = target_height", script_text)
        self.assertIn("if size.x > size.y:", script_text)
        self.assertIn("OfflineMapLayer.new()", script_text)
        self.assertIn("draw_rect(rect", script_text)
        self.assertIn("draw_line", script_text)
        self.assertIn("geo_bounds", script_text)
        self.assertIn("_draw_graticule()", script_text)
        self.assertIn("_draw_land_mass()", script_text)
        self.assertIn('load("res://assets/map/germany_styled.png")', script_text)
        self.assertIn("TRANSPORT_TYPE_ICON", script_text)
        self.assertIn("marker.icon = _icon_for_object(objects[index])", script_text)
        self.assertIn("marker.expand_icon = true", script_text)
        self.assertIn("static func _project_coordinates(", script_text)
        self.assertIn("func map_base_size() -> Vector2:", script_text)
        self.assertIn("static func _map_base_size_for_viewport(", script_text)
        self.assertIn("static func _projected_aspect(", script_text)
        self.assertIn("static func _mercator_y(", script_text)
        self.assertIn('"Köln"', script_text)
        self.assertIn('"München"', script_text)
        self.assertIn('"Dresden"', script_text)
        self.assertIn('"icon_offset": Vector2(0.0, 52.0)', script_text)
        self.assertIn("city_landmarks/outlined/city_%s.png", script_text)
        self.assertIn('load("res://assets/fonts/LiberationSerif-BoldItalic.ttf")', script_text)
        self.assertIn("var city_font := _city_label_font()", script_text)
        self.assertIn("var atlas_font := _map_label_font()", script_text)
        self.assertIn("func _map_label_font() -> Font:", script_text)
        self.assertIn("func _city_label_font() -> Font:", script_text)
        self.assertIn("return get_theme_default_font()", script_text)
        self.assertIn("_draw_city_label(city_font, label_data, occupied_rects)", script_text)
        self.assertIn("_draw_terrain_label(atlas_font, label_data, occupied_rects)", script_text)
        self.assertIn("func _draw_centered_label_text(", script_text)
        self.assertIn("var icon_label_baseline_y: float = round(icon_rect.position.y + icon_rect.size.y - CITY_ICON_LABEL_BASELINE_OVERLAP * zoom)", script_text)
        self.assertIn("const LANDMARK_EDGE_MARGIN := 96.0", script_text)
        self.assertIn("const SECONDARY_CITY_LABEL_ZOOM := 1.20", script_text)
        self.assertIn("func _screen_point_near_viewport(position: Vector2, margin: float) -> bool:", script_text)
        self.assertIn("if not _screen_point_near_viewport(position, LANDMARK_EDGE_MARGIN):", script_text)
        self.assertIn("if is_town and zoom < SECONDARY_CITY_LABEL_ZOOM:", script_text)
        self.assertIn("var map_label_layer: Control", script_text)
        self.assertIn('map_label_layer.name = "ПодписиГородов"', script_text)
        self.assertIn('map_layer.set("draw_terrain_labels", false)', script_text)
        self.assertIn('map_label_layer.set("draw_terrain_labels", false)', script_text)
        self.assertIn("_update_map_reference_data()", script_text)
        self.assertIn('toolbar.name = "ПанельИнструментов"', script_text)
        self.assertIn("toolbar.visible = false", script_text)
        self.assertNotIn("hint_label", script_text)
        self.assertIn("MARKER_SPREAD_DISTANCE", script_text)
        self.assertIn("MARKER_SPREAD_STEP", script_text)
        self.assertNotIn("GRID_LAYOUT_MIN_MARKERS", script_text)
        self.assertNotIn("func _grid_marker_position(", script_text)
        self.assertNotIn("сетка для читаемости", script_text)
        self.assertNotIn("func _draw_reference_routes(", script_text)
        self.assertNotIn("_draw_geo_labels(", script_text)
        self.assertIn("func _spread_marker_position(", script_text)
        self.assertIn("func _is_clear_marker_position(", script_text)
        self.assertIn("func _compact_text(", script_text)
        self.assertIn("empty_state_label.visible = marker_buttons.is_empty()", script_text)

    def test_map_panel_supports_pan_zoom_and_touch_controls(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "var pan_offset := Vector2.ZERO",
            "var zoom := 1.0",
            "const MARKER_ZOOM_SIZE_MIN := 60.0",
            "const MARKER_ZOOM_SIZE_MAX := 96.0",
            "const CLUSTER_MARKER_ZOOM_SIZE_MAX := 88.0",
            "const ICON_VIEWPORT_REFERENCE_WIDTH := 390.0",
            "const ICON_VIEWPORT_SCALE_MIN := 0.92",
            "const ICON_VIEWPORT_SCALE_MAX := 1.30",
            "func _on_map_layer_gui_input(event: InputEvent) -> void:",
            "InputEventMouseButton",
            "InputEventMouseMotion",
            "InputEventScreenTouch",
            "InputEventScreenDrag",
            "InputEventMagnifyGesture",
            "MOUSE_BUTTON_WHEEL_UP",
            "MOUSE_BUTTON_WHEEL_DOWN",
            "const PAN_DRAG_SCALE := 1.0",
            "const TOUCH_PAN_DRAG_SCALE := 1.0",
            "func _pan_by(screen_delta: Vector2) -> void:",
            "pan_offset += screen_delta * PAN_DRAG_SCALE",
            "func _pan_delta_from_mouse_motion(event: InputEventMouseMotion) -> Vector2:",
            "func _pan_delta_from_screen_drag(event: InputEventScreenDrag) -> Vector2:",
            "event.position - previous_position",
            "event.relative",
            "var pan_delta := _pan_delta_from_screen_drag(event)",
            "last_touch_positions[event.index] = event.position",
            "pan_offset = _default_pan_offset()",
            "const ZOOM_STEP := 0.25",
            "func _zoom_by_delta(pivot: Vector2, delta: float) -> void:",
            "clamp(zoom + delta, MIN_ZOOM, MAX_ZOOM)",
            "func _reset_map_view() -> void:",
            "func _default_zoom() -> float:",
            "zoom = _default_zoom()",
            "if map_layer != null and map_layer.size.x > map_layer.size.y:",
            "return DEFAULT_LANDSCAPE_ZOOM",
            "func _clamp_pan_offset() -> void:",
            "func _default_pan_offset() -> Vector2:",
            "func _initial_focus_map_point(layer: OfflineMapLayer) -> Vector2:",
            "const MIN_ZOOM := 0.5",
            "const MAX_ZOOM := 2.0",
            "const DEFAULT_ZOOM := 1.10",
            "const DEFAULT_LANDSCAPE_ZOOM := 1.0",
            "const FIT_CONTROL_SIZE := Vector2(48.0, 48.0)",
            "const PAN_LIMIT_PADDING := 72.0",
            "const DRAG_TAP_SUPPRESS_DISTANCE := 10.0",
            "const OBJECT_CLUSTER_ZOOM_THRESHOLD := 1.45",
            "const OBJECT_CLUSTER_SCREEN_DISTANCE := 118.0",
            "const GERMANY_INITIAL_FOCUS_COORDINATES := Vector2(10.70, 52.00)",
            "OfflineMapLayer._project_coordinates(GERMANY_INITIAL_FOCUS_COORDINATES",
            'button.text = title',
            '"+"',
            '"-"',
            '"⤢"',
            "const MAP_CONTROL_SIZE := Vector2(48.0, 48.0)",
            "var zoom_percent_label: Label",
            "func _add_zoom_percent_label(parent: Container) -> void:",
            '"Текущий масштаб карты"',
            'zoom_percent_label.text = "%d%%" % int(round(zoom * 100.0))',
            'filter_controls.name = "ФильтрКарты"',
            "button.custom_minimum_size = Vector2(52.0, 48.0)",
            "button.custom_minimum_size = minimum_size",
            "_add_zoom_percent_label(zoom_controls)",
            "_add_fit_button(zoom_controls)",
            '_add_filter_button(filter_controls, "✓", MAP_FILTER_VISITED)',
            '_add_filter_button(filter_controls, "○", MAP_FILTER_NOT_VISITED)',
            "map_content.z_index = 10",
            "map_label_layer.z_index = 20",
            "zoom_controls.z_index = 30",
            "marker.mouse_filter = Control.MOUSE_FILTER_PASS",
            'zoom_controls.name = "МасштабКарты"',
            "var suppress_next_marker_press := false",
            "marker.gui_input.connect(_on_marker_gui_input)",
            "func _on_marker_gui_input(event: InputEvent) -> void:",
            "if suppress_next_marker_press:",
            "suppress_next_marker_press = true",
            "func _marker_clusters(bounds: Dictionary) -> Dictionary:",
            "func _nearest_cluster(cluster_list: Array[Dictionary], position: Vector2) -> Dictionary:",
            "func _apply_cluster_marker_style(marker: Button, cluster_indices: PackedInt32Array) -> void:",
            "func _apply_marker_style_if_needed(marker: Button, is_selected: bool) -> void:",
            "func _apply_cluster_marker_style_if_needed(marker: Button, cluster_indices: PackedInt32Array) -> void:",
            "func _cluster_indices_key(cluster_indices: PackedInt32Array) -> String:",
            "marker.set_meta(\"style_key\", style_key)",
            "func _apply_cluster_icon_stack(marker: Button, cluster_indices: PackedInt32Array) -> void:",
            "func _cluster_icon_ids(cluster_indices: PackedInt32Array) -> Array[String]:",
            "const CLUSTER_STACK_MAX_ICONS := 3",
            "sprite.set_meta(\"cluster_stack_icon\", true)",
            "marker.icon = null",
            'marker.text = ""',
            "func _map_point_to_screen(point: Vector2, marker_size: Vector2 = ICON_MARKER_SIZE) -> Vector2:",
            "func _marker_visual_size(is_cluster_marker: bool = false) -> Vector2:",
            "func _apply_marker_visual_size(marker: Button, marker_size: Vector2) -> void:",
            "marker.size = marker_size",
            "func _pixel_snap(point: Vector2) -> Vector2:",
            "return Vector2(round(point.x), round(point.y))",
            "func _marker_icon_texture(icon_id: String) -> Texture2D:",
            '"res://assets/sprites/outlined/%s.png"',
            "func _focus_cluster(marker: Button) -> void:",
            'marker.set_meta("cluster_indices"',
            'marker.set_meta("is_cluster_marker"',
            'marker.set_meta("cluster_center"',
            '"Группа объектов: %s"',
            "func _map_visual_scale() -> float:",
            "viewport_width = map_layer.size.x",
            "clamp(sqrt(viewport_width / ICON_VIEWPORT_REFERENCE_WIDTH), ICON_VIEWPORT_SCALE_MIN, ICON_VIEWPORT_SCALE_MAX)",
            "round(clamp(ICON_MARKER_SIZE.x * _map_visual_scale(), MARKER_ZOOM_SIZE_MIN, max_size))",
            "return _pixel_snap(pan_offset + point * zoom - marker_size * 0.5)",
        ]:
            self.assertIn(expected, script_text)

        for forbidden in [
            "_zoom_at(event.position, event.factor)",
            "current_distance / previous_distance",
            "func _touch_distance_with",
            "1.0 / ZOOM_STEP",
            "event.screen_relative",
        ]:
            self.assertNotIn(forbidden, script_text)

    def test_map_panel_filters_markers_by_visit_status(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")

        for expected in [
            'const MAP_FILTER_ALL := "all"',
            'const MAP_FILTER_VISITED := "visited"',
            'const MAP_FILTER_NOT_VISITED := "not_visited"',
            "var map_filter := MAP_FILTER_ALL",
            "func set_map_filter(next_filter: String) -> void:",
            "func _object_matches_filter(object_data: Dictionary) -> bool:",
            "func _object_visible_in_scope(object_data: Dictionary) -> bool:",
            "if not _object_visible_in_scope(object_data):",
            "func _is_object_visited(object_data: Dictionary) -> bool:",
            'status_id == "visited" or status_id == "favorite"',
            'return object_data.get("visited", false)',
            'marker.visible = _object_matches_filter(objects[index])',

            "Нет точек для выбранного фильтра",
            '"Все"',
            '"✓"',
            '"○"',
            "Показать посещенные",
            "Показать непосещенные",
        ]:
            self.assertIn(expected, script_text)

    def test_city_landmark_icons_are_drawn_after_successful_load(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")
        city_icon_rect_body = script_text.split("func _city_icon_rect", 1)[1].split("func _draw_city_icon", 1)[0]
        city_icon_draw_body = script_text.split("func _draw_city_icon", 1)[1].split("func _city_icon_texture", 1)[0]
        city_label_body = script_text.split("func _draw_city_label", 1)[1].split("func _draw_city_icon", 1)[0]
        centered_label_body = script_text.split("func _centered_label_rect", 1)[1].split("func _left_label_rect", 1)[0]

        self.assertIn("if texture == null:", city_icon_rect_body)
        self.assertIn("return Rect2()", city_icon_rect_body)
        self.assertIn("clamp(48.0 * _landmark_visual_scale(), 42.0, 76.0)", city_icon_rect_body)
        self.assertNotIn("_clamp_landmark_rect", city_icon_rect_body)
        self.assertNotIn("clamp(position.x", centered_label_body)
        self.assertIn("draw_texture_rect(texture, icon_rect, false)", city_icon_draw_body)
        self.assertIn("_centered_label_rect", city_label_body)
        self.assertIn("var icon_label_baseline_y: float = round(icon_rect.position.y + icon_rect.size.y - CITY_ICON_LABEL_BASELINE_OVERLAP * zoom)", city_label_body)
        self.assertIn("_pixel_snap(position + Vector2(-icon_size * 0.5, -icon_size - 9.0 * zoom) + _city_icon_offset(label_data))", city_icon_rect_body)
        self.assertIn("func _city_icon_offset(label_data: Dictionary) -> Vector2:", script_text)
        self.assertIn("+ _city_icon_offset(label_data)", city_icon_rect_body)
        self.assertIn("_rect_overlaps_any", city_label_body)
        self.assertIn("occupied_rects.append(occupied_rect)", city_label_body)
        self.assertNotIn("draw_circle(position", city_label_body)
        self.assertNotIn("draw_circle", city_icon_rect_body)
        self.assertNotIn("draw_rect", city_icon_rect_body)
        self.assertIn("func _landmark_visual_scale() -> float:", script_text)
        self.assertIn("clamp(48.0 * _landmark_visual_scale(), 42.0, 76.0)", script_text)
        self.assertIn("const CITY_ICON_LABEL_BASELINE_OVERLAP := 9.0", script_text)
        self.assertIn("icon_rect.position.y + icon_rect.size.y - CITY_ICON_LABEL_BASELINE_OVERLAP * zoom", script_text)
        self.assertIn("var reserved_label_rects: Array[Rect2] = []", script_text)
        self.assertIn("var occupied_rects: Array[Rect2] = reserved_label_rects.duplicate()", script_text)
        self.assertIn("func _left_label_rect(", script_text)
        self.assertIn("func _update_reserved_label_rects(rects: Array[Rect2]) -> void:", script_text)
        self.assertIn("reserved_rects.append(Rect2(marker.position, marker.size).grow(6.0))", script_text)
        self.assertIn("layer.reserved_label_rects = rects", script_text)
        self.assertIn("label_layer.reserved_label_rects = rects", script_text)
        self.assertIn("var map_label_layer: Control", script_text)
        self.assertIn('map_label_layer.name = "ПодписиГородов"', script_text)
        self.assertIn('map_layer.set("draw_city_labels", false)', script_text)
        self.assertIn('map_label_layer.set("draw_map_background", false)', script_text)
        self.assertIn('map_label_layer.set("draw_city_labels", true)', script_text)
        self.assertIn("func _sync_offline_layer_transform(layer_control: Control) -> void:", script_text)
        self.assertLess(
            city_icon_rect_body.index("if texture == null:"),
            city_icon_rect_body.index("return icon_rect"),
        )

    def test_default_city_labels_have_pictograms_or_stay_hidden(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")
        city_labels_block = script_text.split("const CITY_LABELS := [", 1)[1].split("]", 1)[0]
        city_entries = re.findall(r'\{"name": "([^"]+)".*?"kind": "([^"]+)".*?"icon": "([^"]*)"', city_labels_block)

        self.assertGreaterEqual(len(city_entries), 20)
        self.assertIn("const BARE_CITY_LABEL_ZOOM := 1.55", script_text)
        self.assertIn("func _city_label_has_icon(label_data: Dictionary) -> bool:", script_text)
        self.assertIn("if not _city_label_has_icon(label_data) and zoom < BARE_CITY_LABEL_ZOOM:", script_text)
        self.assertIn('"Nürnberg"', script_text)
        self.assertIn('"München"', script_text)
        self.assertIn('"Düsseldorf"', script_text)
        self.assertNotIn('"Nurnberg"', script_text)
        self.assertNotIn('"Munchen"', script_text)
        self.assertNotIn('"Dusseldorf"', script_text)

        for name, kind, icon_id in city_entries:
            if kind in {"capital", "city"}:
                self.assertTrue(icon_id, f"{name} is visible at default zoom but has no city pictogram")
                self.assertTrue(
                    (ROOT / "assets" / "sprites" / "city_landmarks" / "outlined" / f"city_{icon_id}.png").exists(),
                    f"{name} references a missing outlined city pictogram: {icon_id}",
                )

        no_icon_labels = [name for name, _kind, icon_id in city_entries if not icon_id]
        self.assertIn("Leipzig", no_icon_labels)
        self.assertIn("Nürnberg", no_icon_labels)

    def test_map_pipeline_uses_named_relief_layers(self) -> None:
        pipeline_text = (ROOT / "map_pipeline" / "compose_map.py").read_text(encoding="utf-8")

        for expected in [
            "RELIEF_REGIONS = [",
            '"id": "alps"',
            '"glyph": "alpine"',
            "MAP_SIZE = (1932, 3072)",
            '"ridge_bands": [',
            '"id": "main_alpine_wall"',
            '"id": "northern_alpine_foothills"',
            "ALPINE_MASSIF_SEGMENTS = [",
            '"id": "western_alps_massif"',
            '"id": "swiss_alps_massif"',
            '"id": "bavarian_tyrol_alps_massif"',
            '"id": "german_alpine_edge_massif"',
            '"required_country_overlap": "Germany"',
            '"id": "austrian_alps_massif"',
            '"massif_segments": ALPINE_MASSIF_SEGMENTS',
            '"mountain_glyphs": []',
            '("highland_forest_1", 10.42, 51.82, 226)',
            '("highland_forest_2", 10.86, 51.60, 176)',
            '("border_highland_1", 13.10, 50.66, 145)',
            '"extends_to": ["France", "Switzerland", "Italy", "Austria", "Slovenia"]',
            '"id": "black_forest"',
            '"glyph": "forested_highland"',
            '"id": "black_forest_spine"',
            '"style": "forested"',
            '"id": "harz"',
            '"id": "harz_brocken_spine"',
            '"id": "harz_south_spur"',
            '"custom_renderer": "harz_production_v1"',
            "def _render_harz_production_layer(size, proj, region):",
            '"id": "erzgebirge"',
            '"glyph": "border_highland"',
            '"id": "erzgebirge_border_spine"',
            '"style": "border"',
            '"id": "saxon_switzerland"',
            '"label": "Saxon Switzerland / Elbe Sandstone"',
            '"id": "elbe_sandstone_rim"',
            '"style": "sandstone"',
            '("border_highland_2", 14.18, 50.95, 108)',
            '"id": "bavarian_forest"',
            '"id": "bavarian_forest_spine"',
            '"id": "eifel_hunsrueck_low_spine"',
            '"style": "low"',
            '"id": "northern_lowlands"',
            '"kind": "lowland"',
            '"glyph": "lowland"',
            '"mountains": []',
            "for region in RELIEF_REGIONS:",
            'for glyph_name, lon, lat, width in region.get("mountain_glyphs", []):',
            'for ridge_band in region.get("ridge_bands", []):',
            'for massif_segment in region.get("massif_segments", []):',
            "region_layer = _render_relief_region_decor_layer(canvas.size, proj, region)",
            "def _render_relief_region_decor_layer(size, proj, region):",
            "def _should_export_relief_region_source_layer(region):",
            "def _draw_alpine_ridge_band(canvas, proj, ridge_band):",
            "def _draw_alpine_massif_segment(canvas, proj, segment):",
            "def _render_alpine_massif_segment_layer(size, proj, segment):",
            "def _draw_massif_crest_peaks(draw, arc_points, segment_id):",
            '_stable_hash("massif_crest", segment_id, segment_index, peak_index)',
            "def _save_massif_source_layer(layer, segment, proj):",
            "def _save_relief_region_source_layer(layer, region, proj):",
            "def _massif_source_metadata(segment, image_name, render_bbox, cropped_size, proj):",
            "def _relief_region_source_metadata(region, image_name, render_bbox, cropped_size, proj):",
            "def _source_layer_base_metadata(source, image_name, render_bbox, cropped_size, proj):",
            "def _prepare_massif_source_dir():",
            "def _write_massif_source_manifest():",
            "def audit_massif_source_manifest():",
            "def _expected_source_layer_ids():",
            "cropped.save(os.path.join(MASSIF_DIR, image_name), optimize=True)",
            "json.dump(manifest, file, ensure_ascii=False, indent=2, sort_keys=True)",
            "_draw_glyph_center(layer, proj, glyph_name, lon, lat, width)",
            'for lon, lat, mountain_size in region.get("mountains", []):',
            'region.get("glyph", "alpine")',
            'def _draw_mountains(canvas, draw, proj, lon, lat, size, glyph="alpine"):',
            "GLYPH_DIR = os.path.join(MAP_DIR, \"glyphs\")",
            "MASSIF_DIR = os.path.join(MAP_DIR, \"massifs\")",
            "MASSIF_MANIFEST_PATH = os.path.join(MASSIF_DIR, \"manifest.json\")",
            "TERRAIN_MASSIF_LAYERS_PATH = os.path.join(PIPELINE_DATA_DIR, \"terrain_massif_layers.json\")",
            "EXPORT_MASSIF_SOURCE_LAYERS = True",
            "MASSIF_SOURCE_MANIFEST = []",
            "def audit_terrain_massif_layer_contract():",
            "hash_random_mountain_stamp",
            "terrain source layer {layer_id} manifest source_extent_id does not match contract",
            "def _terrain_massif_contract_layers():",
            "FONT_DIR = os.path.join(os.path.dirname(__file__), \"..\", \"assets\", \"fonts\")",
            "ImageFont.truetype(font_path, key * RENDER_SCALE)",
            "ImageChops.subtract(land_mask, germany_mask)",
            "BAKED_TOWN_DETAILS_ENABLED = False",
            "BAKED_TOWN_DETAILS = []",
            "if BAKED_TOWN_DETAILS_ENABLED:",
            "for lon, lat, size in BAKED_TOWN_DETAILS:",
            "ATLAS_DETAILS = [",
            "MIN_ATLAS_DETAIL_WIDTH = 104",
            "DEFAULT_ATLAS_DETAIL_KINDS = {\"bridge\", \"port\", \"ship\"}",
            "def audit_geography_layers():",
            "CITY_LANDMARK_PLACEMENT_AUDITS = [",
            '"name": "Rostock"',
            '"icon_offset": (0.0, 52.0)',
            '"required_land_samples": ("top", "center", "bottom")',
            "def audit_runtime_landmark_placement(country_geometries=None):",
            "runtime landmark {landmark['name']} {sample_name} sample",
            "def _runtime_map_base_size_for_viewport(viewport_size):",
            "relief_polygons = {region[\"id\"]: Polygon(region[\"points\"])",
            "country_geometries = {row[\"ADMIN\"]: row.geometry for _, row in countries.iterrows()}",
            "northern_lowlands must not define",
            "mountain glyph {glyph_name} is outside relief region",
            "massif {segment['id']} must overlap {required_country}",
            "water body {water_body['id']} needs at least four outline points",
            "atlas detail {detail['id']} must not use relief glyph",
            "forest mass {forest_mass['id']} uses non-forest glyph",
            '"id": "hamburg_port"',
            '"glyph": "detail_port"',
            '"id": "rostock_ferry"',
            '"glyph": "detail_ship"',
            '"id": "dresden_elbe_bridge"',
            '"glyph": "detail_bridge"',
            '"id": "heidelberg_castle"',
            '"glyph": "detail_castle"',
            '"id": "harz_tower"',
            '"glyph": "detail_tower"',
            "ATLAS_ROUTE_SEGMENTS = [",
            '"id": "north_to_harz_trail"',
            '"id": "harz_to_berlin_trail"',
            '"id": "rhine_to_south_trail"',
            "def _draw_atlas_routes(canvas, proj, germany_mask):",
            "def _smooth_polyline(points, subdivisions=10):",
            "def _draw_atlas_dotted_route(draw, points, step):",
            "step * RENDER_SCALE * ATLAS_ROUTE_DOT_SPACING_SCALE",
            "_draw_atlas_routes(canvas, proj, germany_mask)",
            "ATLAS_FOREST_MASSES = [",
            "FOREST_MASS_VISUAL_SCALE = 1.90",
            "FOREST_MASS_MIN_WIDTH = 170",
            "FOREST_CLUSTER_MIN_SOURCE_WIDTH = 96",
            "RELIEF_TREE_CLUSTER_MIN_WIDTH = 146",
            "LAND_DETAIL_VISUAL_SCALE = 0.74",
            "LAND_DETAIL_ALPHA_SCALE = 0.48",
            "LAND_DETAIL_TINT_STRENGTH = 0.28",
            "GROUND_TEXTURE_LON_STEP = 0.62",
            "GROUND_TEXTURE_LAT_STEP = 0.58",
            "INTEGRATED_LAND_PATTERN_LON_STEP = 0.42",
            "INTEGRATED_LAND_PATTERN_LAT_STEP = 0.38",
            "INTEGRATED_LAND_PATTERN_ALPHA_SCALE = 0.46",
            "ATLAS_ROUTE_DOT_SPACING_SCALE = 1.75",
            "ATLAS_ROUTE_DOT_MIN_RADIUS = 4",
            '"atlas_forest_pine_dense"',
            '"atlas_forest_mixed_large"',
            '"atlas_forest_rocky_pine"',
            '"id": "lueneburg_heath"',
            '"id": "mecklenburg_lake_forests"',
            '"id": "spreewald_lausitz"',
            '"id": "thuringian_forest"',
            "ATLAS_LAND_DETAIL_PATCHES = [",
            '"atlas_land_grass_patch"',
            '"atlas_land_flower_meadow"',
            "if width < FOREST_CLUSTER_MIN_SOURCE_WIDTH:",
            "forest mass {forest_mass['id']} cluster {glyph_name} is too small for the default map",
            "if _relief_tree_cluster_width(tree_size) < RELIEF_TREE_CLUSTER_MIN_WIDTH:",
            "def _draw_atlas_forest_masses(canvas, proj, land_mask):",
            "display_width = max(FOREST_MASS_MIN_WIDTH, int(width * FOREST_MASS_VISUAL_SCALE))",
            "def _draw_atlas_land_detail_patches(canvas, proj, germany_mask):",
            "def _blend_land_detail_layer(layer):",
            "_draw_glyph_center(layer, proj, glyph_name, lon, lat, width * LAND_DETAIL_VISUAL_SCALE)",
            "ImageFilter.GaussianBlur(0.9 * RENDER_SCALE)",
            "LAND_DETAIL_ALPHA_SCALE",
            "LAND_DETAIL_TINT_STRENGTH",
            "def _draw_integrated_land_pattern(canvas, proj, germany_mask, germany_geom):",
            '"integrated_land_pattern"',
            "def _draw_land_pattern_mark(draw, x, y, size, kind, seed):",
            "def _relief_tree_cluster_width(radius):",
            "_draw_integrated_land_pattern(canvas, proj, germany_mask, germany)",
            "_draw_atlas_land_detail_patches(canvas, proj, germany_mask)",
            "_draw_atlas_forest_masses(canvas, proj, land_mask)",
            "def _draw_atlas_details(canvas, proj):",
            "for detail in ATLAS_DETAILS:",
            "if detail[\"kind\"] not in DEFAULT_ATLAS_DETAIL_KINDS:",
            "continue",
            "target_width = max(MIN_ATLAS_DETAIL_WIDTH, detail[\"width\"] * kind_scale)",
            "def _draw_base_land_texture(canvas, land_mask, germany_mask):",
            "_stable_hash(\"land_patch\"",
            "_stable_hash(\"land_texture\"",
            "def _draw_base_water_texture(canvas, water_mask):",
            "_draw_base_land_texture(canvas, land_mask, germany_mask)",
            "_draw_base_water_texture(canvas, water_mask)",
            "def _draw_named_water_bodies(canvas, proj, germany_mask):",
            "_draw_named_water_bodies(canvas, proj, germany_mask)",
            "_draw_atlas_details(canvas, proj)",
            "def _load_glyph(name):",
            "def _draw_glyph_center(canvas, proj, glyph_name, lon, lat, target_width):",
            "\"alps_range_1\"",
            "NAMED_WATER_BODIES = [",
            "NAMED_WATER_FILL = (47, 98, 111, 118)",
            "NAMED_WATER_SHORE = (66, 78, 47, 34)",
            '"id": "mueritz"',
            '"id": "bodensee"',
            '"id": "chiemsee"',
            '"id": "mueggelsee"',
            '"id": "wannsee_havel"',
            '"subtle": True',
            "def _draw_named_water_body(draw, proj, water_body):",
            "def _scale_alpha(color, scale):",
            "def _smooth_closed_points(points, subdivisions=6):",
            "for water_body in NAMED_WATER_BODIES:",
            "\"atlas_forest_pine_dense\"",
            "def _draw_alpine_mountains(draw, x, y, s):",
            "def _draw_forested_highland(draw, x, y, s):",
            "def _draw_border_highland(draw, x, y, s):",
            "def _draw_dotted_route(draw, pts):",
            "def _draw_field_patch(draw, proj, lon, lat, width, height):",
            "def _draw_marsh_patch(draw, proj, lon, lat, size):",
            "def _draw_castle_marker(draw, proj, lon, lat, size):",
            "MAP_LABELS = [",
            '"name": "Müritz"',
            '"name": "Rügen"',
            "NEIGHBOR_COUNTRY_LABELS = [",
            '"name": "Dänemark"',
            '"name": "Niederlande"',
            '"name": "Österreich"',
            "def _draw_neighbor_ground_texture(canvas, proj, neighbor_mask):",
            "def _draw_neighbor_country_labels(canvas, proj, neighbor_mask):",
            "_draw_neighbor_ground_texture(canvas, proj, neighbor_mask)",
            "_draw_neighbor_country_labels(canvas, proj, neighbor_mask)",
            "LiberationSerif-BoldItalic.ttf",
            "def _map_label_font(size):",
            "def _pixel_finish(canvas: Image.Image) -> Image.Image:",
            "quantize(colors=64",
            "ImageFilter.UnsharpMask(radius=0.7",
        ]:
            self.assertIn(expected, pipeline_text)

        self.assertNotIn("MAP_SIZE[0] // 2", pipeline_text)
        self.assertNotIn("Image.Resampling.NEAREST", pipeline_text)
        main_text = pipeline_text.split("def main():", 1)[1]
        self.assertNotIn("_draw_routes(canvas, proj, germany_mask)", main_text)
        self.assertNotIn("_draw_waterways(canvas, proj, germany_mask)", main_text)
        atlas_route_body = pipeline_text.split("def _draw_atlas_dotted_route", 1)[1].split("def _draw_routes", 1)[0]
        self.assertNotIn("draw.line", atlas_route_body)
        self.assertNotIn('"name": "Mueritz"', pipeline_text)
        self.assertNotIn('"name": "Ruegen"', pipeline_text)
        self.assertTrue(
            (ROOT / "assets" / "fonts" / "LiberationSerif-BoldItalic.ttf").exists(),
            "Atlas map label font must be vendored for reproducible map text.",
        )

        northern_lowlands = pipeline_text.split('"id": "northern_lowlands"', 1)[1].split("}", 1)[0]
        self.assertIn('"mountains": []', northern_lowlands)
        self.assertNotIn("(13.4, 52.5, 38)", pipeline_text)
        self.assertNotIn("(10.0, 53.5, 34)", pipeline_text)
        self.assertNotIn("(10.0, 53.0, 76)", pipeline_text)
        self.assertNotIn("(12.8, 53.1, 72)", pipeline_text)

    def test_sprite_outline_pipeline_is_reproducible(self) -> None:
        outline_text = (ROOT / "map_pipeline" / "outline_sprites.py").read_text(encoding="utf-8")
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")

        for expected in [
            "def _outline_sprite(source_path: Path, output_path: Path, radius: int, color: tuple[int, int, int, int]) -> None:",
            "ImageFilter.MaxFilter(radius * 2 + 1)",
            "ImageChops.subtract(outline_alpha, alpha)",
            "--source-dir",
            "--out-dir",
            "--prefix",
            "--radius",
            "--color",
        ]:
            self.assertIn(expected, outline_text)

        for path in [
            ROOT / "assets" / "sprites" / "outlined" / "icon_cable_gondola.png",
            ROOT / "assets" / "sprites" / "outlined" / "icon_funicular.png",
            ROOT / "assets" / "sprites" / "city_landmarks" / "outlined" / "city_berlin.png",
            ROOT / "assets" / "sprites" / "city_landmarks" / "outlined" / "city_hamburg.png",
            ROOT / "assets" / "sprites" / "city_landmarks" / "outlined" / "city_rostock.png",
        ]:
            self.assertTrue(path.exists(), f"Missing outlined sprite: {path}")

        self.assertIn('"res://assets/sprites/outlined/%s.png"', script_text)
        self.assertIn("city_landmarks/outlined/city_%s.png", script_text)

    def test_map_panel_initially_focuses_germany_when_present(self) -> None:
        script_text = (ROOT / "scripts" / "map_panel.gd").read_text(encoding="utf-8")

        for expected in [
            'const MAP_SCOPE_GERMANY := "germany"',
            'const MAP_SCOPE_ALL := "all"',
            "var map_scope := MAP_SCOPE_GERMANY",
            "map_scope = MAP_SCOPE_GERMANY if _has_germany_object() else MAP_SCOPE_ALL",
            "func _active_coordinate_bounds() -> Dictionary:",
            '"min_longitude": 4.5',
            '"max_longitude": 16.8',
            '"min_latitude": 43.2',
            '"max_latitude": 55.8',
            "func _coordinate_bounds_for_objects(source_objects: Array) -> Dictionary:",
            "func _germany_objects() -> Array[Dictionary]:",
            "func _has_germany_object() -> bool:",
            "func _is_germany_object(object_data: Dictionary) -> bool:",
            'value.contains("германия")',
            'value.contains("deutschland")',
            'value.contains("germany")',
            "layer.geo_bounds = _active_coordinate_bounds()",
            "var bounds := _active_coordinate_bounds()",
            "func _coordinates_inside_bounds(coordinates: Vector2, bounds: Dictionary) -> bool:",
            "if not _coordinates_inside_bounds(coordinates, bounds):",
            "return _is_germany_object(object_data)",
            "_update_map_reference_data()",
            '"⤢"',
            "Вписать все точки на экран",
        ]:
            self.assertIn(expected, script_text)

    def test_real_map_tiles_follow_up_is_documented(self) -> None:
        doc_text = (ROOT / "docs" / "real-map-tiles-plan.md").read_text(encoding="utf-8")

        for expected in [
            "Real map tiles follow-up",
            "OpenStreetMap",
            "MapLibre",
            "Android",
            "Raster tiles внутри Godot",
            "disk cache",
            "OfflineMapLayer",
            "© OpenStreetMap contributors",
            "feature flag",
        ]:
            self.assertIn(expected, doc_text)

    def test_main_scene_and_controller_wire_map_selection(self) -> None:
        scene_text = (ROOT / "scenes" / "Main.tscn").read_text(encoding="utf-8")
        main_text = (ROOT / "scripts" / "main_screen.gd").read_text(encoding="utf-8")

        self.assertIn('path="res://scripts/map_panel.gd"', scene_text)
        self.assertIn('name="MapPanel" type="PanelContainer"', scene_text)
        self.assertNotIn("Здесь будет карта объектов", scene_text)

        for expected in [
            'const MapPanelScript := preload("res://scripts/map_panel.gd")',
            "@onready var map_panel: MapPanelScript = %MapPanel",
            "map_panel.set_objects(objects)",
            "map_panel.object_selected.connect(_on_map_object_selected)",
            "func _on_map_object_selected(index: int) -> void:",
            "_select_object(index, false)",
            "map_panel.select_object(index)",
            "object_card.show_object(objects[index], storage_runtime_enabled)",
            "map_panel.set_objects(objects)",
        ]:
            self.assertIn(expected, main_text)


if __name__ == "__main__":
    unittest.main()
