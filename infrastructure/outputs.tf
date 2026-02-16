output "photo_bucket_name" {
  value       = aws_s3_bucket.photos.bucket
  description = "S3 bucket for originals"
}

output "photos_table_name" {
  value       = aws_dynamodb_table.photos.name
  description = "DynamoDB table for photo metadata"
}

output "api_base_url" {
  value       = aws_apigatewayv2_api.http_api.api_endpoint
  description = "HTTP API endpoint"
}
