import base64
import json
import os
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

PHOTOS_TABLE = os.environ["PHOTOS_TABLE"]
PHOTO_BUCKET = os.environ["PHOTO_BUCKET"]
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def _parse_limit(raw_limit):
    if raw_limit is None:
        return DEFAULT_LIMIT
    try:
        value = int(raw_limit)
    except (TypeError, ValueError):
        return None
    if value < 1:
        return None
    return min(value, MAX_LIMIT)


def _decode_next_token(token):
    if not token:
        return None
    try:
        decoded = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        payload = json.loads(decoded)
        if "UserId" not in payload or "PhotoId" not in payload:
            return None
        return payload
    except Exception:
        return None


def _encode_next_token(last_key):
    if not last_key:
        return None
    encoded = base64.urlsafe_b64encode(json.dumps(last_key).encode("utf-8")).decode("utf-8")
    return encoded


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

        query_params = event.get("queryStringParameters") or {}
        limit = _parse_limit(query_params.get("limit"))
        if limit is None:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "limit must be an integer between 1 and 100"})
            }

        next_token = query_params.get("nextToken")
        exclusive_start_key = _decode_next_token(next_token)
        if next_token and not exclusive_start_key:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "nextToken is invalid"})
            }

        table = dynamodb.Table(PHOTOS_TABLE)

        query_args = {
            "KeyConditionExpression": Key("UserId").eq(user_id),
            "FilterExpression": Attr("DeletedAt").not_exists(),
            "Limit": limit,
            "ScanIndexForward": False,
        }
        if exclusive_start_key:
            if exclusive_start_key.get("UserId") != user_id:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "nextToken does not belong to current user"})
                }
            query_args["ExclusiveStartKey"] = exclusive_start_key

        result = table.query(**query_args)

        items = result.get("Items") or []
        photos = []
        for item in items:
            # Filter out pending photos, but include items without Status for backward compatibility
            status = item.get("Status")
            if status and status != "ACTIVE":
                continue
            
            created_at = item.get("CreatedAt")
            if isinstance(created_at, datetime):
                created_at = created_at.isoformat()

            file_name = item.get("OriginalFileName")
            if not file_name:
                object_key = item.get("ObjectKey") or ""
                if object_key:
                    file_name = object_key.rsplit("/", 1)[-1]
                else:
                    file_name = item.get("PhotoId")

            photo = {
                "photoId": item.get("PhotoId"),
                "fileName": file_name,
                "objectKey": item.get("ObjectKey"),
                "contentType": item.get("ContentType"),
                "createdAt": created_at,
                "status": status or "ACTIVE",
            }
            
            # Only include optional metadata fields if they have values
            description = item.get("Description")
            subjects = item.get("Subjects")
            taken_at = item.get("TakenAt")
            
            if description:
                photo["description"] = description
            if subjects is not None:  # Include empty arrays
                photo["subjects"] = subjects
            if taken_at:
                photo["takenAt"] = taken_at

            thumbnail_key = item.get("ThumbnailKey")
            if thumbnail_key:
                photo["thumbnailKey"] = thumbnail_key
                try:
                    photo["thumbnailUrl"] = s3.generate_presigned_url(
                        "get_object",
                        Params={
                            "Bucket": PHOTO_BUCKET,
                            "Key": thumbnail_key,
                        },
                        ExpiresIn=3600,
                    )
                except Exception as thumbnail_error:
                    print(f"list thumbnail URL generation error: {thumbnail_error}")
            
            photos.append(photo)

        new_next_token = _encode_next_token(result.get("LastEvaluatedKey"))

        return {
            "statusCode": 200,
            "body": json.dumps({
                "photos": photos,
                "count": len(photos),
                "nextToken": new_next_token,
            })
        }
    except Exception as error:
        print(f"list handler error: {error}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "internal server error"})
        }
