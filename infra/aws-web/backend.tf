terraform {
  backend "s3" {
    bucket       = "cable-world-terraform-state-817685572750"
    key          = "aws-web/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    use_lockfile = true
  }
}
