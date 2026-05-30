# Handoff 2026-05-30

Дата записи: 2026-05-30 18:16 Europe/Berlin.

## Последний стабильный релиз

- Последний опубликованный релиз: `v0.1.19`.
- URL: https://github.com/alexeygrigorev/cable-world/releases/tag/v0.1.19
- Assets проверены:
  - `mir-trossov-android-0.1.19.apk`
  - `mir-trossov-linux-0.1.19.zip`
  - `mir-trossov-web-0.1.19.zip`
- `main` после релиза был чистым до текущих незакоммиченных UX/object-mode правок.

## Открытые задачи

- `#37` Спроектировать и реализовать объектный режим реальных канатных дорог.
- `#40` Object mode: реализовать детальную схему, станцию и поездку для Gärten der Welt.
- `#43` UX shell: упростить стартовый экран до карты и списка.
- `#44` Карта: сфокусировать начальный вид на Германии.

## Важный пользовательский фидбек

Пользователь резко раскритиковал перегруженный интерфейс:

- на начальном экране должны быть только два входа: `Карта` и `Список`;
- карточка, object mode, поездка, наблюдатель, воспоминания, журнал и настройки не должны быть стартовыми вкладками;
- детали должны появляться только после выбора объекта;
- интерфейс должен быть responsive для телефона, компьютера и планшета;
- карта не должна на первом экране растягиваться на Москву/Россию, потому что текущий фокус проекта - Германия.

Следующий агент должен быть критичным к визуальному дизайну и не выпускать патч, если стартовый экран снова выглядит как набор внутренних режимов.

## Субагенты остановлены

Все активные субагенты были остановлены/закрыты:

- `019e79a3-97a3-7eb2-8abc-033956c5b832` / Heisenberg - завершил object mode UI patch.
- `019e79a3-ba3d-7331-a215-2c9128f0a890` / Hubble - подготовил reviewer checklist для object mode, без ACCEPT/REJECT из-за отсутствия UI-патча на момент ревью.
- `019e79aa-3012-7730-a0e5-7c328c72d262` / Pascal the 2nd - завершил Germany-first map patch.
- `019e79aa-1083-7cf2-9dec-8817fed67825` / Herschel the 2nd - остановлен во время работы над simplified shell; его частичный результат уже виден в рабочем дереве.

## Текущее рабочее дерево

На момент handoff рабочее дерево грязное. Коммитить пока не нужно без review.

`git status --short`:

```text
 M scenes/Main.tscn
 M scripts/main_screen.gd
 M scripts/map_panel.gd
 M scripts/object_card_panel.gd
 M tests/test_map_panel_contract.py
?? scripts/object_mode_panel.gd
?? scripts/object_mode_panel.gd.uid
?? tests/test_object_mode_ui_contract.py
?? docs/session-handoff-2026-05-30.md
```

`git diff --stat` без untracked файлов показывает:

```text
 scenes/Main.tscn                 | 49 ++++++++++++++++++++++++++++++++---
 scripts/main_screen.gd           | 12 +++++++++
 scripts/map_panel.gd             | 55 +++++++++++++++++++++++++++++++++++++---
 scripts/object_card_panel.gd     | 16 ++++++++++++
 tests/test_map_panel_contract.py | 29 +++++++++++++++++++++
```

## Что уже сделано в незакоммиченном состоянии

### Object mode patch для `#40`

Файлы:

- `scripts/object_mode_panel.gd`
- `scripts/object_mode_panel.gd.uid`
- `tests/test_object_mode_ui_contract.py`
- изменения в `scripts/main_screen.gd`
- изменения в `scripts/object_card_panel.gd`
- изменения в `scenes/Main.tscn`

Содержательно:

- добавлен `ObjectModePanel`;
- из карточки есть кнопка `Открыть режим объекта`;
- object mode строит 2D-схему из `stations`, `route_directions`, `route_segments_by_direction`;
- для `berlin-gaerten-der-welt` должны быть видны реальные станции `Киенбергпарк`, `Волькенхайн`, `Сады мира`;
- есть выбор направления, кнопки станций 56px и кнопка `Открыть поездку`;
- есть русские empty states.

Проблема:

- первоначально object mode добавил кнопку `Объект` в главную верхнюю навигацию;
- после фидбека это нельзя оставлять как видимый стартовый вход;
- текущий частичный shell patch сделал `ObjectModeButton` и другие детальные кнопки `visible = false`, но это нужно проверить тестами и визуально.

### Simplified shell patch для `#43`

Частично сделано в `scenes/Main.tscn`:

- `MapButton` и `ListButton` стали основными кнопками с `size_flags_horizontal = 3`;
- `CardButton`, `ObjectModeButton`, `CollectionButton`, `JournalButton`, `MemoryButton`, `RideButton`, `ObserverButton`, `SettingsButton` помечены `visible = false`;
- `НавигацияОбласть` уменьшена с 52 до 48.

Нужно проверить:

- не ломается ли программный переход в скрытые разделы через `_show_section("card")`, `_show_section("object_mode")`, `_show_section("ride")`;
- не падает ли `_scroll_navigation_to_current` на скрытых кнопках;
- нужно ли скрывать `CurrentSectionLabel` или менять текст, чтобы стартовый экран был действительно чистым;
- обновить `tests/test_app_shell_contract.py`, потому что он все еще ожидает старую широкую навигацию со всеми разделами.

### Germany-first map patch для `#44`

Файлы:

- `scripts/map_panel.gd`
- `tests/test_map_panel_contract.py`

Содержательно:

- добавлены `MAP_SCOPE_GERMANY` и `MAP_SCOPE_ALL`;
- `set_objects()` выбирает Germany scope, если есть объект со строками `Германия`, `Deutschland` или `Germany`;
- стартовые bounds строятся по немецким объектам;
- кнопка `Вписать` переключает scope на весь каталог, чтобы остальные страны оставались доступны;
- contract test добавлен в `tests/test_map_panel_contract.py`.

Нужно проверить:

- `python3 -m unittest tests.test_map_panel_contract`;
- Godot headless без parse/script ошибок;
- визуально 390x844 и 844x390.

## Последние известные проверки

Перед новым фидбеком и незакоммиченными изменениями:

- `v0.1.19` CI `Проверки` и `Релиз` были зелеными.
- В `v0.1.19` было `211` локальных тестов OK.

После object mode patch worker сообщил:

- `python -m unittest discover -s tests` - OK, `216` tests.
- `godot --headless --path . --quit` - exit 0.
- `git diff --check` - OK.

После Germany-first map patch worker сообщил:

- `python3 -m unittest tests.test_map_panel_contract` - OK, `9` tests.
- `godot --headless --path . --import --quit` - exit 0.
- `godot --headless --path . --quit-after 1` - exit 0.

Эти проверки нужно повторить локально, потому что после остановки shell worker рабочее дерево могло остаться в промежуточном состоянии.

## Reviewer gate перед следующим релизом

Нельзя выпускать следующий APK без reviewer `ACCEPT`.

Нужны скриншоты:

- `390x844` стартовый экран;
- `844x390` стартовый экран;
- `390x844` карта;
- `390x844` список;
- `390x844` карточка выбранного объекта;
- `390x844` object mode для `berlin-gaerten-der-welt`;
- `844x390` object mode.

Минимальный `ACCEPT`:

- стартовый экран показывает только `Карта` и `Список`;
- карта стартует на Германии, Москва/Россия не доминируют;
- выбор объекта с карты или списка открывает карточку;
- object mode доступен из карточки, а не из стартовой навигации;
- в object mode видны `Киенбергпарк`, `Волькенхайн`, `Сады мира`;
- все основные touch targets >= 48px;
- текст не налезает и не обрезается;
- есть понятный возврат назад.

## Следующий рекомендуемый порядок

1. Не запускать новых крупных задач до стабилизации dirty worktree.
2. Прогнать:
   - `python3 -m unittest tests.test_app_shell_contract tests.test_map_panel_contract tests.test_object_mode_ui_contract`
   - `python3 -m unittest discover -s tests`
   - `git diff --check`
   - `godot --headless --path . --quit-after 1` с фильтром только на `Parse Error|Failed to compile|Failed to load script|SCRIPT ERROR`.
3. Исправить app shell contract под новый UX: стартовая навигация только `Карта`/`Список`.
4. Запустить reviewer-субагента на скриншоты.
5. Если reviewer `ACCEPT`, поднять версию до `0.1.20`, коммитить с `Closes #40`, `Closes #43`, `Closes #44` только если все реально выполнено.
6. Пушить `main`, тег `v0.1.20`, дождаться GitHub Actions и проверить APK asset.

## Инфраструктура

AWS/Terraform уже приведены в воспроизводимое состояние ранее:

- `infra/aws-bootstrap` и `infra/aws-web` используют Terraform;
- remote state в S3 bucket `cable-world-terraform-state-817685572750`;
- S3 website URL: `http://cable-world-web-817685572750.s3-website-eu-west-1.amazonaws.com`;
- GitHub release workflow умеет собирать Android/Linux/Web assets;
- ручной web deploy через workflow возможен с `deploy_web=true`.

Эту часть сейчас не трогать, пока основная проблема - UX.

## Update 2026-05-30 18:45 Europe/Berlin

После handoff была сделана локальная проверка текущего `v0.1.20` candidate.
Релиз делать нельзя: визуальный reviewer gate не пройден.

Дополнительные изменения в рабочем дереве:

- `tests/test_app_shell_contract.py` обновлен под новую идею shell: видимая стартовая навигация только `Карта` и `Список`, остальные разделы скрыты как detail routes.
- `tmp/capture_v020_review.gd` создан как временный сценарий для скриншотов; `tmp/` игнорируется и коммитить его не нужно.

Проверки, которые уже прошли:

```text
python3 -m unittest tests.test_app_shell_contract tests.test_map_panel_contract tests.test_object_mode_ui_contract
Ran 23 tests ... OK

git diff --check
OK

godot --headless --path . --quit-after 1
exit 0, parse/script/compile ошибок не найдено
```

Скриншоты сняты через Xvfb:

- `tmp/screenshots/v020-mobile-map.png`
- `tmp/screenshots/v020-mobile-list.png`
- `tmp/screenshots/v020-mobile-card.png`
- `tmp/screenshots/v020-mobile-object-mode.png`
- `tmp/screenshots/v020-landscape-map.png`
- `tmp/screenshots/v020-landscape-object-mode.png`

Визуальный результат:

- стартовая навигация стала ближе к требованию: видны только `Карта` и `Список`;
- карта все еще плохая для релиза: она занимает слишком много места, обрезается, панель `+/-/Вписать` перекрывает область, видны непонятные номерные маркеры без географического смысла;
- на mobile map текст `Выбрано: ...` внизу налезает/обрезается;
- landscape map показывает только верхнюю часть карты, полезного содержимого почти не видно;
- список стал управляемее, но остается визуально плотным;
- карточка объекта выглядит читаемо;
- object mode для Gärten der Welt показывает реальные станции `Киенбергпарк`, `Волькенхайн`, `Сады мира`, но сам экран еще сырой.

Итог: не тегировать `v0.1.20`, пока не исправлен shell/map layout.

Рекомендуемый следующий шаг для нового агента:

1. Зафиксировать IA: на первом экране только `Карта` и `Список`, без `CurrentSectionLabel`, если он не нужен пользователю.
2. Переделать карту как компактную игровую карту Германии/Европы с понятными маркерами и без перекрывающих floating controls.
3. Ограничить высоту карты так, чтобы на mobile сразу был понятный экран, а не обрезанная внутренняя поверхность.
4. Проверить scroll/touch: список должен прокручиваться без случайного открытия карточек.
5. Повторить Xvfb screenshots и принимать только при визуальном `ACCEPT`.

Дополнительно закрыты агенты, которые были видны в текущем контексте сессии:

- `019e794f-b885-7042-aa15-17236439cb1b` / Kepler - сообщил о старом list-left-fix patch (`ListSafeArea`, `_sync_content_width`, contract test), но эти изменения не были автоматически интегрированы в текущий dirty tree.
- `019e798e-b287-73f1-be13-f1624920486e` / Sagan - сообщил дизайн-документ по object mode; код не менял.

## Update 2026-05-30 после прерывания

Пользователь попросил остановиться. Дальше код не дорабатывать, тесты не запускать, релиз не делать, пока новый агент или пользователь явно не продолжит.

Что успело измениться после предыдущей записи:

- `scenes/Main.tscn`
  - `CurrentSectionLabel` скрыт через `visible = false`.
  - `MapPanel` был уменьшен до `custom_minimum_size = Vector2(0, 280)`.
- `scripts/main_screen.gd`
  - `_scroll_navigation_to_current()` теперь ничего не делает для скрытых кнопок.
  - `_update_map_selection()` укорочен до одной строки `Выбрано: название, регион`, без координат, чтобы текст не занимал слишком много места на карте.
- `scripts/map_panel.gd`
  - карта стала компактнее: `MAP_MIN_HEIGHT = 190`, `MAP_VIEW_HEIGHT = 260`, `MAP_LANDSCAPE_MIN_HEIGHT = 160`.
  - добавлены условная иллюстрация Германии и подписи `Берлин`, `Гарц`, `Штутгарт`, `Цугшпитце`.
  - маркеры уменьшены до `44x44`, вместо номеров показывается `•`, выбранный объект остается `✓`.
  - кнопка `Вписать` заменена на компактный символ `⤢`.
  - Germany scope теперь не только задает bounds, но и скрывает не-немецкие маркеры до раскрытия всего каталога.
- `tests/test_app_shell_contract.py` и `tests/test_map_panel_contract.py`
  - частично обновлены под новый UX-контракт: скрытый section label, компактная карта, Germany-first map.

Проверки после этих последних правок:

- До последнего уменьшения карты проходили:
  - `python3 -m unittest tests.test_app_shell_contract tests.test_map_panel_contract tests.test_object_mode_ui_contract` - OK, 23 tests.
  - `godot --headless --path . --quit-after 1` - без parse/script/compile ошибок.
- После последнего уменьшения карты проверки не запускались, потому что пользователь остановил работу.

Последние визуальные скриншоты до финального уменьшения высоты:

- `tmp/screenshots/v020-mobile-map.png` - стало лучше, но карта все еще тяжеловата и занимает много места.
- `tmp/screenshots/v020-mobile-list.png` - список читаемый, но плотный.
- `tmp/screenshots/v020-landscape-map.png` - все еще обрезался; именно из-за этого начато уменьшение высоты карты.
- `tmp/screenshots/v020-mobile-object-mode.png` - объектный режим читаемый, но сырой.

Текущий `git status --short`:

```text
 M scenes/Main.tscn
 M scripts/main_screen.gd
 M scripts/map_panel.gd
 M scripts/object_card_panel.gd
 M tests/test_app_shell_contract.py
 M tests/test_map_panel_contract.py
?? docs/session-handoff-2026-05-30.md
?? scripts/object_mode_panel.gd
?? scripts/object_mode_panel.gd.uid
?? tests/test_object_mode_ui_contract.py
```

Рекомендация следующему агенту:

1. Не делать релиз сразу.
2. Сначала запустить targeted tests:
   - `python3 -m unittest tests.test_app_shell_contract tests.test_map_panel_contract tests.test_object_mode_ui_contract`
   - `godot --headless --path . --quit-after 1` с фильтром `Parse Error|Failed to compile|Failed to load script|SCRIPT ERROR`
3. Переснять Xvfb screenshots через `tmp/capture_v020_review.gd`.
4. Проверить, что landscape map больше не обрезается.
5. Только после визуального ACCEPT думать о коммите и релизе.
