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

### Scenario C: Large Family (5TB, 20 users, 5M photos)

| Service | Usage | Cost/Month | Notes |
|---------|-------|-----------|-------|
| **Lambda** | 50M requests | $10.00 | |
| **S3 Storage** | 5TB | $115.00 | Consider Intelligent-Tiering |
| **S3 Requests** | 500k PUT, 2.5M GET | $25.00 | |
| **DynamoDB** | On-demand | $125.00 | |
| **CloudFront** | 2.5TB outbound | $150.00 | $0.085/GB |
| **Data Transfer** | Regional | $0.00 | |
| **Secrets Manager** | 1 secret | $0.40 | |
| **CloudTrail** | 1 trail | $2.00 | |
| **Other** | | $10.00 | |
| **TOTAL** | | **~$438/month** | Can optimize with Glacier Tier |

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

## Cost Comparison: MillerPic vs Alternatives

### Monthly Cost for 1TB Storage

| Provider | Cost/Month | Notes |
|----------|-----------|-------|
| **MillerPic (AWS Serverless)** | $23-45 | Storage only |
| Google One | $100 | 2TB plan |
| OneDrive | $70 | 1TB plan |
| iCloud+ | $30 | 200GB (limited) |
| Backblaze B2 | $6 | Unlimited |
| **Shotgun + Compute** | | |
| MillerPic (with compute) | $50-100 | Full featured |
| SmugMug | $150+ | Full featured |
| Smugmug + AWS | $80-150 | Self-hosted |

**MillerPic Advantages**
- ✅ Digital ownership (your data, your infrastructure)
- ✅ Full resolution preservation
- ✅ Custom organization
- ✅ No vendor lock-in
- ✅ Unlimited photos (pay by GB)
- ✅ Privacy (no ads, no scanning)

---

## Monthly Cost Projections

```
Year 1 (Growing Collection)
Month 1-3:   $12-15 (AWS free tier)
Month 4-6:   $20-25 (100GB)
Month 7-12:  $40-50 (200-500GB)
Year 1 Total: ~$200

Year 2+ (Steady State)
Assume 2TB library: ~$80/month = $960/year
Compute stabilizes: +$10-20/month
Total Year 2+: ~$1,000-1,200/year
```

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

✅ **Do**
- Monitor costs weekly (first 3 months)
- Use free tier resources fully
- Enable S3 Intelligent-Tiering
- Implement CloudFront caching
- Set budget alerts

❌ **Don't**
- Replicate to multi-region initially
- Use provisioned DynamoDB capacity
- Create unnecessary GSI
- Store full-resolution thumbnails
- Enable analytics on every object

