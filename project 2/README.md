# Project 2: AWS Cost Optimization Automation

A Python-based serverless Lambda automation script using `boto3` to audit and clean up unused cloud assets (idle Elastic IPs, orphaned EBS volumes, old snapshots, and empty load balancers).

---

## Configuration Settings

You can manage the audit settings and toggles inside [config.json](config.json):

* **`dry_run`**: Set to `true` (default) to only scan and report costs. Set to `false` to enable automatic deletion/cleanup of resource waste.
* **`regions`**: List of AWS regions to scan (e.g., `["us-east-1", "us-west-2"]`).
* **`cleanup_settings`**: Toggles to enable/disable specific service sweeps.
* **`rules`**: Threshold age limits (e.g., EBS volume age in available state, snapshot age).

---

## How to Run the Tests

To run the offline test suite simulating active and inactive AWS resources (using the `moto` library):
```bash
cd "project 2"
.\venv\Scripts\python.exe -m pytest
```

---

## How to Run a Dry Run Sweep

To execute the optimizer script locally using your active AWS credentials:
```bash
cd "project 2"
.\venv\Scripts\python.exe lambda_function.py
```

---

## How to Deploy to AWS (AWS SAM)

To deploy the Lambda function, S3 bucket, SNS topic, and EventBridge daily scheduler to your live AWS account:

1. Build the application package:
   ```bash
   sam build
   ```
2. Deploy the CloudFormation stack:
   ```bash
   sam deploy --guided
   ```
