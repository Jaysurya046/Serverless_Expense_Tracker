import json
import os
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

import boto3


TABLE_NAME = os.environ.get("TABLE_NAME", "Expenses")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "OPTIONS,POST",
}


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"message": "Request body must be valid JSON."})

    amount = body.get("amount")
    category = str(body.get("category", "")).strip()
    note = str(body.get("note", "")).strip()
    expense_date = str(body.get("date") or date.today().isoformat()).strip()

    if amount in (None, ""):
        return response(400, {"message": "Amount is required."})

    try:
        amount_decimal = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        return response(400, {"message": "Amount must be a valid number."})

    if amount_decimal <= 0:
        return response(400, {"message": "Amount must be greater than zero."})

    if not category:
        return response(400, {"message": "Category is required."})

    try:
        datetime.strptime(expense_date, "%Y-%m-%d")
    except ValueError:
        return response(400, {"message": "Date must use YYYY-MM-DD format."})

    expense = {
        "expenseId": str(uuid.uuid4()),
        "amount": amount_decimal,
        "category": category,
        "note": note,
        "date": expense_date,
        "createdAt": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
    }

    try:
        table.put_item(Item=expense)
    except Exception as exc:
        return response(500, {"message": "Could not save expense.", "error": str(exc)})

    expense["amount"] = float(expense["amount"])
    return response(201, {"message": "Expense added successfully.", "expense": expense})
