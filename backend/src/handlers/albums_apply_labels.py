import json
import os

import boto3

try:
    from handlers.albums_common import extract_user_id, normalize_photo_subjects, utc_now_iso
except ImportError:
    from albums_common import extract_user_id, normalize_photo_subjects, utc_now_iso  # type: ignore


dynamodb = boto3.resource("dynamodb")
ALBUMS_TABLE = os.environ["ALBUMS_TABLE"]
PHOTOS_TABLE = os.environ["PHOTOS_TABLE"]


def handler(event, context):
    try:
        user_id, auth_error = extract_user_id(event)
        if auth_error:
            return auth_error

        path = event.get("pathParameters") or {}
        album_id = (path.get("albumId") or "").strip()
        photo_id = (path.get("photoId") or "").strip()
        if not album_id or not photo_id:
            return {"statusCode": 400, "body": json.dumps({"error": "albumId and photoId are required"})}

        albums_table = dynamodb.Table(ALBUMS_TABLE)
        album = albums_table.get_item(Key={"UserId": user_id, "AlbumId": album_id}).get("Item")
        if not album:
            return {"statusCode": 404, "body": json.dumps({"error": "album not found"})}

        required_labels = [label for label in (album.get("RequiredLabels") or []) if isinstance(label, str)]

        photos_table = dynamodb.Table(PHOTOS_TABLE)
        photo = photos_table.get_item(Key={"UserId": user_id, "PhotoId": photo_id}).get("Item")
        if not photo:
            return {"statusCode": 404, "body": json.dumps({"error": "photo not found"})}

        subjects = normalize_photo_subjects(photo.get("Subjects"))
        subjects_lower = {item.lower() for item in subjects}

        added_labels = []
        for label in required_labels:
            lowered = label.lower().strip()
            if not lowered or lowered in subjects_lower:
                continue
            subjects.append(label)
            subjects_lower.add(lowered)
            added_labels.append(label)

        photos_table.update_item(
            Key={"UserId": user_id, "PhotoId": photo_id},
            UpdateExpression="SET #subjects = :subjects, #updatedAt = :updatedAt",
            ExpressionAttributeNames={"#subjects": "Subjects", "#updatedAt": "UpdatedAt"},
            ExpressionAttributeValues={":subjects": subjects, ":updatedAt": utc_now_iso()},
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "albumId": album_id,
                    "photoId": photo_id,
                    "addedLabels": added_labels,
                    "subjects": subjects,
                }
            ),
        }
    except Exception as error:
        print(f"albums_apply_labels handler error: {error}")
        return {"statusCode": 500, "body": json.dumps({"error": "internal server error"})}
