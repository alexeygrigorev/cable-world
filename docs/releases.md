# Релизы и окружения

## Версии

До версии `1.0.0` выпускаем регулярные проверочные релизы `0.x.y`. Каждый релиз должен иметь:

- GitHub tag `vX.Y.Z`;
- GitHub Release с Web и Linux zip-артефактами;
- зеленые проверки;
- короткое описание того, что можно проверить вручную.

## Локальная сборка

```bash
scripts/install-godot.sh
python3 -m unittest discover -s tests
godot --headless --path . --import --quit
godot --headless --path . --script tests/godot_runtime_runner.gd
godot --headless --path . --quit-after 1
scripts/export-release.sh "$(cat VERSION)"
```

Python test gate покрывает pipeline/data/schema/export/static contracts. Godot import/run gate покрывает engine import, GDScript compile/load, минимальный runtime startup и базовые GDScript runtime assertions через `godot --headless --path . --script tests/godot_runtime_runner.gd`. Подробная граница между ними зафиксирована в [Testing Strategy](testing-strategy.md).

## APK smoke test

Перед публикацией APK и после установки APK из GitHub Release пройти ручной smoke test. Он покрывает запуск, ориентацию, карту, карточку объекта, фото, статусы посещения и работы объекта, а также поиск объектов Германии, России и первого набора стран Европы.

Для следующего инкремента после `v0.1.16` smoke должен отдельно проверить, что demo/fallback каталог показывает 34 объекта: Германия остается основной подборкой, Россия использует расширенный seed без дублей старых российских записей, а фильтр стран содержит Португалию, Францию, Италию, Чехию, Словакию и Польшу.

Опубликованный APK скачивается со страницы GitHub Release проекта: <https://github.com/alexeygrigorev/cable-world/releases>. В блоке `Assets` нужен файл вида `mir-trossov-android-<version>.apk`.

### Перед сборкой

- Убедиться, что `VERSION`, Android `version/name` и Android `version/code` согласованы: `python3 -m unittest discover -s tests`.
- Для UI-изменений получить reviewer `ACCEPT` со screenshots `390x844` и `844x390`.
- Для object mode reviewer обязан дать явный `ACCEPT` или `REJECT`: текст читается, tap targets пригодны для пальца, скролл или панорамирование не конфликтуют с выбором, возврат назад работает, пустые состояния понятны на русском, объект похож на реальный транспортный или инженерный объект.
- Проверить, что GitHub Actions `Проверки` зеленый на ветке релиза.
- Собрать артефакты локально или через workflow `Релиз`: `scripts/export-release.sh "$(cat VERSION)"`.

### Smoke перед релизом

- Установить APK на Android-устройство или эмулятор как sideload APK.
- Запустить приложение и убедиться, что видно имя «Мир Троссов».
- Проверить «Ориентация»: «Вертикальная», «Горизонтальная», «Как в системе».
- Открыть «Карта»: локальные объекты видны, выбор объекта работает, маркеры читаемы, карту можно двигать и менять масштаб.
- Проверить фильтр карты: «Все», «Посещенные», «Непосещенные».
- Открыть «Список»: найти объекты Германии, России, Португалии, Франции, Италии, Чехии, Словакии и Польши.
- Для России убедиться, что Нижегородская канатная дорога, Московская канатная дорога и Владивостокский фуникулер не дублируются.
- Открыть карточку объекта: видны название, страна, регион или город, координаты, описание и технические поля без внутренних терминов.
- Проверить блок «Работа объекта»: статус работы, дата проверки и источник отображаются отдельно от статуса посещения.
- Изменить статус посещения, закрыть и снова открыть объект, убедиться, что статус сохранился.
- Добавить запись о фото: должна появиться понятная строка без внутреннего пути файла.
- Перейти между «Карта», «Список», «Карточка» и «Журнал», убедиться, что приложение не падает и выбранный объект остается согласованным.

### Smoke после релиза

- Скачать APK из опубликованного GitHub Release, а не из локальной папки `dist`.
- Установить APK поверх предыдущей версии `v0.1.x` без удаления приложения.
- Повторить короткий маршрут: список объектов Германии, карточка объекта, смена статуса, добавление записи о фото, возврат на карту.
- Если установка поверх старой версии не проходит, не менять package id, keystore или миграции в рамках релиза; сначала завести отдельную issue с симптомом и версией APK.

## Web-хостинг в AWS

Текущий test URL: <http://cable-world-web-817685572750.s3-website-eu-west-1.amazonaws.com>.

Это S3 website endpoint по `http`. Он подходит для семейной проверки Web-сборок, но не является финальным публичным HTTPS-хостингом для `1.0`. Для публичного запуска нужен отдельный CloudFront/ACM слой или другой HTTPS endpoint.

Инфраструктура лежит в `infra/aws-web` и управляется Terraform. Remote state создается отдельным bootstrap-модулем `infra/aws-bootstrap`. Подробный runbook: [`infra/aws-web/README.md`](../infra/aws-web/README.md).

`infra/aws-web` создает:

- S3 bucket для статического Web-релиза;
- public-read policy для S3 website endpoint;
- IAM role для GitHub Actions deploy через OIDC.

Первичный bootstrap state backend:

```bash
terraform -chdir=infra/aws-bootstrap init
terraform -chdir=infra/aws-bootstrap apply
terraform -chdir=infra/aws-bootstrap init -migrate-state
terraform -chdir=infra/aws-bootstrap output
```

Это тот же порядок `terraform init` -> `terraform apply`, только с явным `-chdir`, чтобы команды можно было запускать из корня репозитория.

Миграция уже существующего local state в remote backend:

```bash
terraform -chdir=infra/aws-web init -migrate-state
terraform -chdir=infra/aws-web plan
```

Применение web-инфраструктуры после backend init:

```bash
terraform -chdir=infra/aws-web init
terraform -chdir=infra/aws-web apply
terraform -chdir=infra/aws-web output
```

После apply нужно записать или проверить outputs в GitHub repository variables:

- `AWS_REGION`;
- `AWS_WEB_BUCKET`;
- `AWS_ROLE_ARN`.

Ожидаемые текущие значения:

- `AWS_REGION=eu-west-1`;
- `AWS_WEB_BUCKET=cable-world-web-817685572750`;
- `AWS_ROLE_ARN=arn:aws:iam::817685572750:role/cable-world-github-deploy`.

Проверка без изменений:

```bash
terraform -chdir=infra/aws-bootstrap fmt -check
terraform -chdir=infra/aws-bootstrap init -backend=false
terraform -chdir=infra/aws-bootstrap validate
terraform -chdir=infra/aws-web fmt -check
terraform -chdir=infra/aws-web init -backend=false
terraform -chdir=infra/aws-web validate
gh variable list --repo alexeygrigorev/cable-world
```

После этого workflow `Релиз` можно запускать вручную с `deploy_web=true`, и он выложит Web-сборку в S3. Если `AWS_REGION`, `AWS_WEB_BUCKET` или `AWS_ROLE_ARN` пустые, workflow упадет ранним понятным сообщением до сборки.
