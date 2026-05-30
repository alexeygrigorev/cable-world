# Handoff 2026-05-30 — Update 2

Дата записи: 2026-05-30 ~20:30 Europe/Berlin.

## Выполнено субагентами

### Map toolbar refactor (P1 — FIXED)
- Контролы карты (+/-/Вписать, фильтры) вынесены из canvas в тулбар HBoxContainer
- `zoom_controls`: VBoxContainer → HBoxContainer, горизонтально: `-`, `+`, `⤢`
- `filter_controls`: горизонтально: `Все`, `✓`, `○`
- `summary_label` и `selected_label` удалены (дублировали SelectedObjectLabel)
- Функции `_update_summary_label()` и `_update_selection_label()` удалены
- **Результат:** Overlapping children внутри ТочкиОбъектов → 0

### Map heights (P2 — IMPROVED)
- `MAP_MIN_HEIGHT`: 190 → 140
- `MAP_VIEW_HEIGHT`: 260 → 200
- `MAP_LANDSCAPE_MIN_HEIGHT`: 160 → 100
- MapPanel в Main.tscn: custom_minimum_size 280 → 200
- `_sync_map_canvas_height()`: landscape caps at MAP_LANDSCAPE_MIN_HEIGHT
- **Результат:** landscape clipping 35% → 7%

### Germany scope (сохранён)
- Все Germany scope функции восстановлены после рефакторинга
- `_draw_land_mass()`, `_draw_place_labels()` на месте

### Layout dump enhanced
- Добавлена симуляция кликов (tap marker, open object mode)
- Компактный вывод взаимодействия

### Object mode station buttons
- Причина ZERO SIZE найдена: первый объект (SkyTrain) не имеет станций
- Не баг кода, а seed data — только berlin-gaerten-der-welt имеет станции
- Рекомендация: добавить seed data для SkyTrain

## Текущие проверки

```
python3 -m unittest discover -s tests → 218 tests OK
godot --headless --path . --quit-after 1 → exit 0
git diff --check → OK
```

## Оставшиеся проблемы

### P3: ContentScroll clipping ~2%
ContentScroll на 1-2% выходит за ContentViewport. Косметический баг.

### P4: Landscape list/clipping
Landscape list 67% clipped — норма для скролла, но начальный вид перегружен.

### P5: Object mode ZERO SIZE
GridContainer station_buttons = 0 для объекта без станций.
Не баг, но стоит добавить fallback UI.

## Следующий агент

1. Прочитать `process.md`
2. Запустить `godot --headless --script res://tmp/layout_dump.gd --path .` — проверить
3. Решить: релиз v0.1.20 или доработка
4. Если релиз — поднять версию, закоммитить, тег, проверить CI

Рабочее дерево грязное, частичные правки от предыдущих агентов.
Новые правки НЕ вносились — только добавлены инструменты диагностики.

```
git status --short:
 M scenes/Main.tscn
 M scripts/main_screen.gd
 M scripts/map_panel.gd
 M scripts/object_card_panel.gd
 M tests/test_app_shell_contract.py
 M tests/test_map_panel_contract.py
?? docs/session-handoff-2026-05-30.md
?? docs/layout-dump.md
?? scripts/object_mode_panel.gd
?? scripts/object_mode_panel.gd.uid
?? tests/test_object_mode_ui_contract.py
?? tmp/layout_dump.gd
```

Проверки до правок:

```
python3 -m unittest tests.test_app_shell_contract tests.test_map_panel_contract tests.test_object_mode_ui_contract
→ 23 tests OK

godot --headless --path . --quit-after 1
→ exit 0, нет parse/script/compile ошибок

git diff --check
→ OK
```

## Инструмент: layout_dump.gd

Добавлен `tmp/layout_dump.gd` — текстовый дамп дерева Control-узлов.
Позволяет анализировать layout без скриншотов.

### Запуск

```bash
godot --headless --script res://tmp/layout_dump.gd --path .
```

Вывод: stdout + `tmp/layout_dump.txt`.

### Что показывает

Для каждого видимого Control-узла:

- `[V-]` видим / `[H-]` скрыт
- `pos=(x, y)` `size=(w, h)` — локальные
- `global: (x, y) -> (right, bottom) [W x H]` — экранные координаты
- `min=` вычисленный минимум, `custom_min=` заданный вручную
- `*** CLIPPED by parent 'X' ~Y% hidden` — обрезка родителем
- `*** ZERO SIZE` — видим но размер 0
- `Overlapping children` — видимые дети пересекаются

### Документация

Подробная документация: `docs/layout-dump.md`.

## Найденные проблемы (через layout_dump)

### P1: Map — контролы перекрывают канву карты

`МасштабКарты` (VBoxContainer, 48x160px) и `ФильтрКарты` (HBoxContainer, 168x48px)
абсолютно позиционированы внутри `ТочкиОбъектов` (map_layer) и перекрывают
`ПодвижнаяКарта` (маркеры и географию).

```
Overlapping children:
  'ПодвижнаяКарта' <-> 'МасштабКарты' overlap: (48 x 160)
  'ПодвижнаяКарта' <-> 'ФильтрКарты' overlap: (168 x 48)
```

**Решение:** вынести `zoom_controls` и `filter_controls` из `map_layer`
в отдельный `HBoxContainer` toolbar под картой, в layout flow.
Тип `zoom_controls` сменить с `VBoxContainer` на `HBoxContainer`.
Удалить `summary_label` и `selected_label` (дублируют SelectedObjectLabel в сцене).

### P2: Landscape — карта обрезана на 35%

Viewport 844x390: `Секции` обрезаны ContentScroll на ~35%.
MapPanel занимает 276px при видимой области 229px.
SelectedObjectLabel уходит за экран (y=476, viewport bottom=378).

**Решение:** уменьшить `MAP_VIEW_HEIGHT` и `MAP_LANDSCAPE_MIN_HEIGHT`.
Исправить `_sync_map_canvas_height()` — для landscape должна быть
меньшая высота. Уменьшить `custom_minimum_size` MapPanel в сцене.

### P3: ContentScroll вылезает за ContentViewport на ~2%

ContentScroll позиция (-3, 0), на ~2% выходит за bounds.
Мелкая проблема, но может давать артефакты.

### P4: Маркеры карты частично перекрываются

3 пары маркеров накладываются:
```
Маркер3 <-> Маркер20 overlap: (15 x 41)
Маркер7 <-> Маркер34 overlap: (17 x 29)
Маркер14 <-> Маркер34 overlap: (14 x 7)
```

`_spread_marker_position` не всегда находит свободное место при 21+
видимых маркерах на компактной карте.

## Роли и задачи

Согласно `process.md`:

- **orchestrator** (текущий агент) — режет работу на Issues, не правит код;
- **implementer** — делает изменения в отдельном worktree;
- **reviewer** — проверяет результат.

## Рекомендуемые Issues

### Issue: Map toolbar — вынести контролы из canvas

- **Пользовательская цель:** контролы карты (+/-/Вписать, фильтры) не
  перекрывают маркеры и географию, а расположены в компактном тулбаре
  под картой.
- **Файлы:** `scripts/map_panel.gd`, `scenes/Main.tscn`, `tests/test_map_panel_contract.py`
- **Ожидаемое поведение:**
  - `zoom_controls` и `filter_controls` добавлены в `HBoxContainer`
    toolbar после `map_layer` в `rows`, а не внутрь `map_layer`;
  - `zoom_controls` — `HBoxContainer`, кнопки горизонтально: `-`, `+`, `⤢`;
  - `filter_controls` — `HBoxContainer`, кнопки горизонтально: `Все`, `✓`, `○`;
  - toolbar имеет `HBoxContainer` с `filter_controls | spacer | zoom_controls`;
  - `summary_label` и `selected_label` удалены (дублируют SelectedObjectLabel);
  - переменные `summary_label` и `selected_label` удалены из класса;
  - функции `_update_summary_label()` и `_update_selection_label()` удалены;
  - вызовы `_update_selection_label()` удалены из `_refresh_marker_styles()`,
    `select_object()`, `set_map_filter()`;
  - вызовы `_update_summary_label()` удалены из `_refresh_markers()`,
    `set_map_filter()`;
  - `_on_map_layer_resized()` больше не позиционирует zoom_controls,
    filter_controls, selected_label;
  - `_refresh_markers()` обновляет только `_refresh_filter_buttons()`,
    `_refresh_marker_styles()`, `_update_empty_state()`,
    `_update_map_reference_data()`, `_position_markers()`;
  - расстояние между `map_layer` и toolbar: `separation = 4` в rows.
- **Проверки:**
  - `python3 -m unittest discover -s tests` — OK;
  - `godot --headless --path . --quit-after 1` — без ошибок;
  - `godot --headless --script res://tmp/layout_dump.gd --path .` — нет
    Overlapping children внутри ТочкиОбъектов;
  - `git diff --check` — OK.
- **Риски:** тест `test_map_panel_contract.py` проверяет
  `zoom_controls.position`, `filter_controls.position`,
  `selected_label.mouse_filter`, `summary_label.visible` —
  эти проверки нужно обновить под новую структуру.

### Issue: Map heights — уменьшить высоту карты

- **Пользовательская цель:** карта компактная, в landscape не обрезана,
  SelectedObjectLabel виден без скролла.
- **Файлы:** `scripts/map_panel.gd`, `scenes/Main.tscn`, `tests/test_map_panel_contract.py`
- **Ожидаемое поведение:**
  - `MAP_VIEW_HEIGHT := 200.0` (было 260);
  - `MAP_MIN_HEIGHT := 140.0` (было 190);
  - `MAP_LANDSCAPE_MIN_HEIGHT := 100.0` (было 160);
  - MapPanel в Main.tscn: `custom_minimum_size = Vector2(0, 200)`;
  - `_sync_map_canvas_height()` для landscape (`size.x > size.y`)
    использует `MAP_LANDSCAPE_MIN_HEIGHT` как максимум, не `MAP_VIEW_HEIGHT`.
  - в landscape: MapPanel + КартаЗаголовок + SelectedObjectLabel
    помещаются в видимую область ContentScroll без обрезки.
- **Проверки:**
  - те же что выше;
  - `godot --headless --script res://tmp/layout_dump.gd --path .` —
    в landscape viewport Section map: Секции CLIPPED < 15%.
- **Риски:** тесты проверяют конкретные константы — обновить.

### Зависимость

Issue Map heights зависит от Issue Map toolbar (toolbar добавляет
высоту под картой). Сначала toolbar, потом heights.

## Следующий агент

1. Прочитать `process.md`.
2. Прочитать `docs/session-handoff-2026-05-30.md` (оригинальный handoff).
3. Прочитать `docs/layout-dump.md` и понять инструмент.
4. Запустить `godot --headless --script res://tmp/layout_dump.gd --path .`
   и прочитать вывод — убедиться что проблемы воспроизводятся.
5. Создать Issue на GitHub для Map toolbar.
6. Реализовать в отдельном worktree.
7. Запустить все проверки из Issue.
8. Запустить layout_dump — убедиться что overlap ушёл.
9. Если всё OK — запросить review.
