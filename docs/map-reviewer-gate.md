# Map Reviewer Gate

Дата: 2026-05-31.

Этот gate обязателен для всех задач, которые меняют карту, map assets, map runtime, export payload или UX карты. Он дополняет общий процесс: `issue -> worktree -> implementer -> reviewer -> одна reviewed интеграция`.

Reviewer не принимает карту по описанию implementer. Reviewer обязан открыть свежий live Web build, сделать screenshot review и поставить `REJECT`, если карта не соответствует `10/10` из `docs/map-quality-rubric.md`.

## Role Contract

Reviewer должен:

- работать в отдельном review контексте для конкретного Issue, не смешивая изменения между задачами;
- проверить, что implementer работал в issue-specific worktree и не трогал запрещенный scope;
- запустить или проверить live map на `http://127.0.0.1:9000/`, либо явно указать documented URL/commands, если порт занят и `scripts/serve-web.sh` выбрал следующий порт;
- получить свежие screenshots через Playwright и просмотреть их глазами;
- проверить map interaction: pan, zoom, clickability, отсутствие marker jitter;
- сверить визуальное качество с `docs/map-quality-rubric.md`;
- записать итог: `PASS` только для карты `10/10`; `REJECT` для всего, что ниже.

Если карта выглядит как текущий baseline около `6/10`, это не pass. Такой результат может быть технически полезным prototype, но reviewer обязан вернуть задачу на доработку.

## Required Verification Commands

Выполнять из корня worktree задачи:

```bash
python3 -m unittest discover -s tests
```

Godot import and smoke run:

```bash
godot --headless --path . --import --quit
godot --headless --path . --quit-after 1
```

Web export:

```bash
rm -rf build/web
mkdir -p build/web
godot --headless --path . --export-release Web build/web/index.html
```

Serve the exact Web build for review. Preferred URL is `http://127.0.0.1:9000/`; if the port is busy, the script prints the next free `9000..9999` URL and reviewer must use that URL consistently:

```bash
scripts/serve-web.sh --no-export
```

In another shell, set the URL printed by the server:

```bash
REVIEW_URL=http://127.0.0.1:9000/
```

Playwright screenshots. If Playwright is already installed:

```bash
OUT_DIR=tmp/map-review/issue-71 URL="$REVIEW_URL" node scripts/verify-web-map.mjs
```

If Playwright is not available locally, install/use it outside the project dependency graph, then run the same script:

```bash
PLAYWRIGHT_DIR=/tmp/cable-world-playwright
npm install --prefix "$PLAYWRIGHT_DIR" playwright
"$PLAYWRIGHT_DIR/node_modules/.bin/playwright" install chromium
NODE_PATH="$PLAYWRIGHT_DIR/node_modules" OUT_DIR=tmp/map-review/issue-71 URL="$REVIEW_URL" node scripts/verify-web-map.mjs
```

Gzip and cache headers for Web payload:

```bash
for asset in index.wasm index.pck index.js; do
  test -f "build/web/${asset}.gz"
  curl -fsSI -H "Accept-Encoding: gzip" "${REVIEW_URL%/}/${asset}" \
    | tr -d '\r' \
    | grep -Ei '^(Content-Encoding: gzip|Cache-Control: no-store)$'
done
```

Reviewer may add extra manual browser/device checks, but may not skip the commands above for map acceptance.

## Screenshot Review

Review at minimum:

- `mobile-390x844-initial.png`;
- `mobile-390x844-after-marker-click.png`;
- `mobile-390x844-after-drag.png`;
- `desktop-1280x800-initial.png`;
- `desktop-1280x800-after-marker-click.png`;
- `desktop-1280x800-after-drag.png`.

The reviewer must inspect screenshots for:

- first-glance map quality: it must read as a warm RPG/atlas map in 1-2 seconds, not as GIS/procedural underlay;
- city pictograms for visible major cities, including Nürnberg, Leipzig and other visible city labels, without missing or duplicated city landmarks;
- small trees, houses, villages, chapels, mills, ruins and other tiny objects: they must be readable at the shown scale or removed;
- marker jitter after pan/zoom: city landmarks, transport icons and labels must stay visually stable and attached to the map;
- pan/zoom behavior: drag must feel direct, zoom controls must be predictable, touch pinch/magnify must not accidentally change zoom;
- clickability: visible transport objects must open/select correctly and drag must not be swallowed by markers;
- geographic accuracy: cities, coast, lakes, islands and relief must be plausible, with Rostock near the Baltic and Dresden not visually in Czechia;
- Alps readability: the Alpine edge must be a real, strong, cross-border massif, not a random southern sticker;
- Harz readability: Harz must be visible as a central mountain region connected to nearby objects, even if visually exaggerated for gameplay;
- labels: city labels must be legible, close to their pictograms, consistently sized except for intentional hierarchy such as Berlin;
- clutter: details, routes and terrain marks must not compete with markers or create technical stripes/noise.

## Acceptance Rule

`PASS` requires all of the following:

- required commands pass;
- live map loads from the reviewed Web export;
- gzip responses are confirmed for `.wasm`, `.pck` and `.js`;
- screenshots exist and were reviewed;
- interaction review finds no pan, zoom, clickability or jitter blocker;
- geography review finds no visible major mismatch;
- visual review scores `10/10` by `docs/map-quality-rubric.md`.

Anything below `10/10` is `REJECT` for this gate. The reviewer should still record the estimated score and the specific blockers, for example: "current map is about 6/10; reject because city pictograms are missing for visible Nürnberg/Leipzig, small trees read as noise, jitter remains during pan, and Alps/Harz are not readable enough."

## Review Record Template

```text
Issue:
Worktree:
Branch:
Reviewed commit:
Live URL:
Screenshot directory:

Commands:
- python3 -m unittest discover -s tests: PASS/FAIL
- godot --headless --path . --import --quit: PASS/FAIL
- godot --headless --path . --quit-after 1: PASS/FAIL
- godot --headless --path . --export-release Web build/web/index.html: PASS/FAIL
- scripts/serve-web.sh --no-export: PASS/FAIL
- Playwright screenshots: PASS/FAIL
- gzip header check: PASS/FAIL

Rubric score:
Decision: PASS/REJECT
Blockers:
Next action:
```
