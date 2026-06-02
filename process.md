# Процесс работы

Процесс адаптирует подход PocketShell под «Мир Троссов»: маленькие задачи, явный контракт через GitHub Issues, отдельные worktree на задачу и одна проверенная интеграция за раз.

## Контракт задачи

Каждая задача начинается с GitHub Issue. Issue должен содержать:

- пользовательскую цель;
- границы файлов и модулей;
- ожидаемое поведение;
- проверки, которые должны пройти;
- риски для данных, интерфейса или процесса.

Без Issue можно делать только короткие разведочные правки в черновом каркасе, если владелец проекта явно разрешил это в текущем диалоге.

## Роли

- orchestrator уточняет цель, режет работу на Issue и следит за очередью;
- implementer делает изменения в отдельном worktree для конкретного Issue;
- reviewer проверяет результат, запускает проверки и требует доработки при рисках.

Для задач по карте reviewer обязан применять строгий [Map Reviewer Gate](docs/map-reviewer-gate.md): открыть свежий live Web build на `http://127.0.0.1:9000/` или documented fallback port, сделать Playwright screenshots, проверить pan/zoom/clickability/jitter/geography/labels/clutter и отклонить результат, если карта ниже `10/10`.

Для UI-задач reviewer применяет [UI Review Gate](docs/ui-review-gate.md): `mobile-390x844-map.png`, `mobile-390x844-list.png`, `landscape-844x390-map.png`, `landscape-844x390-list.png`, Godot runtime checks и явное `ACCEPT` или `REJECT`. Без явного `ACCEPT` UI-инкремент не интегрируется.

## Worktree

Для каждой задачи создается отдельный worktree от актуальной интеграционной ветки. Название ветки должно ссылаться на Issue, например `issue-12-local-journal`.

Правила:

- один worktree обслуживает одну задачу;
- изменения не смешиваются между Issue;
- незавершенная задача не блокирует подготовку следующей, но не попадает в интеграцию без review;
- конфликтующие изменения решаются явно, без скрытого отката чужой работы.

## Интеграция

В интеграцию попадает только одна reviewed-задача за раз. После слияния запускаются быстрые проверки и, когда появится Godot в CI, headless-сценарии.

Последовательность для любой задачи остается строгой: Issue задает контракт, implementer работает в отдельном worktree, reviewer проверяет этот worktree, затем интегрируется ровно одна reviewed-задача. Незавершенные, непроверенные или rejected map changes не попадают в интеграцию.

## Проверки

Граница тестов описана в [Testing Strategy](docs/testing-strategy.md): Python отвечает за map pipeline, data/schema/export и небольшие static contracts; Godot-native проверки отвечают за GDScript runtime, UI, input и scene behavior.

Сейчас обязательный быстрый gate:

```bash
python3 -m unittest discover -s tests
godot --headless --path . --import --quit
godot --headless --path . --script tests/godot_runtime_runner.gd
godot --headless --path . --quit-after 1
```

Команда `python3 -m unittest discover -s tests` покрывает Python pipeline/static contracts, но не заменяет runtime/UI тесты Godot. Новые runtime/UI/input/scenes issues должны по умолчанию требовать Godot-native тест или явно фиксировать, что задача ограничена static contract.

Для map-related задач обязательный reviewer набор расширяется документом [Map Reviewer Gate](docs/map-reviewer-gate.md): full Python tests, Godot import/run, Web export, local serve на `:9000`, Playwright screenshots и gzip header check.

Позже обязательный набор расширяется:

- GdUnit4;
- проверка миграций SQLite;
- ручная проверка карты и вложений на целевых устройствах.

## Релиз

- Релиз делается после работающего проверяемого инкремента, а не после большой пачки фич.
- APK нельзя выпускать с красными тестами, Godot parse/load errors или reviewer `REJECT`.
- Если текущий APK непригоден для телефона, это релизный блокер выше roadmap-фич.
- При релизе обновляются `VERSION`, Android `version/code` и `version/name`; `package/unique_name="com.mirtrossov.app"` не менять без отдельного решения.
- Релиз создается annotated tag `vX.Y.Z`; release assets должны содержать Android APK.

## Каталог

- Production seed не принимает OSM/Wikidata автоматически без ручной проверки.
- Импорт идет через staging JSON, validator, collector prototype, review states `candidate`/`approved`/`rejected` и preview только из `approved`.
- `operational_status` остается `unknown`, если нет свежего официального источника.
