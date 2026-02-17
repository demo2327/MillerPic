# MillerPic Security Model & Implementation

## Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Zero Trust**: Verify every request, assume breach possible
3. **Principle of Least Privilege**: Minimal permissions for each component
4. **Secure by Default**: Security enabled by default, opt-out requires justification
5. **Transparency**: All security controls documented and auditable

---

## Terraform Static Security Scanning (Checkov)

MillerPic uses Checkov in CI to statically scan Terraform changes.

### Enforcement Model
- Trigger: runs on pull requests/commits that modify Terraform-related files.
- Threshold: High/Critical findings fail CI by default.
- Scope: Terraform under `infrastructure/`, `infrastructure/bootstrap/`, and `gcp/`.

### Local Reproduction
```bash
python -m pip install --upgrade pip
pip install checkov
checkov --config-file .checkov.yml -d infrastructure -d infrastructure/bootstrap -d gcp
```

### Suppression Policy
- Suppressions must be explicit inline comments in Terraform:
  - `#checkov:skip=CKV_AWS_XXX: <reason>`
- Reason must include business/security context and compensating control when applicable.
- Suppressions are reviewed in PR like any other security exception.

### Active Suppressions (Sprint 6)

| Check | Scope | Rationale | Compensating Controls | Owner | Next Review |
| --- | --- | --- | --- | --- | --- |
| `CKV_AWS_50` | Lambda functions in `infrastructure/lambda.tf` | X-Ray tracing deferred due recurring ingestion/storage cost for current family-scale workload | CloudWatch logs and alarms, Lambda DLQ, API error/throttle alarms | MillerPic Platform Team | 2026-03-16 |
| `CKV_AWS_18` | S3 buckets `photos` and `terraform_state` | S3 access logging deferred to avoid additional storage/request cost this budget cycle | CloudTrail audit logs, S3 public access block, versioning, IAM least privilege | MillerPic Platform Team | 2026-03-16 |
| `CKV2_AWS_57` | `aws_secretsmanager_secret.app_sensitive_config` in `infrastructure/bootstrap/main.tf` | Secret stores static sensitive configuration values (issuer/audience/contact), not rotatable credentials | IaC change control, PR review, least-privilege access to secret, explicit monthly review | MillerPic Platform Team | 2026-03-16 |

Suppression scope is intentionally limited to the two budget-approved checks above. Any new suppression requires explicit sprint planning approval.

---

## Authentication & Authorization

### Primary Authentication: Google OAuth 2.0

**Flow**
```
1. User clicks "Sign in with Google"
2. Frontend redirects to Google consent screen
3. User authenticates with Google account (must be workspace account)
4. Google redirects with authorization code
5. Backend exchanges code for ID token
6. Backend validates token signature via Google public keys
7. Verify email domain is @gmail.com (or configured workspace domain)
8. Create/update user in database
9. Generate JWT for frontend use
```

**Implementation**
```javascript
// Backend validation
const { OAuth2Client } = require('google-auth-library');

const oauth2Client = new OAuth2Client(
  process.env.GOOGLE_CLIENT_ID,
  process.env.GOOGLE_CLIENT_SECRET,
  process.env.GOOGLE_REDIRECT_URI
);

// Verify token from Google
const ticket = await oauth2Client.verifyIdToken({
  idToken: idToken,
  audience: process.env.GOOGLE_CLIENT_ID
});

// Validate email domain
const { email_verified, email, hd } = ticket.getPayload();
if (!email_verified || !email.includes('family-domain@gmail.com')) {
  throw new Error('Unauthorized email domain');
}
```

### Secondary Authentication: Client Certificates (mTLS)

**Certificate Lifecycle**
```
1. User registers device via POST /auth/cert/register
2. Frontend generates CSR (Certificate Signing Request)
3. Backend validates JWT and issues cert via Lambda
4. Frontend stores cert in device keystore/Keychain
5. Certificate valid for 365 days
6. Auto-renewal 30 days before expiry
```

**Certificate Validation**
```
Every request includes X-Client-Cert header:
GET /photos HTTP/1.1
X-Client-Cert: -----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----
```

Backend validates:
- Certificate not expired
- Certificate chain valid
- Certificate pinned to user account
- Fingerprint matches expected value

### JWT Token Management

**Token Structure**
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_123",
    "email": "family@gmail.com",
    "iat": 1705276800,
    "exp": 1705280400,
    "auth_method": "oauth|cert",
    "permissions": ["photos:read", "photos:write"]
  },
  "signature": "HMACSHA256(...)"
}
```

**Token Lifecycle**
- Access Token: 1 hour expiry
- Refresh Token: 30 days expiry (stored in DynamoDB)
- Refresh Token rotation: Issue new refresh on each use
- Token revocation: On logout, delete refresh token

**Token Security**
```javascript
const jwt = require('jsonwebtoken');

// Sign token with secret from Secrets Manager
const token = jwt.sign(
  {
    sub: userId,
    email: userEmail,
    permissions: userPermissions,
  },
  AWS_SECRET_VALUE,
  {
    algorithm: 'HS256',
    expiresIn: '1h',
    issuer: 'https://api.millerpic.family',
    audience: 'millerpic-family',
  }
);

// Verify token signature
const decoded = jwt.verify(token, AWS_SECRET_VALUE, {
  algorithms: ['HS256'],
  issuer: 'https://api.millerpic.family',
  audience: 'millerpic-family',
});
```

### Authorization Model

**Role-Based Access Control (RBAC)**
```
Roles:
- owner: Full access, can invite users
- viewer: Read-only access
- curator: Can organize, tag, create albums
```

**Permission Matrix**
```
             Action     | Owner | Curator | Viewer
Upload photos          |  ✓    |   ✓     |   
Delete photos          |  ✓    |         |
Create albums          |  ✓    |   ✓     |
Edit albums            |  ✓    |   ✓     |
Create share links     |  ✓    |   ✓     |
Manage users           |  ✓    |         |
View photos            |  ✓    |   ✓     |   ✓
Download full res      |  ✓    |   ✓     |   ✓
```

**Implementation**
```javascript
// Middleware to check permissions
async function requirePermission(requiredPermission) {
  return async (req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1];
    const decoded = jwt.verify(token, JWT_SECRET);
    
    if (!decoded.permissions.includes(requiredPermission)) {
      return res.status(403).json({
        error: 'FORBIDDEN',
        message: 'Insufficient permissions'
      });
    }
    
    req.user = decoded;
    next();
  };
}

// Usage
router.post('/albums', 
  requirePermission('albums:create'),
  createAlbum
);
```

---

## Data Security

### Encryption at Rest (S3)

**S3 Encryption Configuration**
```hcl
# Terraform configuration
resource "aws_s3_bucket_server_side_encryption_configuration" "photos" {
  bucket = aws_s3_bucket.photos.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}
```

**KMS Key Configuration**
```hcl
resource "aws_kms_key" "s3" {
  description             = "KMS key for MillerPic S3 encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  
  tags = {
    Name = "millerpic-s3-key"
  }
}
```

### Encryption in Transit (TLS 1.3)

**API Gateway Configuration**
```hcl
resource "aws_apigatewayv2_stage" "api" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "prod"
  
  default_route_settings {
    logging_level       = "INFO"
    data_trace_enabled  = false
    throttle_settings {
      burst_limit = 100
      rate_limit  = 50
    }
  }
}
```

**Certificate Management**
- TLS 1.3 minimum
- HSTS header: `max-age=31536000; includeSubDomains`
- Certificate from AWS Certificate Manager (free)
- Auto-renewal enabled

### Database Encryption (DynamoDB)

```hcl
resource "aws_dynamodb_table" "photos" {
  name           = "millerpic-photos"
  billing_mode   = "PAY_PER_REQUEST"
  
  sse_specification {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }
  
  point_in_time_recovery {
    enabled = true
  }
}
```

---

## Network Security

### WAF (Web Application Firewall)

**AWS WAF Rules**
```hcl
resource "aws_wafv2_web_acl" "cloudfront" {
  name        = "millerpic-waf"
  scope       = "CLOUDFRONT"
  default_action {
    allow {}
  }

  # Rate limiting
  rule {
    name     = "RateLimitRule"
    priority = 1
    
    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 10000
        aggregate_key_type = "IP"
      }
    }
  }

  # SQL Injection protection
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 2
    
    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name = "AWSManagedRulesSQLiRuleSet"
      }
    }
  }

  # XSS protection
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 3
    
    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name = "AWSManagedRulesKnownBadInputsRuleSet"
      }
    }
  }
}
```

### VPC Security (If needed)

```hcl
resource "aws_security_group" "lambda" {
  name = "millerpic-lambda-sg"

  # Only allow outbound to necessary services
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

---

## API Security

### CORS Configuration

```hcl
resource "aws_apigatewayv2_integration" "cors" {
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "HTTP_PROXY"
  integration_uri    = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

# Allow only specific origins
resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.main.id
  
  # CORS in Lambda
}
```

**CORS Headers (in Lambda)**
```javascript
const corsHeaders = {
  'Access-Control-Allow-Origin': 'https://millerpic.family',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Client-Cert',
  'Access-Control-Max-Age': '3600'
};
```

### Rate Limiting

**Implementation (Lambda Middleware)**
```javascript
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { 
  GetCommand, 
  UpdateCommand 
} = require('@aws-sdk/lib-dynamodb');

async function rateLimit(userId) {
  const client = new DynamoDBClient();
  const now = Math.floor(Date.now() / 1000);
  const window = Math.floor(now / 300) * 300; // 5-minute window
  
  const key = `${userId}:${window}`;
  
  try {
    const response = await client.send(new UpdateCommand({
      TableName: 'RateLimits',
      Key: { limitKey: key },
      UpdateExpression: 'ADD requestCount :inc SET expiresAt = :exp',
      ExpressionAttributeValues: {
        ':inc': 1,
        ':exp': window + 300 + 60 // +60s buffer
      },
      ReturnValues: 'ALL_NEW'
    }));
    
    if (response.Attributes.requestCount > 100) {
      throw new Error('Rate limit exceeded');
    }
  } catch (err) {
    if (err.message === 'Rate limit exceeded') {
      throw err;
    }
    // DynamoDB error, allow but log
    console.error('Rate limit check failed:', err);
  }
}
```

### Input Validation

```javascript
const Joi = require('joi');

const uploadPhotoSchema = Joi.object({
  fileName: Joi.string()
    .required()
    .max(255)
    .pattern(/^[\w\-. ]+$/, { invert: true })
    .messages({
      'string.pattern.invert.base': 'FileName contains invalid characters'
    }),
  mimeType: Joi.string()
    .required()
    .valid('image/jpeg', 'image/png', 'image/webp', 'video/mp4')
    .messages({
      'any.only': 'MIME type not allowed'
    }),
  fileSize: Joi.number()
    .required()
    .max(5368709120) // 5GB
    .messages({
      'number.max': 'File too large (max 5GB)'
    }),
  metadata: Joi.object({
    tags: Joi.array().items(Joi.string().max(50)).max(20),
    albumIds: Joi.array().items(Joi.string()).max(10)
  })
});

// Usage
const { error, value } = uploadPhotoSchema.validate(req.body);
if (error) {
  return res.status(400).json({
    error: 'INVALID_PARAMETERS',
    details: error.details
  });
}
```

---

## Secrets Management

### AWS Secrets Manager

**Storing Secrets**
```javascript
const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager');

async function getSecret(secretName) {
  const client = new SecretsManagerClient();
  try {
    const response = await client.send(new GetSecretValueCommand({
      SecretId: secretName
    }));
    return JSON.parse(response.SecretString);
  } catch (error) {
    console.error(`Error retrieving secret ${secretName}:`, error);
    throw error;
  }
}

// Usage
const googleCreds = await getSecret('millerpic/google-oauth');
const jwtSecret = await getSecret('millerpic/jwt-secret');
```

**Environment Variables (NOT secrets)**
```bash
# Good - no sensitive data
ENVIRONMENT=production
AWS_REGION=us-east-1
LOG_LEVEL=info

# Bad - never in environment
# JWT_SECRET=xxx
# DB_PASSWORD=xxx
# GOOGLE_CLIENT_SECRET=xxx
```

---

## Audit & Monitoring

### CloudTrail

Track all AWS API calls:
```hcl
resource "aws_cloudtrail" "main" {
  name           = "millerpic-trail"
  s3_bucket_name = aws_s3_bucket.cloudtrail.id
  
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  
  event_selector {
    read_write_type           = "All"
    include_management_events = true
    
    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::${aws_s3_bucket.photos.id}/*"]
    }
  }
}
```

### CloudWatch Logs

```javascript
// Log authentication attempts
console.info(JSON.stringify({
  event: 'AUTH_ATTEMPT',
  userId: user.id,
  method: 'oauth',
  timestamp: new Date().toISOString(),
  success: true
}));

// Log access to sensitive operations
console.info(JSON.stringify({
  event: 'PHOTO_DOWNLOADED',
  userId: user.id,
  photoId: photo.id,
  ipAddress: req.ip,
  timestamp: new Date().toISOString()
}));
```

### Security Alerts

```hcl
resource "aws_cloudwatch_metric_alarm" "failed_auth" {
  alarm_name          = "millerpic-failed-auth-spike"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FailedAuthCount"
  namespace           = "MillerPic"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

---

## Compliance & Standards

- **OWASP Top 10**: Mitigated
- **CWE Top 25**: Considered
- **GDPR**: Data residency in US (adjustable)
- **CCPA**: Compliance ready

---

## Security Incident Response

**If breach suspected:**
1. Revoke all active JWT tokens in database
2. Require password reset on next login
3. Force certificate re-registration
4. Review CloudTrail logs for suspicious activity
5. Notify affected users
6. File incident report

**Testing**
- Annual security audit
- Quarterly penetration testing
- Continuous dependency scanning
- SAST on every commit

