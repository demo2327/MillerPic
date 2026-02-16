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

        photo_id = event.get("pathParameters", {}).get("photoId")
        if not photo_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "photoId is required"})
            }

        table = dynamodb.Table(PHOTOS_TABLE)
        
        # Get the existing photo record to verify ownership and deletion state
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
        
        # Check if the photo is in deleted state
        if not item.get("DeletedAt"):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "photo must be soft deleted before hard delete"})
            }
        
        object_key = item.get("ObjectKey")
        
        # Delete from S3 if object key exists
        if object_key:
            try:
                s3.delete_object(Bucket=PHOTO_BUCKET, Key=object_key)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                # Continue even if object not found in S3 - cleanup metadata
                if error_code != "404" and error_code != "NoSuchKey":
                    raise
        
        # Delete from DynamoDB
        table.delete_item(
            Key={
                "UserId": user_id,
                "PhotoId": photo_id
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "photoId": photo_id,
                "message": "photo permanently deleted"
            })
        }
    except Exception as error:
        print(f"hard delete handler error: {error}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "internal server error"})
        }
