import json
import os
import sys
from datetime import datetime, timezone

import boto3
import pytest
from moto import mock_aws

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from handlers import albums_apply_labels, albums_create, albums_list, albums_photos, albums_remove_labels


@pytest.fixture
def aws_resources():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        albums_table = dynamodb.create_table(
            TableName="albums-test",
            KeySchema=[
                {"AttributeName": "UserId", "KeyType": "HASH"},
                {"AttributeName": "AlbumId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "UserId", "AttributeType": "S"},
                {"AttributeName": "AlbumId", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        photos_table = dynamodb.create_table(
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

        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="photos-test-bucket")

        yield {
            "albums": albums_table,
            "photos": photos_table,
        }


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("ALBUMS_TABLE", "albums-test")
    monkeypatch.setenv("PHOTOS_TABLE", "photos-test")
    monkeypatch.setenv("PHOTO_BUCKET", "photos-test-bucket")


@pytest.fixture
def auth_event_base():
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
        }
    }


class TestAlbums:
    def test_create_and_list_album(self, aws_resources, mock_env, auth_event_base):
        create_event = dict(auth_event_base)
        create_event["body"] = json.dumps(
            {
                "name": "Bob 2026",
                "requiredLabels": ["Bob", "2026", "bob"],
            }
        )

        create_response = albums_create.handler(create_event, None)
        assert create_response["statusCode"] == 200
        created = json.loads(create_response["body"])
        assert created["name"] == "Bob 2026"
        assert created["requiredLabels"] == ["bob", "2026"]
        assert created["albumId"]

        list_response = albums_list.handler(auth_event_base, None)
        assert list_response["statusCode"] == 200
        body = json.loads(list_response["body"])
        assert body["count"] == 1
        assert body["albums"][0]["albumId"] == created["albumId"]

    def test_list_album_photos_derives_membership_from_labels(self, aws_resources, mock_env, auth_event_base):
        now = datetime.now(timezone.utc).isoformat()
        aws_resources["albums"].put_item(
            Item={
                "UserId": "user-123",
                "AlbumId": "album-1",
                "Name": "Bob 2026",
                "RequiredLabels": ["bob", "2026"],
                "CreatedAt": now,
                "UpdatedAt": now,
            }
        )
        aws_resources["photos"].put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-match",
                "OriginalFileName": "match.jpg",
                "ObjectKey": "originals/user-123/photo-match.jpg",
                "ContentType": "image/jpeg",
                "Subjects": ["bob", "2026", "vacation"],
                "Status": "ACTIVE",
                "CreatedAt": now,
            }
        )
        aws_resources["photos"].put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-miss",
                "OriginalFileName": "miss.jpg",
                "ObjectKey": "originals/user-123/photo-miss.jpg",
                "ContentType": "image/jpeg",
                "Subjects": ["bob"],
                "Status": "ACTIVE",
                "CreatedAt": now,
            }
        )

        event = dict(auth_event_base)
        event["pathParameters"] = {"albumId": "album-1"}
        response = albums_photos.handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["albumId"] == "album-1"
        assert body["count"] == 1
        assert body["photos"][0]["photoId"] == "photo-match"

    def test_apply_labels_adds_missing_album_labels(self, aws_resources, mock_env, auth_event_base):
        now = datetime.now(timezone.utc).isoformat()
        aws_resources["albums"].put_item(
            Item={
                "UserId": "user-123",
                "AlbumId": "album-1",
                "Name": "Bob 2026",
                "RequiredLabels": ["bob", "2026"],
                "CreatedAt": now,
                "UpdatedAt": now,
            }
        )
        aws_resources["photos"].put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-1",
                "Subjects": ["bob"],
                "Status": "ACTIVE",
                "CreatedAt": now,
            }
        )

        event = dict(auth_event_base)
        event["pathParameters"] = {"albumId": "album-1", "photoId": "photo-1"}
        response = albums_apply_labels.handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["addedLabels"] == ["2026"]
        assert "2026" in [label.lower() for label in body["subjects"]]

    def test_remove_labels_removes_selected_album_labels(self, aws_resources, mock_env, auth_event_base):
        now = datetime.now(timezone.utc).isoformat()
        aws_resources["albums"].put_item(
            Item={
                "UserId": "user-123",
                "AlbumId": "album-1",
                "Name": "Bob 2026",
                "RequiredLabels": ["bob", "2026"],
                "CreatedAt": now,
                "UpdatedAt": now,
            }
        )
        aws_resources["photos"].put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-1",
                "Subjects": ["bob", "2026", "vacation"],
                "Status": "ACTIVE",
                "CreatedAt": now,
            }
        )

        event = dict(auth_event_base)
        event["pathParameters"] = {"albumId": "album-1", "photoId": "photo-1"}
        event["body"] = json.dumps({"labels": ["2026"]})
        response = albums_remove_labels.handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["removedLabels"] == ["2026"]
        assert "2026" not in [label.lower() for label in body["subjects"]]
        assert "vacation" in [label.lower() for label in body["subjects"]]
