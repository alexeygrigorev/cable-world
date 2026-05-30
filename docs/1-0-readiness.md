# 1.0 readiness checklist

Дата аудита: 2026-05-30.

Вердикт readiness-аудита: `READY_FOR_1_0_CANDIDATE`.

Это не команда выпускать `v1.0.0`. Перед тегом `v1.0.0` все равно нужны зеленые проверки на релизной ветке, `ACCEPT` от reviewer-субагента для последнего UI-состояния и ручной APK smoke test из `docs/release-mvp-checklist.md`.

## Текущая база

- Последний опубликованный релиз: `v0.1.16`.
- Текущая версия в проекте: `0.1.16`.
- Открытые GitHub Issues на момент аудита: `#35`, `#36`; обе задачи расширяют seed-каталог по Европе и России и не блокируют установленный Android MVP, но улучшают содержательность поиска, карты и коллекции перед `1.0.0`.
- V3 issues `#31` и `#33` закрыты реализацией первого среза режимов поездки и наблюдателя; `#32` и `#34` закрыты контрактами/планом и остаются источником будущих игровых задач.
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
- `PASS` Последний `v0.1.16` уже опубликован с Web, Linux и Android assets.
- `PASS` Документы объясняют, где скачать APK из GitHub Release Assets и как пройти smoke test до и после релиза.

## Visual review gate

- `PASS` Роль reviewer описана в `agents.md`.
- `PASS` Для UI-задач reviewer обязан запустить приложение, сохранить скриншот `390x844`, проверить читаемость, touch targets и карту.
- `PASS` Без явного `ACCEPT` от reviewer-субагента UI-задача не идет в релиз.
- `PASS` APK checklist требует `ACCEPT` для UI-изменений перед семейной установкой.

## AWS and infrastructure gate

- `PASS` Terraform-код в `infra/aws-bootstrap` описывает S3 remote state bucket и DynamoDB lock table/bootstrap-ресурс для воспроизводимого Terraform state.
- `PASS` Terraform-код в `infra/aws-web` описывает S3 static website bucket и IAM role для GitHub Actions OIDC deploy.
- `PASS` `infra/aws-web/backend.tf` закрепляет S3 backend `cable-world-terraform-state-817685572750`, key `aws-web/terraform.tfstate`, region `eu-west-1` и современный S3 lockfile.
- `PASS` `docs/releases.md` и `infra/aws-web/README.md` документируют bootstrap, `terraform init`, `terraform -chdir=infra/aws-web init -migrate-state`, import recovery, `terraform apply` и repository variables `AWS_REGION`, `AWS_WEB_BUCKET`, `AWS_ROLE_ARN`.
- `PASS` Workflow `Проверки` запускает `terraform fmt -check`, `terraform init -backend=false` и `terraform validate` для `infra/aws-bootstrap` и `infra/aws-web`.
- `PASS` Workflow `Релиз` проверяет непустые `AWS_REGION`, `AWS_WEB_BUCKET` и `AWS_ROLE_ARN` ранним шагом перед Web deploy.
- `PASS` Workflow `Релиз` умеет выкладывать Web-сборку в S3 при ручном запуске с `deploy_web=true`.
- `PASS` Текущий Web test URL: `http://cable-world-web-817685572750.s3-website-eu-west-1.amazonaws.com`.
- `PASS` S3 website endpoint по `http` принят как семейный/test hosting для семейной проверки и не является финальным публичным HTTPS для `1.0`.
- `PASS` AWS deploy не является blocker-ом для Android 1.0 APK, но воспроизводимость Web-инфраструктуры теперь закреплена bootstrap/backend flow.

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

## До 1.0 / расширение каталога

Открытые задачи содержимого не блокируют уже устанавливаемый APK, но являются правильным следующим инкрементом перед `1.0.0`:

- `#35` Расширить seed-каталог по Европе через review staging-кандидатов.
- `#36` Расширить seed каталога объектами России из research/staging.

## Post-1.0 / V3

Закрытые V3 issues зафиксировали первый игровой фундамент и дальнейшие направления:

- `#31` V3: Добавить режим поездки по маршруту.
- `#32` V3: Добавить инженерный режим объекта.
- `#33` V3: Добавить режим наблюдателя.
- `#34` V3: Добавить режим прогулки по объекту.
