# Протокол работы над «Миром Троссов»

Этот документ нужен, чтобы новую сессию можно было продолжить без потери процесса. Он описывает, как сейчас организована работа: кто делает задачи, когда выпускать APK, какие проверки обязательны и как не сломать установку обновлений.

## Роли

- Главный агент выступает оркестратором: читает состояние репозитория, Issues, CI/CD и релизов; выбирает следующий маленький инкремент; интегрирует результаты; коммитит, тегирует и проверяет release assets.
- Product/code tasks выполняют субагенты. Главный агент не должен вручную реализовывать продуктовые задачи, если пользователь явно не разрешил. Исключения: процессная документация, интеграционные правки, version bump, commit/tag/release, исправление стыков между агентами.
- Для UI-задач отдельный reviewer-субагент обязан запускать приложение, делать скриншоты и выдавать строгий `ACCEPT` или `REJECT`. Для изменений первого экрана, list mode и map/list toggle применять [UI Review Gate](ui-review-gate.md) (`docs/ui-review-gate.md`); для задач по карте дополнительно применять [Map Reviewer Gate](map-reviewer-gate.md).

## Ритм релизов

- Релиз делается после каждого работающего проверяемого инкремента, чтобы APK можно было скачать и протестировать на телефоне.
- Нельзя ждать большой пачки фич, если уже есть стабильный полезный срез.
- Нельзя выпускать APK, если есть красные тесты, Godot compile/script errors или UI reviewer сказал `REJECT`.
- Если пользователь сообщает, что текущий APK непригоден для телефона, это становится релизным блокером выше roadmap-фич.

## Типовой цикл инкремента

1. Сверить состояние:
   - `git status --short`
   - `git log --oneline --decorate -5`
   - `gh issue list --repo alexeygrigorev/cable-world --state open --limit 80`
   - `python3 -m unittest discover -s tests`
   - `godot --headless --path . --quit-after 1` с проверкой лога на `ERROR:`, `Parse Error`, `Failed to compile`, `Failed to load script`, `SCRIPT ERROR`.
2. Выбрать маленький срез, который после завершения даст рабочий результат.
3. Запустить субагентов с четким ownership по файлам/областям. В каждом prompt обязательно указать:
   - все пользовательские строки на русском;
   - не менять `VERSION`, `export_presets.cfg`, release workflow;
   - не откатывать чужие изменения;
   - запустить тесты и сообщить файлы/риски.
4. Дождаться агентов, закрыть завершенные agent threads, проверить общий diff.
5. Запустить полный gate локально.
6. Для UI: запустить visual reviewer-субагента. Без `ACCEPT` релиза нет.
7. Поднять версию и Android `versionCode`.
8. Коммит с `Closes #...`, push, annotated tag, push tag.
9. Дождаться GitHub Actions release workflow.
10. Проверить GitHub Release assets.

## Обязательные проверки

Локально перед коммитом:

```bash
python3 -m unittest discover -s tests
godot --headless --path . --import --quit
godot --headless --path . --script tests/godot_runtime_runner.gd
git diff --check
set -o pipefail
godot --headless --path . --quit-after 1 > tmp/final-headless.log 2>&1
rg -n 'ERROR:|Parse Error|Failed to compile|Failed to load script|SCRIPT ERROR' tmp/final-headless.log && exit 2 || true
```

Граница тестов: Python gate покрывает map pipeline, data/schema/export и static contract checks; Godot runtime gate покрывает import, GDScript compile/load, минимальный scene startup и `godot --headless --path . --script tests/godot_runtime_runner.gd` для базовых GDScript runtime assertions. Для GDScript runtime, UI, input gestures и scene behavior новые issues должны по умолчанию требовать Godot-native tests; Python static assertions не считаются заменой runtime acceptance. Подробная граница: [Testing Strategy](testing-strategy.md).

Для UI-инкрементов reviewer-субагент дополнительно делает:

- `tmp/screenshots/mobile-390x844-*.png`
- `tmp/screenshots/landscape-844x390-*.png`
- визуальную оценку читаемости, touch targets, скролла, карты, навигации и русских строк.

Для list/toggle/map-first задач минимальный набор из [UI Review Gate](ui-review-gate.md):

- `tmp/ui-review/mobile-390x844-map.png`
- `tmp/ui-review/mobile-390x844-list.png`
- `tmp/ui-review/landscape-844x390-map.png`
- `tmp/ui-review/landscape-844x390-list.png`
- `godot --headless --path . --script tests/godot_runtime_runner.gd`

Если reviewer пишет `REJECT`, главный агент не релизит. Нужно запустить fix-worker и повторить review.

## Версионирование и APK

- Текущая стабильная линия: `0.1.x`.
- При каждом релизе обновлять:
  - `VERSION`
  - `export_presets.cfg`: Android `version/code`
  - `export_presets.cfg`: Android `version/name`
- `version/code` увеличивать на 1.
- Нельзя менять `package/unique_name="com.mirtrossov.app"` и signing без отдельного решения, иначе обновления поверх старого APK могут перестать устанавливаться.
- Релиз создается тегом `vX.Y.Z`.
- APK должен появиться в GitHub Release assets как `mir-trossov-android-X.Y.Z.apk`.

Команды релиза:

```bash
git add ...
git commit -m "..." -m "Closes #..."
git push origin main
git tag -a vX.Y.Z -m "Мир Троссов X.Y.Z"
git push origin vX.Y.Z
gh run watch <release-run-id> --repo alexeygrigorev/cable-world --exit-status
gh release view vX.Y.Z --repo alexeygrigorev/cable-world --json url,assets --jq '{url,assets:[.assets[].name]}'
```

## CI/CD и инфраструктура

- GitHub Actions `Проверки` и `Релиз` являются обязательными gates.
- Release workflow собирает Android, Linux и Web artifacts и создает GitHub Release.
- Web deploy в S3 включается только через manual workflow dispatch с `deploy_web=true`.
- AWS-инфраструктура должна оставаться воспроизводимой. Текущий web hosting описан Terraform в `infra/aws-web`.
- Terraform state и планы локально игнорируются; не коммитить `*.tfstate`, `.terraform/`, `tfplan`.

## Работа с картой и UI

- UI должен быть mobile-first. Портрет `390x844` является минимальным проверочным размером.
- Скролл должен работать как скролл, а tap как выбор. Если drag случайно выбирает элементы, это release blocker.
- Карта должна быть похожа на карту или честную схему конкретного объекта, а не случайную сетку.
- Настройки не должны занимать главный экран. Редкие настройки, например ориентация, должны быть в `Настройки`.
- Любая новая UI-фича требует visual reviewer `ACCEPT`.
- Изменения list mode, map/list toggle и map-first shell проходят [UI Review Gate](ui-review-gate.md) с mobile/landscape screenshots и Godot-native runtime checks.

## Работа с каталогом

- Production seed не должен автоматически принимать OSM/Wikidata без ручной проверки.
- Для импорта используется staging pipeline:
  - staging JSON schema;
  - validator;
  - collector prototype;
  - manual review states: `candidate`, `approved`, `rejected`;
  - preview JSON/SQL только из `approved`.
- `operational_status` остается `unknown`, если нет свежего официального источника.

## Возобновление в новой сессии

Новая сессия должна начать так:

```bash
cd /home/alexey/git/cable-world
git status --short
git log --oneline --decorate -10
gh issue list --repo alexeygrigorev/cable-world --state open --limit 80
python3 -m unittest discover -s tests
godot --headless --path . --quit-after 1
gh release view "$(git describe --tags --abbrev=0)" --repo alexeygrigorev/cable-world --json url,assets --jq '{url,assets:[.assets[].name]}'
```

Дальше продолжать от текущих open Issues и пользовательского последнего сообщения. Если есть незакоммиченный worktree, считать это work-in-progress от агентов или пользователя; не откатывать без прямого разрешения.
