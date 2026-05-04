import json
import os
from decimal import Decimal

import boto3


TABLE_NAME = os.environ.get("TABLE_NAME", "Expenses")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "OPTIONS,GET",
}


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def lambda_handler(event, context):
    params = event.get("queryStringParameters") or {}
    category_filter = (params.get("category") or "").strip().lower()

    try:
        items = []
        scan_kwargs = {}

        # DynamoDB scan results are paginated, so keep scanning until no key remains.
        while True:
            result = table.scan(**scan_kwargs)
            items.extend(result.get("Items", []))

            last_key = result.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key

        if category_filter:
            items = [
                item
                for item in items
                if str(item.get("category", "")).strip().lower() == category_filter
            ]

        items.sort(key=lambda item: item.get("date", ""), reverse=True)
        return response(200, {"expenses": items})
    except Exception as exc:
        return response(500, {"message": "Could not retrieve expenses.", "error": str(exc)})
