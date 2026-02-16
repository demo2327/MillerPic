import json
import os
import sys
from datetime import datetime, timezone
import pytest
from moto import mock_aws
import boto3

# Add the handlers directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handlers import trash


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
        "queryStringParameters": None
    }


class TestTrash:
    """Tests for trash handler (list deleted photos)"""
    
    def test_trash_list_deleted_photos(self, dynamodb_table, mock_env, valid_event):
        """Test listing deleted photos"""
        # Insert some photos, some deleted
        now = datetime.now(timezone.utc).isoformat()
        
        dynamodb_table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-1",
                "OriginalFileName": "photo1.jpg",
                "ObjectKey": "uploads/photo-1.jpg",
                "ContentType": "image/jpeg",
                "CreatedAt": now
            }
        )
        
        dynamodb_table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-2",
                "OriginalFileName": "photo2.jpg",
                "ObjectKey": "uploads/photo-2.jpg",
                "ContentType": "image/jpeg",
                "CreatedAt": now,
                "DeletedAt": now,
                "DeletedBy": "user-123",
                "RetentionUntil": now
            }
        )
        
        dynamodb_table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-3",
                "OriginalFileName": "photo3.jpg",
                "ObjectKey": "uploads/photo-3.jpg",
                "ContentType": "image/jpeg",
                "CreatedAt": now,
                "DeletedAt": now,
                "DeletedBy": "user-123",
                "RetentionUntil": now
            }
        )
        
        # List deleted photos
        response = trash.handler(valid_event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "photos" in body
        assert body["count"] == 2  # Only deleted photos
        
        # Verify all returned photos have DeletedAt
        for photo in body["photos"]:
            assert "deletedAt" in photo
            assert "deletedBy" in photo
            assert "retentionUntil" in photo
    
    def test_trash_empty_list(self, dynamodb_table, mock_env, valid_event):
        """Test listing when no deleted photos exist"""
        # Insert a non-deleted photo
        dynamodb_table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-1",
                "OriginalFileName": "photo1.jpg",
                "ObjectKey": "uploads/photo-1.jpg",
                "ContentType": "image/jpeg"
            }
        )
        
        response = trash.handler(valid_event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["count"] == 0
        assert body["photos"] == []
    
    def test_trash_missing_user_id(self, dynamodb_table, mock_env, valid_event):
        """Test missing JWT subject claim returns 401"""
        event = valid_event.copy()
        event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"] = None
        
        response = trash.handler(event, None)
        
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "error" in body
    
    def test_trash_unverified_email(self, dynamodb_table, mock_env, valid_event):
        """Test unverified email returns 403"""
        event = valid_event.copy()
        event["requestContext"]["authorizer"]["jwt"]["claims"]["email_verified"] = "false"
        
        response = trash.handler(event, None)
        
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "email is not verified" in body["error"]
    
    def test_trash_pagination_limit(self, dynamodb_table, mock_env, valid_event):
        """Test pagination with limit parameter"""
        now = datetime.now(timezone.utc).isoformat()
        
        # Insert multiple deleted photos
        for i in range(5):
            dynamodb_table.put_item(
                Item={
                    "UserId": "user-123",
                    "PhotoId": f"photo-{i}",
                    "OriginalFileName": f"photo{i}.jpg",
                    "ObjectKey": f"uploads/photo-{i}.jpg",
                    "ContentType": "image/jpeg",
                    "CreatedAt": now,
                    "DeletedAt": now,
                    "DeletedBy": "user-123",
                    "RetentionUntil": now
                }
            )
        
        event = valid_event.copy()
        event["queryStringParameters"] = {"limit": "2"}
        
        response = trash.handler(event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["count"] == 2
        assert "nextToken" in body
    
    def test_trash_invalid_limit(self, dynamodb_table, mock_env, valid_event):
        """Test invalid limit parameter returns 400"""
        event = valid_event.copy()
        event["queryStringParameters"] = {"limit": "invalid"}
        
        response = trash.handler(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "limit must be an integer" in body["error"]
