terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.bootstrap_profile
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

locals {
  state_bucket_name         = "${var.state_bucket_prefix}-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
  app_sensitive_secret_name = "${var.project_name}/${var.environment}/app-sensitive-config"
}

resource "aws_s3_bucket" "terraform_state" {
  #checkov:skip=CKV_AWS_18: Budget-approved exception for bootstrap/state bucket; S3 access logs deferred to avoid additional bucket + log retention cost. Compensating controls: CloudTrail and strict IAM on state resources. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  #checkov:skip=CKV_AWS_144: Cross-region replication deferred due cost constraints for bootstrap/state workload; current durability posture is sufficient for present recovery objectives. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  bucket = local.state_bucket_name
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state_bucket.arn
    }

    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_iam_user" "terraform_deployer" {
  #checkov:skip=CKV_AWS_273: Terraform deployer remains an IAM user by explicit operational choice; access keys are managed manually with strict rotation/revocation procedures outside Terraform. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  name = var.terraform_deployer_user_name
}

resource "aws_iam_group" "terraform_deployer" {
  name = "${var.project_name}-terraform-deployer-group"
}

resource "aws_iam_group_membership" "terraform_deployer" {
  name  = "${var.project_name}-terraform-deployer-membership"
  users = [aws_iam_user.terraform_deployer.name]
  group = aws_iam_group.terraform_deployer.name
}

resource "aws_kms_key" "app_sensitive_config" {
  description             = "CMK for ${var.project_name} ${var.environment} app sensitive config secret"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EnableRootPermissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowSecretsManagerUse"
        Effect = "Allow"
        Principal = {
          Service = "secretsmanager.amazonaws.com"
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
            "kms:ViaService" = "secretsmanager.${var.aws_region}.amazonaws.com"
          }
        }
      }
    ]
  })
}

resource "aws_kms_key" "terraform_state_bucket" {
  description             = "CMK for bootstrap terraform state bucket encryption"
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

resource "aws_kms_alias" "terraform_state_bucket" {
  name          = "alias/${var.project_name}-terraform-state-${var.environment}"
  target_key_id = aws_kms_key.terraform_state_bucket.key_id
}

resource "aws_kms_alias" "app_sensitive_config" {
  name          = "alias/${var.project_name}-app-sensitive-config-${var.environment}"
  target_key_id = aws_kms_key.app_sensitive_config.key_id
}

resource "aws_secretsmanager_secret" "app_sensitive_config" {
  #checkov:skip=CKV2_AWS_57: Secret contains static sensitive configuration values (issuer/audience/contact), not rotatable credentials. Rotating identical values adds no security benefit; changes are controlled through IaC review and deployment process. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  name        = local.app_sensitive_secret_name
  description = "Sensitive application configuration for ${var.project_name} ${var.environment}"
  kms_key_id  = aws_kms_key.app_sensitive_config.arn
}

resource "aws_secretsmanager_secret_version" "app_sensitive_config" {
  secret_id = aws_secretsmanager_secret.app_sensitive_config.id
  secret_string = jsonencode({
    jwt_issuer       = var.jwt_issuer
    jwt_audience     = var.jwt_audience
    cost_alert_email = var.cost_alert_email
  })
}

resource "aws_iam_policy" "terraform_deployer" {
  name = "${var.project_name}-terraform-deployer-inline"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TerraformStateBucketAccess"
        Effect = "Allow"
        Action = [
          "s3:CreateBucket",
          "s3:DeleteBucket",
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:GetBucketVersioning",
          "s3:PutBucketVersioning",
          "s3:GetBucketPublicAccessBlock",
          "s3:PutBucketPublicAccessBlock",
          "s3:GetEncryptionConfiguration",
          "s3:PutEncryptionConfiguration",
          "s3:GetBucketPolicy",
          "s3:PutBucketPolicy",
          "s3:DeleteBucketPolicy"
        ]
        Resource = [
          aws_s3_bucket.terraform_state.arn
        ]
      },
      {
        Sid    = "TerraformStateObjectsAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:AbortMultipartUpload",
          "s3:ListBucketMultipartUploads",
          "s3:ListMultipartUploadParts"
        ]
        Resource = [
          "${aws_s3_bucket.terraform_state.arn}/*"
        ]
      },
      {
        Sid    = "ProjectInfrastructureControlPlane"
        Effect = "Allow"
        Action = [
          "apigateway:*",
          "budgets:*",
          "cloudwatch:*",
          "dynamodb:*",
          "events:*",
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:GetRole",
          "iam:TagRole",
          "iam:UntagRole",
          "iam:UpdateAssumeRolePolicy",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies",
          "iam:GetRolePolicy",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:CreatePolicy",
          "iam:DeletePolicy",
          "iam:GetPolicy",
          "iam:TagPolicy",
          "iam:UntagPolicy",
          "iam:GetPolicyVersion",
          "iam:CreatePolicyVersion",
          "iam:DeletePolicyVersion",
          "iam:ListPolicyVersions",
          "lambda:*",
          "logs:*",
          "s3:*",
          "secretsmanager:*",
          "sns:*",
          "xray:*",
          "sts:GetCallerIdentity"
        ]
        Resource = "*"
      },
      {
        Sid    = "PassRolesToServices"
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = "arn:${data.aws_partition.current.partition}:iam::*:role/${var.project_name}-*"
      }
    ]
  })
}

resource "aws_iam_group_policy_attachment" "terraform_deployer" {
  group      = aws_iam_group.terraform_deployer.name
  policy_arn = aws_iam_policy.terraform_deployer.arn
}
