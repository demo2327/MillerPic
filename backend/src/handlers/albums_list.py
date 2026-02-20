import json
import os

import boto3
from boto3.dynamodb.conditions import Key

from handlers.albums_common import album_response, extract_user_id


dynamodb = boto3.resource("dynamodb")
ALBUMS_TABLE = os.environ["ALBUMS_TABLE"]


def handler(event, context):
    try:
        user_id, auth_error = extract_user_id(event)
        if auth_error:
            return auth_error

        table = dynamodb.Table(ALBUMS_TABLE)
        response = table.query(
            KeyConditionExpression=Key("UserId").eq(user_id),
            ScanIndexForward=False,
            Limit=200,
        )

        items = response.get("Items") or []
        albums = [album_response(item) for item in items]

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "albums": albums,
                    "count": len(albums),
                }
            ),
        }
    except Exception as error:
        print(f"albums_list handler error: {error}")
        return {"statusCode": 500, "body": json.dumps({"error": "internal server error"})}
