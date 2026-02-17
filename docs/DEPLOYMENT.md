# MillerPic Deployment Guide (Terraform)

## Prerequisites

1. **AWS Account**: With appropriate permissions
2. **Terraform**: v1.6+
3. **AWS CLI**: Configured with credentials
4. **Node.js**: v20+ (for Lambda packaging)
5. **Google OAuth Credentials**: From Google Cloud Console

## Infrastructure Overview

The Terraform configuration deploys a complete serverless stack:

- **Compute**: Lambda functions with appropriate IAM roles
- **Storage**: S3 for photos, DynamoDB for metadata
- **Networking**: API Gateway, CloudFront, WAF
- **Security**: Secrets Manager, KMS encryption
- **Monitoring**: CloudWatch, X-Ray

## Directory Structure

```
infrastructure/
├── main.tf                 # Root module
├── variables.tf            # Variable definitions
├── outputs.tf              # Output values
├── vpc.tf                  # VPC configuration (if needed)
├── s3.tf                   # S3 buckets
├── dynamodb.tf             # DynamoDB tables
├── lambda.tf               # Lambda functions & IAM
├── api-gateway.tf          # API Gateway setup
├── cloudfront.tf           # CloudFront distribution
├── iam.tf                  # IAM roles & policies
├── secrets.tf              # Secrets Manager
├── networking.tf           # WAF & security
├── monitoring.tf           # CloudWatch setup
├── terraform.tfvars.example  # Example variables
├── environments/           # Environment-specific configs
│   ├── dev.tfvars
│   ├── staging.tfvars
│   └── prod.tfvars
└── modules/                # Reusable modules (optional)
    ├── lambda/
    ├── s3/
    └── dynamodb/
```

## Setup Instructions

### 1. Initialize Terraform

```bash
cd infrastructure

# Copy example vars file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

### 2. Configure Variables

**terraform.tfvars:**
```hcl
aws_region = "us-east-1"
environment = "dev"
project_name = "millerpic"
family_domain = "millerpic.family"

# Google OAuth
google_client_id = "your-client-id.apps.googleusercontent.com"
google_client_secret = "your-client-secret"

# Storage
s3_bucket_prefix = "millerpic-photos"
storage_quota_gb = 500

# Networking
allowed_origins = ["https://millerpic.family"]
rate_limit = 100 # requests per 5 minutes

# Tags
tags = {
  Project = "MillerPic"
  ManagedBy = "Terraform"
  CostCenter = "Family"
}
```

### 3. Initialize Backend

Set up remote state in S3:

```bash
# Create S3 bucket for state (one-time)
aws s3api create-bucket \
  --bucket millerpic-terraform-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket millerpic-terraform-state \
  --versioning-configuration Status=Enabled

# Create backend.tf
cat > backend.tf << 'EOF'
terraform {
  backend "s3" {
    bucket         = "millerpic-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
EOF
```

### 4. Plan Deployment

```bash
# Initialize Terraform
terraform init

# Review changes
terraform plan -out=tfplan

# Optional: Save plan for review
terraform show tfplan > plan.txt
```

### 4.1 Run Checkov (Terraform Security Scan)

Run Checkov locally before opening a Terraform PR:

```bash
python -m pip install --upgrade pip
pip install checkov
checkov --config-file ../.checkov.yml -d . -d bootstrap
```

Policy:
- CI enforces Checkov on Terraform changes.
- High/Critical findings fail checks by default.
- Any suppression must use explicit `checkov:skip=` comment with a clear justification.

Current approved suppressions (Sprint 6):
- `CKV_AWS_50` (Lambda X-Ray) — owner: MillerPic Platform Team; next review: 2026-03-16.
- `CKV_AWS_18` (S3 access logging) — owner: MillerPic Platform Team; next review: 2026-03-16.
- `CKV2_AWS_57` (Secrets Manager rotation for static sensitive config secret) — owner: MillerPic Platform Team; next review: 2026-03-16.

Governance:
- Suppressions must include compensating controls in the inline reason.
- Scope must remain limited to approved resources only.
- Reassessment is required at the next monthly budget/security review.

### 5. Deploy Infrastructure

```bash
# Apply changes
terraform apply tfplan

# Save outputs
terraform output > deployment-outputs.json
```

### 6. Configure Secrets

```bash
# Add Google OAuth credentials to Secrets Manager
aws secretsmanager create-secret \
  --name millerpic/google-oauth \
  --secret-string '{
    "client_id": "xxx",
    "client_secret": "xxx"
  }' \
  --region us-east-1
```

## Key Terraform Files

### main.tf
```hcl
terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

resource "aws_s3_bucket" "photos" {
  bucket = "${var.s3_bucket_prefix}-${var.environment}"
}

# ... more resources
```

### variables.tf
```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true
}

# ... more variables
```

### outputs.tf
```hcl
output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_stage.api.invoke_url
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain"
  value       = aws_cloudfront_distribution.cdn.domain_name
}

output "s3_bucket_name" {
  description = "S3 Photos bucket name"
  value       = aws_s3_bucket.photos.id
}

output "dynamodb_tables" {
  description = "DynamoDB table names"
  value = {
    photos        = aws_dynamodb_table.photos.name
    users         = aws_dynamodb_table.users.name
    albums        = aws_dynamodb_table.albums.name
    shared_links  = aws_dynamodb_table.shared_links.name
  }
}
```

## Environment-Specific Deployments

### Development
```bash
terraform plan -var-file="environments/dev.tfvars"
terraform apply -var-file="environments/dev.tfvars"
```

### Staging
```bash
terraform plan -var-file="environments/staging.tfvars"
terraform apply -var-file="environments/staging.tfvars"
```

### Production
```bash
terraform plan -var-file="environments/prod.tfvars" -out=prod-plan
terraform apply prod-plan
```

## Scaling & Configuration

### Lambda Concurrency
```hcl
resource "aws_lambda_provisioned_concurrency_config" "api" {
  function_name                     = aws_lambda_function.api.function_name
  provisioned_concurrent_executions = 100
  qualifier                         = aws_lambda_alias.live.name
}
```

### DynamoDB Capacity

**All Environments - On-Demand Billing (Recommended)**:
```hcl
# DynamoDB on-demand: ~$20/month for family usage
# Scales automatically, no provisioning needed
resource "aws_dynamodb_table" "photos" {
  billing_mode = "PAY_PER_REQUEST"  # ← On-demand, not provisioned
  
  # No capacity units needed - AWS manages scaling
  # Costs ~$1.25 per 1M writes, $0.25 per 1M reads
}
```

**Why:** 
- Simpler management (no capacity planning)
- Better for unpredictable family usage patterns
- ~$20/month for 6 users (steady state)
- Automatically scales up for spikes
- No complex autoscaling policies needed

### S3 Lifecycle
```hcl
resource "aws_s3_lifecycle_configuration" "photos" {
  bucket = aws_s3_bucket.photos.id

  rule {
    id     = "archive-old"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "INTELLIGENT_TIERING"
    }
  }
}
```

## Maintenance & Updates

### State Management

```bash
# List resources
terraform state list

# Show resource details
terraform state show 'aws_s3_bucket.photos'

# Backup state
cp terraform.tfstate terraform.tfstate.backup

# Pull latest state
terraform state pull > current-state.json
```

### Updates
```bash
# Check for updates
terraform plan

# Update specific resource
terraform apply -target=aws_lambda_function.api

# Full update
terraform apply
```

### Destroy (Careful!)
```bash
# Preview destruction
terraform plan -destroy

# Destroy everything
terraform destroy -var-file="environments/dev.tfvars"

# Destroy specific resource
terraform destroy -target=aws_lambda_function.api
```

## Monitoring Deployment

### CloudWatch
```bash
# View Lambda logs
aws logs tail /aws/lambda/millerpic-api --follow

# Get API metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

### X-Ray
```bash
# Enable X-Ray sampling
aws xray update-sampling-rule --cli-input-json file://sampling-rule.json
```

## Cost Optimization

### Reserved Capacity (Production)
```hcl
resource "aws_ec2_compute_reservation" "reserved" {
  # Saves 50-70% vs on-demand
}
```

### S3 Intelligent-Tiering
```hcl
resource "aws_s3_bucket_intelligent_tiering_configuration" "photos" {
  bucket = aws_s3_bucket.photos.id
  name   = "AutoArchive"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }
}
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Deploy Infrastructure

on:
  push:
    paths:
      - 'infrastructure/**'
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.6.0

      - name: Terraform Init
        run: cd infrastructure && terraform init

      - name: Terraform Plan
        run: cd infrastructure && terraform plan -out=tfplan

      - name: Terraform Apply
        run: cd infrastructure && terraform apply tfplan
```

## Troubleshooting

### Common Issues

**Issue**: `Error: error reading S3 Bucket`
```bash
# Solution: Check bucket policies and permissions
aws s3api get-bucket-policy --bucket millerpic-photos-dev
```

**Issue**: `Error: Invalid provider version`
```bash
# Solution: Update Terraform
terraform init -upgrade
```

**Issue**: `DynamoDB throttling`
```bash
# Solution: Increase capacity or enable autoscaling
terraform apply -var="read_capacity=500"
```

## Next Steps

1. Deploy core infrastructure
2. Package Lambda functions
3. Deploy web frontend to S3/CloudFront
4. Configure custom domain with Route53
5. Set up monitoring and alerts
6. Configure backup and disaster recovery

