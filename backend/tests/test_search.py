import json
import os
import sys
from datetime import datetime, timezone

import boto3
import pytest
from moto import mock_aws

# Add the handlers directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handlers import search


@pytest.fixture
def dynamodb_table():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="photos-test",
            KeySchema=[
                {"AttributeName": "UserId", "KeyType": "HASH"},
                {"AttributeName": "PhotoId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "UserId", "AttributeType": "S"},
                {"AttributeName": "PhotoId", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield table


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("PHOTOS_TABLE", "photos-test")


@pytest.fixture
def valid_event():
    return {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "user-123",
                        "email_verified": "true",
                    }
                }
            }
        },
        "queryStringParameters": {
            "q": "manual",
            "limit": "20",
        },
    }


class TestSearch:
    def test_search_matches_legacy_rows_without_original_file_name(self, dynamodb_table, mock_env, valid_event):
        now = datetime.now(timezone.utc).isoformat()
        dynamodb_table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-manual-001",
                "ObjectKey": "originals/user-123/photo-manual-001.webp",
                "ContentType": "image/webp",
                "CreatedAt": now,
                "Status": "ACTIVE",
            }
        )

        response = search.handler(valid_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["count"] == 1
        assert body["photos"][0]["photoId"] == "photo-manual-001"
        assert body["photos"][0]["fileName"] == "photo-manual-001.webp"

    def test_search_excludes_pending_items(self, dynamodb_table, mock_env, valid_event):
        now = datetime.now(timezone.utc).isoformat()
        dynamodb_table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "pending-1",
                "OriginalFileName": "IMAG0077.jpg",
                "ObjectKey": "originals/user-123/pending-1.webp",
                "ContentType": "image/jpeg",
                "CreatedAt": now,
                "Status": "PENDING",
            }
        )

        event = valid_event.copy()
        event["queryStringParameters"] = {"q": "imag0077", "limit": "20"}

        response = search.handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["count"] == 0
        assert body["photos"] == []

    def test_search_matches_active_original_filename_case_insensitive(self, dynamodb_table, mock_env, valid_event):
        now = datetime.now(timezone.utc).isoformat()
        dynamodb_table.put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "active-1",
                "OriginalFileName": "IMAG0077.jpg",
                "ObjectKey": "originals/user-123/active-1.webp",
                "ContentType": "image/jpeg",
                "CreatedAt": now,
                "Status": "ACTIVE",
            }
        )

        event = valid_event.copy()
        event["queryStringParameters"] = {"q": "imag0077", "limit": "20"}

        response = search.handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["count"] == 1
        assert body["photos"][0]["photoId"] == "active-1"
        assert body["photos"][0]["fileName"] == "IMAG0077.jpg"
