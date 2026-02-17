locals {
  lambda_runtime       = "python3.12"
  lambda_target_vpc_id = "vpc-0d9d34e0e08aad1f7"
}

data "aws_caller_identity" "current" {}

data "aws_subnets" "lambda_target_vpc" {
  filter {
    name   = "vpc-id"
    values = [local.lambda_target_vpc_id]
  }
}

data "aws_subnet" "lambda_target_vpc" {
  for_each = toset(data.aws_subnets.lambda_target_vpc.ids)
  id       = each.value
}

locals {
  lambda_private_subnet_ids = [for subnet in data.aws_subnet.lambda_target_vpc : subnet.id if can(regex("private", lower(try(subnet.tags["Name"], ""))))]
}

locals {
  lambda_signing_profile_name_resolved = var.lambda_signing_profile_name != "" ? var.lambda_signing_profile_name : lower(replace(replace("${var.project_name}lambdasigner${var.environment}", "-", ""), "_", ""))
}

data "aws_signer_signing_profile" "lambda" {
  name = local.lambda_signing_profile_name_resolved
}

resource "aws_lambda_code_signing_config" "millerpic" {
  allowed_publishers {
    signing_profile_version_arns = [data.aws_signer_signing_profile.lambda.version_arn]
  }

  policies {
    untrusted_artifact_on_deployment = "Enforce"
  }
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

resource "aws_security_group" "lambda_vpc" {
  name        = "${var.project_name}-lambda-vpc-${var.environment}"
  description = "Security group for MillerPic Lambdas in private subnets"
  vpc_id      = local.lambda_target_vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_kms_key" "lambda_env" {
  description             = "CMK for Lambda environment variable encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EnableIAMUserPermissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      }
    ]
  })
}

resource "aws_kms_alias" "lambda_env" {
  name          = "alias/${var.project_name}-lambda-env-${var.environment}"
  target_key_id = aws_kms_key.lambda_env.key_id
}

resource "aws_kms_key" "lambda_dlq" {
  description             = "CMK for Lambda DLQ SQS encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowRootAccountAdmin"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowSQSServiceUse"
        Effect = "Allow"
        Principal = {
          Service = "sqs.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey*",
          "kms:ReEncrypt*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:CallerAccount" = data.aws_caller_identity.current.account_id
          }
          StringLike = {
            "kms:ViaService" = "sqs.${var.aws_region}.amazonaws.com"
          }
        }
      }
    ]
  })
}

resource "aws_kms_alias" "lambda_dlq" {
  name          = "alias/${var.project_name}-lambda-dlq-${var.environment}"
  target_key_id = aws_kms_key.lambda_dlq.key_id
}

resource "aws_sqs_queue" "lambda_dlq" {
  name                      = "${var.project_name}-lambda-dlq-${var.environment}"
  message_retention_seconds = 1209600
  kms_master_key_id         = aws_kms_key.lambda_dlq.arn
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

resource "aws_lambda_function" "upload" {
  #checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  function_name                  = "${var.project_name}-upload-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "upload.handler"
  s3_bucket                      = var.lambda_artifacts_bucket_name
  s3_key                         = lookup(var.lambda_artifact_object_keys, "upload", "signed/upload.zip")
  s3_object_version              = lookup(var.lambda_artifact_object_versions, "upload", null)
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  kms_key_arn             = aws_kms_key.lambda_env.arn
  code_signing_config_arn = aws_lambda_code_signing_config.millerpic.arn

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  vpc_config {
    subnet_ids         = local.lambda_private_subnet_ids
    security_group_ids = [aws_security_group.lambda_vpc.id]
  }

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

resource "aws_lambda_function" "download" {
  #checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  function_name                  = "${var.project_name}-download-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "download.handler"
  s3_bucket                      = var.lambda_artifacts_bucket_name
  s3_key                         = lookup(var.lambda_artifact_object_keys, "download", "signed/download.zip")
  s3_object_version              = lookup(var.lambda_artifact_object_versions, "download", null)
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  kms_key_arn             = aws_kms_key.lambda_env.arn
  code_signing_config_arn = aws_lambda_code_signing_config.millerpic.arn

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  vpc_config {
    subnet_ids         = local.lambda_private_subnet_ids
    security_group_ids = [aws_security_group.lambda_vpc.id]
  }

  environment {
    variables = {
      PHOTO_BUCKET             = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE             = aws_dynamodb_table.photos.name
      DOWNLOAD_URL_TTL_SECONDS = tostring(var.download_url_ttl_seconds)
    }
  }
}

resource "aws_lambda_function" "list" {
  #checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  function_name                  = "${var.project_name}-list-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "list.handler"
  s3_bucket                      = var.lambda_artifacts_bucket_name
  s3_key                         = lookup(var.lambda_artifact_object_keys, "list", "signed/list.zip")
  s3_object_version              = lookup(var.lambda_artifact_object_versions, "list", null)
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  kms_key_arn             = aws_kms_key.lambda_env.arn
  code_signing_config_arn = aws_lambda_code_signing_config.millerpic.arn

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  vpc_config {
    subnet_ids         = local.lambda_private_subnet_ids
    security_group_ids = [aws_security_group.lambda_vpc.id]
  }

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

resource "aws_lambda_function" "upload_complete" {
  #checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  function_name                  = "${var.project_name}-upload-complete-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "upload_complete.handler"
  s3_bucket                      = var.lambda_artifacts_bucket_name
  s3_key                         = lookup(var.lambda_artifact_object_keys, "upload_complete", "signed/upload_complete.zip")
  s3_object_version              = lookup(var.lambda_artifact_object_versions, "upload_complete", null)
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  kms_key_arn             = aws_kms_key.lambda_env.arn
  code_signing_config_arn = aws_lambda_code_signing_config.millerpic.arn

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  vpc_config {
    subnet_ids         = local.lambda_private_subnet_ids
    security_group_ids = [aws_security_group.lambda_vpc.id]
  }

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

resource "aws_lambda_function" "delete" {
  #checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  function_name                  = "${var.project_name}-delete-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "delete.handler"
  s3_bucket                      = var.lambda_artifacts_bucket_name
  s3_key                         = lookup(var.lambda_artifact_object_keys, "delete", "signed/delete.zip")
  s3_object_version              = lookup(var.lambda_artifact_object_versions, "delete", null)
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  kms_key_arn             = aws_kms_key.lambda_env.arn
  code_signing_config_arn = aws_lambda_code_signing_config.millerpic.arn

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  vpc_config {
    subnet_ids         = local.lambda_private_subnet_ids
    security_group_ids = [aws_security_group.lambda_vpc.id]
  }

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

resource "aws_lambda_function" "trash" {
  #checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  function_name                  = "${var.project_name}-trash-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "trash.handler"
  s3_bucket                      = var.lambda_artifacts_bucket_name
  s3_key                         = lookup(var.lambda_artifact_object_keys, "trash", "signed/trash.zip")
  s3_object_version              = lookup(var.lambda_artifact_object_versions, "trash", null)
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  kms_key_arn             = aws_kms_key.lambda_env.arn
  code_signing_config_arn = aws_lambda_code_signing_config.millerpic.arn

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  vpc_config {
    subnet_ids         = local.lambda_private_subnet_ids
    security_group_ids = [aws_security_group.lambda_vpc.id]
  }

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

resource "aws_lambda_function" "hard_delete" {
  #checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  function_name                  = "${var.project_name}-hard-delete-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "hard_delete.handler"
  s3_bucket                      = var.lambda_artifacts_bucket_name
  s3_key                         = lookup(var.lambda_artifact_object_keys, "hard_delete", "signed/hard_delete.zip")
  s3_object_version              = lookup(var.lambda_artifact_object_versions, "hard_delete", null)
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  kms_key_arn             = aws_kms_key.lambda_env.arn
  code_signing_config_arn = aws_lambda_code_signing_config.millerpic.arn

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  vpc_config {
    subnet_ids         = local.lambda_private_subnet_ids
    security_group_ids = [aws_security_group.lambda_vpc.id]
  }

  environment {
    variables = {
      PHOTO_BUCKET = aws_s3_bucket.photos.bucket
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

resource "aws_lambda_function" "patch_photo" {
  #checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  function_name                  = "${var.project_name}-patch-photo-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "patch_photo.handler"
  s3_bucket                      = var.lambda_artifacts_bucket_name
  s3_key                         = lookup(var.lambda_artifact_object_keys, "patch_photo", "signed/patch_photo.zip")
  s3_object_version              = lookup(var.lambda_artifact_object_versions, "patch_photo", null)
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  kms_key_arn             = aws_kms_key.lambda_env.arn
  code_signing_config_arn = aws_lambda_code_signing_config.millerpic.arn

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  vpc_config {
    subnet_ids         = local.lambda_private_subnet_ids
    security_group_ids = [aws_security_group.lambda_vpc.id]
  }

  environment {
    variables = {
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

resource "aws_lambda_function" "search" {
  #checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  function_name                  = "${var.project_name}-search-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "search.handler"
  s3_bucket                      = var.lambda_artifacts_bucket_name
  s3_key                         = lookup(var.lambda_artifact_object_keys, "search", "signed/search.zip")
  s3_object_version              = lookup(var.lambda_artifact_object_versions, "search", null)
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  kms_key_arn             = aws_kms_key.lambda_env.arn
  code_signing_config_arn = aws_lambda_code_signing_config.millerpic.arn

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  vpc_config {
    subnet_ids         = local.lambda_private_subnet_ids
    security_group_ids = [aws_security_group.lambda_vpc.id]
  }

  environment {
    variables = {
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}

resource "aws_lambda_function" "get_photo" {
  #checkov:skip=CKV_AWS_50: Budget-approved exception; X-Ray tracing deferred to avoid always-on trace ingestion/storage cost for family workload. Compensating controls: CloudWatch alarms/logs and DLQ coverage. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  function_name                  = "${var.project_name}-get-photo-${var.environment}"
  role                           = aws_iam_role.lambda_exec.arn
  runtime                        = local.lambda_runtime
  handler                        = "get_photo.handler"
  s3_bucket                      = var.lambda_artifacts_bucket_name
  s3_key                         = lookup(var.lambda_artifact_object_keys, "get_photo", "signed/get_photo.zip")
  s3_object_version              = lookup(var.lambda_artifact_object_versions, "get_photo", null)
  reserved_concurrent_executions = var.lambda_reserved_concurrency_per_function

  kms_key_arn             = aws_kms_key.lambda_env.arn
  code_signing_config_arn = aws_lambda_code_signing_config.millerpic.arn

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  vpc_config {
    subnet_ids         = local.lambda_private_subnet_ids
    security_group_ids = [aws_security_group.lambda_vpc.id]
  }

  environment {
    variables = {
      PHOTOS_TABLE = aws_dynamodb_table.photos.name
    }
  }
}
