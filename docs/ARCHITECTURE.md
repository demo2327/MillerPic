# MillerPic Architecture

## System Overview

MillerPic is a serverless, family photo storage and sharing platform built on AWS, with Google Suite authentication, client certificate support for enhanced security, and multi-client access (web, mobile, desktop).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FAMILY USERS                                 │
│    (Web Browser | Android Phone | Windows Desktop)                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  CloudFront CDN │
                    │  (Caching)      │
                    └────────┬────────┘
                             │
            ┌────────────────▼────────────────┐
            │    API Gateway + WAF            │
            │  (Rate limiting, DDoS)          │
            └────────────────┬────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐         ┌────▼────┐        ┌───────▼──────┐
   │ Lambda  │         │ Lambda  │        │ Lambda       │
   │ Auth    │         │ Gallery │        │ Upload       │
   │Handler  │         │ Handler │        │ Handler      │
   └────┬────┘         └────┬────┘        └───────┬──────┘
        │                   │                     │
        └───────────────────┼─────────────────────┘
                            │
                  ┌─────────▼──────────┐
                  │   DynamoDB         │
                  │  (Metadata DB)     │
                  │  - Photos table    │
                  │  - Users table     │
                  │  - Albums table    │
                  │  - Share links     │
                  └────────────────────┘
                            
        ┌───────────────────────────────────────┐
        │   AWS Secrets Manager                 │
        │  - OAuth credentials                  │
        │  - API keys                           │
        └───────────────────────────────────────┘
                            │
                  ┌─────────▼──────────┐
                  │  Google OAuth 2.0  │
                  │  + Client Certs    │
                  └────────────────────┘

        ┌───────────────────────────────────────┐
        │          S3 Photo Storage             │
        │  - Original files (full resolution)   │
        │  - Encrypted at rest (AES-256)        │
        │  - Versioning enabled                 │
        │  - Lifecycle policies                 │
        └───────────────────────────────────────┘

        ┌───────────────────────────────────────┐
        │      CloudWatch Monitoring            │
        │  - Logs, metrics, alarms              │
        └───────────────────────────────────────┘
```

## Key Components

### 1. **Frontend Applications**

#### Web Application (React + TypeScript)
- Gallery view with lazy loading
- Album management
- Share link generation
- Google OAuth login
- Client certificate management
- Responsive design (desktop/tablet)

#### Android Application (React Native)
- Photo gallery with infinite scroll
- Bulk upload capability
- Offline sync (when online)
- Native Android components where needed
- Client certificate support
- Push notifications for shares

#### Desktop Client (Future - Windows/Mac)
- Bulk upload/download tools
- Local sync folders
- Automatic backup
- Client certificate provisioning
- System tray integration

### 2. **Backend (AWS Lambda + API Gateway)**

**API Endpoints:**
- `POST /auth/login` - Google OAuth initiation
- `POST /auth/callback` - OAuth callback handler
- `GET /photos` - List photos with pagination
- `GET /photos/{id}` - Get photo metadata
- `POST /photos/upload` - Initiate multipart upload
- `GET /photos/{id}/download` - Download photo
- `POST /albums` - Create album
- `GET /albums` - List albums
- `POST /albums/{id}/photos` - Add photos to album
- `POST /share/generate-link` - Generate shareable link
- `GET /share/{link-id}` - Access shared photos
- `POST/users/profile` - User profile management

**Lambda Functions (Node.js):**
- Auth handler: OAuth flow, token validation, client cert verification
- Gallery handler: Photo listing, search, filtering
- Upload handler: S3 presigned URLs, multipart upload
- Share handler: Link generation, access control
- Admin handler: User management, settings

### 3. **Storage (S3 + DynamoDB)**

**S3 Structure:**
```
s3://millerpic-photos/
├── originals/{userId}/{photoId}/original.jpg
├── thumbnails/{userId}/{photoId}/thumb-{size}.jpg
└── metadata/{userId}/{photoId}/metadata.json
```

**DynamoDB Tables:**
- `Photos`: photoId, userId, timestamp, exif, s3Key, etc.
- `Users`: userId, googleId, email, roles, settings, clientCerts
- `Albums`: albumId, userId, name, photos, createdAt
- `SharedLinks`: linkId, albumId, photoIds, expiresAt, accessCount
- `SyncState`: userId, lastSync, changes (for mobile sync)

### 4. **Authentication & Security**

- **Primary**: Google OAuth 2.0 (Google Workspace family account)
- **Secondary**: mTLS with client certificates
- **Token**: JWT with 1-hour expiry, refresh tokens stored in DynamoDB
- **Certificate Chain**: Self-signed CA, issued per device
- **TLS 1.3**: All API communication
- **WAF**: CloudFront + API Gateway WAF rules
- **Rate Limiting**: 100 req/min per user, 1000 req/min per IP

### 5. **Infrastructure (Terraform)**

Managed via Terraform from `infrastructure/` directory:
- VPC (if needed for Lambda functions)
- IAM roles and policies
- S3 buckets with versioning, encryption, lifecycle
- DynamoDB tables with point-in-time recovery
- Lambda layers and functions
- API Gateway
- CloudFront distribution
- CloudWatch log groups
- SNS/SQS for async processing
- Secrets Manager for credentials

### 6. **CI/CD (GitHub Actions)**

- Test on each commit
- Build Docker images (where applicable)
- Deploy to staging on PR
- Security scanning (dependencies, SAST)
- Manual approval for production
- Automated rollback capability

---

## Data Flow

### Upload Flow
1. User selects photo in app
2. Frontend calls `POST /photos/upload` with metadata
3. Lambda generates presigned S3 URL
4. Frontend uploads directly to S3
5. S3 event triggers Lambda for thumbnail generation
6. Metadata stored in DynamoDB
7. Frontend polls for completion or uses WebSocket notification

### View Flow
1. User requests photo gallery
2. Lambda queries DynamoDB for photo metadata
3. Frontend displays thumbnails from CloudFront cache
4. On click, frontend shows full-res from S3 via CloudFront
5. EXIF data displayed from DynamoDB

### Share Flow
1. User selects photos/album to share
2. Lambda generates unique link with temporary token
3. Token stored in DynamoDB with expiry time
4. User shares link via text/email
5. Recipient accesses without login (or guests require link password)
6. Lambda validates token and returns shared photos

---

## Scalability & Performance

- **Lambda Concurrency**: Auto-scales to 1000 concurrent executions
- **DynamoDB**: On-demand billing (scales automatically)
- **S3**: Unlimited objects, partitioning by userId for key distribution
- **CloudFront**: 600+ edge locations globally
- **Caching Strategy**:
  - Thumbnails: 1 month cache
  - Metadata: 5 minute cache
  - Full images: 1 week cache (user-controlled)

---

## Cost Optimization

- **Lambda**: ~$0.20 per 1M requests
- **S3 Storage**: $0.023 per GB/month
- **DynamoDB On-Demand**: Auto-scales, ~$1.25 per 1M read units
- **CloudFront**: $0.085-0.170 per GB (varies by region)
- **Estimated**: ~$20-50/month for typical family
- **Free tier eligible**: First 400,000 GB-seconds Lambda, 25GB storage

---

## Security Layers

1. **Network**: CloudFront + WAF, TLS 1.3, DDoS protection
2. **Authentication**: OAuth 2.0 + mTLS certificates
3. **Authorization**: Role-based access control (owner, viewer, curator)
4. **Storage**: AES-256 encryption, versioning
5. **Transport**: All data encrypted in transit
6. **Monitoring**: CloudWatch Logs, X-Ray tracing
7. **Secrets**: AWS Secrets Manager for credentials
8. **Audit**: CloudTrail for all API calls

