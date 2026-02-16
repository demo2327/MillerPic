import json
import os
from datetime import datetime, timezone

import boto3

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

PHOTO_BUCKET = os.environ["PHOTO_BUCKET"]
PHOTOS_TABLE = os.environ["PHOTOS_TABLE"]

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

        if not photo_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "photoId is required"})
            }

        object_key = f"originals/{user_id}/{photo_id}.webp"

        table = dynamodb.Table(PHOTOS_TABLE)
        table.put_item(
            Item={
                "UserId": user_id,
                "PhotoId": photo_id,
                "ObjectKey": object_key,
                "ContentType": content_type,
                "CreatedAt": datetime.now(timezone.utc).isoformat()
            }
        )

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
