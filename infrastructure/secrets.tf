locals {
  effective_sensitive_config_secret_name = trimspace(var.sensitive_config_secret_name) != "" ? var.sensitive_config_secret_name : "${var.project_name}/${var.environment}/app-sensitive-config"
}

data "aws_secretsmanager_secret" "app_sensitive_config" {
  count = var.load_sensitive_config_from_secrets && var.enable_jwt_auth ? 1 : 0

  name = local.effective_sensitive_config_secret_name
}

data "aws_secretsmanager_secret_version" "app_sensitive_config" {
  count = var.load_sensitive_config_from_secrets && var.enable_jwt_auth ? 1 : 0

  secret_id = data.aws_secretsmanager_secret.app_sensitive_config[0].id
}

locals {
  app_sensitive_config = merge(
    {
      jwt_issuer       = var.jwt_issuer
      jwt_audience     = var.jwt_audience
      cost_alert_email = var.cost_alert_email
    },
    try(jsondecode(data.aws_secretsmanager_secret_version.app_sensitive_config[0].secret_string), {})
  )

  jwt_issuer_effective       = try(local.app_sensitive_config.jwt_issuer, var.jwt_issuer)
  jwt_audience_effective     = try(local.app_sensitive_config.jwt_audience, var.jwt_audience)
  cost_alert_email_effective = trimspace(try(local.app_sensitive_config.cost_alert_email, var.cost_alert_email))
}
