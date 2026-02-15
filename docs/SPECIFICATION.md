# MillerPic Technical Specification

## 1. Project Information

**Project Name**: MillerPic  
**Description**: Serverless family photo storage and sharing platform  
**AWS Region**: us-east-1 (primary)  
**Architecture Type**: Serverless + CDN  
**IaC**: Terraform  
**CI/CD**: GitHub Actions  

## 2. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend (Web)** | React + TypeScript | 18.x |
| **Frontend (Mobile)** | React Native | 0.72.x |
| **Backend Runtime** | Node.js | 20.x (Lambda) |
| **API Gateway** | AWS API Gateway | v2 (HTTP) |
| **Database** | DynamoDB | On-Demand |
| **Storage** | S3 | Standard + Intelligent Tiering |
| **Auth** | Google OAuth 2.0 + mTLS | OIDC 1.0 |
| **CDN** | CloudFront | Latest |
| **IaC** | Terraform | 1.6+ |
| **Package Manager** | npm | 10.x |
| **Build Tool (Web)** | Vite | 5.x |
| **Build Tool (Mobile)** | Expo CLI | 50.x |

## 3. Application Structure

```
MillerPic/
├── backend/                    # Node.js Lambda functions
│   ├── src/
│   │   ├── handlers/          # Lambda entry points
│   │   ├── services/          # Business logic
│   │   ├── middleware/        # Auth, validation
│   │   ├── utils/             # Helpers
│   │   └── types/             # TypeScript types
│   ├── tests/
│   ├── package.json
│   └── tsconfig.json
├── web-client/                 # React web application
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Route pages
│   │   ├── services/          # API calls
│   │   ├── hooks/             # Custom hooks
│   │   ├── context/           # React context
│   │   └── types/             # TypeScript types
│   ├── tests/
│   ├── package.json
│   └── vite.config.ts
├── mobile-client/              # React Native Android app
│   ├── src/
│   │   ├── screens/           # Screens
│   │   ├── components/        # Components
│   │   ├── services/          # API/storage
│   │   └── types/             # TypeScript types
│   ├── app.json
│   └── package.json
├── infrastructure/             # Terraform IaC
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── vpc.tf
│   ├── s3.tf
│   ├── dynamodb.tf
│   ├── lambda.tf
│   ├── api-gateway.tf
│   ├── cloudfront.tf
│   ├── iam.tf
│   ├── secrets.tf
│   └── terraform.tfvars.example
├── .github/
│   └── workflows/
│       ├── deploy-backend.yaml
│       ├── deploy-frontend.yaml
│       ├── deploy-mobile.yaml
│       └── security-scan.yaml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API_DESIGN.md
│   ├── SECURITY.md
│   ├── DEPLOYMENT.md
│   └── COST_ESTIMATE.md
└── README.md
```

## 4. API Specification

### Base URL
```
https://api.millerpic.family/v1
```

### Authentication Headers
```
Authorization: Bearer {jwt_token}
X-Client-Cert: {base64_encoded_cert}
X-Request-ID: {uuid}
Content-Type: application/json
```

### Core Endpoints

#### Authentication
- `POST /auth/google/start` - Initiate Google OAuth
- `POST /auth/google/callback` - Handle OAuth callback
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - Invalidate session
- `POST /auth/cert/register` - Register client certificate

#### Photos
- `GET /photos` - List photos (paginated, filterable)
- `GET /photos/{photoId}` - Get photo metadata
- `POST /photos/upload-init` - Initiate upload
- `POST /photos/upload-complete` - Finalize upload
- `GET /photos/{photoId}/download` - Get download URL
- `DELETE /photos/{photoId}` - Delete photo
- `PATCH /photos/{photoId}` - Update metadata
- `GET /photos/search` - Search photos by date/tag

#### Albums
- `GET /albums` - List user albums
- `POST /albums` - Create album
- `GET /albums/{albumId}` - Get album details
- `PUT /albums/{albumId}` - Update album
- `DELETE /albums/{albumId}` - Delete album
- `POST /albums/{albumId}/photos` - Add photos to album
- `DELETE /albums/{albumId}/photos/{photoId}` - Remove from album

#### Sharing
- `POST /share/links` - Generate shareable link
- `GET /share/links` - List shared links
- `GET /share/{linkId}` - Access shared content
- `DELETE /share/{linkId}` - Revoke link

#### Users
- `GET /users/profile` - Get current user profile
- `PUT /users/profile` - Update profile
- `GET /users/settings` - Get user settings
- `PUT /users/settings` - Update settings

### Response Format

**Success (200)**
```json
{
  "status": "success",
  "data": { ... },
  "requestId": "uuid"
}
```

**Error (4xx/5xx)**
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { ... }
  },
  "requestId": "uuid"
}
```

## 5. Database Schema

### DynamoDB Tables

#### Photos
```
PK: UserId (String)
SK: PhotoId (String)
Attributes:
  - UploadedAt (Number - epoch)
  - FileName (String)
  - MimeType (String)
  - FileSize (Number)
  - S3Key (String)
  - ThumbnailS3Key (String)
  - EXIF (Map - optional)
  - Tags (StringSet)
  - AlbumIds (StringSet)
  - Shared (Boolean)
  - CreatedAt (Number)
  - UpdatedAt (Number)
```

#### Users
```
PK: UserId (String)
Attributes:
  - GoogleId (String - unique)
  - Email (String)
  - Name (String)
  - ProfilePicture (String)
  - Role (String: owner, viewer, curator)
  - StorageQuotaGB (Number)
  - StorageUsedGB (Number)
  - LastLoginAt (Number)
  - ClientCertificates (List)
  - Settings (Map)
  - CreatedAt (Number)
```

#### Albums
```
PK: UserId (String)
SK: AlbumId (String)
Attributes:
  - AlbumName (String)
  - Description (String)
  - CoverPhotoId (String)
  - PhotoCount (Number)
  - CreatedAt (Number)
  - UpdatedAt (Number)
  - Shared (Boolean)
```

#### SharedLinks
```
PK: LinkId (String)
Attributes:
  - UserId (String)
  - AlbumIds (StringSet)
  - PhotoIds (StringSet)
  - ExpiresAt (Number - TTL)
  - Password (String - optional hash)
  - AccessCount (Number)
  - CreatedAt (Number)
```

## 6. Environment Configuration

### Backend (.env)
```
NODE_ENV=development|production
AWS_REGION=us-east-1
STAGE=dev|staging|prod

# Google OAuth
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=https://api.millerpic.family/auth/google/callback

# JWT
JWT_SECRET=xxx
JWT_EXPIRY=3600

# AWS
S3_BUCKET=millerpic-photos-{stage}
DYNAMODB_REGION=us-east-1

# Feature Flags
FEATURE_CLIENT_CERT=true
FEATURE_ADVANCED_SHARING=false
```

### Web Frontend (.env)
```
VITE_API_URL=https://api.millerpic.family/v1
VITE_GOOGLE_CLIENT_ID=xxx
VITE_STAGE=dev|prod
VITE_ENABLE_CERT_AUTH=true
```

## 7. Security Requirements

- **TLS**: 1.3 minimum
- **HSTS**: Enabled with 1-year max-age
- **CORS**: Whitelist specific domains only
- **CSP**: Strict content security policy
- **Rate Limiting**: 100 req/min per user
- **JWT Expiry**: 1 hour
- **Refresh Token**: 30 days
- **Password Policy**: N/A (OAuth-based)
- **Audit Logging**: All API calls logged to CloudWatch

## 8. Scalability Targets

| Metric | Target | Baseline |
|--------|--------|----------|
| Concurrent Users | 10,000 | 100 |
| Photos per User | 100,000 | 10,000 |
| Total Photos | 1,000,000 | 100,000 |
| Storage | 50TB | 1TB |
| API Requests/sec | 1,000 | 100 |
| P99 Latency | 500ms | 100ms |

## 9. Monitoring & Logging

**CloudWatch Metrics**
- Lambda invocations, duration, errors
- DynamoDB read/write capacity
- S3 PUT/GET requests
- API Gateway error rates
- CloudFront cache hit ratio

**X-Ray Tracing**
- Full request tracing
- Service map visualization
- Performance bottleneck identification

**Alarms**
- Lambda error rate > 1%
- API Gateway 5xx > 10/min
- DynamoDB throttling
- Unauthorized login attempts

## 10. Development Workflow

1. **Local Development**: Docker Compose for LocalStack
2. **Feature Branch**: Create branch from `main`
3. **Testing**: Unit + integration tests
4. **PR Review**: Peer review + CI tests pass
5. **Staging Deploy**: Automated on merge to staging branch
6. **Production Deploy**: Manual approval + automated deployment
7. **Monitoring**: Post-deploy verification

## 11. Success Criteria

- ✅ Sub-100ms photo gallery load
- ✅ Sub-500ms full-resolution download
- ✅ 99.9% uptime SLA
- ✅ Zero authentication bypasses
- ✅ <$50/month cost for 1TB storage
- ✅ Family can access photos from any device
- ✅ Secure sharing via links
- ✅ No vendor lock-in for data

