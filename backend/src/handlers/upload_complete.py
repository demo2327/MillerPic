import json
import os
from io import BytesIO

import boto3
from botocore.exceptions import ClientError

try:
    from PIL import Image
except Exception:
    Image = None

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

PHOTO_BUCKET = os.environ["PHOTO_BUCKET"]
PHOTOS_TABLE = os.environ["PHOTOS_TABLE"]
THUMBNAIL_MAX_SIZE = int(os.environ.get("THUMBNAIL_MAX_SIZE", "320"))


def _build_thumbnail_key(user_id, photo_id):
    return f"thumbnails/{user_id}/{photo_id}.webp"


def _create_thumbnail_bytes(source_bytes):
    if Image is None:
        return None

    with Image.open(BytesIO(source_bytes)) as image:
        normalized = image.convert("RGB")
        normalized.thumbnail((THUMBNAIL_MAX_SIZE, THUMBNAIL_MAX_SIZE))
        output = BytesIO()
        normalized.save(output, format="WEBP", quality=80)
        return output.getvalue()


def _try_generate_thumbnail(user_id, photo_id, object_key, content_type):
    content_type_normalized = (content_type or "").lower()
    if not content_type_normalized.startswith("image/"):
        return None

    source_object = s3.get_object(Bucket=PHOTO_BUCKET, Key=object_key)
    source_bytes = source_object.get("Body").read()
    thumbnail_bytes = _create_thumbnail_bytes(source_bytes)
    if not thumbnail_bytes:
        return None

    thumbnail_key = _build_thumbnail_key(user_id, photo_id)
    s3.put_object(
        Bucket=PHOTO_BUCKET,
        Key=thumbnail_key,
        Body=thumbnail_bytes,
        ContentType="image/webp",
        CacheControl="public, max-age=31536000",
    )
    return thumbnail_key

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
        
        thumbnail_key = None
        try:
            thumbnail_key = _try_generate_thumbnail(
                user_id=user_id,
                photo_id=photo_id,
                object_key=object_key,
                content_type=item.get("ContentType"),
            )
        except Exception as thumbnail_error:
            print(f"upload-complete thumbnail generation skipped: {thumbnail_error}")

        update_expression = "SET #status = :active"
        expression_attribute_names = {
            "#status": "Status",
        }
        expression_attribute_values = {
            ":active": "ACTIVE",
        }

        if thumbnail_key:
            update_expression += ", #thumbnailKey = :thumbnailKey"
            expression_attribute_names["#thumbnailKey"] = "ThumbnailKey"
            expression_attribute_values[":thumbnailKey"] = thumbnail_key

        table.update_item(
            Key={
                "UserId": user_id,
                "PhotoId": photo_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "photoId": photo_id,
                "status": "ACTIVE",
                "thumbnailKey": thumbnail_key,
            })
        }
    except Exception as error:
        print(f"upload-complete handler error: {error}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "internal server error"})
        }
