# MillerPic

**Family photo storage platform on AWS serverless architecture.**

Store your family's lifetime collection of photos and videos with full resolution preservation, complete privacy, and secure family access.

## 📖 Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design, data flow, components
- **[SPECIFICATION.md](docs/SPECIFICATION.md)** - Technical specs, tech stack, database schema
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Terraform infrastructure setup & management
- **[API_DESIGN.md](docs/API_DESIGN.md)** - Complete REST API specification
- **[SECURITY.md](docs/SECURITY.md)** - Security model, OAuth, mTLS, encryption
- **[COST_ESTIMATE.md](docs/COST_ESTIMATE.md)** - AWS cost analysis & optimization
- **[IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md)** - 6-phase delivery plan (32 weeks)

## 🎯 Features

- ✅ Google Workspace authentication (family domain login)
- ✅ Client certificate support (mTLS) for enhanced security
- ✅ Full-resolution photo preservation (original files stored in S3)
- ✅ Serverless architecture (no EC2 instances, cost-efficient)
- ✅ Web gallery (React + TypeScript)
- ✅ Android mobile app (React Native)
- ✅ Album organization & smart organizing
- ✅ Secure sharing via time-limited links
- ✅ Encrypted storage (AES-256 at rest, TLS 1.3 in transit)
- ✅ Family collaboration with role-based access
- ✅ 99.9% uptime SLA
- ✅ Fully automated CI/CD via GitHub Actions

## 💰 Cost

**Estimated monthly cost for family of 4:**
- **100GB**: ~$12/month (free tier year 1)
- **1TB**: ~$93/month
- **5TB**: ~$438/month

Includes: storage, compute, CDN, database, monitoring.

Compare to:
- Google One: $100/month (2TB limit)
- OneDrive: $70/month (1TB limit)
- Shutterfly/SmugMug: $150+/month

## 🏗️ Architecture

**Serverless Stack:**
- **Frontend**: React web + React Native mobile
- **Backend**: Node.js Lambda functions
- **Database**: DynamoDB (metadata)
- **Storage**: S3 (full-resolution photos)
- **CDN**: CloudFront (fast delivery)
- **Auth**: Google OAuth 2.0 + mTLS certificates
- **Infrastructure**: Terraform (IaC)
- **CI/CD**: GitHub Actions

**AWS Services:**
```
API Gateway → Lambda → DynamoDB
              ↓
             S3 ← CloudFront ← Users
              
Secrets Manager, KMS, WAF, CloudWatch, CloudTrail
```

## 🚀 Quick Start

### Prerequisites
- AWS account with appropriate permissions
- Node.js v20+
- Terraform v1.6+
- Google OAuth app registered
- AWS CLI configured

### 1. Clone & Setup

```bash
git clone https://github.com/demo2327/MillerPic.git
cd MillerPic

# Install dependencies
npm install
```

### 2. Configure Infrastructure

```bash
cd infrastructure

# Copy example config
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

### 3. Deploy Infrastructure

```bash
terraform init
terraform plan
terraform apply
```

### 4. Deploy Backend

```bash
cd ../backend
npm install
npm run build
# Deployment handled by GitHub Actions after push
```

### 5. Deploy Web Client

```bash
cd ../web-client
npm install
npm run build
npm run deploy
```

### 6. Build Mobile App

```bash
cd ../mobile-client
npm install
npm run android
```

## 📁 Project Structure

```
MillerPic/
├── docs/                       # Complete documentation
│   ├── ARCHITECTURE.md
│   ├── SPECIFICATION.md
│   ├── DEPLOYMENT.md
│   ├── API_DESIGN.md
│   ├── SECURITY.md
│   ├── COST_ESTIMATE.md
│   └── IMPLEMENTATION_ROADMAP.md
├── infrastructure/             # Terraform IaC
│   ├── main.tf
│   ├── variables.tf
│   ├── s3.tf
│   ├── dynamodb.tf
│   ├── lambda.tf
│   ├── api-gateway.tf
│   └── ...
├── backend/                    # Node.js Lambda functions
│   ├── src/
│   │   ├── handlers/
│   │   ├── services/
│   │   ├── middleware/
│   │   └── utils/
│   └── package.json
├── web-client/                 # React web application
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── vite.config.ts
├── mobile-client/              # React Native Android
│   ├── src/
│   │   ├── screens/
│   │   └── components/
│   └── package.json
├── .github/
│   └── workflows/              # CI/CD pipelines
│       ├── deploy-backend.yaml
│       ├── deploy-frontend.yaml
│       └── security-scan.yaml
└── README.md
```

## 🔒 Security

- **Authentication**: Google OAuth 2.0 + optional mTLS client certificates
- **Encryption**: AES-256 at rest (S3/DynamoDB), TLS 1.3 in transit
- **Authorization**: Role-based access control (Owner, Curator, Viewer)
- **DLP**: WAF, rate limiting, input validation
- **Audit**: CloudTrail, CloudWatch Logs, X-Ray tracing
- **Secrets**: AWS Secrets Manager for credentials

See [SECURITY.md](docs/SECURITY.md) for details.

## 📋 Development Phases

| Phase | Duration | Focus |
|-------|----------|-------|
| **1** | Weeks 1-4 | Foundation, Auth, CI/CD |
| **2** | Weeks 5-12 | Web gallery, upload/download |
| **3** | Weeks 13-18 | Android mobile app |
| **4** | Weeks 19-26 | Albums, sharing, collaboration |
| **5** | Weeks 27-32 | Security hardening, production launch |
| **6** | Ongoing | Advanced features (AI, desktop, iOS) |

See [IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md) for details.

## 🧪 Local Development

```bash
# Start backend locally
cd backend
npm install
npm run dev

# Start web in another terminal
cd web-client
npm install
npm run dev

# Start mobile in another terminal
cd mobile-client
npm install
npm start
```

## 📊 Monitoring

- **CloudWatch Dashboard**: Real-time metrics
- **X-Ray**: Distributed tracing
- **CloudWatch Alarms**: Cost, error rate, performance alerts
- **CloudTrail**: All API calls logged

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test: `npm test`
3. Push: `git push origin feature/your-feature`
4. Create PR with description
5. Wait for CI/CD and review approval
6. Merge to main

## 📝 License

Private/Family Use

## 🙋 Support

For questions or issues:
1. Check [docs/](docs/) for comprehensive documentation
2. Review [IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md) for context
3. See [SECURITY.md](docs/SECURITY.md) for security questions

---

**Next Steps:**
1. Read [ARCHITECTURE.md](docs/ARCHITECTURE.md) for system overview
2. Review [DEPLOYMENT.md](docs/DEPLOYMENT.md) for infrastructure setup
3. Start [Phase 1](docs/IMPLEMENTATION_ROADMAP.md) of implementation roadmap