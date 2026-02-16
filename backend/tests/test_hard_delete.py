import json
import os
import sys
from datetime import datetime, timezone
import pytest
from moto import mock_aws
import boto3

# Add the handlers directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handlers import hard_delete


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


class TestHardDelete:
    """Tests for hard_delete handler (permanent deletion)"""
    
    def test_hard_delete_success(self, aws_resources, mock_env, valid_event):
        """Test successful hard delete of a soft-deleted photo"""
        table = aws_resources["table"]
        s3 = aws_resources["s3"]
        
        # Upload a file to S3
        s3.put_object(
            Bucket="photos-test-bucket",
            Key="uploads/photo-456.jpg",
            Body=b"fake image data"
        )
        
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
        
        # Hard delete the photo
        response = hard_delete.handler(valid_event, None)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["photoId"] == "photo-456"
        assert "permanently deleted" in body["message"]
        
        # Verify the photo is removed from DynamoDB
        result = table.get_item(
            Key={"UserId": "user-123", "PhotoId": "photo-456"}
        )
        assert "Item" not in result
        
        # Verify the object is removed from S3
        from botocore.exceptions import ClientError
        try:
            s3.head_object(Bucket="photos-test-bucket", Key="uploads/photo-456.jpg")
            assert False, "Object should have been deleted from S3"
        except ClientError as e:
            # Expected - object should be deleted
            assert e.response['Error']['Code'] == '404'
    
    def test_hard_delete_not_found(self, aws_resources, mock_env, valid_event):
        """Test hard deleting non-existent photo returns 404"""
        response = hard_delete.handler(valid_event, None)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "error" in body
        assert "not found" in body["error"]
    
    def test_hard_delete_not_soft_deleted(self, aws_resources, mock_env, valid_event):
        """Test hard deleting photo that isn't soft-deleted returns 400"""
        table = aws_resources["table"]
        
        # Insert a photo that's NOT deleted
        table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-456",
                "OriginalFileName": "photo.jpg",
                "ObjectKey": "uploads/photo-456.jpg",
                "ContentType": "image/jpeg"
            }
        )
        
        response = hard_delete.handler(valid_event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "must be soft deleted" in body["error"]
    
    def test_hard_delete_missing_user_id(self, aws_resources, mock_env, valid_event):
        """Test missing JWT subject claim returns 401"""
        event = valid_event.copy()
        event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"] = None
        
        response = hard_delete.handler(event, None)
        
        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "error" in body
    
    def test_hard_delete_unverified_email(self, aws_resources, mock_env, valid_event):
        """Test unverified email returns 403"""
        event = valid_event.copy()
        event["requestContext"]["authorizer"]["jwt"]["claims"]["email_verified"] = "false"
        
        response = hard_delete.handler(event, None)
        
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "email is not verified" in body["error"]
    
    def test_hard_delete_missing_photo_id(self, aws_resources, mock_env, valid_event):
        """Test missing photoId returns 400"""
        event = valid_event.copy()
        event["pathParameters"]["photoId"] = None
        
        response = hard_delete.handler(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "photoId is required" in body["error"]
    
    def test_hard_delete_without_s3_object(self, aws_resources, mock_env, valid_event):
        """Test hard delete when S3 object doesn't exist"""
        table = aws_resources["table"]
        
        # Insert a soft-deleted photo WITHOUT S3 object
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
        
        # Hard delete should still succeed even if S3 object is missing
        response = hard_delete.handler(valid_event, None)
        
        assert response["statusCode"] == 200
        
        # Verify the photo metadata is still removed from DynamoDB
        result = table.get_item(
            Key={"UserId": "user-123", "PhotoId": "photo-456"}
        )
        assert "Item" not in result
    
    def test_hard_delete_no_object_key(self, aws_resources, mock_env, valid_event):
        """Test hard delete when photo has no ObjectKey"""
        table = aws_resources["table"]
        
        # Insert a soft-deleted photo without ObjectKey
        table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-456",
                "OriginalFileName": "photo.jpg",
                "ContentType": "image/jpeg",
                "DeletedAt": datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Hard delete should succeed
        response = hard_delete.handler(valid_event, None)
        
        assert response["statusCode"] == 200
        
        # Verify the photo metadata is removed from DynamoDB
        result = table.get_item(
            Key={"UserId": "user-123", "PhotoId": "photo-456"}
        )
        assert "Item" not in result

    def test_hard_delete_preserves_shared_object(self, aws_resources, mock_env, valid_event):
        table = aws_resources["table"]
        s3 = aws_resources["s3"]

        shared_key = "originals/user-source/shared.webp"
        s3.put_object(
            Bucket="photos-test-bucket",
            Key=shared_key,
            Body=b"shared-image",
        )

        table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-456",
                "ObjectKey": shared_key,
                "DeletedAt": datetime.now(timezone.utc).isoformat(),
            }
        )
        table.put_item(
            Item={
                "UserId": "user-999",
                "PhotoId": "photo-shared",
                "ObjectKey": shared_key,
                "Status": "ACTIVE",
            }
        )

        response = hard_delete.handler(valid_event, None)
        assert response["statusCode"] == 200

        # Metadata row for deleted photo is gone.
        removed = table.get_item(Key={"UserId": "user-123", "PhotoId": "photo-456"})
        assert "Item" not in removed

        # Shared object is still present due to another reference.
        existing = s3.head_object(Bucket="photos-test-bucket", Key=shared_key)
        assert existing["ResponseMetadata"]["HTTPStatusCode"] == 200
