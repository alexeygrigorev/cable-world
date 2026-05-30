variable "aws_region" {
  description = "AWS регион для Terraform remote state."
  type        = string
  default     = "eu-west-1"
}

variable "state_bucket_name" {
  description = "Имя S3 bucket для Terraform state."
  type        = string
  default     = "cable-world-terraform-state-817685572750"
}

variable "lock_table_name" {
  description = "Имя DynamoDB таблицы для блокировки Terraform state."
  type        = string
  default     = "cable-world-terraform-locks"
}
