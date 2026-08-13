# Project 14: GitOps Infrastructure Drift Auto-Reconciliation

An advanced cloud infrastructure security controller built using **Terraform (IaC)**, **Python**, and **Shell automation**. This project implements a **GitOps Self-Healing Loop** for cloud resources: automatically scanning deployed AWS configurations, identifying manual edits or security overrides (out-of-band changes), reporting compliance drift, and automatically applying remediation blocks in real-time.

---

## 🏗️ Architecture Blueprint

```text
  [ Git Repository ] ──► (Validates Compliance) ──► [ AWS Security Group ]
                                                            │
                                                            ▼ (Manual Console/CLI Changes)
  [ Drift Healer Controller ] ◄── (Detailed Exitcode Plan) ◄─ [ AWS Config State ]
             │
             ├─► (Detects Drift: Exit Code 2) ──► Executes `terraform apply -auto-approve`
             │
             └─► Overwrites manual changes, restores compliance, and logs Slack Alert
```

---

## 🔒 Self-Healing Logic

*   **Drift Detection**: The Python controller (`drift_healer.py`) runs `terraform plan -detailed-exitcode` in a background subprocess.
    -   `Exit Code 0`: Desired state matches actual cloud state (No drift).
    -   `Exit Code 2`: Actual cloud state has drifted from desired Git configuration.
*   **Auto-Reconciliation**: If a drift condition is caught (Code 2), the controller parses the plan output to list the drifted resources, automatically triggers `terraform apply -auto-approve` to override the insecure changes, and logs a simulated secure Slack alert payload.

---

## 🚀 Setup & Deployment Guide

Ensure you have your AWS credentials configured locally (`aws configure`).

### 1. Provision the Initial Infrastructure
1. Navigate to the `terraform` directory:
   ```bash
   cd "Project 14/terraform"
   ```
2. Initialize Terraform:
   ```bash
   terraform init
   ```
3. Deploy the compliance Security Group:
   ```bash
   terraform apply -auto-approve
   ```
   *Take note of the `security_group_id` output at the end of the run (e.g. `sg-xxxxxxxxxxxxxxxxx`).*

---

## 🧪 Testing Self-Healing & Reconciliation

### Test 1: Verify Initial Compliance
Run the drift healer controller. Since no modifications have been made, it should report success:
```powershell
# Run using the PowerShell helper script
..\scripts\run_drift_check.ps1
```
👉 **Result**: The script will output:
`✅ COMPLIANCE VERIFIED: Desired state matches actual cloud state. No drift detected.`

---

### Test 2: Inject Drift (Manually open port 22 in AWS)
Simulate an operator bypassing GitOps and manually making an insecure configuration change:

1. Open port `22` (SSH) on the Security Group using the AWS CLI:
   ```powershell
   aws ec2 authorize-security-group-ingress --group-id <YOUR_SECURITY_GROUP_ID> --protocol tcp --port 22 --cidr 0.0.0.0/0
   ```
2. Verify that the rule was successfully added:
   ```powershell
   aws ec2 describe-security-groups --group-ids <YOUR_SECURITY_GROUP_ID> --query "SecurityGroups[0].IpPermissions"
   ```
   *You will see port 22 listed in the active ingress permissions.*

---

### Test 3: Trigger the Self-Healing Loop
Run the drift check script again to detect and auto-remediate the drift:
```powershell
..\scripts\run_drift_check.ps1
```
👉 **What to Observe**:
1. The script detects the drift and warns you:
   `🚨 STATE DRIFT DETECTED: Manual out-of-band modifications identified in AWS console!`
2. It parses the changes and lists the exact drift details:
   `Drift Details Identified:`
   `- egress will be destroyed` / `- ingress rule (port 22) will be destroyed`
3. It triggers the self-healing loop:
   `Initiating Self-Healing: Applying Git-declared configurations to overwrite manual changes...`
4. Re-enforces compliance:
   `✅ SELF-HEALING COMPLETE: Infrastructure successfully restored to Git-declared state.`

---

### Test 4: Verify Restoration
Confirm that the manual rule was automatically stripped and the Security Group is compliant:
```powershell
aws ec2 describe-security-groups --group-ids <YOUR_SECURITY_GROUP_ID> --query "SecurityGroups[0].IpPermissions"
```
👉 **Result**: Port 22 is completely gone! Only ports 80 and 443 remain.

---

## 🧹 Project Teardown
To destroy the monitored Security Group:
```bash
terraform destroy -auto-approve
```
