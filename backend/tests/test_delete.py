import json
import os
import sys
from datetime import datetime, timezone
import pytest
from moto import mock_aws
import boto3

# Add the handlers directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handlers import delete


@pytest.fixture
def dynamodb_table():
    """Fixture to create a mock DynamoDB table"""
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
        
        yield table


@pytest.fixture
def mock_env(monkeypatch):
    """Set required environment variables"""
    monkeypatch.setenv("PHOTOS_TABLE", "photos-test")


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


class TestDelete:
    """Tests for delete handler (soft delete)"""
    
    def test_delete_success(self, dynamodb_table, mock_env, valid_event):
        """Test successful soft delete of a photo"""
        # Insert a photo first
        dynamodb_table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-456",
                "OriginalFileName": "photo.jpg",
                "ObjectKey": "uploads/photo-456.jpg",
                "ContentType": "image/jpeg"
            }
        )
        
        # Delete the photo
        response = delete.handler(valid_event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["photoId"] == "photo-456"
        assert "deletedAt" in body
        assert "retentionUntil" in body
        
        # Verify the photo is marked as deleted in the database
        result = dynamodb_table.get_item(
            Key={"UserId": "user-123", "PhotoId": "photo-456"}
        )
        item = result.get("Item")
        assert item is not None
        assert "DeletedAt" in item
        assert "DeletedBy" in item
        assert item["DeletedBy"] == "user-123"
        assert "RetentionUntil" in item
    
    def test_delete_not_found(self, dynamodb_table, mock_env, valid_event):
        """Test deleting non-existent photo returns 404"""
        response = delete.handler(valid_event, None)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "error" in body
        assert "not found" in body["error"]
    
    def test_delete_already_deleted(self, dynamodb_table, mock_env, valid_event):
        """Test deleting already deleted photo returns 409"""
        # Insert a photo that's already deleted
        dynamodb_table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-456",
                "OriginalFileName": "photo.jpg",
                "ObjectKey": "uploads/photo-456.jpg",
                "DeletedAt": datetime.now(timezone.utc).isoformat()
            }
        )
        
        response = delete.handler(valid_event, None)
        
        assert response["statusCode"] == 409
        body = json.loads(response["body"])
        assert "already deleted" in body["error"]
    
    def test_delete_missing_user_id(self, dynamodb_table, mock_env, valid_event):
        """Test missing JWT subject claim returns 401"""
        event = valid_event.copy()
        event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"] = None
        
        response = delete.handler(event, None)
        
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "error" in body
    
    def test_delete_unverified_email(self, dynamodb_table, mock_env, valid_event):
        """Test unverified email returns 403"""
        event = valid_event.copy()
        event["requestContext"]["authorizer"]["jwt"]["claims"]["email_verified"] = "false"
        
        response = delete.handler(event, None)
        
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "email is not verified" in body["error"]
    
    def test_delete_missing_photo_id(self, dynamodb_table, mock_env, valid_event):
        """Test missing photoId returns 400"""
        event = valid_event.copy()
        event["pathParameters"]["photoId"] = None
        
        response = delete.handler(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "photoId is required" in body["error"]
    
    def test_delete_retention_period(self, dynamodb_table, mock_env, valid_event):
        """Test that retention period is set correctly"""
        # Insert a photo first
        dynamodb_table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-456",
                "OriginalFileName": "photo.jpg",
                "ObjectKey": "uploads/photo-456.jpg"
            }
        )
        
        before_delete = datetime.now(timezone.utc)
        response = delete.handler(valid_event, None)
        after_delete = datetime.now(timezone.utc)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        
        # Parse the retention date
        retention_until = datetime.fromisoformat(body["retentionUntil"].replace('Z', '+00:00'))
        deleted_at = datetime.fromisoformat(body["deletedAt"].replace('Z', '+00:00'))
        
        # Verify it's approximately 60 days in the future
        delta = retention_until - deleted_at
        assert 59 <= delta.days <= 60  # Allow for small time differences
