variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "Local AWS CLI profile Terraform should use"
  type        = string
  default     = "millerpic_tf"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "millerpic"
}

variable "s3_bucket_prefix" {
  description = "Prefix used for the photo bucket"
  type        = string
  default     = "millerpic-photos"
}

variable "lambda_artifacts_bucket_name" {
  description = "S3 bucket containing signed Lambda deployment artifacts"
  type        = string
  default     = ""
}

variable "lambda_signing_profile_name" {
  description = "AWS Signer profile name used for Lambda code signing"
  type        = string
  default     = ""
}

variable "lambda_artifact_object_keys" {
  description = "Map of Lambda handler names to signed S3 object keys"
  type        = map(string)
  default = {
    upload          = "signed/upload.zip"
    download        = "signed/download.zip"
    list            = "signed/list.zip"
    upload_complete = "signed/upload_complete.zip"
    delete          = "signed/delete.zip"
    trash           = "signed/trash.zip"
    hard_delete     = "signed/hard_delete.zip"
    patch_photo     = "signed/patch_photo.zip"
    search          = "signed/search.zip"
    get_photo       = "signed/get_photo.zip"
  }
}

variable "lambda_artifact_object_versions" {
  description = "Map of Lambda handler names to signed S3 object versions"
  type        = map(string)
  default     = {}
}

variable "enable_jwt_auth" {
  description = "Enable API Gateway JWT authorizer on routes"
  type        = bool
  default     = false
}

variable "jwt_issuer" {
  description = "JWT issuer URL for API authorizer"
  type        = string
  default     = "https://example.com/"
}

variable "jwt_audience" {
  description = "Allowed JWT audiences for API authorizer"
  type        = list(string)
  default     = ["millerpic"]
}

variable "load_sensitive_config_from_secrets" {
  description = "Load JWT and other sensitive config from AWS Secrets Manager"
  type        = bool
  default     = true
}

variable "sensitive_config_secret_name" {
  description = "Optional override for Secrets Manager name containing sensitive app config"
  type        = string
  default     = ""
}

variable "api_throttle_rate_limit" {
  description = "Steady-state API Gateway requests per second across routes"
  type        = number
  default     = 20
}

variable "api_throttle_burst_limit" {
  description = "API Gateway burst requests across routes"
  type        = number
  default     = 40
}

variable "lambda_reserved_concurrency_per_function" {
  description = "Reserved concurrency cap per public Lambda function (-1 to disable)"
  type        = number
  default     = 10

  validation {
    condition     = var.lambda_reserved_concurrency_per_function == -1 || var.lambda_reserved_concurrency_per_function >= 1
    error_message = "lambda_reserved_concurrency_per_function must be -1 or >= 1."
  }
}

variable "download_url_ttl_seconds" {
  description = "Presigned download URL TTL in seconds"
  type        = number
  default     = 900

  validation {
    condition     = var.download_url_ttl_seconds >= 60 && var.download_url_ttl_seconds <= 3600
    error_message = "download_url_ttl_seconds must be between 60 and 3600 seconds."
  }
}

variable "enable_cost_protection" {
  description = "Enable budgets and CloudWatch/SNS cost guardrails"
  type        = bool
  default     = true
}

variable "cost_alert_email" {
  description = "Email to subscribe to cost/security alarms (optional, requires SNS confirmation)"
  type        = string
  default     = ""
}

variable "enable_sns_alert_topic" {
  description = "Create SNS topic for alarm actions (requires sns:CreateTopic permissions)"
  type        = bool
  default     = false
}

variable "monthly_cost_budget_usd" {
  description = "Monthly account budget in USD"
  type        = number
  default     = 25
}

variable "enable_aws_budgets" {
  description = "Create AWS Budgets monthly budget resource (requires budgets permissions)"
  type        = bool
  default     = false
}

variable "monthly_cost_forecast_alert_threshold_percent" {
  description = "Forecasted budget threshold percent for alerting"
  type        = number
  default     = 80
}

variable "api_4xx_alarm_threshold" {
  description = "Alarm threshold for API 4xx count per period"
  type        = number
  default     = 200
}

variable "api_5xx_alarm_threshold" {
  description = "Alarm threshold for API 5xx count per period"
  type        = number
  default     = 20
}

variable "api_request_count_alarm_threshold" {
  description = "Alarm threshold for total API requests per period"
  type        = number
  default     = 5000
}

variable "lambda_errors_alarm_threshold" {
  description = "Alarm threshold for Lambda errors per function per period"
  type        = number
  default     = 5
}

variable "lambda_throttles_alarm_threshold" {
  description = "Alarm threshold for Lambda throttles per function per period"
  type        = number
  default     = 1
}

variable "alarm_period_seconds" {
  description = "CloudWatch alarm period in seconds"
  type        = number
  default     = 300
}

variable "alarm_evaluation_periods" {
  description = "CloudWatch alarm evaluation periods"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Default tags applied to all resources"
  type        = map(string)
  default = {
    Project   = "MillerPic"
    ManagedBy = "Terraform"
  }
}
