# AWS Resources Setup

Step-by-step guide to create the AWS pieces this project expects: **DynamoDB**, **SQS**, and **IAM**, based on the code in this repo:

- `backend/app/services/database.py` → uses DynamoDB table **`aam_requests`**
- `backend/app/services/governance.py` → uses DynamoDB table **`aam_governance_logs`**
- `infrastructure/create_governance_table.py` → can create the governance table for you
- `backend/app/services/message_intake.py` → optionally sends to SQS if a queue URL is present
- `backend/.env.example` → shows AWS-related environment variables

--

## 1. Prerequisites

1. AWS account.
2. Permissions to create **DynamoDB**, **SQS**, and **IAM** resources.
3. Region: the repo uses **`us-west-2`** in multiple places. Use that unless you deliberately change it (and if you do, change it everywhere).

---

## 2. Environment Variables

The backend reads these (see `backend/.env.example`):

```env
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

AWS_SQS_QUEUE_URL=your_sqs_queue_url_here
AWS_DYNAMODB_TABLE_NAME=aam_requests
AWS_DYNAMODB_GOVERNANCE_TABLE=aam_governance_logs
