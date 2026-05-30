variable "aws_region" {
  description = "AWS регион для статического хостинга."
  type        = string
  default     = "eu-west-1"
}

variable "bucket_name" {
  description = "Имя S3 bucket. Если пусто, Terraform использует cable-world-web-<account_id>."
  type        = string
  default     = ""
}

variable "github_repository" {
  description = "GitHub repository в формате owner/name для OIDC trust policy."
  type        = string
  default     = "alexeygrigorev/cable-world"
}

variable "create_github_oidc_provider" {
  description = "Создать GitHub OIDC provider. Поставить false, если provider уже есть в аккаунте."
  type        = bool
  default     = false
}
