# UI Review Gate

Этот gate применяется к UI-задачам, которые меняют первый экран, list mode, map/list toggle или возврат из списка на карту. Он не заменяет [Map Reviewer Gate](map-reviewer-gate.md): если задача меняет карту, маркеры, terrain, glyphs, pan/zoom или географию, нужно проходить оба gate.

## Decision

Reviewer обязан поставить ровно одно решение:

- `ACCEPT` - только если screenshots и Godot-native runtime checks подтверждают весь scope issue.
- `REJECT` - если есть визуальная регрессия, сломанный flow, слабая читаемость, чужой стиль списка, неподходящая пиктограмма, потеря состояния карты или недостаточные проверки.

Без явного `ACCEPT` UI-задача не интегрируется и не идет в release.

## Required Screenshots

Для задач про list mode, map/list toggle и map-first shell reviewer сохраняет и глазами проверяет:

- `mobile-390x844-map.png` - стартовая fullscreen-карта.
- `mobile-390x844-list.png` - список после нажатия map/list toggle.
- `landscape-844x390-map.png` - карта в landscape.
- `landscape-844x390-list.png` - список в landscape.

Воспроизводимая команда:

```bash
xvfb-run -a godot --path . --script scripts/capture_ui_review_screenshots.gd
```

Скрипт пишет PNG в `tmp/ui-review/`. Reviewer может добавить Playwright/Web screenshots, но эти four Godot-native screenshots остаются обязательным минимумом для list/toggle задач.

## Runtime Checks

Перед screenshot review должны пройти:

```bash
godot --headless --path . --script tests/godot_runtime_runner.gd
```

Минимальные Godot-native инварианты:

- приложение стартует на fullscreen-карте, list section скрыт;
- на карте есть только компактный icon-only map/list toggle, без текстовой кнопки списка;
- map/list toggle открывает list mode;
- list mode не возвращает generic global navigation chrome;
- list mode имеет atlas-style header/ledger и явный return-to-map control;
- return-to-map восстанавливает pan, zoom, выбранный объект и выбранный map marker;
- list filtering, row rebuild, empty state и row selection работают в runtime;
- scroll/tap behavior не должен вызывать случайный выбор при скролле.

Python static tests могут оставаться дополнительными contract guards, но не заменяют Godot-native runtime checks для user-facing UI behavior.

## Visual Checklist

Reviewer проверяет screenshots по этим критериям:

- **Map-first:** первый экран остается картой, без title/header/list panel/объясняющего текста поверх карты.
- **Toggle:** пиктограмма переключения понятна, atlas-style, icon-only на карте, не выглядит как generic hamburger/list button и не сливается с zoom controls.
- **List style parity:** список выглядит частью той же atlas UI-системы, что и карта: parchment/ledger palette, consistent borders, row states, typography and spacing.
- **Return state:** в list mode есть понятный парный control для возврата на карту; после возврата карта сохраняет состояние.
- **Mobile readability:** на `390x844` строки, controls and touch targets readable; текст не обрезается и не налезает.
- **Landscape stability:** на `844x390` layout не растягивается некрасиво, список не превращается в чужой desktop panel, карта не теряет основной фокус.
- **Russian UI:** все видимые строки на русском.

## Review Report Template

```markdown
Decision: REJECT
Issue:
Commit:

Runtime:
- godot --headless --path . --script tests/godot_runtime_runner.gd: PASS/FAIL

Screenshots Checked:
- tmp/ui-review/mobile-390x844-map.png: checked/not checked
- tmp/ui-review/mobile-390x844-list.png: checked/not checked
- tmp/ui-review/landscape-844x390-map.png: checked/not checked
- tmp/ui-review/landscape-844x390-list.png: checked/not checked

Verdict:
- Map-first:
- Toggle:
- List style parity:
- Return state:
- Mobile readability:
- Landscape stability:
- Russian UI:

Blockers if REJECT:
- ...
```

`Decision: ACCEPT` разрешен только после просмотра всех required screenshots и зеленых runtime checks.
