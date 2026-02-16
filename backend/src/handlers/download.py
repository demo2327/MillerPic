import json
import os

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

        path_parameters = event.get("pathParameters") or {}
        photo_id = path_parameters.get("photoId")

        if not photo_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "photoId path param is required"})
            }

        table = dynamodb.Table(PHOTOS_TABLE)
        result = table.get_item(Key={"UserId": user_id, "PhotoId": photo_id})
        item = result.get("Item")

        if not item:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "photo not found"})
            }
        
        # Check if photo is soft deleted
        if item.get("DeletedAt"):
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "photo not found"})
            }

        download_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": PHOTO_BUCKET,
                "Key": item["ObjectKey"]
            },
            ExpiresIn=3600
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "downloadUrl": download_url,
                "expiresInSeconds": 3600
            })
        }
    except Exception as error:
        print(f"download handler error: {error}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "internal server error"})
        }
