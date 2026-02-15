# MillerPic API Design & Specification

## API Overview

**Base URL**: `https://api.millerpic.family/v1`  
**Protocol**: HTTPS (TLS 1.3)  
**Format**: JSON  
**Version**: 1.0  

## Authentication

### Google OAuth 2.0 Flow

```
1. Frontend requests /auth/google/start
2. User redirected to Google consent screen
3. Google redirects to /auth/google/callback with code
4. Backend exchanges code for ID token
5. Backend validates token and creates JWT
6. Frontend stores JWT in localStorage
```

### Client Certificate Authentication (mTLS)

```
1. Client generates CSR
2. Backend issues certificate via POST /auth/cert/register
3. Client pins certificate for future requests
4. Every request includes X-Client-Cert header
5. Backend validates certificate chain
```

### Headers

```
Authorization: Bearer {jwt_token}
X-Client-Cert: {base64_encoded_certificate}
X-Request-ID: {uuid}
Content-Type: application/json
```

## Error Responses

### Standard Error Format

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {
      "field": "description"
    }
  },
  "requestId": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `UNAUTHORIZED` | 401 | Token invalid/expired |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `INVALID_PARAMETERS` | 400 | Invalid request parameters |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `CERT_INVALID` | 401 | Client certificate invalid |

---

## Authentication Endpoints

### POST /auth/google/start

Initiate Google OAuth login.

**Request**
```json
{
  "redirectUri": "https://millerpic.family/auth/callback"
}
```

**Response (302 Redirect)**
```
Location: https://accounts.google.com/o/oauth2/v2/auth?...
```

### POST /auth/google/callback

Handle OAuth callback.

**Query Parameters**
- `code` - Authorization code from Google
- `state` - CSRF protection token

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "refresh_token_xyz",
    "expiresIn": 3600,
    "user": {
      "userId": "user_123",
      "email": "family@gmail.com",
      "name": "Family Miller",
      "picture": "https://..."
    }
  }
}
```

### POST /auth/refresh

Refresh expired JWT token.

**Request**
```json
{
  "refreshToken": "refresh_token_xyz"
}
```

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 3600
  }
}
```

### POST /auth/logout

Invalidate current session.

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "message": "Logged out successfully"
  }
}
```

### POST /auth/cert/register

Register a new client certificate.

**Request**
```json
{
  "deviceName": "iPhone 15 Pro",
  "deviceType": "mobile",
  "publicKey": "-----BEGIN PUBLIC KEY-----\n..."
}
```

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "certificate": "-----BEGIN CERTIFICATE-----\n...",
    "certificateId": "cert_xyz123",
    "expiresAt": 1735689600,
    "fingerprint": "SHA256:..."
  }
}
```

---

## Photo Endpoints

### GET /photos

List user's photos with pagination and filters.

**Query Parameters**
- `limit` - Items per page (default: 20, max: 100)
- `offset` - Pagination offset (default: 0)
- `sortBy` - `uploadedAt` | `fileName` | `fileSize` (default: uploadedAt)
- `sortOrder` - `asc` | `desc` (default: desc)
- `startDate` - ISO 8601 timestamp
- `endDate` - ISO 8601 timestamp
- `tags` - Comma-separated tag names
- `albumId` - Filter by album

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "photos": [
      {
        "photoId": "photo_123",
        "fileName": "vacation-2024-01.jpg",
        "mimeType": "image/jpeg",
        "fileSize": 2097152,
        "uploadedAt": 1705276800,
        "thumbnailUrl": "https://cdn.millerpic.family/thumb/photo_123.jpg",
        "previewUrl": "https://cdn.millerpic.family/preview/photo_123.jpg",
        "tags": ["beach", "family"],
        "exif": {
          "camera": "iPhone 15 Pro",
          "iso": 100,
          "aperture": 1.8,
          "shutterSpeed": "1/120"
        },
        "width": 4032,
        "height": 3024,
        "geoLocation": {
          "latitude": 25.7617,
          "longitude": -80.1918
        }
      }
    ],
    "pagination": {
      "total": 15420,
      "limit": 20,
      "offset": 0,
      "hasMore": true
    }
  }
}
```

### GET /photos/{photoId}

Get specific photo metadata.

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "photoId": "photo_123",
    "fileName": "vacation-2024-01.jpg",
    "mimeType": "image/jpeg",
    "fileSize": 2097152,
    "uploadedAt": 1705276800,
    "thumbnailUrl": "https://cdn.millerpic.family/thumb/photo_123.jpg",
    "previewUrl": "https://cdn.millerpic.family/preview/photo_123.jpg",
    "downloadUrl": "https://s3.amazonaws.com/...",
    "tags": ["beach", "family"],
    "exif": { /* ... */ },
    "sharedCount": 2,
    "albumIds": ["album_1", "album_2"]
  }
}
```

### POST /photos/upload-init

Initiate multipart upload.

**Request**
```json
{
  "fileName": "vacation-2024-01.jpg",
  "mimeType": "image/jpeg",
  "fileSize": 2097152,
  "metadata": {
    "tags": ["beach", "family"],
    "albumIds": ["album_1"]
  }
}
```

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "uploadId": "upload_abc123",
    "presignedUrls": [
      "https://s3.amazonaws.com/...?partNumber=1",
      "https://s3.amazonaws.com/...?partNumber=2"
    ],
    "parts": 5,
    "expiresIn": 3600
  }
}
```

### POST /photos/upload-complete

Complete multipart upload.

**Request**
```json
{
  "uploadId": "upload_abc123",
  "parts": [
    {
      "partNumber": 1,
      "etag": "\"abc123def456\""
    },
    {
      "partNumber": 2,
      "etag": "\"xyz789uvw012\""
    }
  ]
}
```

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "photoId": "photo_123",
    "fileName": "vacation-2024-01.jpg",
    "uploadedAt": 1705276800,
    "thumbnailUrl": "https://cdn.millerpic.family/thumb/photo_123.jpg"
  }
}
```

### GET /photos/{photoId}/download

Get presigned URL for full-resolution download.

**Query Parameters**
- `expiresIn` - URL expiry in seconds (default: 3600, max: 86400)

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "downloadUrl": "https://s3.amazonaws.com/...",
    "expiresAt": 1705280400,
    "fileName": "vacation-2024-01.jpg"
  }
}
```

### DELETE /photos/{photoId}

Delete a photo.

**Response (204)**
```
No content
```

### PATCH /photos/{photoId}

Update photo metadata (tags, description).

**Request**
```json
{
  "tags": ["beach", "family", "2024"],
  "description": "Family vacation in Miami"
}
```

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "photoId": "photo_123",
    "tags": ["beach", "family", "2024"],
    "description": "Family vacation in Miami"
  }
}
```

### GET /photos/search

Search photos by various criteria.

**Query Parameters**
- `q` - Text search (fileName, description)
- `tags` - Comma-separated required tags
- `startDate` - ISO 8601
- `endDate` - ISO 8601
- `limit` - Items per page
- `offset` - Pagination offset

**Response (200)** - Same as GET /photos

---

## Album Endpoints

### GET /albums

List user's albums.

**Query Parameters**
- `limit`, `offset` - Pagination

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "albums": [
      {
        "albumId": "album_1",
        "name": "Vacation 2024",
        "description": "Summer vacation in Miami",
        "coverPhotoId": "photo_123",
        "photoCount": 256,
        "createdAt": 1704067200,
        "shared": false
      }
    ],
    "pagination": { /* ... */ }
  }
}
```

### POST /albums

Create new album.

**Request**
```json
{
  "name": "Vacation 2024",
  "description": "Summer vacation in Miami",
  "coverPhotoId": "photo_123"
}
```

**Response (201)**
```json
{
  "status": "success",
  "data": {
    "albumId": "album_1",
    "name": "Vacation 2024",
    "description": "Summer vacation in Miami",
    "createdAt": 1704067200
  }
}
```

### GET /albums/{albumId}

Get album details with photos.

**Query Parameters**
- `limit`, `offset` - Pagination for photos

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "albumId": "album_1",
    "name": "Vacation 2024",
    "description": "Summer vacation in Miami",
    "photoCount": 256,
    "createdAt": 1704067200,
    "photos": [ /* paginated photos */ ]
  }
}
```

### PUT /albums/{albumId}

Update album metadata.

**Request**
```json
{
  "name": "Updated Album Name",
  "description": "Updated description",
  "coverPhotoId": "photo_456"
}
```

**Response (200)**
```json
{
  "status": "success",
  "data": { /* updated album */ }
}
```

### DELETE /albums/{albumId}

Delete album (photos not deleted).

**Response (204)**
```
No content
```

### POST /albums/{albumId}/photos

Add photos to album.

**Request**
```json
{
  "photoIds": ["photo_123", "photo_456", "photo_789"]
}
```

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "albumId": "album_1",
    "photoIds": ["photo_123", "photo_456", "photo_789"],
    "photoCount": 259
  }
}
```

### DELETE /albums/{albumId}/photos/{photoId}

Remove photo from album.

**Response (204)**
```
No content
```

---

## Share Endpoints

### POST /share/links

Generate shareable link.

**Request**
```json
{
  "albumIds": ["album_1"],
  "photoIds": [],
  "expiresInDays": 7,
  "password": "optional-password",
  "allowDownload": true
}
```

**Response (201)**
```json
{
  "status": "success",
  "data": {
    "linkId": "share_abc123",
    "shareUrl": "https://millerpic.family/share/share_abc123",
    "expiresAt": 1705881600,
    "password": true,
    "createdAt": 1705276800
  }
}
```

### GET /share/links

List active share links.

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "links": [
      {
        "linkId": "share_abc123",
        "albumIds": ["album_1"],
        "shareUrl": "https://millerpic.family/share/share_abc123",
        "expiresAt": 1705881600,
        "accessCount": 5,
        "createdAt": 1705276800
      }
    ]
  }
}
```

### GET /share/{linkId}

Access shared content (no auth required).

**Query Parameters**
- `password` - If link is password-protected

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "albums": [ /* shared albums */ ],
    "photos": [ /* shared photos */ ],
    "expiresAt": 1705881600
  }
}
```

### DELETE /share/{linkId}

Revoke share link.

**Response (204)**
```
No content
```

---

## User Endpoints

### GET /users/profile

Get current user profile.

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "userId": "user_123",
    "googleId": "google-id-xyz",
    "email": "family@gmail.com",
    "name": "Family Miller",
    "picture": "https://...",
    "role": "owner",
    "storageQuotaGB": 500,
    "storageUsedGB": 125.5,
    "createdAt": 1609459200,
    "lastLoginAt": 1705276800
  }
}
```

### PUT /users/profile

Update user profile.

**Request**
```json
{
  "name": "New Name",
  "settings": {
    "theme": "dark",
    "notificationsEnabled": true
  }
}
```

**Response (200)**
```json
{
  "status": "success",
  "data": { /* updated profile */ }
}
```

### GET /users/settings

Get user preferences.

**Response (200)**
```json
{
  "status": "success",
  "data": {
    "theme": "dark",
    "language": "en",
    "notificationsEnabled": true,
    "autoBackup": true,
    "shareNotifications": false,
    "displayDensity": "compact"
  }
}
```

### PUT /users/settings

Update user settings.

**Response (200)**
```json
{
  "status": "success",
  "data": { /* updated settings */ }
}
```

---

## Rate Limiting

**Limits per User (5-minute window)**
- Authentication endpoints: 10 requests
- Photo upload: 50 requests
- Photo read: 300 requests
- Share access: 100 requests

**Response Headers**
```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 295
X-RateLimit-Reset: 1705280400
```

**Rate Limit Exceeded (429)**
```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded. Retry after 60 seconds.",
    "retryAfter": 60
  }
}
```

---

## Pagination

All list endpoints support pagination:

```json
{
  "pagination": {
    "total": 15420,
    "limit": 20,
    "offset": 0,
    "hasMore": true
  }
}
```

**Query Parameters**
- `limit` - Items per page (1-100, default 20)
- `offset` - Pagination offset (default 0)

---

## Request IDs & Tracing

Every response includes `requestId` for debugging:

```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

Use this ID to track issues in CloudWatch logs.

