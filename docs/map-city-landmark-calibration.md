# City Landmark Coordinate Calibration

This contract protects runtime city landmark anchors against drift from real geography.

Runtime city labels in `scripts/map_panel.gd` use lon/lat coordinates.
They use the same Mercator bounds as the generated Germany underlay.
The source coordinate remains the city anchor.
Icon offsets are only for visual attachment on the stylized coastline.

Protected #55 anchors:

- Hamburg: `Vector2(9.9937, 53.5511)`, visible, pictogram `hamburg`.
- Berlin: `Vector2(13.4050, 52.5200)`, visible, pictogram `berlin`.
- Dresden: `Vector2(13.7373, 51.0504)`, visible, pictogram `dresden`.
- Köln: `Vector2(6.9603, 50.9375)`, visible, pictogram `cologne`.
- Stuttgart: `Vector2(9.1829, 48.7758)`, visible, pictogram `stuttgart`.
- München: `Vector2(11.5820, 48.1351)`, visible, pictogram `munich`.
- Bremen: `Vector2(8.8017, 53.0793)`, hidden until town zoom, no pictogram.
- Hannover: `Vector2(9.7320, 52.3759)`, hidden until town zoom, no pictogram.
- Leipzig: `Vector2(12.3731, 51.3397)`, hidden until town zoom, no pictogram.
- Nürnberg: `Vector2(11.0767, 49.4521)`, hidden until town zoom, no pictogram.

Rostock uses `Vector2(0.0, 52.0)` as a manual visual offset. This keeps the coastal city pictogram attached to land on the stylized Baltic coastline. The real city coordinate remains `Vector2(12.0991, 54.0924)`.

Contract coverage:

- `tests/test_map_panel_contract.py` protects exact coordinates, city kind, icon IDs, default-visible pictogram coverage, hidden bare labels for major towns without pictograms, label attachment to icon rectangles, and broad geographic ordering.
- `tests/test_map_geography_audit.py` keeps the Rostock landward offset in the runtime landmark audit and checks northern coastal landmarks against Germany geometry when map pipeline dependencies are installed.
