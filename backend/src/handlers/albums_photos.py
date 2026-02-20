import json
import os
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Attr, Key

try:
    from handlers.albums_common import extract_user_id
except ImportError:
    from albums_common import extract_user_id  # type: ignore


dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

ALBUMS_TABLE = os.environ["ALBUMS_TABLE"]
PHOTOS_TABLE = os.environ["PHOTOS_TABLE"]
PHOTO_BUCKET = os.environ["PHOTO_BUCKET"]


def _normalize_subject_set(subjects):
    if not isinstance(subjects, list):
        return set()
    result = set()
    for value in subjects:
        if isinstance(value, str):
            cleaned = value.strip().lower()
            if cleaned:
                result.add(cleaned)
    return result


def _build_photo_response(item):
    created_at = item.get("CreatedAt")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()

    photo = {
        "photoId": item.get("PhotoId"),
        "fileName": item.get("OriginalFileName") or item.get("PhotoId"),
        "objectKey": item.get("ObjectKey"),
        "contentType": item.get("ContentType"),
        "createdAt": created_at,
        "status": item.get("Status") or "ACTIVE",
        "subjects": item.get("Subjects") or [],
    }

    thumbnail_key = item.get("ThumbnailKey")
    thumbnail_source_key = thumbnail_key
    content_type = str(item.get("ContentType") or "").lower()
    if not thumbnail_source_key and content_type.startswith("image/"):
        thumbnail_source_key = item.get("ObjectKey")

    if thumbnail_key:
        photo["thumbnailKey"] = thumbnail_key

    if thumbnail_source_key:
        try:
            photo["thumbnailUrl"] = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": PHOTO_BUCKET, "Key": thumbnail_source_key},
                ExpiresIn=3600,
            )
        except Exception as thumbnail_error:
            print(f"albums_photos thumbnail URL generation error: {thumbnail_error}")

    return photo


def handler(event, context):
    try:
        user_id, auth_error = extract_user_id(event)
        if auth_error:
            return auth_error

        album_id = ((event.get("pathParameters") or {}).get("albumId") or "").strip()
        if not album_id:
            return {"statusCode": 400, "body": json.dumps({"error": "albumId is required"})}

        albums_table = dynamodb.Table(ALBUMS_TABLE)
        album_result = albums_table.get_item(Key={"UserId": user_id, "AlbumId": album_id})
        album = album_result.get("Item")
        if not album:
            return {"statusCode": 404, "body": json.dumps({"error": "album not found"})}

        required_labels = _normalize_subject_set(album.get("RequiredLabels"))

        photos_table = dynamodb.Table(PHOTOS_TABLE)
        query_result = photos_table.query(
            KeyConditionExpression=Key("UserId").eq(user_id),
            FilterExpression=Attr("DeletedAt").not_exists(),
            ScanIndexForward=False,
            Limit=300,
        )

        photos = []
        for item in query_result.get("Items") or []:
            status = item.get("Status")
            if status and status != "ACTIVE":
                continue

            subject_set = _normalize_subject_set(item.get("Subjects"))
            if not required_labels.issubset(subject_set):
                continue

            photos.append(_build_photo_response(item))

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "albumId": album_id,
                    "requiredLabels": sorted(required_labels),
                    "photos": photos,
                    "count": len(photos),
                }
            ),
        }
    except Exception as error:
        print(f"albums_photos handler error: {error}")
        return {"statusCode": 500, "body": json.dumps({"error": "internal server error"})}
