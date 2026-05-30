output "bucket_name" {
  value = aws_s3_bucket.web.bucket
}

output "website_endpoint" {
  value = aws_s3_bucket_website_configuration.web.website_endpoint
}

output "website_url" {
  value = "http://${aws_s3_bucket_website_configuration.web.website_endpoint}"
}

output "github_actions_role_arn" {
  value = aws_iam_role.github_deploy.arn
}
