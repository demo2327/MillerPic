import json
import os
import sys
from datetime import datetime, timezone
import pytest
from moto import mock_aws
import boto3

# Add the handlers directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handlers import download


@pytest.fixture
def aws_resources():
    """Fixture to create mock AWS resources"""
    with mock_aws():
        # Create DynamoDB resource
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        
        # Create table
        table = dynamodb.create_table(
            TableName="photos-test",
            KeySchema=[
                {"AttributeName": "UserId", "KeyType": "HASH"},
                {"AttributeName": "PhotoId", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "UserId", "AttributeType": "S"},
                {"AttributeName": "PhotoId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        
        # Create S3 bucket
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="photos-test-bucket")
        
        yield {
            "table": table,
            "s3": s3
        }


@pytest.fixture
def mock_env(monkeypatch):
    """Set required environment variables"""
    monkeypatch.setenv("PHOTOS_TABLE", "photos-test")
    monkeypatch.setenv("PHOTO_BUCKET", "photos-test-bucket")


@pytest.fixture
def valid_event():
    """Sample valid API Gateway event"""
    return {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "user-123",
                        "email_verified": "true"
                    }
                }
            }
        },
        "pathParameters": {
            "photoId": "photo-456"
        }
    }


class TestDownload:
    """Tests for download handler"""
    
    def test_download_success(self, aws_resources, mock_env, valid_event):
        """Test successful download URL generation"""
        table = aws_resources["table"]
        s3 = aws_resources["s3"]
        
        # Upload a file to S3
        s3.put_object(
            Bucket="photos-test-bucket",
            Key="uploads/photo-456.jpg",
            Body=b"fake image data"
        )
        
        # Insert a photo
        table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-456",
                "OriginalFileName": "photo.jpg",
                "ObjectKey": "uploads/photo-456.jpg",
                "ContentType": "image/jpeg"
            }
        )
        
        # Get download URL
        response = download.handler(valid_event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "downloadUrl" in body
        assert "expiresInSeconds" in body
        assert body["expiresInSeconds"] == 3600
        assert "photos-test-bucket" in body["downloadUrl"]
        assert "photo-456.jpg" in body["downloadUrl"]
    
    def test_download_not_found(self, aws_resources, mock_env, valid_event):
        """Test downloading non-existent photo returns 404"""
        response = download.handler(valid_event, None)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "error" in body
        assert "not found" in body["error"]
    
    def test_download_deleted_photo(self, aws_resources, mock_env, valid_event):
        """Test downloading soft-deleted photo returns 404"""
        table = aws_resources["table"]
        
        # Insert a soft-deleted photo
        table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-456",
                "OriginalFileName": "photo.jpg",
                "ObjectKey": "uploads/photo-456.jpg",
                "ContentType": "image/jpeg",
                "DeletedAt": datetime.now(timezone.utc).isoformat()
            }
        )
        
        response = download.handler(valid_event, None)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "error" in body
        assert "not found" in body["error"]
    
    def test_download_missing_user_id(self, aws_resources, mock_env, valid_event):
        """Test missing JWT subject claim returns 401"""
        event = valid_event.copy()
        event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"] = None
        
        response = download.handler(event, None)
        
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "error" in body
    
    def test_download_unverified_email(self, aws_resources, mock_env, valid_event):
        """Test unverified email returns 403"""
        event = valid_event.copy()
        event["requestContext"]["authorizer"]["jwt"]["claims"]["email_verified"] = "false"
        
        response = download.handler(event, None)
        
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "email is not verified" in body["error"]
    
    def test_download_missing_photo_id(self, aws_resources, mock_env, valid_event):
        """Test missing photoId returns 400"""
        event = valid_event.copy()
        event["pathParameters"]["photoId"] = None
        
        response = download.handler(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "photoId" in body["error"]
