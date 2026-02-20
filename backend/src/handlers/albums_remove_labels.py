import json
import os

import boto3

try:
    from handlers.albums_common import extract_user_id, normalize_label, normalize_photo_subjects, utc_now_iso
except ImportError:
    from albums_common import extract_user_id, normalize_label, normalize_photo_subjects, utc_now_iso  # type: ignore


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

        body = json.loads(event.get("body") or "{}")
        labels_input = body.get("labels")
        if not isinstance(labels_input, list) or not labels_input:
            return {"statusCode": 400, "body": json.dumps({"error": "labels must be a non-empty array"})}

        normalized_request = []
        for value in labels_input:
            normalized = normalize_label(value)
            if not normalized:
                return {"statusCode": 400, "body": json.dumps({"error": "labels must be non-empty strings"})}
            if normalized not in normalized_request:
                normalized_request.append(normalized)

        albums_table = dynamodb.Table(ALBUMS_TABLE)
        album = albums_table.get_item(Key={"UserId": user_id, "AlbumId": album_id}).get("Item")
        if not album:
            return {"statusCode": 404, "body": json.dumps({"error": "album not found"})}

        album_labels = {
            normalize_label(value)
            for value in (album.get("RequiredLabels") or [])
            if normalize_label(value)
        }

        if not set(normalized_request).issubset(album_labels):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "all requested labels must belong to album requiredLabels"}),
            }

        photos_table = dynamodb.Table(PHOTOS_TABLE)
        photo = photos_table.get_item(Key={"UserId": user_id, "PhotoId": photo_id}).get("Item")
        if not photo:
            return {"statusCode": 404, "body": json.dumps({"error": "photo not found"})}

        subjects = normalize_photo_subjects(photo.get("Subjects"))
        to_remove = set(normalized_request)

        next_subjects = []
        removed_labels = []
        for subject in subjects:
            lowered = subject.lower()
            if lowered in to_remove:
                removed_labels.append(lowered)
                continue
            next_subjects.append(subject)

        photos_table.update_item(
            Key={"UserId": user_id, "PhotoId": photo_id},
            UpdateExpression="SET #subjects = :subjects, #updatedAt = :updatedAt",
            ExpressionAttributeNames={"#subjects": "Subjects", "#updatedAt": "UpdatedAt"},
            ExpressionAttributeValues={":subjects": next_subjects, ":updatedAt": utc_now_iso()},
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "albumId": album_id,
                    "photoId": photo_id,
                    "removedLabels": sorted(set(removed_labels)),
                    "subjects": next_subjects,
                }
            ),
        }
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "invalid JSON in request body"})}
    except Exception as error:
        print(f"albums_remove_labels handler error: {error}")
        return {"statusCode": 500, "body": json.dumps({"error": "internal server error"})}
