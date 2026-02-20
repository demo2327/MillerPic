import json
import os
import sys

import boto3
import pytest
from moto import mock_aws

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handlers import upload
from handlers import upload_complete


@pytest.fixture
def aws_resources():
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

        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="photos-test-bucket")

        yield {
            "table": table,
            "s3": s3,
        }


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
        "body": json.dumps(
            {
                "photoId": "photo-123",
                "contentType": "image/webp",
                "originalFileName": "family-photo.webp",
            }
        ),
    }


class TestUpload:
    def test_upload_success(self, aws_resources, valid_event):
        response = upload.handler(valid_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "uploadUrl" in body
        assert body["objectKey"] == "originals/user-123/photo-123.webp"

        item = aws_resources["table"].get_item(Key={"UserId": "user-123", "PhotoId": "photo-123"})["Item"]
        assert item["Status"] == "PENDING"
        assert item["OriginalFileName"] == "family-photo.webp"

    def test_upload_stores_subjects_when_provided(self, aws_resources, valid_event):
        event = dict(valid_event)
        event["body"] = json.dumps(
            {
                "photoId": "photo-subjects",
                "contentType": "image/webp",
                "originalFileName": "trip.webp",
                "subjects": ["folder:Trips", "folder:trips", "date:2024-05-01"],
            }
        )

        response = upload.handler(event, None)

        assert response["statusCode"] == 200
        item = aws_resources["table"].get_item(Key={"UserId": "user-123", "PhotoId": "photo-subjects"})["Item"]
        assert item["Subjects"] == ["folder:Trips", "date:2024-05-01"]

    def test_upload_rejects_invalid_subjects(self, valid_event):
        event = dict(valid_event)
        event["body"] = json.dumps(
            {
                "photoId": "photo-invalid-subjects",
                "contentType": "image/webp",
                "subjects": "not-an-array",
            }
        )

        response = upload.handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "subjects" in body["error"]

    def test_upload_rejects_invalid_content_hash(self, valid_event):
        event = dict(valid_event)
        event["body"] = json.dumps(
            {
                "photoId": "photo-invalid-hash",
                "contentType": "image/webp",
                "contentHash": "not-a-valid-hash",
            }
        )

        response = upload.handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "contentHash" in body["error"]

    def test_upload_deduplicates_by_content_hash(self, aws_resources):
        aws_resources["table"].put_item(
            Item={
                "UserId": "user-source",
                "PhotoId": "photo-source",
                "ObjectKey": "originals/user-source/photo-source.webp",
                "ContentType": "image/webp",
                "OriginalFileName": "source.webp",
                "Status": "ACTIVE",
                "ContentHash": "a" * 64,
            }
        )

        event = {
            "requestContext": {
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "sub": "user-target",
                            "email_verified": "true",
                        }
                    }
                }
            },
            "body": json.dumps(
                {
                    "photoId": "photo-target",
                    "contentType": "image/webp",
                    "originalFileName": "target.webp",
                    "contentHash": "a" * 64,
                }
            ),
        }

        response = upload.handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["uploadRequired"] is False
        assert body["deduplicated"] is True

        target_item = aws_resources["table"].get_item(Key={"UserId": "user-target", "PhotoId": "photo-target"})["Item"]
        assert target_item["Status"] == "ACTIVE"
        assert target_item["ObjectKey"] == "originals/user-source/photo-source.webp"
        assert target_item["DeduplicatedFromPhotoId"] == "photo-source"


class TestUploadCompleteDateLabels:
    def test_upload_complete_adds_date_label_from_metadata(self, aws_resources, monkeypatch):
        aws_resources["table"].put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-date-1",
                "ObjectKey": "originals/user-123/photo-date-1.webp",
                "ContentType": "image/webp",
                "Status": "PENDING",
                "Subjects": ["bob"],
            }
        )
        aws_resources["s3"].put_object(
            Bucket="photos-test-bucket",
            Key="originals/user-123/photo-date-1.webp",
            Body=b"fake-image-bytes",
            ContentType="image/webp",
        )

        monkeypatch.setattr(upload_complete, "_load_source_bytes", lambda _key: b"fake-image-bytes")
        monkeypatch.setattr(upload_complete, "_extract_date_label_from_image", lambda _bytes: "date:2024-04-12")
        monkeypatch.setattr(upload_complete, "_try_generate_thumbnail", lambda **_kwargs: None)

        event = {
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
            "body": json.dumps({"photoId": "photo-date-1"}),
        }

        response = upload_complete.handler(event, None)

        assert response["statusCode"] == 200
        item = aws_resources["table"].get_item(Key={"UserId": "user-123", "PhotoId": "photo-date-1"})["Item"]
        assert item["Status"] == "ACTIVE"
        assert item["Subjects"] == ["bob", "date:2024-04-12"]

    def test_upload_complete_does_not_duplicate_existing_date_label(self, aws_resources, monkeypatch):
        aws_resources["table"].put_item(
            Item={
                "UserId": "user-123",
                "PhotoId": "photo-date-2",
                "ObjectKey": "originals/user-123/photo-date-2.webp",
                "ContentType": "image/webp",
                "Status": "PENDING",
                "Subjects": ["bob", "date:2024-04-12"],
            }
        )
        aws_resources["s3"].put_object(
            Bucket="photos-test-bucket",
            Key="originals/user-123/photo-date-2.webp",
            Body=b"fake-image-bytes",
            ContentType="image/webp",
        )

        monkeypatch.setattr(upload_complete, "_load_source_bytes", lambda _key: b"fake-image-bytes")
        monkeypatch.setattr(upload_complete, "_extract_date_label_from_image", lambda _bytes: "date:2024-04-12")
        monkeypatch.setattr(upload_complete, "_try_generate_thumbnail", lambda **_kwargs: None)

        event = {
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
            "body": json.dumps({"photoId": "photo-date-2"}),
        }

        response = upload_complete.handler(event, None)

        assert response["statusCode"] == 200
        item = aws_resources["table"].get_item(Key={"UserId": "user-123", "PhotoId": "photo-date-2"})["Item"]
        assert item["Status"] == "ACTIVE"
        assert item["Subjects"] == ["bob", "date:2024-04-12"]
