output "bootstrap_profile_used" {
  description = "AWS profile used for bootstrap"
  value       = var.bootstrap_profile
}

output "terraform_state_bucket_name" {
  description = "S3 bucket name for Terraform remote state"
  value       = aws_s3_bucket.terraform_state.bucket
}

output "terraform_deployer_user_name" {
  description = "IAM user created for Terraform deployments"
  value       = aws_iam_user.terraform_deployer.name
}

output "app_sensitive_config_secret_name" {
  description = "Secrets Manager name containing app sensitive config"
  value       = aws_secretsmanager_secret.app_sensitive_config.name
}

output "app_sensitive_config_secret_arn" {
  description = "Secrets Manager ARN containing app sensitive config"
  value       = aws_secretsmanager_secret.app_sensitive_config.arn
}

output "suggested_backend_block" {
  description = "Suggested backend block to paste into infrastructure/backend.tf"
  value       = <<EOT
terraform {
  backend "s3" {
    bucket  = "${aws_s3_bucket.terraform_state.bucket}"
    key     = "${var.project_name}/${var.aws_region}/terraform.tfstate"
    region  = "${var.aws_region}"
    encrypt = true
    profile = "millerpic_tf"
  }
}
EOT
}
