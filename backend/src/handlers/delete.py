import json
import os
from datetime import datetime, timezone, timedelta

import boto3

dynamodb = boto3.resource("dynamodb")

PHOTOS_TABLE = os.environ["PHOTOS_TABLE"]
DEFAULT_RETENTION_DAYS = 60

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

        photo_id = event.get("pathParameters", {}).get("photoId")
        if not photo_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "photoId is required"})
            }

        table = dynamodb.Table(PHOTOS_TABLE)
        
        # Get the existing photo record to verify ownership
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
        
        # Check if already deleted
        if item.get("DeletedAt"):
            return {
                "statusCode": 409,
                "body": json.dumps({"error": "photo already deleted"})
            }
        
        # Soft delete: set DeletedAt, DeletedBy, and RetentionUntil
        now = datetime.now(timezone.utc)
        retention_until = now + timedelta(days=DEFAULT_RETENTION_DAYS)
        
        table.update_item(
            Key={
                "UserId": user_id,
                "PhotoId": photo_id
            },
            UpdateExpression="SET DeletedAt = :deleted_at, DeletedBy = :deleted_by, RetentionUntil = :retention_until",
            ExpressionAttributeValues={
                ":deleted_at": now.isoformat(),
                ":deleted_by": user_id,
                ":retention_until": retention_until.isoformat()
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "photoId": photo_id,
                "deletedAt": now.isoformat(),
                "retentionUntil": retention_until.isoformat()
            })
        }
    except Exception as error:
        print(f"delete handler error: {error}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "internal server error"})
        }
