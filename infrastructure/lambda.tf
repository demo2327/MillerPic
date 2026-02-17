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

data "archive_file" "upload_complete" {
  type        = "zip"
  source_file = "${path.module}/../backend/src/handlers/upload_complete.py"
  output_path = "${path.module}/.artifacts/upload_complete.zip"
}

data "archive_file" "patch_photo" {
  type        = "zip"
  source_file = "${path.module}/../backend/src/handlers/patch_photo.py"
  output_path = "${path.module}/.artifacts/patch_photo.zip"
}

data "archive_file" "delete" {
  type        = "zip"
  source_file = "${path.module}/../backend/src/handlers/delete.py"
  output_path = "${path.module}/.artifacts/delete.zip"
}

data "archive_file" "trash" {
  type        = "zip"
  source_file = "${path.module}/../backend/src/handlers/trash.py"
  output_path = "${path.module}/.artifacts/trash.zip"
}

data "archive_file" "hard_delete" {
  type        = "zip"
  source_file = "${path.module}/../backend/src/handlers/hard_delete.py"
  output_path = "${path.module}/.artifacts/hard_delete.zip"
}

data "archive_file" "search" {
  type        = "zip"
  source_file = "${path.module}/../backend/src/handlers/search.py"
  output_path = "${path.module}/.artifacts/search.zip"
}

data "archive_file" "get_photo" {
  type        = "zip"
  source_file = "${path.module}/../backend/src/handlers/get_photo.py"
  output_path = "${path.module}/.artifacts/get_photo.zip"
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

resource "aws_sqs_queue" "lambda_dlq" {
  name                      = "${var.project_name}-lambda-dlq-${var.environment}"
  message_retention_seconds = 1209600
  kms_master_key_id         = "alias/aws/sqs"
}

resource "aws_iam_policy" "app_policy" {
  name = "${var.project_name}-lambda-policy-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:HeadObject", "s3:DeleteObject"]
        Resource = "${aws_s3_bucket.photos.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query", "dynamodb:UpdateItem", "dynamodb:DeleteItem"]
        Resource = aws_dynamodb_table.photos.arn
      },
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = aws_sqs_queue.lambda_dlq.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "app_policy_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.app_policy.arn
}

#checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
resource "aws_lambda_function" "upload" {
  function_name                  = "${var.project_name}-upload-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "upload.handler"
  filename                       = data.archive_file.upload.output_path
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  source_code_hash = data.archive_file.upload.output_base64sha256

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

#checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
resource "aws_lambda_function" "download" {
  function_name                  = "${var.project_name}-download-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "download.handler"
  filename                       = data.archive_file.download.output_path
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  source_code_hash = data.archive_file.download.output_base64sha256

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  environment {
    variables = {
      PHOTO_BUCKET             = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE             = aws_dynamodb_table.photos.name
      DOWNLOAD_URL_TTL_SECONDS = tostring(var.download_url_ttl_seconds)
    }
  }
}

#checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
resource "aws_lambda_function" "list" {
  function_name                  = "${var.project_name}-list-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "list.handler"
  filename                       = data.archive_file.list.output_path
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  source_code_hash = data.archive_file.list.output_base64sha256

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

#checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
resource "aws_lambda_function" "upload_complete" {
  function_name                  = "${var.project_name}-upload-complete-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "upload_complete.handler"
  filename                       = data.archive_file.upload_complete.output_path
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  source_code_hash = data.archive_file.upload_complete.output_base64sha256

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

#checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
resource "aws_lambda_function" "delete" {
  function_name                  = "${var.project_name}-delete-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "delete.handler"
  filename                       = data.archive_file.delete.output_path
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  source_code_hash = data.archive_file.delete.output_base64sha256

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

#checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
resource "aws_lambda_function" "trash" {
  function_name                  = "${var.project_name}-trash-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "trash.handler"
  filename                       = data.archive_file.trash.output_path
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  source_code_hash = data.archive_file.trash.output_base64sha256

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

#checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
resource "aws_lambda_function" "hard_delete" {
  function_name                  = "${var.project_name}-hard-delete-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "hard_delete.handler"
  filename                       = data.archive_file.hard_delete.output_path
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  source_code_hash = data.archive_file.hard_delete.output_base64sha256

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

#checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
resource "aws_lambda_function" "patch_photo" {
  function_name                  = "${var.project_name}-patch-photo-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "patch_photo.handler"
  filename                       = data.archive_file.patch_photo.output_path
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  source_code_hash = data.archive_file.patch_photo.output_base64sha256

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  environment {
    variables = {
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

#checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
resource "aws_lambda_function" "search" {
  function_name                  = "${var.project_name}-search-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "search.handler"
  filename                       = data.archive_file.search.output_path
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  source_code_hash = data.archive_file.search.output_base64sha256

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  environment {
    variables = {
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

#checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
resource "aws_lambda_function" "get_photo" {
  function_name                  = "${var.project_name}-get-photo-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "get_photo.handler"
  filename                       = data.archive_file.get_photo.output_path
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  source_code_hash = data.archive_file.get_photo.output_base64sha256

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  environment {
    variables = {
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}
