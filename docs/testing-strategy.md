# Testing Strategy

Дата: 2026-05-31.

Этот документ фиксирует границу между Python-проверками проекта и Godot-native тестами. Цель границы: не превращать Python в замену runtime/UI тестам Godot, но сохранить быстрые проверки для map pipeline, данных, схем и экспортного payload.

## Быстрый gate

Минимальный gate для обычного инкремента запускается из корня worktree:

```bash
python3 -m unittest discover -s tests
godot --headless --path . --import --quit
godot --headless --path . --quit-after 1
```

Для текущего SQLite runtime contract дополнительно используется Python harness, который запускает Godot script внутри engine runtime:

```bash
python3 -m unittest tests.test_godot_storage_contract
```

Когда появится GdUnit4 или другой Godot-native runner, runtime/UI задачи должны добавлять его команду в issue acceptance и release gate рядом с командами выше.

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
