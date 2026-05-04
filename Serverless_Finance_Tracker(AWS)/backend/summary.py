import json
import os
from collections import defaultdict
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
    try:
        totals = defaultdict(Decimal)
        scan_kwargs = {}

        # DynamoDB scan results are paginated, so keep scanning until no key remains.
        while True:
            result = table.scan(**scan_kwargs)
            for item in result.get("Items", []):
                expense_date = str(item.get("date", ""))
                amount = item.get("amount", Decimal("0"))
                if len(expense_date) >= 7:
                    month = expense_date[:7]
                    totals[month] += Decimal(str(amount))

            last_key = result.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key

        summary = [
            {"month": month, "total": total}
            for month, total in sorted(totals.items())
        ]

        return response(200, {"summary": summary})
    except Exception as exc:
        return response(500, {"message": "Could not build summary.", "error": str(exc)})
