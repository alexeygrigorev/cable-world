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
scripts/export-release.sh "$(cat VERSION)"
```

## Web-хостинг в AWS

Инфраструктура лежит в `infra/aws-web` и управляется Terraform. Она создает:

- S3 bucket для статического Web-релиза;
- public-read policy для S3 website endpoint;
- IAM role для GitHub Actions deploy через OIDC.

Применение:

```bash
cd infra/aws-web
terraform init
terraform apply
```

После apply нужно записать outputs в GitHub repository variables:

- `AWS_REGION`;
- `AWS_WEB_BUCKET`;
- `AWS_ROLE_ARN`.

После этого workflow `Релиз` можно запускать вручную с `deploy_web=true`, и он выложит Web-сборку в S3.
