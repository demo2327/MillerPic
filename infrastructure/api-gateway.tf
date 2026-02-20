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
    issuer   = local.jwt_issuer_effective
    audience = local.jwt_audience_effective
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

resource "aws_apigatewayv2_integration" "patch_photo" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.patch_photo.invoke_arn
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

resource "aws_apigatewayv2_integration" "search" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.search.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "get_photo" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.get_photo.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "albums_create" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.albums_create.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "albums_list" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.albums_list.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "albums_photos" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.albums_photos.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "albums_apply_labels" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.albums_apply_labels.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "albums_remove_labels" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.albums_remove_labels.invoke_arn
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

resource "aws_apigatewayv2_route" "patch_photo" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "PATCH /photos/{photoId}"
  target             = "integrations/${aws_apigatewayv2_integration.patch_photo.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_apigatewayv2_route" "get_photo" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "GET /photos/{photoId}"
  target             = "integrations/${aws_apigatewayv2_integration.get_photo.id}"
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

resource "aws_apigatewayv2_route" "search" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "GET /photos/search"
  target             = "integrations/${aws_apigatewayv2_integration.search.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_apigatewayv2_route" "albums_create" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "POST /albums"
  target             = "integrations/${aws_apigatewayv2_integration.albums_create.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_apigatewayv2_route" "albums_list" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "GET /albums"
  target             = "integrations/${aws_apigatewayv2_integration.albums_list.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_apigatewayv2_route" "albums_photos" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "GET /albums/{albumId}/photos"
  target             = "integrations/${aws_apigatewayv2_integration.albums_photos.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_apigatewayv2_route" "albums_apply_labels" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "POST /albums/{albumId}/photos/{photoId}/apply-labels"
  target             = "integrations/${aws_apigatewayv2_integration.albums_apply_labels.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_apigatewayv2_route" "albums_remove_labels" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "POST /albums/{albumId}/photos/{photoId}/remove-labels"
  target             = "integrations/${aws_apigatewayv2_integration.albums_remove_labels.id}"
  authorization_type = var.enable_jwt_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_jwt_auth ? aws_apigatewayv2_authorizer.jwt[0].id : null
}

resource "aws_cloudwatch_log_group" "api_access" {
  name              = "/aws/apigateway/${var.project_name}-http-api-${var.environment}"
  retention_in_days = 365
  kms_key_id        = "alias/aws/logs"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access.arn
    format = jsonencode({
      requestId               = "$context.requestId"
      ip                      = "$context.identity.sourceIp"
      requestTime             = "$context.requestTime"
      httpMethod              = "$context.httpMethod"
      routeKey                = "$context.routeKey"
      status                  = "$context.status"
      protocol                = "$context.protocol"
      responseLength          = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
    })
  }

  default_route_settings {
    throttling_rate_limit  = var.api_throttle_rate_limit
    throttling_burst_limit = var.api_throttle_burst_limit
  }
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

resource "aws_lambda_permission" "allow_apigw_patch_photo" {
  statement_id  = "AllowAPIGatewayInvokePatchPhoto"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.patch_photo.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_get_photo" {
  statement_id  = "AllowAPIGatewayInvokeGetPhoto"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_photo.function_name
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

resource "aws_lambda_permission" "allow_apigw_search" {
  statement_id  = "AllowAPIGatewayInvokeSearch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.search.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_albums_create" {
  statement_id  = "AllowAPIGatewayInvokeAlbumsCreate"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.albums_create.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_albums_list" {
  statement_id  = "AllowAPIGatewayInvokeAlbumsList"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.albums_list.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_albums_photos" {
  statement_id  = "AllowAPIGatewayInvokeAlbumsPhotos"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.albums_photos.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_albums_apply_labels" {
  statement_id  = "AllowAPIGatewayInvokeAlbumsApplyLabels"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.albums_apply_labels.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_albums_remove_labels" {
  statement_id  = "AllowAPIGatewayInvokeAlbumsRemoveLabels"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.albums_remove_labels.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}
