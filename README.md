# MillerPic

Store Pictures and Videos from computers and mobile phones using AWS serverless architecture.

## Components

- **Backend**: AWS Lambda functions for API endpoints
- **Desktop Client**: Windows application for uploading from computers
- **Android Client**: Mobile app for uploading from Android devices
- **Infrastructure**: CloudFormation templates for AWS resources

## Setup

### Prerequisites

- Node.js for backend
- .NET SDK for desktop client
- Android Studio for Android client
- AWS CLI configured

### Backend

```bash
cd backend
npm install
```

### Desktop Client

```bash
cd desktop-client
# Setup .NET project
```

### Android Client

```bash
cd android-client
# Setup Android project
```

### Infrastructure

```bash
cd infrastructure
# Deploy CloudFormation
```

## Deployment

Use AWS CDK or CloudFormation to deploy infrastructure and backend.