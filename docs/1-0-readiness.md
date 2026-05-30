# 1.0 readiness checklist

Дата аудита: 2026-05-30.

Вердикт readiness-аудита: `READY_FOR_1_0_CANDIDATE`.

Это не команда выпускать `v1.0.0`. Перед тегом `v1.0.0` все равно нужны зеленые проверки на релизной ветке, `ACCEPT` от reviewer-субагента для последнего UI-состояния и ручной APK smoke test из `docs/release-mvp-checklist.md`.

## Текущая база

- Последний опубликованный релиз: `v0.1.14`.
- Текущая версия в проекте: `0.1.14`.
- Открытые GitHub Issues на момент аудита: `#31`, `#32`, `#33`, `#34`; все помечены как `V3` и не являются blocker-ами для 1.0 MVP.
- 1.0 scope остается семейным sideload APK и регулярными GitHub Releases, не Google Play production release.

## 1.0 MVP gates

- `PASS` Русский интерфейс и русские пользовательские документы закреплены контрактами i18n.
- `PASS` Главный экран содержит разделы «Карта», «Список», «Карточка», «Воспоминание», «Коллекция», «Журнал».
- `PASS` Карта доступна офлайн как локальная схема объектов с маркерами, pan/zoom, фильтрами «Все», «Посещенные», «Непосещенные» и выбором объекта.
- `PASS` Список поддерживает фильтры по типу, статусу посещения и стране из коллекции.
- `PASS` Карточка показывает описание, координаты, статус посещения, статус работы объекта, станции, направления, фото, видео, билеты и посещения без внутренних терминов.
- `PASS` SQLite-хранилище, миграции и demo seed закреплены тестами; при недоступном runtime есть честный fallback на `DemoCatalog`.
- `PASS` В demo/fallback данных есть достаточный набор объектов Германии, включая канатные дороги, фуникулеры, зубчатую железную дорогу и подвесный транспорт.
- `PASS` Android APK имеет стабильный package id `com.mirtrossov.app`, имя «Мир Троссов», стабильный `android/debug.keystore` и монотонный `version/code`.

## Release and CI/CD gates

- `PASS` Workflow `Проверки` запускает `python3 -m unittest discover -s tests` на push и pull_request.
- `PASS` Workflow `Релиз` запускается по tag `v*` и вручную через `workflow_dispatch`.
- `PASS` Workflow `Релиз` запускает contract tests до сборки артефактов.
- `PASS` `scripts/export-release.sh` собирает Web, Linux и Android APK.
- `PASS` GitHub Release по tag получает `mir-trossov-web-<version>.zip`, `mir-trossov-linux-<version>.zip` и `mir-trossov-android-<version>.apk`.
- `PASS` Последний `v0.1.14` уже опубликован с Web, Linux и Android assets.
- `PASS` Документы объясняют, где скачать APK из GitHub Release Assets и как пройти smoke test до и после релиза.

## Visual review gate

- `PASS` Роль reviewer описана в `agents.md`.
- `PASS` Для UI-задач reviewer обязан запустить приложение, сохранить скриншот `390x844`, проверить читаемость, touch targets и карту.
- `PASS` Без явного `ACCEPT` от reviewer-субагента UI-задача не идет в релиз.
- `PASS` APK checklist требует `ACCEPT` для UI-изменений перед семейной установкой.

## AWS and infrastructure gate

- `PASS` Terraform-код в `infra/aws-web` описывает S3 static website bucket и IAM role для GitHub Actions OIDC deploy.
- `PASS` `docs/releases.md` документирует `terraform init`, `terraform apply` и repository variables `AWS_REGION`, `AWS_WEB_BUCKET`, `AWS_ROLE_ARN`.
- `PASS` Workflow `Релиз` умеет выкладывать Web-сборку в S3 при ручном запуске с `deploy_web=true`.
- `PASS` AWS deploy не является blocker-ом для Android 1.0 APK, но воспроизводимость Web-инфраструктуры задокументирована.

## Release assets gate

- `PASS` Public install point для Android: GitHub Release asset `mir-trossov-android-<version>.apk`.
- `PASS` Public desktop/web assets: `mir-trossov-linux-<version>.zip` и `mir-trossov-web-<version>.zip`.
- `PASS` APK sideload, подпись и условия установки поверх предыдущего `v0.1.x` описаны в `README.md`, `android/README.md` и `docs/release-mvp-checklist.md`.

## 1.0 blockers

На момент аудита реальные blockers для 1.0 candidate не обнаружены.

Остаточные обязательные действия перед фактическим `v1.0.0`:

- пройти `docs/release-mvp-checklist.md` на Android-устройстве или эмуляторе;
- получить свежий reviewer `ACCEPT` для финального UI-состояния;
- убедиться, что GitHub Actions `Проверки` зеленый на commit, который будет тегирован;
- не менять package id, keystore, Android versioning или release workflow прямо перед тегом без отдельного review.

## Post-1.0 / V3

Открытые V3 issues остаются после 1.0 и не блокируют MVP:

- `#31` V3: Добавить режим поездки по маршруту.
- `#32` V3: Добавить инженерный режим объекта.
- `#33` V3: Добавить режим наблюдателя.
- `#34` V3: Добавить режим прогулки по объекту.

