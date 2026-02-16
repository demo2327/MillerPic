import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import pytest
from moto import mock_aws
import boto3

# Add the handlers directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handlers import patch_photo


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
        },
        "body": json.dumps({
            "fileName": "updated-photo.jpg",
            "description": "Updated description"
        })
    }


class TestPatchPhoto:
    """Tests for patch_photo handler"""
    
    def test_patch_photo_success(self, dynamodb_table, mock_env, valid_event):
        """Test successful photo metadata update"""
        # Insert a photo first
        dynamodb_table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-456",
                "OriginalFileName": "old-photo.jpg",
                "ObjectKey": "uploads/photo-456.jpg",
                "ContentType": "image/jpeg"
            }
        )
        
        # Update the photo metadata
        response = patch_photo.handler(valid_event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["photoId"] == "photo-456"
        assert body["fileName"] == "updated-photo.jpg"
        assert body["description"] == "Updated description"
    
    def test_patch_photo_not_found(self, dynamodb_table, mock_env, valid_event):
        """Test updating non-existent photo returns 404"""
        response = patch_photo.handler(valid_event, None)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "error" in body
        assert "not found" in body["error"]
    
    def test_patch_photo_missing_user_id(self, dynamodb_table, mock_env, valid_event):
        """Test missing JWT subject claim returns 401"""
        event = valid_event.copy()
        event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"] = None
        
        response = patch_photo.handler(event, None)
        
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "error" in body
    
    def test_patch_photo_unverified_email(self, dynamodb_table, mock_env, valid_event):
        """Test unverified email returns 403"""
        event = valid_event.copy()
        event["requestContext"]["authorizer"]["jwt"]["claims"]["email_verified"] = "false"
        
        response = patch_photo.handler(event, None)
        
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "email is not verified" in body["error"]
    
    def test_patch_photo_missing_photo_id(self, dynamodb_table, mock_env, valid_event):
        """Test missing photoId returns 400"""
        event = valid_event.copy()
        event["pathParameters"]["photoId"] = None
        
        response = patch_photo.handler(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "photoId is required" in body["error"]
    
    def test_patch_photo_no_fields(self, dynamodb_table, mock_env, valid_event):
        """Test no fields provided returns 400"""
        event = valid_event.copy()
        event["body"] = json.dumps({})
        
        response = patch_photo.handler(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "at least one field must be provided" in body["error"]
    
    def test_patch_photo_invalid_filename(self, dynamodb_table, mock_env, valid_event):
        """Test empty fileName returns 400"""
        event = valid_event.copy()
        event["body"] = json.dumps({"fileName": "   "})
        
        response = patch_photo.handler(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "fileName cannot be empty" in body["error"]
    
    def test_patch_photo_filename_too_long(self, dynamodb_table, mock_env, valid_event):
        """Test fileName exceeding max length returns 400"""
        event = valid_event.copy()
        long_name = "a" * 256
        event["body"] = json.dumps({"fileName": long_name})
        
        response = patch_photo.handler(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "exceeds maximum length" in body["error"]
    
    def test_patch_photo_invalid_description(self, dynamodb_table, mock_env, valid_event):
        """Test empty description returns 400"""
        event = valid_event.copy()
        event["body"] = json.dumps({"description": "   "})
        
        response = patch_photo.handler(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "description cannot be empty" in body["error"]
    
    def test_patch_photo_description_too_long(self, dynamodb_table, mock_env, valid_event):
        """Test description exceeding max length returns 400"""
        event = valid_event.copy()
        long_desc = "a" * 1001
        event["body"] = json.dumps({"description": long_desc})
        
        response = patch_photo.handler(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "exceeds maximum length" in body["error"]
    
    def test_patch_photo_invalid_subjects(self, dynamodb_table, mock_env, valid_event):
        """Test invalid subjects format returns 400"""
        event = valid_event.copy()
        event["body"] = json.dumps({"subjects": "not-a-list"})
        
        response = patch_photo.handler(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "subjects must be an array" in body["error"]
    
    def test_patch_photo_valid_subjects(self, dynamodb_table, mock_env, valid_event):
        """Test valid subjects array"""
        # Insert a photo first
        dynamodb_table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-456",
                "OriginalFileName": "photo.jpg",
                "ObjectKey": "uploads/photo-456.jpg"
            }
        )
        
        event = valid_event.copy()
        event["body"] = json.dumps({"subjects": ["person1", "person2"]})
        
        response = patch_photo.handler(event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["subjects"] == ["person1", "person2"]
    
    def test_patch_photo_invalid_taken_at(self, dynamodb_table, mock_env, valid_event):
        """Test invalid takenAt format returns 400"""
        event = valid_event.copy()
        event["body"] = json.dumps({"takenAt": "not-a-date"})
        
        response = patch_photo.handler(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "valid ISO 8601" in body["error"]
    
    def test_patch_photo_valid_taken_at(self, dynamodb_table, mock_env, valid_event):
        """Test valid takenAt ISO date"""
        # Insert a photo first
        dynamodb_table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-456",
                "OriginalFileName": "photo.jpg",
                "ObjectKey": "uploads/photo-456.jpg"
            }
        )
        
        event = valid_event.copy()
        event["body"] = json.dumps({"takenAt": "2024-01-15T10:30:00Z"})
        
        response = patch_photo.handler(event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["takenAt"] == "2024-01-15T10:30:00Z"
    
    def test_patch_photo_invalid_json(self, dynamodb_table, mock_env, valid_event):
        """Test invalid JSON in body returns 400"""
        event = valid_event.copy()
        event["body"] = "invalid json"
        
        response = patch_photo.handler(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "invalid JSON" in body["error"]
