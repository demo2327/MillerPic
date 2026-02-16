resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.project_name}-api-${var.environment}"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_authorizer" "jwt" {
  count = var.enable_jwt_auth ? 1 : 0

  api_id          = aws_apigatewayv2_api.http_api.id
  authorizer_type = "JWT"
  identity_sources = [
    "$request.header.Authorization"
  ]
  name = "${var.project_name}-jwt-authorizer-${var.environment}"

  jwt_configuration {
    issuer   = var.jwt_issuer
    audience = var.jwt_audience
  }
}

resource "aws_apigatewayv2_integration" "upload" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.upload.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "download" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.download.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "list" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.list.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "upload_complete" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.upload_complete.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "delete" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.delete.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "trash" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.trash.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "hard_delete" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.hard_delete.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "upload" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "POST /photos/upload-url"
  target             = "integrations/${aws_apigatewayv2_integration.upload.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_apigatewayv2_route" "download" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "GET /photos/{photoId}/download-url"
  target             = "integrations/${aws_apigatewayv2_integration.download.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_apigatewayv2_route" "list" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "GET /photos"
  target             = "integrations/${aws_apigatewayv2_integration.list.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_apigatewayv2_route" "upload_complete" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "POST /photos/upload-complete"
  target             = "integrations/${aws_apigatewayv2_integration.upload_complete.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_apigatewayv2_route" "delete" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "DELETE /photos/{photoId}"
  target             = "integrations/${aws_apigatewayv2_integration.delete.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_apigatewayv2_route" "trash" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "GET /photos/trash"
  target             = "integrations/${aws_apigatewayv2_integration.trash.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_apigatewayv2_route" "hard_delete" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "DELETE /photos/{photoId}/hard"
  target             = "integrations/${aws_apigatewayv2_integration.hard_delete.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "allow_apigw_upload" {
  statement_id  = "AllowAPIGatewayInvokeUpload"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.upload.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_download" {
  statement_id  = "AllowAPIGatewayInvokeDownload"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.download.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_list" {
  statement_id  = "AllowAPIGatewayInvokeList"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.list.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_upload_complete" {
  statement_id  = "AllowAPIGatewayInvokeUploadComplete"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.upload_complete.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_delete" {
  statement_id  = "AllowAPIGatewayInvokeDelete"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.delete.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_trash" {
  statement_id  = "AllowAPIGatewayInvokeTrash"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trash.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_hard_delete" {
  statement_id  = "AllowAPIGatewayInvokeHardDelete"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hard_delete.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}
