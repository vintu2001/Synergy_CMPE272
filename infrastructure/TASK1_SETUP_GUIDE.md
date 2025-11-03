# Ticket 1: Project Infrastructure Setup Guide

**Assigned To:** Member 4 (Frontend & DevOps)  
**Estimated Time:** 4-6 hours

## Overview
Set up foundational infrastructure including GitHub repository configuration, AWS resources, and monitoring accounts.

## Tasks Checklist

### 1. GitHub Repository Setup
- [x] Repository created: `Synergy_CMPE272`
- [ ] Main branch protection rules configured
  - Go to: Settings → Branches → Add rule
  - Branch name pattern: `main`
  - Enable:
    - ✅ Require pull request reviews before merging (at least 1 reviewer)
    - ✅ Require status checks to pass
    - ✅ Include administrators

### 2. AWS S3 Bucket Creation
Create an S3 bucket for storing project artifacts (trained models, configuration files).

**Steps:**
1. Log into AWS Console
2. Navigate to S3 service
3. Click "Create bucket"
4. Bucket name: `aam-artifacts-<your-name>` (must be globally unique)
5. Region: `us-west-2` (or your preferred region)
6. Uncheck "Block all public access"
7. Enable versioning (optional but recommended)
8. Click "Create bucket"

**Document the bucket name in:** `backend/.env.example` (update `AWS_S3_BUCKET_NAME`)

### 3. AWS IAM Roles Configuration
Create IAM roles with necessary permissions for services.

**Steps:**
1. Navigate to IAM → Roles → Create role
2. Select "AWS service" → "Lambda"
3. Attach policies:
   - `AmazonS3FullAccess` (or custom policy for specific bucket)
   - `AmazonSQSFullAccess`
   - `AmazonDynamoDBFullAccess`
   - `CloudWatchLogsFullAccess`
4. Role name: `aam-lambda-execution-role`
5. Note the Role ARN for later use

**For Local Development:**
1. Navigate to IAM → Users
2. Create a new user: `aam-developer`
3. Attach policies (same as above) or create custom policy
4. Create access keys
5. Store credentials securely (use AWS Secrets Manager or environment variables)

**Security Note:** Use least privilege principle. Only grant necessary permissions.

### 4. Instana Account Access
Set up shared Instana account for team monitoring.

**Steps:**
1. Sign up at https://www.ibm.com/cloud/instana
2. Create a team account (or use provided credentials)
3. Share account credentials with team (use secure channel)
4. Document access information in shared password manager or secure doc

**Alternative:** If Instana is not available, document this in the setup and use CloudWatch for monitoring.

### 5. Environment Configuration
Update environment variable templates.

**Files to update:**
- `backend/.env.example` - Update with your AWS resource names

**Example .env file:**
```bash
AWS_REGION=us-west-2
AWS_S3_BUCKET_NAME=aam-artifacts-yourname
AWS_SQS_QUEUE_URL=https://sqs.us-west-2.amazonaws.com/.../aam-messages
AWS_DYNAMODB_TABLE_NAME=aam_requests
```

## Verification Checklist
- [ ] Main branch protection enabled
- [ ] S3 bucket created and accessible
- [ ] IAM roles created with appropriate permissions
- [ ] Team has access to Instana (or alternative monitoring)
- [ ] Environment variables documented in `.env.example`
- [ ] Team members have AWS credentials configured locally

## Next Steps
After completing Ticket 1:
- Team members can clone repository and set up local environments
- Proceed with Ticket 2 (Synthetic Message Generator)
- Proceed with Ticket 4 (Message Intake Service)

## Troubleshooting

### GitHub Branch Protection
- If you can't push to main, that's expected - create a feature branch
- Contact repository admin if you need main branch access

### AWS Access Issues
- Verify IAM user has correct permissions
- Check AWS region matches configuration
- Ensure credentials are properly configured (`aws configure`)

### Instana Access
- If Instana is unavailable, focus on CloudWatch setup
- Document this in project notes

## Resources
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)

