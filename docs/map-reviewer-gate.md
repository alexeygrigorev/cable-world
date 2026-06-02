# Map Reviewer Gate

Этот gate обязателен для задач, которые меняют карту, map assets, map runtime, export payload или UX карты.

Reviewer не принимает карту по описанию implementer. Нужны fresh Web build, screenshots, ручной visual review и решение `ACCEPT`/`REJECT`. Для integration карта должна быть `10/10`; все ниже возвращается на доработку.

## Role Contract

Reviewer должен:

- работать в отдельном review контексте для конкретного Issue, не смешивая изменения между задачами;
- проверить, что implementer работал в issue-specific worktree и не трогал запрещенный scope;
- запустить или проверить live map на `http://127.0.0.1:9000/`, либо явно указать documented URL/commands, если порт занят и `scripts/serve-web.sh` выбрал следующий порт;
- получить свежие screenshots через Playwright и просмотреть их глазами;
- проверить map interaction: pan, zoom, clickability, отсутствие marker jitter;
- сверить visual quality, geography, interaction и glyph scale по критериям ниже;
- записать итог: `ACCEPT` только для карты `10/10`; `REJECT` для всего, что ниже.

Если карта выглядит как текущий baseline около `6/10`, это не pass. Такой результат может быть технически полезным prototype, но reviewer обязан вернуть задачу на доработку.

## Commands

Выполнять из корня worktree задачи:

```bash
python3 -m unittest discover -s tests
```

Godot import and smoke run:

```bash
godot --headless --path . --import --quit
godot --headless --path . --quit-after 1
```

Canonical review bundle:

```bash
ISSUE=issue-81 scripts/create-map-review-bundle.sh
```

This command rebuilds/exports the Web build through `scripts/serve-web.sh`, serves the exact reviewed build on `http://127.0.0.1:9000/` or the next documented free port, collects Playwright screenshots, checks gzip/no-cache headers, copies build metadata and writes `review-report.md`.

The bundle contains:

- `screenshots/` with all required screenshots;
- `web-build.json` copied from the reviewed live build;
- `index.reviewed.html` with the reviewed build stamp;
- `reviewed-commit.txt`;
- `git-status.txt`;
- `logs/serve-web.log`;
- `logs/playwright-screenshots.log`;
- `logs/header-check.log`;
- `review-report.md`.

`review-report.md` starts as `Decision: REJECT`. Reviewer may change it to `ACCEPT` only after naming every screenshot as checked and scoring the touched scope `10/10`.

If Playwright is not available locally, install/use it outside the project dependency graph, then run the same bundle command:

```bash
PLAYWRIGHT_DIR=/tmp/cable-world-playwright
npm install --prefix "$PLAYWRIGHT_DIR" playwright
"$PLAYWRIGHT_DIR/node_modules/.bin/playwright" install chromium
PLAYWRIGHT_PACKAGE="$PLAYWRIGHT_DIR/node_modules/playwright" ISSUE=issue-81 scripts/create-map-review-bundle.sh
```

Manual fallback/debug sequence, if the bundle command needs to be inspected step by step:

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

Gzip and cache headers for Web payload. The server must disable reuse of stale Web exports and serve gzip for the Godot payload plus map PNGs:

```bash
for asset in index.html index.wasm index.pck index.js; do
  test -f "build/web/${asset}.gz"
  curl -fsSI -H "Accept-Encoding: gzip" "${REVIEW_URL%/}/${asset}" \
    | tr -d '\r' \
    | grep -Ei '^(Content-Encoding: gzip|Cache-Control: no-store, no-cache, must-revalidate, max-age=0|Pragma: no-cache|Expires: 0)$'
done
for png in build/web/*.png; do
  test -e "$png" || continue
  asset="$(basename "$png")"
  test -f "${png}.gz"
  curl -fsSI -H "Accept-Encoding: gzip" "${REVIEW_URL%/}/${asset}" \
    | tr -d '\r' \
    | grep -Ei '^(Content-Encoding: gzip|Cache-Control: no-store, no-cache, must-revalidate, max-age=0|Pragma: no-cache|Expires: 0)$'
done
curl -fsS "${REVIEW_URL%/}/.web-build.json" | grep -F '"build_id"'
curl -fsS "${REVIEW_URL%/}/index.html" | grep -F 'name="cable-world-web-build"'
scripts/serve-web.sh --check-headers
```

Reviewer may add extra manual browser/device checks, but may not skip the commands above for map acceptance.

## Screenshots

Review at minimum:

- `mobile-390x844-initial.png`;
- `mobile-390x844-zoom-150.png`;
- `mobile-390x844-zoom-200.png`;
- `mobile-390x844-after-marker-click.png`;
- `mobile-390x844-after-drag.png`;
- `desktop-1280x800-initial.png`;
- `desktop-1280x800-after-marker-click.png`;
- `desktop-1280x800-after-drag.png`.

## Quality Criteria

Reviewer must inspect:

- first-glance quality: warm RPG/atlas map in 1-2 seconds, not a GIS/procedural underlay;
- aspect ratio: the map is not stretched to viewport;
- interaction: pan, drag, zoom and click work naturally;
- stability: transport markers, city landmarks and labels do not jitter or detach during pan/zoom;
- geography: cities, coast, lakes, islands and relief are plausible;
- relief: Alps are a real cross-border massif through Austria, Switzerland and northern Italy; Harz, Black Forest, Erzgebirge and other massifs are recognizable and not random stickers;
- lowlands: large mountains are absent from real lowlands such as North German Plain;
- city layer: visible major city labels have city pictograms/landmarks, without missing or duplicated landmarks;
- glyph scale: trees, houses, villages, chapels, mills, ruins and details are readable at screenshot scale or removed;
- labels: city labels stay close to pictograms and use consistent hierarchy;
- clutter: routes and terrain marks do not look like technical stripes or visual noise;
- UI: fullscreen map remains primary, with only minimal map UI over it;
- Web payload: gzip/no-cache/build metadata checks pass.

## Score Caps

These caps override averages:

- Procedural/GIS-looking map: max `4/10`.
- No adventure atlas feeling in 1-2 seconds: max `5/10`.
- Art layers look unrelated or randomly pasted: max `6/10`.
- Technical stripes, cut artifacts, dust-like details or tiny unreadable glyphs: max `6/10`.
- Marker jitter, detached overlays or unstable labels: max `6/10`.
- Missing city pictograms for visible major city labels: max `6/10`.
- Mountains/relief visibly wrong or random: max `6/10`.
- Alps not source-backed or not cross-border: max `6/10`.
- Harz not readable as central mountain region: max `7/10`.
- Map looks empty or boring at default/mobile viewport: max `6/10`.
- User still reports "looks bad" for the reviewed build: max `5/10`.

The score must be based on the screenshots and live build, not on implementation effort.

## Score Scale

`1/10`: карта технически сломана: Web build не грузится, маркеры не видны, есть runtime errors.

`2/10`: карта открывается, но выглядит как placeholder/debug layer; UX не соответствует задаче.

`3/10`: fullscreen есть, но это простая GIS/procedural схема: пусто, плоско, горы/леса не читаются, pan/click ненадежны.

`4/10`: базовая техника работает, но подложка все еще выглядит процедурной, а горы/леса/города выглядят как отдельные наклейки.

`5/10`: рабочая карта без грубых UX багов, но композиция слабая и хочется заменить картинку.

`6/10`: usable prototype: география в целом понятна, рельеф и маршруты читаются, но остаются раздражающие дефекты вроде мелкого шума, jitter, слабых ориентиров или технических полос.

`7/10`: хорошая рабочая версия: карта уже выглядит приятно, mobile аккуратный, glyphs достаточно крупные, но есть заметные стилистические компромиссы.

`8/10`: достойный результат: с первого взгляда adventure atlas, основные города/горы/вода узнаваемы, pan/drag/click стабильны, нет технического шума.

`9/10`: сильный art-directed результат: регионы имеют характер, markers являются частью карты, desktop/mobile/landscape выглядят профессионально, нет заметных артефактов.

`10/10`: карту хочется оставить именно в этом виде. Она выглядит как цельный warm RPG/atlas world, интерактив работает без оговорок, geography/relief/cities/water/objects проверены, glyph scale читаемый на mobile и desktop, Web payload оптимизирован, screenshots свежие и без видимых проблем.

## Acceptance Rule

`ACCEPT` requires all of the following:

- required commands pass;
- live map loads from the reviewed Web export;
- gzip responses are confirmed for `.html`, `.wasm`, `.pck`, `.js` and present top-level `.png` files;
- `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` plus build metadata are confirmed for the reviewed Web export;
- screenshots exist and were reviewed;
- interaction review finds no pan, zoom, clickability or jitter blocker;
- geography review finds no visible major mismatch;
- visual review scores `10/10` by this gate.

Anything below `10/10` is `REJECT` for this gate. Any visual regression in map readability, glyph scale, icon/label alignment, terrain plausibility or list/map switch affordance is `REJECT`. Rejected visual regressions go back to an implementer/fix-worker before integration. Reviewer still records the estimated score and concrete blockers.

## Review Record Template

```text
Issue:
Worktree:
Branch:
Reviewed commit:
Live URL:
Review bundle:
Screenshot directory:
Build metadata:

Commands:
- python3 -m unittest discover -s tests: PASS/FAIL
- godot --headless --path . --import --quit: PASS/FAIL
- godot --headless --path . --quit-after 1: PASS/FAIL
- ISSUE=issue-81 scripts/create-map-review-bundle.sh: PASS/FAIL
- Web rebuild/export via scripts/serve-web.sh: PASS/FAIL
- Playwright screenshots via scripts/verify-web-map.mjs: PASS/FAIL
- gzip/no-cache/header/build metadata check: PASS/FAIL

Screenshots checked:
- mobile-390x844-initial.png: CHECKED/REJECT
- mobile-390x844-zoom-150.png: CHECKED/REJECT
- mobile-390x844-zoom-200.png: CHECKED/REJECT
- mobile-390x844-after-marker-click.png: CHECKED/REJECT
- mobile-390x844-after-drag.png: CHECKED/REJECT
- desktop-1280x800-initial.png: CHECKED/REJECT
- desktop-1280x800-after-marker-click.png: CHECKED/REJECT
- desktop-1280x800-after-drag.png: CHECKED/REJECT

Rubric score:
Decision: ACCEPT/REJECT
Blockers:
Next action:
```
