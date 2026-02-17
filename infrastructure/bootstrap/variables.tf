variable "aws_region" {
  description = "AWS region for bootstrap resources"
  type        = string
  default     = "us-east-1"
}

variable "bootstrap_profile" {
  description = "Local AWS profile used to create bootstrap resources"
  type        = string
  default     = "pandacloud"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "millerpic"
}

variable "environment" {
  description = "Deployment environment name used in secret naming"
  type        = string
  default     = "dev"
}

variable "state_bucket_prefix" {
  description = "Prefix for Terraform state bucket"
  type        = string
  default     = "millerpic-terraform-state"
}

variable "terraform_deployer_user_name" {
  description = "IAM user name for Terraform deployment operations"
  type        = string
  default     = "millerpic_tf"
}

variable "jwt_issuer" {
  description = "JWT issuer URL stored in Secrets Manager for app infrastructure"
  type        = string
  default     = "https://accounts.google.com"
}

variable "jwt_audience" {
  description = "JWT audiences stored in Secrets Manager for app infrastructure"
  type        = list(string)
  default     = []
}

variable "cost_alert_email" {
  description = "Optional alert email stored in Secrets Manager"
  type        = string
  default     = ""
}
