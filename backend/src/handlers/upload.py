import json
import os
import re
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Attr

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

PHOTO_BUCKET = os.environ["PHOTO_BUCKET"]
PHOTOS_TABLE = os.environ["PHOTOS_TABLE"]
MAX_SUBJECTS = 50
CONTENT_HASH_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")


def _sanitize_subjects(subjects):
    if subjects is None:
        return None
    if not isinstance(subjects, list):
        return None

    trimmed = []
    for value in subjects:
        if not isinstance(value, str):
            return None
        cleaned = value.strip()
        if cleaned:
            trimmed.append(cleaned)

    seen = set()
    deduped = []
    for item in trimmed:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(item)

    if len(deduped) > MAX_SUBJECTS:
        deduped = deduped[:MAX_SUBJECTS]

    return deduped


def _sanitize_content_hash(content_hash):
    if content_hash is None:
        return None
    if not isinstance(content_hash, str):
        return None

    normalized = content_hash.strip().lower()
    if not CONTENT_HASH_PATTERN.match(normalized):
        return None
    return normalized

def handler(event, context):
    try:
        claims = (((event.get("requestContext") or {}).get("authorizer") or {}).get("jwt") or {}).get("claims") or {}
        user_id = claims.get("sub")

        if not user_id:
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "missing or invalid JWT subject claim"})
            }

        email_verified = claims.get("email_verified")
        if isinstance(email_verified, str):
            email_verified = email_verified.lower() == "true"
        if email_verified is False:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "email is not verified"})
            }

        body = json.loads(event.get("body") or "{}")
        photo_id = body.get("photoId")
        content_type = body.get("contentType", "image/webp")
        original_file_name = body.get("originalFileName")
        subjects = _sanitize_subjects(body.get("subjects"))
        content_hash = _sanitize_content_hash(body.get("contentHash"))

        if body.get("subjects") is not None and subjects is None:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "subjects must be an array of strings"})
            }

        if body.get("contentHash") is not None and content_hash is None:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "contentHash must be a 64-character hex SHA-256 string"})
            }

        if original_file_name:
            original_file_name = os.path.basename(str(original_file_name))[:255]

        if not photo_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "photoId is required"})
            }

        table = dynamodb.Table(PHOTOS_TABLE)
        dedupe_source = None
        if content_hash:
            dedupe_result = table.scan(
                FilterExpression=Attr("ContentHash").eq(content_hash) & Attr("Status").eq("ACTIVE"),
                ProjectionExpression="UserId, PhotoId, ObjectKey",
                Limit=1,
            )
            dedupe_items = dedupe_result.get("Items") or []
            if dedupe_items:
                dedupe_source = dedupe_items[0]

        object_key = dedupe_source.get("ObjectKey") if dedupe_source else f"originals/{user_id}/{photo_id}.webp"

        status = "ACTIVE" if dedupe_source else "PENDING"
        item = {
            "UserId": user_id,
            "PhotoId": photo_id,
            "ObjectKey": object_key,
            "ContentType": content_type,
            "OriginalFileName": original_file_name,
            "CreatedAt": datetime.now(timezone.utc).isoformat(),
            "Status": status
        }
        if subjects is not None:
            item["Subjects"] = subjects
        if content_hash is not None:
            item["ContentHash"] = content_hash
        if dedupe_source:
            item["DeduplicatedFromPhotoId"] = dedupe_source.get("PhotoId")
            item["DeduplicatedFromUserId"] = dedupe_source.get("UserId")

        table.put_item(Item=item)

        if dedupe_source:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "uploadRequired": False,
                    "deduplicated": True,
                    "objectKey": object_key,
                    "linkedToPhotoId": dedupe_source.get("PhotoId"),
                    "linkedToUserId": dedupe_source.get("UserId"),
                })
            }

        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": PHOTO_BUCKET,
                "Key": object_key,
                "ContentType": content_type
            },
            ExpiresIn=900
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "uploadRequired": True,
                "deduplicated": False,
                "uploadUrl": upload_url,
                "objectKey": object_key,
                "expiresInSeconds": 900
            })
        }
    except Exception as error:
        print(f"upload handler error: {error}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "internal server error"})
        }
