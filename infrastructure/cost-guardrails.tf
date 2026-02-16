locals {
  lambda_alarm_functions = {
    upload          = aws_lambda_function.upload.function_name
    download        = aws_lambda_function.download.function_name
    list            = aws_lambda_function.list.function_name
    upload_complete = aws_lambda_function.upload_complete.function_name
    patch_photo     = aws_lambda_function.patch_photo.function_name
    delete          = aws_lambda_function.delete.function_name
    trash           = aws_lambda_function.trash.function_name
    hard_delete     = aws_lambda_function.hard_delete.function_name
    search          = aws_lambda_function.search.function_name
    get_photo       = aws_lambda_function.get_photo.function_name
  }

  alert_email               = local.cost_alert_email_effective
  use_sns_alert_topic       = var.enable_cost_protection && var.enable_sns_alert_topic
  budget_has_any_subscriber = local.alert_email != "" || local.use_sns_alert_topic
  alarm_action_arns         = local.use_sns_alert_topic ? [aws_sns_topic.security_cost_alerts[0].arn] : []
  budget_sns_topic_arns     = local.use_sns_alert_topic ? [aws_sns_topic.security_cost_alerts[0].arn] : []
  budget_subscriber_emails  = local.alert_email != "" ? [local.alert_email] : []
  budget_notifications = local.budget_has_any_subscriber ? [
    {
      notification_type = "ACTUAL"
      threshold         = 100
    },
    {
      notification_type = "FORECASTED"
      threshold         = var.monthly_cost_forecast_alert_threshold_percent
    }
  ] : []
}

resource "aws_sns_topic" "security_cost_alerts" {
  count = local.use_sns_alert_topic ? 1 : 0

  name = "${var.project_name}-security-cost-alerts-${var.environment}"
}

resource "aws_sns_topic_subscription" "security_cost_alerts_email" {
  count = local.use_sns_alert_topic && local.alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.security_cost_alerts[0].arn
  protocol  = "email"
  endpoint  = local.alert_email
}

resource "aws_budgets_budget" "monthly_account_budget" {
  count = var.enable_cost_protection && var.enable_aws_budgets ? 1 : 0

  name              = "${var.project_name}-${var.environment}-monthly-budget"
  budget_type       = "COST"
  limit_amount      = tostring(var.monthly_cost_budget_usd)
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = "2026-01-01_00:00"

  dynamic "notification" {
    for_each = local.budget_notifications

    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value.threshold
      threshold_type             = "PERCENTAGE"
      notification_type          = notification.value.notification_type
      subscriber_sns_topic_arns  = local.budget_sns_topic_arns
      subscriber_email_addresses = local.budget_subscriber_emails
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "billing_estimated_charges" {
  count = var.enable_cost_protection && var.aws_region == "us-east-1" ? 1 : 0

  alarm_name          = "${var.project_name}-${var.environment}-billing-estimated-charges"
  alarm_description   = "Estimated AWS charges exceeded configured monthly budget threshold"
  namespace           = "AWS/Billing"
  metric_name         = "EstimatedCharges"
  statistic           = "Maximum"
  period              = 21600
  evaluation_periods  = 1
  threshold           = var.monthly_cost_budget_usd
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_action_arns

  dimensions = {
    Currency = "USD"
  }
}

resource "aws_cloudwatch_metric_alarm" "api_4xx" {
  count = var.enable_cost_protection ? 1 : 0

  alarm_name          = "${var.project_name}-${var.environment}-api-4xx-spike"
  alarm_description   = "API Gateway 4xx count exceeded threshold"
  namespace           = "AWS/ApiGateway"
  metric_name         = "4xx"
  statistic           = "Sum"
  period              = var.alarm_period_seconds
  evaluation_periods  = var.alarm_evaluation_periods
  threshold           = var.api_4xx_alarm_threshold
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_action_arns

  dimensions = {
    ApiId = aws_apigatewayv2_api.http_api.id
    Stage = aws_apigatewayv2_stage.default.name
  }
}

resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  count = var.enable_cost_protection ? 1 : 0

  alarm_name          = "${var.project_name}-${var.environment}-api-5xx-spike"
  alarm_description   = "API Gateway 5xx count exceeded threshold"
  namespace           = "AWS/ApiGateway"
  metric_name         = "5xx"
  statistic           = "Sum"
  period              = var.alarm_period_seconds
  evaluation_periods  = var.alarm_evaluation_periods
  threshold           = var.api_5xx_alarm_threshold
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_action_arns

  dimensions = {
    ApiId = aws_apigatewayv2_api.http_api.id
    Stage = aws_apigatewayv2_stage.default.name
  }
}

resource "aws_cloudwatch_metric_alarm" "api_request_count" {
  count = var.enable_cost_protection ? 1 : 0

  alarm_name          = "${var.project_name}-${var.environment}-api-request-surge"
  alarm_description   = "API Gateway request count exceeded threshold"
  namespace           = "AWS/ApiGateway"
  metric_name         = "Count"
  statistic           = "Sum"
  period              = var.alarm_period_seconds
  evaluation_periods  = var.alarm_evaluation_periods
  threshold           = var.api_request_count_alarm_threshold
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_action_arns

  dimensions = {
    ApiId = aws_apigatewayv2_api.http_api.id
    Stage = aws_apigatewayv2_stage.default.name
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = var.enable_cost_protection ? local.lambda_alarm_functions : {}

  alarm_name          = "${var.project_name}-${var.environment}-lambda-errors-${each.key}"
  alarm_description   = "Lambda errors exceeded threshold for ${each.key}"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = var.alarm_period_seconds
  evaluation_periods  = var.alarm_evaluation_periods
  threshold           = var.lambda_errors_alarm_threshold
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_action_arns

  dimensions = {
    FunctionName = each.value
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  for_each = var.enable_cost_protection ? local.lambda_alarm_functions : {}

  alarm_name          = "${var.project_name}-${var.environment}-lambda-throttles-${each.key}"
  alarm_description   = "Lambda throttles exceeded threshold for ${each.key}"
  namespace           = "AWS/Lambda"
  metric_name         = "Throttles"
  statistic           = "Sum"
  period              = var.alarm_period_seconds
  evaluation_periods  = var.alarm_evaluation_periods
  threshold           = var.lambda_throttles_alarm_threshold
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.alarm_action_arns

  dimensions = {
    FunctionName = each.value
  }
}
