import json
import os

import boto3
from botocore.exceptions import ClientError

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

        if not photo_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "photoId is required"})
            }

        table = dynamodb.Table(PHOTOS_TABLE)
        
        # Get the existing photo record to verify ownership and get object key
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
        
        object_key = item.get("ObjectKey")
        if not object_key:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "photo record missing object key"})
            }
        
        # Verify the object exists in S3
        try:
            s3.head_object(Bucket=PHOTO_BUCKET, Key=object_key)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                return {
                    "statusCode": 404,
                    "body": json.dumps({"error": "photo not found in storage"})
                }
            raise
        
        # Update the status to ACTIVE
        table.update_item(
            Key={
                "UserId": user_id,
                "PhotoId": photo_id
            },
            UpdateExpression="SET #status = :active",
            ExpressionAttributeNames={
                "#status": "Status"
            },
            ExpressionAttributeValues={
                ":active": "ACTIVE"
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "photoId": photo_id,
                "status": "ACTIVE"
            })
        }
    except Exception as error:
        print(f"upload-complete handler error: {error}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "internal server error"})
        }
