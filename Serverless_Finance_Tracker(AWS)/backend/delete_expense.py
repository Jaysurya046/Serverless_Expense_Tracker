import json
import os

import boto3
from botocore.exceptions import ClientError


TABLE_NAME = os.environ.get("TABLE_NAME", "Expenses")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "OPTIONS,DELETE",
}


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    expense_id = (event.get("pathParameters") or {}).get("id")

    if not expense_id:
        return response(400, {"message": "Expense id is required."})

    try:
        table.delete_item(
            Key={"expenseId": expense_id},
            ConditionExpression="attribute_exists(expenseId)",
        )
        return response(200, {"message": "Expense deleted successfully."})
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return response(404, {"message": "Expense not found."})
        return response(500, {"message": "Could not delete expense.", "error": str(exc)})
    except Exception as exc:
        return response(500, {"message": "Could not delete expense.", "error": str(exc)})
