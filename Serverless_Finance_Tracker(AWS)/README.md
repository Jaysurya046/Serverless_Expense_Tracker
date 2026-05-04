# serverless finance tracker

A production-ready starter Expense Tracker built with the standard AWS serverless pattern:

- Amazon S3 for static frontend hosting
- Amazon API Gateway REST API for HTTP routes
- AWS Lambda with Python for backend compute
- Amazon DynamoDB for persistent storage

## Project Structure

```text
.
├── backend
│   ├── add_expense.py
│   ├── delete_expense.py
│   ├── get_expenses.py
│   ├── requirements.txt
│   └── summary.py
├── frontend
│   ├── app.js
│   ├── index.html
│   └── style.css
├── template.yaml
└── README.md
```

## API Routes

| Method | Route | Lambda | Description |
| --- | --- | --- | --- |
| POST | `/expense` | `add_expense.py` | Adds an expense and generates `expenseId` |
| GET | `/expenses` | `get_expenses.py` | Returns all expenses |
| GET | `/expenses?category=Food` | `get_expenses.py` | Returns expenses for one category |
| DELETE | `/expense/{id}` | `delete_expense.py` | Deletes an expense |
| GET | `/summary` | `summary.py` | Returns monthly totals grouped by `YYYY-MM` |

## Data Model

DynamoDB table: `Expenses`

Partition key:

- `expenseId` string

Expense item:

```json
{
  "expenseId": "uuid",
  "amount": 45.75,
  "category": "Groceries",
  "note": "Weekly market run",
  "date": "2026-05-04",
  "createdAt": "2026-05-04T12:30:00Z"
}
```

## Prerequisites

Install and configure:

- AWS CLI
- AWS SAM CLI
- Python 3.12
- An AWS account and configured credentials

```bash
aws configure
sam --version
```

## Deploy Backend and Infrastructure

From the project root:

```bash
sam build
sam deploy
```

This repository includes `samconfig.toml` with these defaults:

- Stack name: `serverless-expense-tracker`
- Region: `ap-south-1`
- S3 artifact bucket: automatically managed by SAM with `resolve_s3`
- IAM capabilities: `CAPABILITY_IAM`
- Confirm changes before deploy: enabled

To use another Region:

```bash
sam deploy --region us-east-1
```

After deployment, SAM prints stack outputs. Copy:

- `ApiBaseUrl`
- `FrontendBucketName`
- `FrontendWebsiteUrl`

## Configure and Upload Frontend

Open `frontend/app.js` and replace:

```js
const API_BASE_URL = "REPLACE_WITH_API_GATEWAY_URL";
```

with your deployed API Gateway URL, for example:

```js
const API_BASE_URL = "https://abc123.execute-api.us-east-1.amazonaws.com/Prod";
```

Upload the frontend files to the S3 bucket created by the stack:

```bash
aws s3 sync frontend/ s3://YOUR_FRONTEND_BUCKET_NAME --delete
```

Then open the `FrontendWebsiteUrl` output in a browser.

## Example Requests

Add an expense:

```bash
curl -X POST "$API_BASE_URL/expense" \
  -H "Content-Type: application/json" \
  -d '{"amount": 45.75, "category": "Groceries", "note": "Weekly market run", "date": "2026-05-04"}'
```

Get expenses:

```bash
curl "$API_BASE_URL/expenses"
```

Filter by category:

```bash
curl "$API_BASE_URL/expenses?category=Groceries"
```

Get monthly summary:

```bash
curl "$API_BASE_URL/summary"
```

Delete an expense:

```bash
curl -X DELETE "$API_BASE_URL/expense/YOUR_EXPENSE_ID"
```

## IAM Permissions

SAM creates Lambda execution roles with the DynamoDB permissions declared in `template.yaml`.

Runtime permissions used by the Lambda functions:

- `dynamodb:PutItem`
- `dynamodb:Scan`
- `dynamodb:DeleteItem`
- `dynamodb:DescribeTable`

The deployer identity needs permissions to create and update these services:

- CloudFormation stacks
- IAM roles and policies
- Lambda functions
- API Gateway REST APIs
- DynamoDB tables
- S3 buckets and bucket policies
- CloudWatch Logs

For a managed-policy starter in a demo account, use:

- `AWSCloudFormationFullAccess`
- `IAMFullAccess`
- `AWSLambda_FullAccess`
- `AmazonAPIGatewayAdministrator`
- `AmazonDynamoDBFullAccess`
- `AmazonS3FullAccess`
- `CloudWatchLogsFullAccess`

For production, replace broad deployer policies with least-privilege CI/CD permissions scoped to this stack.

## CORS

CORS is enabled in API Gateway for:

- `GET`
- `POST`
- `DELETE`
- `OPTIONS`

The sample uses `*` for quick demos. For production, restrict `AllowOrigin` in `template.yaml` to your S3 or CloudFront frontend origin.

## Notes

- The frontend uses Chart.js from a CDN.
- DynamoDB uses on-demand billing with `PAY_PER_REQUEST`.
- Lambda reads the DynamoDB table name from the `TABLE_NAME` environment variable.
- This project intentionally avoids server-based frameworks such as Express, Django, or Flask.
