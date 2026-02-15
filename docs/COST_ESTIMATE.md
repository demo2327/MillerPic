# MillerPic Cost Estimate & Optimization

## AWS Pricing Calculator (Monthly Estimates)

### Scenario A: Small Family (100GB, 5 users, 100k photos)

| Service | Usage | Cost/Month | Notes |
|---------|-------|-----------|-------|
| **Lambda** | 1M requests | $0.20 | Free tier: 1M/month |
| **S3 Storage** | 100GB | $2.30 | Standard storage |
| **S3 Requests** | 10k PUT, 50k GET | $0.50 | |
| **DynamoDB** | On-demand | $2.50 | Free tier: 25GB writes |
| **CloudFront** | 50GB outbound | $3.00 | $0.085/GB average |
| **Data Transfer** | Intra-AWS | $0.00 | No charge |
| **Secrets Manager** | 1 secret | $0.40 | $0.40/secret/month |
| **CloudTrail** | 1 trail | $2.00 | |
| **Other** (logs, etc) | | $1.00 | |
| **TOTAL** | | **~$12/month** | *AWS Free Tier eligible* |

### Scenario B: Medium Family (1TB, 10 users, 1M photos)

| Service | Usage | Cost/Month | Notes |
|---------|-------|-----------|-------|
| **Lambda** | 10M requests | $2.00 | Scales automatically |
| **S3 Storage** | 1TB | $23.00 | Standard storage |
| **S3 Requests** | 100k PUT, 500k GET | $5.00 | |
| **DynamoDB** | On-demand | $25.00 | Scales with usage |
| **CloudFront** | 500GB outbound | $30.00 | $0.085/GB |
| **Data Transfer** | Regional | $0.00 | |
| **Secrets Manager** | 1 secret | $0.40 | |
| **CloudTrail** | 1 trail | $2.00 | |
| **Other** | | $5.00 | |
| **TOTAL** | | **~$93/month** | |

### Scenario C: Large Family (5TB, 6 users, 5M photos)

**⚠️ WARNING: Standard Configuration (NOT RECOMMENDED)**

| Service | Usage | Cost/Month | Notes |
|---------|-------|-----------|-------|
| **Lambda** | 50M requests | $10.00 | |
| **S3 Storage** | 5TB | $115.00 | |
| **S3 Requests** | 500k PUT, 2.5M GET | $25.00 | |
| **DynamoDB** | On-demand | $125.00 | ❌ Most expensive for this scale |
| **CloudFront** | 2.5TB outbound | $150.00 | ❌ Unnecessary for family-only use |
| **Data Transfer** | Regional | $0.00 | |
| **Secrets Manager** | 1 secret | $0.40 | |
| **CloudTrail** | 1 trail | $2.00 | |
| **Other** | | $10.00 | |
| **TOTAL** | | **~$438/month** | ❌ NOT OPTIMIZED |

---

### Scenario C Optimized: (5TB, 6 users, 5M photos)

**✅ RECOMMENDED: Optimized for Private Family Use**

| Service | Usage | Cost/Month | Optimization |
|---------|-------|-----------|-------|
| **Lambda** | 20M requests | $5.00 | Direct S3 access, caching |
| **S3 Storage** | 5TB (Intelligent-Tiering) | $75.00 | Auto-archive old photos |
| **S3 Requests** | 200k PUT, 500k GET | $3.00 | Batch operations, direct access |
| **DynamoDB** | Provisioned w/ autoscaling | $50.00 | ✅ 60% savings vs on-demand |
| **DynamoDB DAX** | Caching layer | $15.00 | ✅ Reduces database reads 70% |
| **CloudFront** | Thumbnails only | $10.00 | ✅ Skip full images (family only) |
| **S3 Gateway Endpoint** | VPC access | $0.00 | No NAT gateway costs |
| **Secrets Manager** | 1 secret | $0.40 | |
| **CloudTrail** | 1 trail | $2.00 | |
| **Other** | | $5.00 | |
| **TOTAL** | | **~$165/month** | **✅ 62% COST REDUCTION** |

---

---

## Optimization Strategy: From $438 to $165/Month

### Key Insight: You're a **Private Family System**, Not a Public CDN

The main cost driver ($150/month CloudFront) assumes massive external sharing/downloading. **You don't need this.**

For a family photo system:
- ✅ Family members access from home/office (predictable bandwidth)
- ✅ Occasional sharing of albums via links (temporary spikes)
- ❌ Not serving millions of external users
- ❌ Not a public photo sharing site

### Optimization Breakdown

#### 1. **Skip CloudFront for Full Images** (-$140/month)

**Standard Approach** (Your current plan):
- Every download goes through CloudFront CDN worldwide
- Cost: $0.085/GB × 2.5TB = $150/month

**Optimized Approach**:
- CloudFront only for **thumbnails + web assets** (10GB/month)
- Family downloads directly from S3 via **presigned URLs** + **direct S3 access**
- Regional S3 is free for same-region Lambda
- Cost: $0.085 × 10GB = $0.85/month

**Why this works**:
- You have only 6 users (not millions)
- They're downloading from 1-2 regions (probably US)
- S3 is fast enough for internal family use (100-200ms)
- You save $140+ per month

**Implementation in Lambda**:
```javascript
// Instead of serving through CloudFront
const presignedUrl = await s3.getSignedUrlPromise('getObject', {
  Bucket: BUCKET,
  Key: `originals/${userId}/${photoId}.jpg`,
  Expires: 3600 // 1 hour
});

// Return this URL to family member
// They download directly from S3 (same region = free)
return { downloadUrl: presignedUrl };
```

#### 2. **DynamoDB: On-Demand → Provisioned + DAX** (-$60/month)

**Standard Approach** (On-Demand):
- Scales automatically but expensive
- Cost: $125/month for typical family usage

**Optimized Approach**:
- **Provisioned capacity**: 200 RCU + 100 WCU = $60/month
  - Based on: Family of 6 users, typical evening/morning usage
  - Auto-scaling handles spikes
- **DynamoDB Accelerator (DAX)**: $15/month
  - Caches hot data (recent photos, popular albums)
  - Reduces DynamoDB reads by 70%
  - Actually SAVES money despite added service
- Cost: $60 + $15 = $75/month

**Why this works**:
- Your access patterns are predictable
- 6 users = consistent workload
- DAX eliminates repeated queries
- Still cheaper than on-demand

```hcl
# Terraform: Provisioned with autoscaling
resource "aws_dynamodb_table" "photos" {
  billing_mode = "PROVISIONED"
  read_capacity_units  = 200
  write_capacity_units = 100
  
  autoscaling {
    index_name          = "GSI1"
    max_capacity        = 400
    min_capacity        = 100
    target_utilization  = 70
  }
}

# Add DAX cluster
resource "aws_dax_cluster" "cache" {
  iam_role_arn       = aws_iam_role.dax.arn
  node_type          = "dax.r5.large"
  replication_factor = 2  # HA
  
  subnet_group_name = aws_dax_subnet_group.main.name
}
```

#### 3. **S3 Intelligent-Tiering** (-$40/month)

**Standard Approach**:
- All 5TB stays in S3 Standard
- Cost: $0.023/GB × 5000GB = $115/month

**Optimized Approach**:
- Enable **S3 Intelligent-Tiering**
- Automatically moves old photos to cheaper tiers:
  - Recent (0-30 days): Frequent tier
  - Medium age (30-90 days): Infrequent tier (50% cheaper)
  - Old (90+ days): Archive tier (80% cheaper)
- Cost: ~$75/month average

**Why this works**:
- Family photos naturally follow access patterns
- You view recent vacation photos often
- Old photos (2020 and earlier) rarely accessed
- System automatically moves them and saves money

```hcl
resource "aws_s3_bucket_intelligent_tiering_configuration" "archive" {
  bucket = aws_s3_bucket.photos.id
  name   = "AutoArchive"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90   # Move to archive after 3 months
  }

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180  # Move to deep archive after 6 months
  }
}
```

#### 4. **Lambda Optimization** (-$5/month)

**Standard Approach**:
- Every request initializes fresh connections
- Cost: $10/month

**Optimized Approach**:
- Connection reuse (Lambda keeps warm)
- CloudWatch cache layer (avoid repeated database queries)
- Batch operations (reduce request count)
- Cost: $5/month

#### 5. **Reduce Unnecessary Requests** (-$10/month)

**Optimizations**:
- CloudFront caching headers for thumbnails (reduce GET requests)
- Browser caching for static assets
- Batch operations for bulk uploads
- Cost: Save $10/month in S3 request charges

---

## Cost Breakdown by Component

### 1. Compute (Lambda)

**Pricing Model**
- $0.20 per 1M requests
- $0.0000166667 per GB-second
- Free tier: 1M requests/month, 400k GB-seconds/month

**Estimated Usage**
```
Photo upload: 100 requests/day → 3k/month
Photo view: 10k requests/day → 300k/month
Album operations: 1k requests/day → 30k/month
Share access: 2k requests/day → 60k/month
Total: ~400k requests/month (Free tier)
```

**Optimization**
- Use Provisioned Concurrency for peaks (saves 50%)
- Cache responses with CloudFront
- Batch operations where possible

### 2. Storage (S3)

**Pricing Model**
- Standard: $0.023/GB/month
- Intelligent-Tiering: $0.0125/GB (frequent) + transitions
- Glacier: $0.004/GB/month (long-term archive)

**1TB Example**
```
Current month usage:
- Standard: 800GB @ $0.023 = $18.40
- Intelligent-Tiering: 200GB @ $0.0125 = $2.50
Total: $20.90/month

Annual savings with Intelligent-Tiering: ~$10-15/month
```

**S3 Requests**
```
PUT: $0.005 per 1k requests (uploads)
GET: $0.0004 per 1k requests (downloads)

Scenario: 10k uploads, 100k downloads/month
- PUT: (10k/1k) × $0.005 = $0.05
- GET: (100k/1k) × $0.0004 = $0.04
Total: $0.09/month
```

**Optimization**
- Enable S3 Intelligent-Tiering (auto-transitions cold data)
- Compress images before upload
- Delete old thumbnails automatically
- Use CloudFront caching

### 3. Database (DynamoDB)

**Pricing Model (On-Demand)**
- Write: $1.25 per 1M write units
- Read: $0.25 per 1M read units
- Storage: $0.25 per GB/month

**Estimated Usage**
```
Photo metadata writes: 50/day = 1,500/month
User/album writes: 100/day = 3,000/month
Total writes: 4,500/month → $0.0056

Photo list reads: 100,000/day = 3M/month
Photo detail reads: 50,000/day = 1.5M/month
Total reads: 4.5M/month → $1.125

Storage: 1GB metadata = $0.25
Total DynamoDB: ~$1.38/month (free tier up to 25GB writes)
```

**Optimization**
- Use GSI selectively (added cost)
- Batch operations (reduces write units)
- Monitor for hot partitions
- Consider Provisioned for predictable traffic

### 4. Content Delivery (CloudFront)

**Pricing Model**
- Data transfer: $0.085/GB (varies by region)
- HTTP requests: $0.0075 per 10k requests
- Cache invalidation: Free (up to 3k/month)

**Estimated Usage**
```
Photo thumbnail delivery: 100MB/day = 3GB/month
Photo full-resolution: 50MB/day = 1.5GB/month
Web assets: 10MB/day = 300MB/month
Total: 4.8GB/month → 4.8 × $0.085 = $0.41 + requests

HTTP requests: ~500k/month = $0.375
Total CloudFront: ~$0.79/month
```

**Optimization**
- Thumbnail caching: 1 month TTL
- Web assets: 1 week TTL
- Enable gzip compression
- Use signed URLs for sensitive content

### 5. Network (Data Transfer)

**Pricing Model**
- same region: FREE
- Inter-region: $0.02/GB out
- Out to internet: $0.09/GB first 10TB

**Scenario: All in us-east-1**
- Lambda → S3: FREE (same region)
- S3 → CloudFront: FREE (same region)
- CloudFront → Users: Included in CloudFront pricing
- Total: $0 additional

---

| Provider | Cost/Month | Notes |
|----------|-----------|-------|
| **MillerPic (Optimized)** | **$165** | ✅ Full features + infrastructure |
| Google One | $100 | 2TB only (not enough) |
| Google Workspace (1 user) | $10 | 1TB per user (need 6 = $60+) |
| OneDrive | $70 | 1TB only |
| Backblaze B2 | $120 | Storage only, no interface |
| SmugMug Premium | $240 | Full featured but limited |
| Flickr Pro | $130 | 1TB only |
| Amazon Photos | $120 | Part of Prime (requires membership) |
| iCloud+ | $100 | 2TB but Apple ecosystem only |
| Shutterfly (avg) | $150-200 | Photo printing focus |

**MillerPic Advantages**
- ✅ Digital ownership (your data, your infrastructure forever)
- ✅ Full resolution preservation (no compression)
- ✅ Complete privacy (no ads, no scanning, no AI)
- ✅ Custom organization and workflows
- ✅ No vendor lock-in (export anytime)
- ✅ Unlimited storage (pay by actual GB)
- ✅ Family multi-user built-in
- ✅ Secure sharing with control
- ✅ Predictable costs (AWS pricing stable)

---

## Monthly Cost Projections

```
PESSIMISTIC (Standard config, all CDN, on-demand DB):
Year 1 (Growing Collection):
  Month 1-3:    $25-40 (AWS free tier)
  Month 4-6:    $80-120 (200GB)
  Month 7-12:   $200-300 (500GB-1TB)
Year 1 Total:   ~$1,500

Year 2+ (5TB Steady State):
  Monthly:      $430-450
  Annual:       ~$5,200
  10-Year:      ~$52,000

OPTIMIZED (Presigned URLs, DynamoDB provisioned + DAX, Intelligent-Tiering):
Year 1 (Growing Collection):
  Month 1-3:    $10-20 (AWS free tier)
  Month 4-6:    $30-50 (200GB)
  Month 7-12:   $80-120 (500GB)
Year 1 Total:   ~$600

Year 2+ (5TB Steady State):
  Monthly:      $155-175
  Annual:       ~$1,900
  10-Year:      ~$19,000

SAVINGS: $33,000 over 10 years ($27.50/month savings)
```

## Monthly Cost Projections - Detailed

---

## Cost Optimization Strategies

### 1. S3 Storage Optimization

```hcl
# Intelligent-Tiering (automatic cost optimization)
resource "aws_s3_bucket_intelligent_tiering_configuration" "auto" {
  bucket = aws_s3_bucket.photos.id
  name   = "AutoArchive"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90  # Auto-archive after 3 months
  }

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180  # Ultra-cheap after 6 months
  }
}
```

**Estimated Savings**
- Year 1: $2-5/month (minimal old data)
- Year 2+: $10-15/month (significant archival)

### 2. Image Optimization

```
Original JPEG:     4MB (4032x3024 pixels, 12MP)
Thumbnail (120px): 5KB (lazy load)
Preview (600px):   80KB (gallery view)
Web optimized:     600KB (full download)

Savings: Store 1 original + 3 versions = 0.69MB vs 4MB = 83% savings
```

### 3. Lambda Optimization

```javascript
// Bad: Cold start every time
exports.handler = async (event) => {
  // Initialize at every invocation
  const AWS = require('aws-sdk');
  const s3 = new AWS.S3();
  // ...
};

// Good: Initialize outside handler
const AWS = require('aws-sdk');
const s3 = new AWS.S3();

exports.handler = async (event) => {
  // Reuse connection
  // ...
};

// Savings: ~100-200ms per request = reduced billing
```

### 4. DynamoDB Optimization

```hcl
# Use GSI sparingly
# Only create indexes you'll actually query
resource "aws_dynamodb_global_secondary_index" "email_lookup" {
  name            = "EmailIndex"
  hash_key        = "Email"
  projection_type = "INCLUDE"
  
  # Only project necessary attributes
  non_key_attributes = ["UserId", "Name"]
}
```

### 5. CloudFront Optimization

```
WITHOUT CloudFront:
- No caching, all requests → S3
- 100k requests × $0.0004 = $0.04
- 500GB transfer × $0.089 = $44.50
Total: $44.54/month

WITH CloudFront:
- 90% cache hit rate
- 10k origin requests × $0.0075 = $0.075
- 500GB transfer × $0.085 = $42.50
- CloudFront requests: $0.375
Total: $42.95/month
Savings: ~$1.59/month (5-10% for high-bandwidth users)

Better for latency (global delivery):
- US users: 100ms reduces to 10ms
- EU users: 200ms reduces to 50ms
- APAC users: 300ms reduces to 100ms
```

---

## Budget Alerts

### Set up AWS Budgets

```bash
# Create budget alert for $200/month
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

**budget.json**
```json
{
  "BudgetName": "MillerPic-Monthly",
  "BudgetLimit": {
    "Amount": "200",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

### CloudWatch Alarms

```hcl
resource "aws_cloudwatch_metric_alarm" "s3_cost_spike" {
  alarm_name          = "millerpic-s3-cost-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = "86400"
  statistic           = "Maximum"
  threshold           = "100"
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

---

## Cost Monitoring

### Monthly Review Checklist

```
□ S3 storage growth rate (GB/month)
□ DynamoDB read/write patterns
□ Lambda invocation count
□ CloudFront cache hit ratio
□ Top cost drivers
□ Any unexpected spikes
□ Optimization opportunities
```

### Tracking Dashboard

Create CloudWatch dashboard:
```bash
aws cloudwatch put-dashboard \
  --dashboard-name MillerPic-Costs \
  --dashboard-body file://dashboard.json
```

---

## Annual Comparison

```
Year 1 (Setup & Growth):
- Infrastructure setup: ~$50 (one-time)
- AWS costs: ~$400 (heavy usage as features added)
- Your time: ~200 hours @ free (or $?,??? value)
- Total: $450 infrastructure

Year 2+ (Steady State):
- Azure/Google: $1,200+/year (storage only)
- Flickr Pro: $700/year (unlimited)
- SmugMug+AWS: $2,000+/year
- MillerPic: $960-1,200/year (full control)

10-Year Savings vs Alternatives:
- vs Google One: ~$9,000
- vs SmugMug: ~$12,000+
- vs Shutterfly: ~$3,000
```

---

## Scaling Cost Impact

| Feature | Cost |
|---------|------|
| Video support (10x storage) | $80-100/month |
| Facial recognition | +$20-50/month |
| Advanced search | +$5-10/month |
| Backup replication (multi-region) | +$100/month |
| Mobile app notifications | +$5-10/month |

---

## Recommendations

✅ **Do (Cost Optimization)**
- ✅ **Skip public CDN** - Use presigned S3 URLs for family downloads
- ✅ **Enable S3 Intelligent-Tiering** - Automatic cost savings over time
- ✅ **Use DynamoDB provisioned** instead of on-demand for predictable load
- ✅ **Add DynamoDB DAX caching** - Reduces queries 70%, saves money
- ✅ **Monitor costs weekly** - Set CloudWatch alarms at $200/month
- ✅ **CloudFront only for thumbnails** - Minimal cost, big UX improvement
- ✅ **Batch operations** - Reduce Lambda invocations
- ✅ **Connection pooling** - Lambda reuses DB connections

❌ **Don't (Avoid These Costs)**
- ❌ Don't use CloudFront for ALL image deliveries (wastes money on family use)
- ❌ Don't use on-demand DynamoDB at scale (1.5x+ more expensive)
- ❌ Don't replicate to multi-region without need
- ❌ Don't create unnecessary GSI (each adds cost)
- ❌ Don't store full-resolution + uncompressed thumbnails
- ❌ Don't call database on every request (use caching)
- ❌ Don't enable logging everywhere (just what you need)

---

## Implementation Guide: Terraform Configuration for $165/Month

### Step 1: Presigned URLs Instead of CloudFront

**Backend Lambda (Node.js)**
```javascript
const AWS = require('aws-sdk');
const s3 = new AWS.S3();

exports.getDownloadUrl = async (event) => {
  const { photoId } = event.pathParameters;
  const { userId } = event.requestContext.authorizer;
  
  // Verify user owns this photo (omitted for brevity)
  
  // Generate presigned URL pointing directly to S3
  // NO CloudFront involved for full resolution
  const url = await s3.getSignedUrlPromise('getObject', {
    Bucket: process.env.PHOTO_BUCKET,
    Key: `originals/${userId}/${photoId}.jpg`,
    Expires: 3600, // 1 hour
    ResponseContentDisposition: `attachment; filename="${photoId}.jpg"`
  });
  
  return {
    statusCode: 200,
    body: JSON.stringify({
      status: 'success',
      data: { downloadUrl: url } // User downloads directly from S3
    })
  };
};
```

**Cloud Front only for thumbnails:**
```hcl
# Terraform: CloudFront ONLY for thumbnails
resource "aws_cloudfront_distribution" "thumbnails" {
  enabled = true
  
  origin {
    domain_name = aws_s3_bucket.photos.bucket_regional_domain_name
    origin_id   = "S3-Thumbnails"
  }
  
  default_cache_behavior {
    allowed_methods  = ["GET"]
    cached_methods   = ["GET"]
    target_origin_id = "S3-Thumbnails"
    
    # Cache TTL for thumbnails (long - they don't change)
    min_ttl     = 86400   # 1 day
    default_ttl = 2592000 # 30 days
    max_ttl     = 31536000 # 1 year
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
  }
  
  # Restrict to only thumbnail paths
  cache_behaviors {
    path_pattern     = "/thumbnails/*"
    allowed_methods  = ["GET"]
    cached_methods   = ["GET"]
    target_origin_id = "S3-Thumbnails"
    # ... same caching settings
  }
  
  # Deny full image paths
  cache_behaviors {
    path_pattern     = "/originals/*"
    target_origin_id = "S3-Thumbnails"
    
    viewer_protocol_policy = "deny"
    # This returns 403 Forbidden
    # Forces users to use presigned URLs instead
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
```

Result: CloudFront only serves ~10GB thumbnails/month = **$0.85/month** instead of $150

### Step 2: DynamoDB Provisioned + DAX

```hcl
# Terraform: DynamoDB with provisioned capacity + autoscaling
resource "aws_dynamodb_table" "photos" {
  name           = "millerpic-photos"
  billing_mode   = "PROVISIONED"
  hash_key       = "UserId"
  range_key      = "PhotoId"
  
  read_capacity_units  = 200   # Adjust based on family usage
  write_capacity_units = 100
  
  attribute {
    name = "UserId"
    type = "S"
  }
  
  attribute {
    name = "PhotoId"
    type = "S"
  }
  
  attribute {
    name = "UploadedAt"
    type = "N"
  }
  
  ttl {
    attribute_name = "ExpiresAt"
    enabled        = true
  }
  
  sse_specification {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }
  
  point_in_time_recovery {
    enabled = true
  }
  
  # GSI for queries by upload date
  global_secondary_index {
    name            = "UploadDateIndex"
    hash_key        = "UserId"
    range_key       = "UploadedAt"
    projection_type = "ALL"
    
    read_capacity_units  = 100
    write_capacity_units = 50
  }
}

# Autoscaling for main table
resource "aws_appautoscaling_target" "photos_read" {
  max_capacity       = 400
  min_capacity       = 200
  resource_id        = "table/${aws_dynamodb_table.photos.name}"
  scalable_dimension = "dynamodb:table:ReadCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "photos_read_policy" {
  policy_name               = "DynamoDBReadScaling"
  policy_type               = "TargetTrackingScaling"
  resource_id               = aws_appautoscaling_target.photos_read.resource_id
  scalable_dimension        = aws_appautoscaling_target.photos_read.scalable_dimension
  service_namespace         = aws_appautoscaling_target.photos_read.service_namespace
  
  target_tracking_scaling_policy_configuration {
    target_value = 70 # Target 70% utilization
  }
}

# DynamoDB Accelerator (DAX) for caching
resource "aws_dax_cluster" "cache" {
  cluster_name       = "millerpic-cache"
  iam_role_arn       = aws_iam_role.dax.arn
  node_type          = "dax.r5.large"
  replication_factor = 2  # High availability
  
  # Only 2 nodes = $15/month
  
  subnet_group_name = aws_dax_subnet_group.dax.name
  
  security_group_ids = [aws_security_group.dax.id]
}

# Subnet group for DAX
resource "aws_dax_subnet_group" "dax" {
  name       = "millerpic-dax"
  subnet_ids = [aws_subnet.private1.id, aws_subnet.private2.id]
}
```

**Cost calculation:**
- DynamoDB Provisioned (200 RCU): $50/month
- Auto-scaling (handles spikes): No additional cost
- DAX cluster (2 nodes, cache-heavy usage): $15/month
- **Total: $65/month** vs $125/month on-demand = **$60/month savings**

### Step 3: S3 Intelligent-Tiering

```hcl
resource "aws_s3_bucket_intelligent_tiering_configuration" "archive" {
  bucket = aws_s3_bucket.photos.id
  name   = "OptimalArchive"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }
}
```

**Cost model:**
- Frequent (new): 2TB @ $0.023/GB = $46
- Infrequent (medium): 2TB @ $0.0125/GB = $25
- Archive (old): 1TB @ $0.004/GB = $4
- **Total: ~$75/month** vs $115/month = **$40/month savings**

### Deployment Script

```bash
#!/bin/bash
# deploy-optimized.sh

cd infrastructure

# Set variables
export TF_VAR_environment="prod"
export TF_VAR_enable_dax=true
export TF_VAR_cloudfront_for_originals=false  # Only thumbnails!
export TF_VAR_dynamodb_billing_mode="PROVISIONED"
export TF_VAR_dynamodb_rcu=200
export TF_VAR_dynamodb_wcu=100

# Plan & apply
terraform init
terraform plan -out=tfplan
terraform apply tfplan

echo "Deployment complete!"
echo "Cost should be ~$165/month"
```

---

## Realistic Cost for Your Family

**Your expected monthly costs with 5TB, 6 users:**

| Component | Cost |
|-----------|------|
| S3 Storage (5TB with Intelligent-Tiering) | $75 |
| S3 Requests (optimized) | $3 |
| Lambda (optimized) | $5 |
| DynamoDB + DAX (provisioned + cache) | $65 |
| CloudFront (thumbnails only) | $1 |
| KMS, Secrets, Monitoring, Other | $8 |
| **TOTAL MONTHLY** | **$157** |
| **ANNUAL** | **$1,884** |

**Comparing to alternatives for 5TB:**
- MillerPic Optimized: **$157/month** ✅
- Google Workspace (6 users @ 1TB each): $10 × 6 = **$60** (but only 6TB storage)
- Google One (2TB): **$100** (not enough storage)
- OneDrive (6 users with 1TB each): $120 × 6 = **$720** 😱
- Backblaze B2 storage only: ~$115 (no interface/app)
- SmugMug unlimited: **$240-300**
- Shutterfly: **$150-200**

**The reality:**
- ✅ You get a **full-featured** photo app (web + mobile + desktop)
- ✅ **Complete control** of your data forever
- ✅ **Unlimited storage** (pay only by actual GB used)
- ✅ **No subscription games** or vendor lock-in
- ✅ **Multiple family members** with proper roles
- ✅ Still cheaper than most alternatives once you add compute/interface
- ✅ Predictable costs that won't change arbitrarily

With these optimizations, **$157/month is very reasonable** for storing a lifetime of family photos with full resolution, multiple users, secure sharing, and complete privacy.

---

## Final Checklist: Implementing the $157/Month Setup

Before deploying, ensure you:

- [ ] Understand the presigned URL approach (NO CloudFront for full images)
- [ ] Have AWS account ready with admin access
- [ ] Have Terraform v1.6+ installed locally
- [ ] Have AWS CLI configured with credentials
- [ ] Read through the Implementation Guide above
- [ ] Set CloudWatch alarm at $200/month
- [ ] Plan for Year 1 costs (start lower, grow to ~$157 by month 12)
- [ ] Accept that $157 is your steady-state cost (doesn't scale after ~5TB)
- [ ] Understand S3 Intelligent-Tiering is automatic (no management needed)
- [ ] Know that presigned URLs require HTTPS but no other changes



