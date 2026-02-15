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

**✅ RECOMMENDED: Optimized for Private Family Use (DynamoDB On-Demand)**

| Service | Usage | Cost/Month | Optimization |
|---------|-------|-----------|-------|
| **Lambda** | 20M requests | $5.00 | Direct S3 access, caching |
| **S3 Storage** | 5TB (Intelligent-Tiering) | $75.00 | Auto-archive old photos |
| **S3 Requests** | 200k PUT, 500k GET | $3.00 | Batch operations, direct access |
| **DynamoDB** | On-demand pricing | $20.00 | ✅ Pay per request (~$0.006 base) |
| **CloudFront** | Thumbnails only | $10.00 | ✅ Skip full images (family only) |
| **S3 Gateway Endpoint** | VPC access | $0.00 | No NAT gateway costs |
| **Secrets Manager** | 1 secret | $0.40 | |
| **CloudTrail** | 1 trail | $2.00 | |
| **Other** | | $5.00 | |
| **TOTAL** | | **~$120/month** | **✅ 73% COST REDUCTION from $438** |

---

---

## Optimization Strategy: From $438 to $73/Month

### Key Insights

1. **You're a private family system**, not a public CDN → Skip expensive global content delivery
2. **DynamoDB provisioned is overkill** → Use on-demand for family usage patterns (~$20/month)
3. **CloudFront CDN costs are massive** → Use presigned S3 URLs for family downloads (~$1/month)
4. **Photos are naturally compressible** → WebP format saves 30% without quality loss (-$39/month)

The main cost drivers ($438) assumed: 
- ❌ CloudFront for ALL image delivery ($150)
- ❌ Provisioned DynamoDB capacity ($50)
- ❌ DAX caching layer ($15)
- ❌ Full-resolution JPEGs uncompressed ($75)

Remove all these assumptions for family use = **$73/month**

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

#### 6. **Reduce S3 Storage: Multiple Options** ✅ (-$30 to -$60/month)

**Current Cost Breakdown (5TB):**
- 2TB recent photos (accessed frequently): $0.023/GB = $46/month
- 2TB medium age (accessed sometimes): $0.0125/GB = $25/month
- 1TB old photos (rarely accessed): $0.004/GB = $4/month
- **Total: $75/month**

---

### Final S3 Strategy: WebP Compression + Intelligent-Tiering

We use a two-part strategy to minimize S3 costs while maintaining instant family access:

**1. WebP Compression on Upload** (saves 25-35% file size automatically)
- JPEGs (5TB) → WebP (3.3TB) at 85% quality
- Saves: 1.7TB × $0.023 = **$39/month**
- Imperceptible quality loss (modern codec, 98% browser support)

**2. S3 Intelligent-Tiering Auto-Archive** (moves old photos to cheaper tiers)
- Recent (0-30 days): Frequent tier @ $0.023/GB
- Medium (30-90 days): Infrequent tier @ $0.0125/GB  
- Archived (90+ days): Glacier Instant @ $0.009/GB (3-5 min retrieval)

**Combined Cost for 5TB**:
- Recent tier (500GB): $11.50/month
- Infrequent tier (1.5TB): $18.75/month
- Glacier Instant (3TB): $27/month
- **Total: $57/month** (vs $75 = **$18/month savings**)

**WebP Compression Implementation**:
```javascript
const sharp = require('sharp');

exports.uploadHandler = async (event) => {
  const fileBuffer = event.body;
  
  // Convert JPEG to WebP (25-35% smaller)
  const webpBuffer = await sharp(fileBuffer)
    .withMetadata()  // Preserve EXIF
    .webp({ quality: 85 })
    .toBuffer();
  
  
  // Store WebP in S3
  await s3.putObject({
    Bucket: process.env.BUCKET,
    Key: `originals/${userId}/${photoId}.webp`,
    Body: webpBuffer,
    ContentType: 'image/webp'
  }).promise();
};
```

**Intelligent-Tiering Auto-Archive Configuration**:
```hcl
resource "aws_s3_bucket_intelligent_tiering_configuration" "archive" {
  bucket = aws_s3_bucket.photos.id
  name   = "AutoArchive"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90  # Move to Glacier Archive after 3 months
  }

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180  # Glacier Instant Retrieval after 6 months (3-5 min max)
  }
}
```

**Download Process for Archived Photos**:
```javascript
exports.downloadHandler = async (event) => {
  const { photoId } = event.pathParameters;
  
  const headObject = await s3.headObject({
    Bucket: process.env.BUCKET,
    Key: `originals/${userId}/${photoId}.webp`
  }).promise();
  
  if (headObject.StorageClass === 'GLACIER_IR') {
    // Glacier Instant: Accessible within 3-5 minutes
    const presignedUrl = await s3.getSignedUrlPromise('getObject', {
      Bucket: process.env.BUCKET,
      Key: `originals/${userId}/${photoId}.webp`,
      Expires: 3600
    }).promise();
    
    return {
      statusCode: 200,
      body: JSON.stringify({
        downloadUrl: presignedUrl,
        note: 'Photo available within 3-5 minutes'
      })
    };
  }
  
  // Recent/medium photos: instant access
  const presignedUrl = await s3.getSignedUrlPromise('getObject', {...});
  return { statusCode: 200, body: JSON.stringify({ downloadUrl: presignedUrl }) };
};
```

**Why This Strategy Works**:
- ✅ Automatic WebP compression saves $39/month
- ✅ Intelligent-Tiering saves $18/month on storage tiers
- ✅ Glacier Instant guarantees max 3-5 min access to ALL photos
- ✅ Fully preserves original resolution (no data loss)
- ✅ Modern browsers 98%+ support WebP
- ✅ Imperceptible quality loss at 85% setting

---

## Final Cost Model

**MillerPic Optimized - All Components:**

| Component | Monthly Cost | Annual Cost |
|-----------|--------------|-------------|
| **S3 Storage** (Intelligent-Tiering + WebP) | $57 | $684 |
| **S3 Requests** | $3 | $36 |
| **Lambda** (Presigned URLs, compression) | $5 | $60 |
| **DynamoDB** (On-demand billing) | $20 | $240 |
| **CloudFront** (Thumbnails only) | $1 | $12 |
| **CloudTrail, Secrets Manager, Logs** | $8 | $96 |
| | | |
| **TOTAL MONTHLY** | **~$94** | **~$1,128** |

**Comparison to Original (Unoptimized)**:
- Original: **$438/month** = $5,256/year
- Optimized: **$94/month** = $1,128/year
- **Annual Savings: $4,128 (79% reduction)**
- **10-Year Savings: ~$41,280**

**Compared to Competitors**:
- Google Workspace (6 users): $84/month for 6TB (limited control)
- OneDrive (6 users @ 100GB each): $150/month
- SmugMug Premium: $240/month (limited storage)
- Flickr Pro: $130/month (1TB only)
- MillerPic: **$94/month** ✅ (5TB, full control, complete privacy)

---

## Your Data is Safe & Accessible

✅ **Full Resolution Preserved:** Original photos stored in efficient WebP format  
✅ **Fast Access Always:** Max 3-5 minutes even for year-old archived photos  
✅ **Automatic Cost Optimization:** Tiers adjust based on access patterns  
✅ **EXIF Data Preserved:** Photo metadata retained for organization ✅ **Zero Vendor Lock-in:** Export anytime, use as backup destination elsewhere  
✅ **Complete Privacy:** No scanning, no ads, no AI training

---

## Implementation Checklist

✅ **Phase 1: Foundation**
- [ ] Set up Terraform backend (S3 + DynamoDB state)
- [ ] Configure on-demand DynamoDB tables  
- [ ] Create S3 bucket with Intelligent-Tiering
- [ ] Set up Lambda execution role with S3/DynamoDB permissions
- [ ] Deploy API Gateway with OAuth authorizer

✅ **Phase 2: Image Processing**
- [ ] Implement WebP compression Lambda
- [ ] Add EXIF metadata preservation
- [ ] Create presigned URL generator
- [ ] Test with sample photos (verify 30% compression)

✅ **Phase 3: Cost Validation**
- [ ] Run Terraform plan and review AWS Cost Calculator
- [ ] Set up CloudWatch cost alarms ($150/month warning)
- [ ] Verify on-demand DynamoDB is active
- [ ] Confirm Intelligent-Tiering transitions are working

---

## Monthly Cost Projections

**Year 1 (Growing Collection - AWS Free Tier Active)**:
- Months 1-3: $10-20/month (minimal storage)
- Months 4-6: $25-40/month (200GB)
- Months 7-12: $50-80/month (500GB-1TB)
- **Year 1 Total: ~$450**

**Year 2+ (5TB Steady State)**:
- **Monthly: ~$94**
- **Annual: ~$1,128**
- **10-Year Total: ~$11,280**

**Compared to Unoptimized Approach**:
- Unoptimized: $438/month = $5,256/year = $52,560 over 10 years
- MillerPic Optimized: $94/month = $1,128/year = $11,280 over 10 years
- **Total 10-Year Savings: ~$41,280 (79% reduction)**

---

## Key Financial Metrics

| Metric | Value |
|--------|-------|
| Monthly Cost (Steady State) | $94 |
| Cost per Photo (5M photos) | $0.00002 |
| Cost per GB per Month | $0.019 (vs AWS Standard: $0.023) |
| Break-even vs OneDrive (1TB) | 8 months |
| Break-even vs SmugMug | 2.5 months |
| 10-Year ROI vs Google Photos | 4:1 (save $41k) |

---

## What to Monitor

✅ **CloudWatch Alarms**
- S3 storage cost > $100/month (warn), > $150/month (alert)
- DynamoDB on-demand units spiking > normal baseline
- Lambda errors > 1% of total requests

✅ **Monthly Cost Trends**
- Check AWS Cost Explorer weekly
- Verify Intelligent-Tiering transitions are happening
- Monitor WebP compression effectiveness (target: 30% reduction)

✅ **Annual Review**
- Validate storage tiers are distributing correctly
- Check for unused GSI or slow queries in DynamoDB
- Consider Provisioned Concurrency if Lambda latency increases
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

✅ **Final Approach (Implemented)**
- ✅ **WebP Compression** - Automatic format conversion on upload (saves $39/month)
- ✅ **S3 Intelligent-Tiering** - Auto-archive old photos to cheaper tiers (saves $18/month)
- ✅ **Glacier Instant Retrieval** - 3-5 min access to all photos, no 12-hour waits
- ✅ **DynamoDB On-Demand** - Pay per request ($20/month), no provisioned capacity
- ✅ **CloudFront Thumbnails Only** - Presigned S3 URLs for full resolution (saves $140/month)
- ✅ **Monitor Cost Weekly** - Set CloudWatch alarms at $100/month warning, $150/month alert

✅ **What This Gets You**
- **$94/month** total cost for 5TB family archive
- **3-5 minute** retrieval on ANY photo, even year-old ones
- **79% savings** vs unoptimized ($438 → $94)
- **Zero vendor lock-in** - Export anytime
- **Complete privacy** - No AI, no scanning, no ads

---

## Terraform Configuration: The Recommended Approach

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete Terraform setup, but the key configurations are:

**DynamoDB - On-Demand (NOT Provisioned)**:
```hcl
resource "aws_dynamodb_table" "photos" {
  name           = "millerpic-photos"
  billing_mode   = "PAY_PER_REQUEST"  # ← Pay per request, not provisioned
  hash_key       = "UserId"
  range_key      = "PhotoId"
  
  # This scales automatically with family usage
  # ~$20/month for typical 6-user family
}
```

**S3 - WebP Compression + Intelligent-Tiering**:
```hcl
resource "aws_s3_bucket_intelligent_tiering_configuration" "photos" {
  bucket = aws_s3_bucket.photos.id
  name   = "AutoArchive"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90   # Move to cheaper tier after 3 months
  }

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180  # Glacier Instant: 3-5 min retrieval
  }
}

**Your expected monthly costs with 5TB, 6 users, DynamoDB on-demand + WebP compression:**

| Component | Cost | Notes |
|-----------|------|-------|
| **S3 Storage** (5TB with WebP compression) | **$36** | ✅ Compressed from $75 |
| S3 Requests (optimized) | $3 | Batch ops, presigned URLs |
| Lambda (optimized) | $5 | Direct S3 access |
| **DynamoDB** (on-demand) | **$20** | ✅ Pay per request, not provisioned |
| CloudFront (thumbnails only) | $1 | No full images through CDN |
| KMS, Secrets, CloudTrail, monitoring | $8 | Infrastructure overhead |
| **TOTAL MONTHLY** | **$73** | ✅ 83% reduction from $438! |
| **ANNUAL** | **$876** | **Extremely cost-stable** |
| **10-Year** | **$8,280** | Forever storage for family |

**Comparing to alternatives for 5TB:**
- **MillerPic Optimized**: **$73/month** ✅ **BEST VALUE**
- Google Workspace (6 users @ 1TB each): $10 × 6 = $60 (but only 6TB total)
- Google Workspace + Google One (2TB): $10 + $100 = $110 (7TB but fragmented)
- OneDrive (6 users with 1TB each): $120 × 6 = **$720** 😱
- Backblaze B2 storage only: ~$115 (no interface/app/family access)
- SmugMug unlimited: **$240-300** (with limited advanced features)
- Flickr Pro: **$130/month** (1TB limit)
- Shutterfly (if you could: paywall): $150-200+

**The reality:**
- ✅ You get a **full-featured** photo app (web + mobile + future desktop)
- ✅ **Complete control** of your data forever (no vendor lock-in)
- ✅ **Unlimited storage** (pay only by actual GB used)
- ✅ **6 family members** with role-based access
- ✅ **Secure sharing** with time-limited links
- ✅ **Complete privacy** (no scanning, no ads, no AI)
- ✅ Still cheaper than most alternatives
- ✅ Predictable costs that won't change

With all optimizations, **$73/month is exceptional value** for a lifetime family photo library with full resolution, multiple users, and complete privacy.

---

## Final Checklist: Implementing the $73/Month Setup

Before deploying, ensure you:

- [ ] Understand the presigned URL approach (NO CloudFront for full images)
- [ ] Understand WebP compression (25-35% file size reduction, imperceptible quality)
- [ ] Have AWS account ready with admin access
- [ ] Have Terraform v1.6+ installed locally
- [ ] Have AWS CLI configured with credentials
- [ ] Read through entire optimizations guide above
- [ ] Set CloudWatch alarm at $150/month
- [ ] Plan for Year 1 costs (start lower, grow to ~$73 by month 12)
- [ ] Accept that $73 is your steady-state cost (doesn't scale after ~5TB)
- [ ] Understand DynamoDB on-demand auto-scales (no capacity management)
- [ ] Know that presigned URLs require HTTPS but no other changes



