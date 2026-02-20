import json
from datetime import datetime, timezone

MAX_ALBUM_NAME_LENGTH = 120
MAX_REQUIRED_LABELS = 20
MAX_LABEL_LENGTH = 64


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def unauthorized_response():
    return {
        "statusCode": 401,
        "body": json.dumps({"error": "missing or invalid JWT subject claim"}),
    }


def forbidden_response():
    return {
        "statusCode": 403,
        "body": json.dumps({"error": "email is not verified"}),
    }


def extract_user_id(event):
    claims = (((event.get("requestContext") or {}).get("authorizer") or {}).get("jwt") or {}).get("claims") or {}
    user_id = claims.get("sub")
    if not user_id:
        return None, unauthorized_response()

    email_verified = claims.get("email_verified")
    if isinstance(email_verified, str):
        email_verified = email_verified.lower() == "true"
    if email_verified is False:
        return None, forbidden_response()

    return user_id, None


def normalize_label(value):
    if not isinstance(value, str):
        return None
    cleaned = value.strip().lower()
    if not cleaned:
        return None
    if len(cleaned) > MAX_LABEL_LENGTH:
        return None
    return cleaned


def normalize_required_labels(values):
    if not isinstance(values, list):
        return None

    seen = set()
    normalized = []
    for value in values:
        label = normalize_label(value)
        if not label:
            return None
        if label in seen:
            continue
        seen.add(label)
        normalized.append(label)

    if not normalized:
        return None

    if len(normalized) > MAX_REQUIRED_LABELS:
        normalized = normalized[:MAX_REQUIRED_LABELS]

    return normalized


def normalize_photo_subjects(subjects):
    if not isinstance(subjects, list):
        return []

    result = []
    seen = set()
    for value in subjects:
        if not isinstance(value, str):
            continue
        cleaned = value.strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        result.append(cleaned)
    return result


def album_response(item):
    return {
        "albumId": item.get("AlbumId"),
        "name": item.get("Name"),
        "requiredLabels": item.get("RequiredLabels") or [],
        "createdAt": item.get("CreatedAt"),
        "updatedAt": item.get("UpdatedAt"),
    }
