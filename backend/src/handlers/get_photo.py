import json
import os
from datetime import datetime

import boto3

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

PHOTOS_TABLE = os.environ["PHOTOS_TABLE"]
PHOTO_BUCKET = os.environ["PHOTO_BUCKET"]


def handler(event, context):
    try:
        # Extract JWT claims for authorization
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
        if email_verified is not True:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "email is not verified"})
            }

        # Get photoId from path parameters
        photo_id = event.get("pathParameters", {}).get("photoId")
        if not photo_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "photoId is required"})
            }

        table = dynamodb.Table(PHOTOS_TABLE)
        
        # Get the photo record to verify ownership
        response = table.get_item(
            Key={
                "UserId": user_id,
                "PhotoId": photo_id
            }
        )
        
        item = response.get("Item")
        if not item:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "photo not found"})
            }
        
        # Only return ACTIVE photos (filter out PENDING and DELETED)
        status = item.get("Status")
        if status and status != "ACTIVE":
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "photo not found"})
            }
        
        # Build response with full metadata (same format as list.py)
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
                print(f"get_photo thumbnail URL generation error: {thumbnail_error}")

        return {
            "statusCode": 200,
            "body": json.dumps(photo)
        }
    except Exception as error:
        print(f"get_photo handler error: {error}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "internal server error"})
        }
