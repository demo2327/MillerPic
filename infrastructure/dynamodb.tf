resource "aws_dynamodb_table" "photos" {
  name         = "${var.project_name}-photos-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "UserId"
  range_key    = "PhotoId"

  attribute {
    name = "UserId"
    type = "S"
  }

  attribute {
    name = "PhotoId"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }
}
