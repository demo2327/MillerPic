locals {
  lambda_runtime = "python3.12"
}

data "archive_file" "upload" {
  type        = "zip"
  source_file = "${path.module}/../backend/src/handlers/upload.py"
  output_path = "${path.module}/.artifacts/upload.zip"
}

data "archive_file" "download" {
  type        = "zip"
  source_file = "${path.module}/../backend/src/handlers/download.py"
  output_path = "${path.module}/.artifacts/download.zip"
}

data "archive_file" "list" {
  type        = "zip"
  source_file = "${path.module}/../backend/src/handlers/list.py"
  output_path = "${path.module}/.artifacts/list.zip"
}

resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "app_policy" {
  name = "${var.project_name}-lambda-policy-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:HeadObject"]
        Resource = "${aws_s3_bucket.photos.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query"]
        Resource = aws_dynamodb_table.photos.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "app_policy_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.app_policy.arn
}

resource "aws_lambda_function" "upload" {
  function_name = "${var.project_name}-upload-${var.environment}"
  role          = aws_iam_role.lambda_exec.arn
  runtime       = local.lambda_runtime
  handler       = "upload.handler"
  filename      = data.archive_file.upload.output_path

  source_code_hash = data.archive_file.upload.output_base64sha256

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

resource "aws_lambda_function" "download" {
  function_name = "${var.project_name}-download-${var.environment}"
  role          = aws_iam_role.lambda_exec.arn
  runtime       = local.lambda_runtime
  handler       = "download.handler"
  filename      = data.archive_file.download.output_path

  source_code_hash = data.archive_file.download.output_base64sha256

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

resource "aws_lambda_function" "list" {
  function_name = "${var.project_name}-list-${var.environment}"
  role          = aws_iam_role.lambda_exec.arn
  runtime       = local.lambda_runtime
  handler       = "list.handler"
  filename      = data.archive_file.list.output_path

  source_code_hash = data.archive_file.list.output_base64sha256

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}
