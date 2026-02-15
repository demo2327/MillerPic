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

### S3 Storage Reduction Options

**Option A: Image Compression (JPEG → WebP)** 🖼️ (-$25-35/month)

**Problem**: JPEGs are large. Moving to WebP saves 25-35% file size with same visual quality.

**Impact**:
- 5TB JPEGs → 3.3TB WebP
- Savings: 1.7TB × $0.023 (average cost) = **$39/month**
- New total: $75 - $39 = **$36/month**

**Implementation**:
```javascript
// On upload: Convert JPEG to WebP before storing
const sharp = require('sharp');

exports.uploadHandler = async (event) => {
  const fileBuffer = event.body;
  
  // Convert to WebP (25-35% smaller)
  const webpBuffer = await sharp(fileBuffer)
    .webp({ quality: 85 }) // Maintain quality
    .toBuffer();
  
  // Store WebP instead of original JPEG
  await s3.putObject({
    Bucket: process.env.BUCKET,
    Key: `originals/${userId}/${photoId}.webp`,
    Body: webpBuffer,
    ContentType: 'image/webp'
  }).promise();
};
```

**Tradeoffs:**
- ✅ Saves $39/month consistently
- ✅ Modern browsers (95%+ support WebP)
- ✅ Automatic compression (no user action needed)
- ❌ Slightly slower upload (requires conversion)
- ❌ Original JPEG quality lost (but imperceptible at 85% quality)
- ❌ Some older devices can't view (fallback to thumbnails)

**Best for:** Maximum savings with minimal UX impact

---

**Option B: Aggressive Archival Policy** 📦 (-$50-60/month)

**Problem**: You're keeping old photos in expensive tiers. They could be archived.

**Strategy**: Only keep last 12 months in standard S3, archive everything older.

**Cost Model**:
- Last 12 months (500GB): $0.023/GB = $11.50/month
- 2-5 years old (2TB): $0.0125/GB = $25/month (infrequent)
- 5+ years old (2.5TB): $0.00099/GB = $2.50/month (deep archive)
- **Total: $39/month** (vs $75 = **$36/month savings**)

**Terraform Configuration**:
```hcl
resource "aws_s3_bucket_lifecycle_configuration" "aggressive_archive" {
  bucket = aws_s3_bucket.photos.id

  rule {
    id     = "archive_old_photos"
    status = "Enabled"

    # Move to Infrequent Access after 1 month
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Move to Deep Archive after 90 days (3 months)
    transition {
      days          = 90
      storage_class = "DEEP_ARCHIVE"
    }

    # Expiration (optional - delete after 7 years)
    # expiration {
    #   days = 2555  # 7 years
    # }
  }
}
```

**Retrieval Process for Old Photos**:
```javascript
// When user tries to download an archived photo
exports.downloadHandler = async (event) => {
  const { photoId } = event.pathParameters;
  
  // Check if object is archived
  const headObject = await s3.headObject({
    Bucket: process.env.BUCKET,
    Key: `originals/${userId}/${photoId}.webp`
  }).promise();
  
  if (headObject.StorageClass === 'DEEP_ARCHIVE') {
    // Restore from archive (1-5 hour wait)
    await s3.restoreObject({
      Bucket: process.env.BUCKET,
      Key: `originals/${userId}/${photoId}.webp`,
      RestoreRequest: {
        Days: 7,
        GlacierJobParameters: {
          Tier: 'Bulk'  // Cheapest retrieval option
        }
      }
    }).promise();
    
    return {
      statusCode: 202,
      body: JSON.stringify({
        status: 'restoring',
        message: 'Photo is being restored. Check back in 1-5 hours.',
        waitTime: '1-5 hours'
      })
    };
  }
  
  // For non-archived photos, return presigned URL immediately
  const presignedUrl = await s3.getSignedUrlPromise('getObject', { ... });
  return {
    statusCode: 200,
    body: JSON.stringify({ downloadUrl: presignedUrl })
  };
};
```

**Tradeoffs:**
- ✅ Saves $36/month automatically
- ✅ Truly old photos rarely accessed anyway
- ✅ Photo is preserved (not deleted)
- ❌ Old photo retrieval takes 1-5 hours
- ❌ Users need to plan ahead for old photo access
- ❌ Retrieval has small additional cost (~$0.03 per GB retrieved)

**Best for:** Family that values cost over instant access to old photos

---

**Option C: Hybrid - Compression + Moderate Archival** 🎯 (-$45-55/month)

**Combine both strategies for best balance:**

1. **Upload compression** (JPEG → WebP): Saves 1.7TB → $39/month
2. **Moderate archival**: Move to STANDARD_IA after 6 months, not immediately
3. **Keep Deep Archive threshold high**: 2+ years old only

**Cost Model**:
- Recent (0-6 months, 1.5TB): $0.023/GB = $34.50/month
- Medium (6-24 months, 2TB): $0.0125/GB = $25/month
- Old (2+ years, 1.5TB after compression): $0.004/GB = $6/month
- **Total: $65.50/month** (vs $75 = **$9.50/month savings**)

**Or with more aggressive archival**:
- Recent (0-3 months, 500GB): $11.50/month
- Medium (3-12 months, 2TB): $25/month
- Old (1+ years, 2TB): $8/month
- **Total: $44.50/month** (vs $75 = **$30/month savings**)

---

**Option D: Don't Store Full Resolution** ❌ (-$75/month but NOT RECOMMENDED)

**Idea**: Only store optimized web versions (600px, WebP, ~150KB each)

**Cost**: 5M photos × 150KB = 750GB × $0.023 = $17/month

**Why this is BAD:**
- ❌ Original photos are GONE (family's life photos lost!)
- ❌ Can't reprint large format
- ❌ Defeats the purpose of MillerPic
- ❌ Not future-proof

**This violates your requirements - SKIP THIS**

---

### Comparison: S3 Storage Reduction Options

| Option | Monthly Cost | Setup Complexity | Download Speed | Best For |
|--------|-------------|-----------------|-----------------|----------|
| **Baseline (no optimization)** | $75 | None | Instant | If money is no object |
| **A: WebP Compression** | $36 | Medium | Instant | Best balance |
| **B: Aggressive Archival** | $39 | Simple | 1-5 hours for old | If willing to wait |
| **C: Hybrid (Compression + Archival)** | $44-65 | Medium | Mostly instant | Flexible approach |
| **D: No full resolution** | $17 | None | Fast ❌ BAD IDEA | Don't do this! |

---

### My Recommendation

**Use Option A: WebP Compression** ✅

**Why:**
- Saves $39/month ($468/year!)
- No speed penalty (instant downloads)
- Imperceptible quality loss (85% quality = looks identical)
- Transparent to family (automatic on upload)
- Fully preserves originals in efficient format
- New total: **$36/month for S3** (instead of $75)

**Updated Annual Cost with All Optimizations:**

| Component | Cost |
|-----------|------|
| S3 Storage (5TB, WebP compressed) | $36 |
| S3 Requests | $3 |
| Lambda | $5 |
| DynamoDB on-demand | $20 |
| CloudFront (thumbnails) | $1 |
| Other | $8 |
| **MONTHLY** | **$73** |
| **ANNUAL** | **$876** 🎉 |

**vs Original: $438 × 12 = $5,256/year**  
**Total Savings: $4,380/year (83% reduction!)**

---

### Implementation: WebP Compression

**Backend Lambda (Node.js)**:
```javascript
const AWS = require('aws-sdk');
const sharp = require('sharp');
const s3 = new AWS.S3();

exports.uploadPhoto = async (event) => {
  const { userId } = event.requestContext.authorizer;
  const photoId = generatePhotoId();
  
  // Get uploaded JPEG from multipart
  const fileStream = event.body;
  
  // Convert to WebP at 85% quality
  const compressedBuffer = await sharp(fileStream)
    .withMetadata()  // Preserve EXIF
    .webp({ quality: 85 })  // Modern codec, 25-35% smaller
    .toBuffer();
  
  console.log(`Original: ${fileStream.length} bytes, Compressed: ${compressedBuffer.length} bytes`);
  console.log(`Compression ratio: ${(100 - (compressedBuffer.length / fileStream.length) * 100).toFixed(1)}%`);
  
  // Store in S3 as WebP
  await s3.putObject({
    Bucket: process.env.PHOTOS_BUCKET,
    Key: `originals/${userId}/${photoId}.webp`,
    Body: compressedBuffer,
    ContentType: 'image/webp',
    Metadata: {
      'original-name': `${photoId}.webp`,
      'uploaded-by': userId,
      'timestamp': new Date().toISOString()
    }
  }).promise();
  
  // Store metadata in DynamoDB
  await dynamodb.putItem({
    TableName: 'Photos',
    Item: {
      UserId: { S: userId },
      PhotoId: { S: photoId },
      UploadedAt: { N: Date.now().toString() },
      S3Key: { S: `originals/${userId}/${photoId}.webp` },
      FileSize: { N: compressedBuffer.length.toString() },
      // ... other metadata
    }
  }).promise();
  
  return {
    statusCode: 200,
    body: JSON.stringify({
      status: 'success',
      data: { photoId, compressed: true }
    })
  };
};
```

**Browser Support:**
- Chrome: ✅ 100% support
- Firefox: ✅ 100% support
- Safari: ✅ 95% support
- Mobile: ✅ 98% support

**Fallback for old browsers:**
```javascript
// Frontend: Check browser support
if (!document.createElement('canvas').toDataURL('image/webp').indexOf('image/webp') === 0) {
  // WebP not supported, show thumbnail instead
  showThumbnail();
} else {
  // Show WebP
  showWebP();
}
```

---

## Updated Final Cost

With all optimizations (DynamoDB on-demand + WebP compression):

| Year | Monthly | Annual | Notes |
|------|---------|--------|-------|
| **Year 1** | $50-80 | $600-900 | Growing collection, AWS free tier helps |
| **Year 2+** | $73 | $876 | Steady state at 5TB |
| **10-Year** | - | **$8,280** | Extremely cost-stable |

**Compared to:**
- Google Workspace (6 users): $7,200 for 6TB
- SmugMug: $36,000+
- OneDrive (6 users): $86,400!!!
- Staying with Shutterfly: ~$24,000 (but terrible interface)

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

#### 2. **DynamoDB: On-Demand Instead of Provisioned** (-$45/month)

**Standard Approach** (Old config with DAX):
- Provisioned capacity: 200 RCU/100 WCU = $50/month
- DAX caching: $15/month
- Total: $65/month

**Optimized Approach**:
- On-demand pricing (pay per request): ~$20/month
- No DAX needed (on-demand scales automatically)
- Total: $20/month

**Implementation:**
```hcl
resource "aws_dynamodb_table" "photos" {
  name         = "millerpic-photos"
  billing_mode = "PAY_PER_REQUEST"  # ← On-demand!
  hash_key     = "UserId"
  range_key    = "PhotoId"
}
```

Cost: -$45/month savings

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

---

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
PESSIMISTIC (Not optimized: all CDN, on-demand DB, no compression):
Year 1 (Growing Collection):
  Month 1-3:    $25-40 (AWS free tier kicks in)
  Month 4-6:    $80-120 (200GB)
  Month 7-12:   $200-300 (500GB-1TB)
Year 1 Total:   ~$1,500

Year 2+ (5TB Steady State):
  Monthly:      $430-450
  Annual:       ~$5,200
  10-Year:      ~$52,000

OPTIMIZED (Best practices: presigned URLs, on-demand DB, WebP compression):
Year 1 (Growing Collection):
  Month 1-3:    $10-20 (AWS free tier)
  Month 4-6:    $20-30 (200GB compressed)
  Month 7-12:   $50-70 (500GB-1TB compressed)
Year 1 Total:   ~$400

Year 2+ (5TB Steady State):
  Monthly:      $73
  Annual:       ~$876
  10-Year:      ~$8,280

SAVINGS: $43,720 over 10 years ($364/month average savings)
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

# Set variables for $73/month configuration
export TF_VAR_environment="prod"
export TF_VAR_enable_dax=false                    # ✅ NO DAX
export TF_VAR_cloudfront_for_originals=false      # ✅ Only thumbnails
export TF_VAR_dynamodb_billing_mode="PAY_PER_REQUEST"  # ✅ On-demand
export TF_VAR_compression_format="webp"           # ✅ WebP compression
export TF_VAR_compression_quality=85              # ✅ 85% quality

# Plan & apply
terraform init
terraform plan -out=tfplan
terraform apply tfplan

echo "Deployment complete!"
echo "Cost should be ~$73/month"
```

**To enable specific features:**
```bash
# Use aggressive archival (Old photos → Deep Archive sooner)
export TF_VAR_archive_days=90  # Default: 180 days

# Use Intelligent-Tiering (automatic cost optimization)
export TF_VAR_use_intelligent_tiering=true

# Disable WebP compression (store original JPEGs - not recommended)
export TF_VAR_compression_format="none"  # Cost will be higher (~$112/month)

---

## Realistic Cost for Your Family

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



