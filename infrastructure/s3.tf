locals {
  photo_bucket_name = "${var.s3_bucket_prefix}-${var.environment}"
}

resource "aws_kms_key" "photos_bucket" {
  description             = "CMK for photos bucket default encryption"
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

resource "aws_kms_alias" "photos_bucket" {
  name          = "alias/${var.project_name}-photos-bucket-${var.environment}"
  target_key_id = aws_kms_key.photos_bucket.key_id
}

resource "aws_s3_bucket" "photos" {
  #checkov:skip=CKV_AWS_18: Budget-approved exception for family-scale workload; access logs deferred to avoid recurring storage/request cost. Compensating controls: CloudTrail, CloudWatch alarms, versioning, public access block. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  #checkov:skip=CKV_AWS_144: Cross-region replication deferred due cost constraints for family-scale workload; durability and recovery objectives currently met without CRR. Owner=MillerPic Platform Team; ReviewBy=2026-03-16.
  bucket = local.photo_bucket_name
}

resource "aws_s3_bucket_public_access_block" "photos" {
  bucket = aws_s3_bucket.photos.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "photos" {
  bucket = aws_s3_bucket.photos.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "photos" {
  bucket = aws_s3_bucket.photos.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.photos_bucket.arn
    }

    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_intelligent_tiering_configuration" "archive" {
  bucket = aws_s3_bucket.photos.id
  name   = "AutoArchive"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "photos" {
  bucket = aws_s3_bucket.photos.id

  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}
