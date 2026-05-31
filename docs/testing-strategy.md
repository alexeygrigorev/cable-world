# Testing Strategy

Дата: 2026-05-31.

Этот документ фиксирует границу между Python-проверками проекта и Godot-native тестами. Цель границы: не превращать Python в замену runtime/UI тестам Godot, но сохранить быстрые проверки для map pipeline, данных, схем и экспортного payload.

## Быстрый gate

Минимальный gate для обычного инкремента запускается из корня worktree:

```bash
python3 -m unittest discover -s tests
godot --headless --path . --import --quit
godot --headless --path . --script tests/godot_runtime_runner.gd
godot --headless --path . --quit-after 1
```

Для текущего SQLite runtime contract дополнительно используется Python harness, который запускает Godot script внутри engine runtime:

```bash
python3 -m unittest tests.test_godot_storage_contract
```

Когда появится GdUnit4 или другой Godot-native runner, runtime/UI задачи должны добавлять его команду в issue acceptance и release gate рядом с командами выше.
Минимальный встроенный runner уже доступен без внешнего addon:

```bash
godot --headless --path . --script tests/godot_runtime_runner.gd
```

Он выполняет GDScript smoke/runtime checks из `tests/godot_runtime_smoke.gd` и возвращает non-zero при failure. Новые маленькие runtime checks можно добавлять отдельными `test_*` методами или подключать новым script path в runner.
Для локальной проверки другого набора scripts runner принимает comma-separated override через `MIR_TROSSOV_GODOT_RUNTIME_TEST_SCRIPTS`.

## Headless diagnostics

Issue #65 audit split current Godot headless output into project-owned problems and known engine/headless teardown diagnostics.

Project-owned findings fixed in the runtime/test layer:

- run `godot --headless --path . --import --quit` before headless scene checks in a fresh worktree; otherwise missing `.godot/imported/*.ctex` and `.fontdata` resources create noisy load errors and shutdown leaks;
- `MapPanel._on_map_layer_resized()` must not write `size` directly to full-rect anchored child controls during `_ready()` resize notifications;
- runtime tests that instantiate `Main.tscn` must use `MIR_TROSSOV_DATABASE_PATH` to isolate SQLite `user://` data and avoid stale database locks;
- `tests/godot_runtime_runner.gd` treats a loaded but non-instantiable GDScript as a failure, so parse/load errors cannot be hidden behind a zero-check pass.

Known remaining Godot 4.6.3 headless diagnostics:

- `godot --headless --path . --quit-after 1` exits `0` but can print `CanvasItem`, `DummyTexture`, `ShapedTextDataAdvanced` and `FontAdvanced` leak diagnostics after loading the live main scene;
- the full runtime runner can still print `CanvasItem`/`FontAdvanced` diagnostics when a test instantiates `Main.tscn`;
- the narrower smoke runner without live `Main.tscn` is clean after import:

```bash
MIR_TROSSOV_GODOT_RUNTIME_TEST_SCRIPTS=res://tests/godot_runtime_smoke.gd godot --headless --path . --script tests/godot_runtime_runner.gd
```

These remaining diagnostics are treated as known headless teardown noise for now, not as proof of a project resource leak. New parse errors, missing resources, SQL lock errors, anchor warnings, non-zero exit codes, or new leak categories are not covered by this exception and should fail review.

## UI/static migration inventory

File-level classification for current `tests/test_*contract.py` files:

| Contract files | Primary layer | Decision |
| --- | --- | --- |
| `test_map_panel_contract.py`, `test_map_geography_audit.py`, `test_europe_expansion_plan_contract.py`, `test_europe_catalog_research_contract.py`, `test_europe_seed_review_contract.py`, `test_russia_research_contract.py`, `test_russia_seed_review_contract.py`, `test_visual_style_directions_contract.py` | map pipeline/data/geography | Keep Python: data, source asset and geography contracts are not runtime UI checks. |
| `test_android_export_contract.py`, `test_export_payload_contract.py`, `test_web_serve_contract.py`, `test_infra_reproducibility_contract.py`, `test_1_0_readiness_contract.py`, `test_map_review_bundle_contract.py` | export/release/process | Keep Python: these assert files, workflows, scripts and release gates. |
| `test_data_model_contract.py`, `test_project_contract.py`, `test_collection_contract.py`, `test_storage_contract.py`, `test_media_metadata_contract.py`, `test_i18n_contract.py` | schema/domain/storage/static | Keep Python: these are cheap source/data contracts. Runtime storage remains covered by `test_godot_storage_contract.py`. |
| `test_demo_catalog_europe_contract.py`, `test_demo_catalog_russia_contract.py` | catalog/data | Keep Python: catalog completeness and seed geography are data contracts. |
| `test_app_shell_contract.py`, `test_object_list_contract.py`, `test_object_card_contract.py`, `test_memory_screen_contract.py`, `test_object_mode_contract.py`, `test_object_mode_ui_contract.py`, `test_observer_mode_contract.py`, `test_ride_mode_contract.py`, `test_v3_scene_contract.py`, `test_v3_scene_modes_contract.py`, `test_engineering_scene_contract.py` | UI/static scene | Keep static coverage, but migrate user-facing runtime behavior to Godot when touched. #83 duplicates the map/list shell and object-list filtering checks natively. |
| `test_godot_runtime_runner_contract.py`, `test_godot_storage_contract.py`, `test_testing_strategy_contract.py` | test infrastructure/docs/runtime bridge | Keep Python: these verify the runner, bridge command and strategy docs. |

Migrated high-value runtime checks:

| Python contract | Runtime risk | Decision |
| --- | --- | --- |
| `tests/test_app_shell_contract.py::test_map_list_toggle_opens_secondary_list_without_breaking_map_first_chrome` | Map-first chrome, icon-only map/list toggle and section visibility can regress while static source strings still exist. | Duplicate temporarily: `tests/godot_runtime_app_shell.gd::test_main_scene_map_list_toggle_runtime` loads `Main.tscn` and verifies live section/chrome state. Keep Python as cheap scene/source guard. |
| `tests/test_object_list_contract.py::test_list_panel_filters_visible_objects_before_emitting_selection` | Filter composition, row rebuilding, empty-state visibility and emitted source indices depend on runtime state. | Duplicate temporarily: `tests/godot_runtime_app_shell.gd::test_object_list_filtering_and_selection_runtime` exercises `ObjectListPanel` behavior directly in Godot. Keep Python static checks for helper/API presence. |
| `tests/test_object_list_contract.py::test_list_section_has_left_safe_area_without_horizontal_overflow` | Layout overflow is scene/runtime-sensitive, but needs visual/device review to prove pixels. | Keep Python static contract for now; migrate later with screenshot/runtime layout bounds coverage. |

## Что проверяет Python

Python остается владельцем проверок, где запуск Godot runtime не нужен или является только внешним smoke/packaging шагом:

- map generation pipeline: генерация, адаптация и аудит source/runtime map assets;
- geographic audits, DEM/data contracts и static checks по координатам;
- JSON/schema/staging validation для import candidates и seed review;
- catalog/data/model contracts: обязательные поля, страны, статусы, отсутствие дублей;
- export payload contracts: включение нужных файлов и исключение source assets из runtime export;
- release/process/docs contracts: workflow gates, чеклисты, protocol docs;
- небольшие статические аудиты GDScript/scene файлов, например наличие scene resources, typed scripts и user-facing строк.

Текущие Python tests по назначению:

- map pipeline и география: `tests/test_map_panel_contract.py`, `tests/test_map_geography_audit.py`, `tests/test_export_payload_contract.py`, `tests/test_android_export_contract.py`;
- staging/schema/data pipeline: `tests/test_import_candidate_collector.py`, `tests/test_staging_candidate_validator.py`, `tests/test_import_review_preview.py`, `tests/test_osm_wikidata_import_plan.py`;
- catalog и доменные контракты: `tests/test_project_contract.py`, `tests/test_data_model_contract.py`, `tests/test_demo_catalog_europe_contract.py`, `tests/test_demo_catalog_russia_contract.py`, `tests/test_collection_stats.py`, `tests/test_achievements.py`;
- UI/static scene contracts: `tests/test_app_shell_contract.py`, `tests/test_object_mode_ui_contract.py`, `tests/test_map_panel_contract.py`, `tests/test_v3_scene_contract.py`;
- release/process/docs contracts: `tests/test_release_mvp_checklist.py`, `tests/test_1_0_readiness_contract.py`, `tests/test_infra_reproducibility_contract.py`;
- Godot smoke/bridge checks: `tests/test_godot_headless.py`, `tests/test_godot_storage_contract.py`.

Python может читать `.gd`, `.tscn`, JSON, SQL, PNG metadata и export artifacts. Python не должен утверждать, что пользовательский runtime сценарий работает, если этот сценарий требует engine lifecycle, input, focus, layout, signals или scene tree behavior.

## Что проверяет Godot-native

Godot-native tests являются дефолтом для новых runtime/UI issues. Если задача меняет GDScript runtime behavior, scene interaction или UI state, acceptance criteria должны требовать Godot-native проверку или явно объяснять, почему текущий Godot smoke достаточен.

Godot-native зона ответственности:

- GDScript units и scene behavior;
- UI state transitions, focus, visibility, disabled/enabled state и navigation;
- input gestures: tap, drag, pan, zoom, pinch, back navigation;
- map marker transforms, clickability, selection и отсутствие jitter во время pan/zoom;
- runtime resource loading, signals, timers, storage adapter behavior и platform-specific runtime paths;
- visual/runtime regressions, которые видны только после запуска scene tree.

До подключения полноценного Godot-native runner минимальный runtime gate для таких задач:

```bash
godot --headless --path . --import --quit
godot --headless --path . --script tests/godot_runtime_runner.gd
godot --headless --path . --quit-after 1
```

Если задача затрагивает SQLite runtime, запускать также:

```bash
python3 -m unittest tests.test_godot_storage_contract
```

Для UI/map задач этот gate не заменяет reviewer-проверку. Map-related changes дополнительно проходят [Map Reviewer Gate](map-reviewer-gate.md) с Web export, live serve, Playwright screenshots и ручной оценкой карты.

## Правило для новых issues

Новые pipeline/data/schema/export задачи по умолчанию получают Python tests.

Новые runtime/UI/input/scenes задачи по умолчанию получают Godot-native tests. Если подходящего runner еще нет, issue должен включать один из вариантов:

- добавить минимальный Godot script/GdUnit4 тест как часть задачи;
- записать, что задача ограничена static contract и не претендует на runtime acceptance;
- передать runtime acceptance в отдельный follow-up issue до релиза.

Release protocol должен называть оба класса проверок явно: Python pipeline/static contracts и Godot runtime/import smoke. Формулировка "запустить только `python3 -m unittest discover -s tests`" недостаточна для релизного решения.
