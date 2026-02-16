# Committed environment defaults only.
# Do not store secrets in this file.
# Sensitive values (JWT audience/issuer, alert emails, credentials) must come from
# AWS Secrets Manager or SSM Parameter Store.

aws_region       = "us-east-1"
environment      = "dev"
project_name     = "millerpic"
s3_bucket_prefix = "millerpic-photos"

enable_jwt_auth = true

enable_cost_protection                        = true
enable_sns_alert_topic                        = true
enable_aws_budgets                            = true
monthly_cost_budget_usd                       = 25
monthly_cost_forecast_alert_threshold_percent = 80

api_throttle_rate_limit  = 20
api_throttle_burst_limit = 40

lambda_reserved_concurrency_per_function = 10
download_url_ttl_seconds                 = 900

api_4xx_alarm_threshold           = 200
api_5xx_alarm_threshold           = 20
api_request_count_alarm_threshold = 5000
lambda_errors_alarm_threshold     = 5
lambda_throttles_alarm_threshold  = 1
alarm_period_seconds              = 300
alarm_evaluation_periods          = 1

tags = {
  Project   = "MillerPic"
  ManagedBy = "Terraform"
}
