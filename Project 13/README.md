# Project 13: Event-Driven Cloud Compliance & Auto-Remediation

An enterprise-grade **Serverless Cloud Security Guardrail** deployed using **Terraform**. This project demonstrates event-driven configuration monitoring and automated self-healing: automatically detecting insecure S3 bucket public access adjustments in real-time and auto-remediating them using **AWS EventBridge, AWS Lambda (Python/Boto3), and IAM Policies**.

---

## 🏗️ Architecture Blueprint

```text
  [ Developer / IAM User ] ──► (Disables Block Public Access) ──► [ S3 Bucket ]
                                                                        │
                                                                        ▼ (PutBucketPublicAccessBlock)
  [ AWS Lambda: Remediator ] ◄── [ EventBridge Event Rule ] ◄──── [ AWS CloudTrail ]
             │
             ├─► (Calls S3 API) ──► Enforces 'Block Public Access' back to TRUE
             │
             └─► Logs simulated Slack webhook notification alert
```

---

## 🔒 Auto-Remediation Logic & Guardrails

*   **Detection**: AWS EventBridge monitors API logs (via CloudTrail) and intercepts `PutBucketPublicAccessBlock` or `DeleteBucketPublicAccessBlock` API calls.
*   **Remediation**: If an API call turns off any public access protection, EventBridge triggers a Python Lambda function. Using the `boto3` library, the Lambda instantly overrides the settings, applying a strict `BlockPublicAccess` configuration (setting all 4 public access blocks to `true`).
*   **Alerting**: The Lambda logs a JSON-formatted payload mimicking a secure Slack notification to alert the security team.

---

## 🚀 Setup & Deployment Guide

Ensure you have your AWS credentials configured locally (`aws configure`).

### 1. Provision the Infrastructure
1. Navigate to the `terraform` directory:
   ```bash
   cd "Project 13/terraform"
   ```
2. Initialize Terraform and download the AWS provider:
   ```bash
   terraform init
   ```
3. Deploy the S3 bucket, Lambda function, IAM roles, and EventBridge rules:
   ```bash
   terraform apply -auto-approve
   ```
   *Take note of the `target_bucket_name` output at the end of the run (e.g. `compliance-test-bucket-xxxxxx`).*

---

## 🧪 Testing the Compliance Guardrail

### Test 1: Direct Lambda Invocation (Fastest Test - 2 Seconds)
Because CloudTrail API delivery to EventBridge can take up to 10 minutes, the Lambda is designed to support direct test payloads for instant validation:

1. **Intentionally break compliance** on your bucket by turning off all Public Access Blocks via the AWS CLI:
   ```bash
   aws s3api put-public-access-block --bucket <your-target-bucket-name> --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
   ```
2. **Verify it is broken**: Go to your S3 Console, check your bucket, and verify that "Block all public access" is **Off**.
3. **Trigger the remediator**: Invoke the Lambda function directly using the AWS CLI:
   ```bash
   aws lambda invoke --function-name idp-s3-compliance-auto-remediator --payload '{"bucket_name": "<your-target-bucket-name>"}' --cli-binary-format raw-in-base64-out response.json
   ```
4. **What to Observe**:
   - Check `response.json`. It will show a `200 Success` status.
   - Run a quick S3 query:
     ```bash
     aws s3api get-public-access-block --bucket <your-target-bucket-name>
     ```
     👉 **Result**: The output will show all blocks are successfully restored to `true`!

---

### Test 2: Checking Auto-Remediation Logs (CloudWatch)
Verify that the Lambda function logged the simulated Slack alert:

1. Retrieve the latest logs from CloudWatch:
   ```bash
   aws logs filter-log-events --log-group-name "/aws/lambda/idp-s3-compliance-auto-remediator" --query "events[].message" --limit 10
   ```
2. **What to Observe**:
   You will see the logged JSON alert notifying you that the security violation was rectified and a Slack notification was generated:
   ```json
   "SIMULATED SECURE SLACK NOTIFICATION: {\"channel\": \"#security-alerts\", \"text\": \"🚨 SECURITY VIOLATION RECTIFIED 🚨...\"}"
   ```

---

## 🧹 Project Teardown
To destroy the S3 bucket, Lambda function, and EventBridge rules to prevent any active charges:
```bash
terraform destroy -auto-approve
```
