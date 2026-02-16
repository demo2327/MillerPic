import base64
import json
import os
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")

PHOTOS_TABLE = os.environ["PHOTOS_TABLE"]
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
QUERY_BATCH_SIZE = 100


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
        
        # Validate query parameter
        search_query = query_params.get("q")
        if not search_query or not search_query.strip():
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "query parameter 'q' is required and cannot be empty"})
            }
        
        # Parse and validate limit
        limit = _parse_limit(query_params.get("limit"))
        if limit is None:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "limit must be an integer between 1 and 100"})
            }

        # Parse and validate nextToken
        next_token = query_params.get("nextToken")
        exclusive_start_key = _decode_next_token(next_token)
        if next_token and not exclusive_start_key:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "nextToken is invalid"})
            }

        table = dynamodb.Table(PHOTOS_TABLE)

        # Build filter expression for case-insensitive search on OriginalFileName and Subjects
        # Note: DynamoDB doesn't support case-insensitive search natively, so we query by UserId
        # and filter in the application layer. For better performance, consider using a search
        # service like OpenSearch for production use.
        search_lower = search_query.lower()
        
        photos = []
        last_evaluated_key = exclusive_start_key
        
        # Continue querying until we have enough matching results or run out of items
        while len(photos) < limit:
            query_args = {
                "KeyConditionExpression": Key("UserId").eq(user_id),
                "FilterExpression": Attr("DeletedAt").not_exists(),
                "Limit": QUERY_BATCH_SIZE,
                "ScanIndexForward": False,
            }
            if last_evaluated_key:
                if last_evaluated_key.get("UserId") != user_id:
                    return {
                        "statusCode": 400,
                        "body": json.dumps({"error": "nextToken is invalid"})
                    }
                query_args["ExclusiveStartKey"] = last_evaluated_key

            result = table.query(**query_args)

            items = result.get("Items") or []
            
            for item in items:
                # Filter out pending photos, but include items without Status for backward compatibility
                status = item.get("Status")
                if status and status != "ACTIVE":
                    continue
                
                # Case-insensitive search in OriginalFileName
                file_name = item.get("OriginalFileName", "")
                file_name_match = search_lower in file_name.lower() if file_name else False
                
                # Case-insensitive search in Subjects (list of strings)
                subjects = item.get("Subjects", [])
                subjects_match = False
                if subjects:
                    for subject in subjects:
                        if search_lower in subject.lower():
                            subjects_match = True
                            break
                
                # Skip if no match
                if not file_name_match and not subjects_match:
                    continue
                
                created_at = item.get("CreatedAt")
                if isinstance(created_at, datetime):
                    created_at = created_at.isoformat()

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
                taken_at = item.get("TakenAt")
                
                if description:
                    photo["description"] = description
                if subjects is not None:  # Include empty arrays
                    photo["subjects"] = subjects
                if taken_at:
                    photo["takenAt"] = taken_at
                
                photos.append(photo)
                
                # Stop if we have enough results
                if len(photos) >= limit:
                    break
            
            # Update last evaluated key for next iteration
            last_evaluated_key = result.get("LastEvaluatedKey")
            
            # Break if no more items to query
            if not last_evaluated_key:
                break

        # Handle pagination: only set nextToken if we have more items to query
        new_next_token = None
        if last_evaluated_key and len(photos) >= limit:
            new_next_token = _encode_next_token(last_evaluated_key)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "photos": photos,
                "count": len(photos),
                "nextToken": new_next_token,
            })
        }
    except Exception as error:
        print(f"search handler error: {error}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "internal server error"})
        }
