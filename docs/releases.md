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

Перед публикацией APK и после установки APK из GitHub Release пройти [MVP-чеклист релиза APK](release-mvp-checklist.md). Он покрывает запуск, ориентацию, карту, карточку объекта, фото, статусы посещения и работы объекта, а также поиск объектов Германии, России и первого набора стран Европы.

Для следующего инкремента после `v0.1.16` smoke должен отдельно проверить, что demo/fallback каталог показывает 34 объекта: Германия остается основной подборкой, Россия использует расширенный seed без дублей старых российских записей, а фильтр стран содержит Португалию, Францию, Италию, Чехию, Словакию и Польшу.

Опубликованный APK скачивается со страницы GitHub Release проекта: <https://github.com/alexeygrigorev/cable-world/releases>. В блоке `Assets` нужен файл вида `mir-trossov-android-<version>.apk`.

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
