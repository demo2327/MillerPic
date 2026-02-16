import json
import os
from datetime import datetime

import boto3

dynamodb = boto3.resource("dynamodb")

PHOTOS_TABLE = os.environ["PHOTOS_TABLE"]
MAX_SUBJECTS = 50
MAX_DESCRIPTION_LENGTH = 1000
MAX_FILENAME_LENGTH = 255


def _sanitize_subjects(subjects):
    """Sanitize subjects list: trim, dedupe, limit count."""
    if not isinstance(subjects, list):
        return None
    
    # Trim and filter empty strings
    trimmed = []
    for s in subjects:
        if not isinstance(s, str):
            return None
        cleaned = s.strip()
        if cleaned:
            trimmed.append(cleaned)
    
    # Remove duplicates while preserving order
    seen = set()
    deduplicated = []
    for item in trimmed:
        if item not in seen:
            seen.add(item)
            deduplicated.append(item)
    
    # Limit count
    if len(deduplicated) > MAX_SUBJECTS:
        deduplicated = deduplicated[:MAX_SUBJECTS]
    
    return deduplicated


def _validate_iso_date(date_str):
    """Validate ISO 8601 datetime string."""
    if not isinstance(date_str, str):
        return False
    try:
        datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError):
        return False


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
        if email_verified != True:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "email is not verified"})
            }

        # Get photoId from path parameters
        path_params = event.get("pathParameters") or {}
        photo_id = path_params.get("photoId")

        if not photo_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "photoId is required"})
            }

        # Parse request body
        body = json.loads(event.get("body") or "{}")
        
        # Extract allowed fields
        file_name = body.get("fileName")
        description = body.get("description")
        subjects = body.get("subjects")
        taken_at = body.get("takenAt")

        # Validate at least one field is provided
        if file_name is None and description is None and subjects is None and taken_at is None:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "at least one field must be provided"})
            }

        # Build update expression
        update_parts = []
        expr_names = {}
        expr_values = {}
        
        # Validate and add fileName
        if file_name is not None:
            if not isinstance(file_name, str):
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "fileName must be a string"})
                }
            file_name = file_name.strip()
            if not file_name:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "fileName cannot be empty"})
                }
            if len(file_name) > MAX_FILENAME_LENGTH:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": f"fileName exceeds maximum length of {MAX_FILENAME_LENGTH}"})
                }
            update_parts.append("#fileName = :fileName")
            expr_names["#fileName"] = "FileName"
            expr_values[":fileName"] = file_name

        # Validate and add description
        if description is not None:
            if not isinstance(description, str):
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "description must be a string"})
                }
            description = description.strip()
            if not description:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "description cannot be empty"})
                }
            if len(description) > MAX_DESCRIPTION_LENGTH:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": f"description exceeds maximum length of {MAX_DESCRIPTION_LENGTH}"})
                }
            update_parts.append("#description = :description")
            expr_names["#description"] = "Description"
            expr_values[":description"] = description

        # Validate and add subjects
        if subjects is not None:
            sanitized_subjects = _sanitize_subjects(subjects)
            if sanitized_subjects is None:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "subjects must be an array of strings"})
                }
            if sanitized_subjects:
                update_parts.append("#subjects = :subjects")
                expr_names["#subjects"] = "Subjects"
                expr_values[":subjects"] = sanitized_subjects

        # Validate and add takenAt
        if taken_at is not None:
            if not _validate_iso_date(taken_at):
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "takenAt must be a valid ISO 8601 datetime string"})
                }
            update_parts.append("#takenAt = :takenAt")
            expr_names["#takenAt"] = "TakenAt"
            expr_values[":takenAt"] = taken_at

        # Check if any updates to perform
        if not update_parts:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "no valid fields to update"})
            }

        # Update the photo metadata with ownership check
        table = dynamodb.Table(PHOTOS_TABLE)
        
        try:
            # Use ConditionExpression to ensure the photo belongs to the user
            response = table.update_item(
                Key={
                    "UserId": user_id,
                    "PhotoId": photo_id
                },
                UpdateExpression="SET " + ", ".join(update_parts),
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
                ConditionExpression="attribute_exists(UserId)",
                ReturnValues="ALL_NEW"
            )
            
            updated_item = response.get("Attributes", {})
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "photoId": photo_id,
                    "fileName": updated_item.get("FileName"),
                    "description": updated_item.get("Description"),
                    "subjects": updated_item.get("Subjects"),
                    "takenAt": updated_item.get("TakenAt")
                })
            }
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "photo not found"})
            }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "invalid JSON in request body"})
        }
    except Exception as error:
        print(f"patch_photo handler error: {error}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "internal server error"})
        }
