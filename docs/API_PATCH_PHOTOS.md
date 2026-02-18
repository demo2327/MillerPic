# PATCH /photos/{photoId} - Metadata Update Endpoint

## Overview
This endpoint allows authenticated users to update metadata for their photos, including file name, description, subjects (tags), and capture timestamp.

## Endpoint
```
PATCH /photos/{photoId}
```

## Authentication
- **Required**: JWT token via Authorization header
- **Claims Required**: 
  - `sub` (user ID)
  - `email_verified: true`

## Authorization
- Users can only update photos they own (matched by JWT `sub` claim)
- Ownership is verified via DynamoDB conditional update

## Request Body
All fields are optional, but **at least one field must be provided**.

```json
{
  "fileName": "string (max 255 chars)",
  "description": "string (max 1000 chars)",
  "subjects": ["array", "of", "strings"],
  "takenAt": "ISO 8601 datetime string"
}
```

### Field Details

#### fileName
- **Type**: String
- **Max Length**: 255 characters
- **Validation**: Trimmed, must be non-empty after trimming
- **Example**: `"beach_vacation_2024.jpg"`

#### description
- **Type**: String
- **Max Length**: 1000 characters
- **Validation**: Trimmed, must be non-empty after trimming
- **Example**: `"Family vacation at Myrtle Beach in summer 2024"`

#### subjects
- **Type**: Array of strings
- **Max Count**: 50 subjects
- **Sanitization**: 
  - Each string is trimmed
  - Empty strings are removed
  - Duplicates are removed (case-sensitive)
  - Limited to first 50 items
- **Example**: `["beach", "summer", "family", "vacation"]`

#### takenAt
- **Type**: ISO 8601 datetime string
- **Validation**: Must be valid ISO 8601 format
- **Examples**: 
  - `"2024-07-15T10:30:00Z"`
  - `"2024-07-15T10:30:00+00:00"`
  - `"2024-07-15T10:30:00.123Z"`

## Response

### Success (200)
```json
{
  "photoId": "photo-123",
  "fileName": "beach_vacation_2024.jpg",
  "description": "Family vacation at Myrtle Beach",
  "subjects": ["beach", "summer", "family"],
  "takenAt": "2024-07-15T10:30:00Z"
}
```

### Error Responses

#### 400 Bad Request
Invalid input data:
```json
{
  "error": "at least one field must be provided"
}
```

Other 400 errors:
- `"subjects must be an array of strings"`
- `"takenAt must be a valid ISO 8601 datetime string"`
- `"fileName exceeds maximum length of 255"`
- `"description exceeds maximum length of 1000"`
- `"fileName must be a string"`
- `"description must be a string"`
- `"invalid JSON in request body"`

#### 401 Unauthorized
```json
{
  "error": "missing or invalid JWT subject claim"
}
```

#### 403 Forbidden
```json
{
  "error": "email is not verified"
}
```

#### 404 Not Found
Photo does not exist or user does not own it:
```json
{
  "error": "photo not found"
}
```

#### 500 Internal Server Error
```json
{
  "error": "internal server error"
}
```

## Examples

### Example 1: Update All Fields
```bash
curl -X PATCH "https://api.example.com/photos/photo-123" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "fileName": "summer_vacation.jpg",
    "description": "Beautiful day at the beach with the family",
    "subjects": ["beach", "summer", "2024", "family"],
    "takenAt": "2024-07-15T14:30:00Z"
  }'
```

### Example 2: Update Only Subjects
```bash
curl -X PATCH "https://api.example.com/photos/photo-123" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "subjects": ["nature", "wildlife", "birds"]
  }'
```

### Example 3: Update Only Description
```bash
curl -X PATCH "https://api.example.com/photos/photo-123" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description for this photo"
  }'
```

## Subjects Sanitization Examples

Input:
```json
{
  "subjects": ["  beach  ", "summer", "beach", "  ", "family", "summer"]
}
```

Output (after sanitization):
```json
{
  "subjects": ["beach", "summer", "family"]
}
```

## Integration with List Endpoint

The `GET /photos` endpoint now includes the new metadata fields in its response:

```json
{
  "photos": [
    {
      "photoId": "photo-123",
      "fileName": "summer_vacation.jpg",
      "objectKey": "originals/user-456/photo-123.webp",
      "contentType": "image/webp",
      "createdAt": "2024-07-15T10:00:00Z",
      "status": "ACTIVE",
      "thumbnailKey": "thumbnails/user-456/photo-123.webp",
      "thumbnailUrl": "https://...signed-thumbnail-url...",
      "description": "Beautiful day at the beach",
      "subjects": ["beach", "summer", "family"],
      "takenAt": "2024-07-15T14:30:00Z"
    }
  ],
  "count": 1,
  "nextToken": null
}
```

## Implementation Notes

### DynamoDB Updates
- Uses `UpdateItem` with `ConditionExpression` to ensure photo exists
- Only updates fields that are provided in the request
- Returns updated item attributes

### Performance
- Single DynamoDB UpdateItem operation
- No S3 operations required
- Typical response time: < 100ms

### Security
- JWT-based authentication required
- Ownership verified via conditional update
- Input sanitization prevents injection attacks
- All string inputs are trimmed and validated

### Future Enhancements (Non-Goals for Now)
- NLP-based auto-tagging
- Typed subject taxonomy (e.g., categories)
- Bulk metadata updates
- AI-generated descriptions
