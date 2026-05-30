# AWS Web-инфраструктура

Этот каталог описывает семейный/test Web-хостинг «Мира Троссов» в AWS:

- S3 bucket `cable-world-web-817685572750` для статической Web-сборки;
- S3 website endpoint `http://cable-world-web-817685572750.s3-website-eu-west-1.amazonaws.com`;
- IAM role `cable-world-github-deploy` для GitHub Actions через OIDC;
- public-read policy для S3 website endpoint.

S3 website endpoint работает по `http`. Это осознанный семейный/test hosting для проверки Web-сборок и не является финальным публичным HTTPS для `1.0`. Для публичного `1.0` с HTTPS нужен отдельный слой CloudFront/ACM.

## Bootstrap remote state

Terraform state хранится в S3 backend. Сначала один раз поднимается bootstrap-модуль:

```bash
terraform -chdir=infra/aws-bootstrap init
terraform -chdir=infra/aws-bootstrap apply
terraform -chdir=infra/aws-bootstrap init -migrate-state
terraform -chdir=infra/aws-bootstrap output
```

Значения по умолчанию:

- bucket state: `cable-world-terraform-state-817685572750`;
- S3 lockfile включен в backend; lock table `cable-world-terraform-locks` создан как bootstrap-ресурс совместимости;
- region: `eu-west-1`.

Если аккаунт или имена меняются, перед apply передайте variables:

```bash
terraform -chdir=infra/aws-bootstrap apply \
  -var='state_bucket_name=cable-world-terraform-state-<account_id>' \
  -var='lock_table_name=cable-world-terraform-locks' \
  -var='aws_region=eu-west-1'
```

## Миграция существующего local state

Если `infra/aws-web/terraform.tfstate` уже есть локально и описывает текущие AWS-ресурсы, после bootstrap выполнить:

```bash
terraform -chdir=infra/aws-web init -migrate-state
terraform -chdir=infra/aws-web plan
```

Ожидаемый результат после миграции для уже поднятой инфраструктуры: `No changes`. Если backend уже инициализирован, можно использовать обычный `terraform -chdir=infra/aws-web init`.

## Восстановление из чистого checkout

1. Проверить доступ к AWS аккаунту `817685572750`.
2. Поднять или проверить bootstrap:

```bash
terraform -chdir=infra/aws-bootstrap init
terraform -chdir=infra/aws-bootstrap plan
```

3. Инициализировать web-инфраструктуру с remote backend:

```bash
terraform -chdir=infra/aws-web init
terraform -chdir=infra/aws-web plan
terraform -chdir=infra/aws-web output
```

Если remote state bootstrap потерян, но AWS-ресурсы state bucket/lock table существуют, их нужно импортировать перед apply:

```bash
terraform -chdir=infra/aws-bootstrap import aws_s3_bucket.terraform_state cable-world-terraform-state-817685572750
terraform -chdir=infra/aws-bootstrap import aws_s3_bucket_versioning.terraform_state cable-world-terraform-state-817685572750
terraform -chdir=infra/aws-bootstrap import aws_s3_bucket_server_side_encryption_configuration.terraform_state cable-world-terraform-state-817685572750
terraform -chdir=infra/aws-bootstrap import aws_s3_bucket_public_access_block.terraform_state cable-world-terraform-state-817685572750
terraform -chdir=infra/aws-bootstrap import aws_dynamodb_table.terraform_locks cable-world-terraform-locks
terraform -chdir=infra/aws-bootstrap plan
```

Если remote state web-инфраструктуры потерян, но AWS-ресурсы существуют, их нужно импортировать перед apply:

```bash
terraform -chdir=infra/aws-web import aws_s3_bucket.web cable-world-web-817685572750
terraform -chdir=infra/aws-web import aws_s3_bucket_ownership_controls.web cable-world-web-817685572750
terraform -chdir=infra/aws-web import aws_s3_bucket_public_access_block.web cable-world-web-817685572750
terraform -chdir=infra/aws-web import aws_s3_bucket_website_configuration.web cable-world-web-817685572750
terraform -chdir=infra/aws-web import aws_s3_bucket_policy.public_read cable-world-web-817685572750
terraform -chdir=infra/aws-web import aws_iam_role.github_deploy cable-world-github-deploy
terraform -chdir=infra/aws-web import aws_iam_role_policy.github_deploy cable-world-github-deploy:cable-world-web-deploy
terraform -chdir=infra/aws-web plan
```

## GitHub variables

После `terraform -chdir=infra/aws-web apply` или `output` проверить repository variables:

```bash
gh variable list --repo alexeygrigorev/cable-world
terraform -chdir=infra/aws-web output -raw bucket_name
terraform -chdir=infra/aws-web output -raw github_actions_role_arn
terraform -chdir=infra/aws-web output -raw website_url
```

Должны быть заданы:

- `AWS_REGION=eu-west-1`;
- `AWS_WEB_BUCKET=cable-world-web-817685572750`;
- `AWS_ROLE_ARN=arn:aws:iam::817685572750:role/cable-world-github-deploy`.

Если переменные пустые, workflow `Релиз` остановится ранним guard-step перед сборкой и deploy.
