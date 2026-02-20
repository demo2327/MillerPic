import json
import os
import uuid

import boto3

try:
    from handlers.albums_common import (
        MAX_ALBUM_NAME_LENGTH,
        album_response,
        extract_user_id,
        normalize_required_labels,
        utc_now_iso,
    )
except ImportError:
    from albums_common import (  # type: ignore
        MAX_ALBUM_NAME_LENGTH,
        album_response,
        extract_user_id,
        normalize_required_labels,
        utc_now_iso,
    )


dynamodb = boto3.resource("dynamodb")
ALBUMS_TABLE = os.environ["ALBUMS_TABLE"]


def handler(event, context):
    try:
        user_id, auth_error = extract_user_id(event)
        if auth_error:
            return auth_error

        body = json.loads(event.get("body") or "{}")
        name_raw = body.get("name")
        required_labels = normalize_required_labels(body.get("requiredLabels"))

        if not isinstance(name_raw, str):
            return {"statusCode": 400, "body": json.dumps({"error": "name must be a string"})}

        name = name_raw.strip()
        if not name:
            return {"statusCode": 400, "body": json.dumps({"error": "name cannot be empty"})}
        if len(name) > MAX_ALBUM_NAME_LENGTH:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"name exceeds maximum length of {MAX_ALBUM_NAME_LENGTH}"}),
            }

        if required_labels is None:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "requiredLabels must be a non-empty array of strings"}),
            }

        table = dynamodb.Table(ALBUMS_TABLE)
        now = utc_now_iso()
        item = {
            "UserId": user_id,
            "AlbumId": uuid.uuid4().hex,
            "Name": name,
            "RequiredLabels": required_labels,
            "CreatedAt": now,
            "UpdatedAt": now,
        }
        table.put_item(Item=item)

        return {"statusCode": 200, "body": json.dumps(album_response(item))}
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "invalid JSON in request body"})}
    except Exception as error:
        print(f"albums_create handler error: {error}")
        return {"statusCode": 500, "body": json.dumps({"error": "internal server error"})}
