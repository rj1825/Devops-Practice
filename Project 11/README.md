# Project 11: Self-Service Internal Developer Platform (IDP) Portal

An enterprise-grade, local **Platform Engineering Sandbox** that demonstrates developer self-service infrastructure provisioning wrapped in **Policy-as-Code (Guardrails)**. 

Developers can provision S3 and EC2 services via a dark-mode web dashboard. The platform's Node.js backend automatically runs validation rules to block compliance/budget violations, executes Terraform, and streams the live console logs back to the web portal using **Server-Sent Events (SSE)**.

---

## 🏗️ Platform Flow & Architecture

```text
  [ Developer ]
       │
       ▼ (Submits Form)
  [ Glassmorphic Web Portal ] ◄────────────── (Streams Live Terraform Logs)
       │                                                      ▲
       ▼ (POST /api/provision)                                │
  [ Node.js IDP Server ] ──► [ Policy Engine (guardrails.js) ] │
                                       │                      │
                                       ├─► (FAIL) ──► [ Block & Return Error ]
                                       │
                                       └─► (PASS) ──► [ Generate tfvars ]
                                                            │
                                                            ▼
                                                     [ Terraform Executable ]
```

---

## 🛡️ Corporate Guardrails (Policy-as-Code)

To prevent developers from creating massive cloud bills or launching insecure setups, the backend runs validation logic prior to running Terraform:

1.  **S3 Security Gate (Encryption Check)**:
    -   All S3 buckets **must** have server-side encryption enabled.
    -   *If unchecked*: The engine blocks the request immediately with a security policy violation message.
2.  **EC2 Cost Gate (Size Check)**:
    -   Self-service virtual machine sizes are restricted to Free-Tier eligible classes (`t2.micro`, `t2.small`, `t3.micro`, `t3.small`).
    -   *If developer selects `m5.large` or `c5.xlarge`*: The engine blocks the build with a budget limit violation.

---

## 🚀 Local Deployment & Sandbox Guide

### 1. Prerequisite Checks
Ensure you have **Node.js (version 18+)** and the **Terraform CLI** installed on your system:
```bash
node -v
terraform -v
```

---

### 2. Install and Start the Portal
1. Navigate to the project directory:
   ```bash
   cd "Project 11"
   ```
2. Install npm dependencies (Express and CORS):
   ```bash
   npm install
   ```
3. Start the IDP platform server:
   ```bash
   npm start
   ```
   *The server will boot on `http://localhost:8080`.*

---

### 3. Open the Dashboard
Open your web browser and go to:
👉 **[http://localhost:8080](http://localhost:8080)**

---

## 🧪 Testing the Sandboxed Scenarios

### Test 1: Successful S3 Provisioning (Pass-State)
1. Fill out the S3 Bucket form with a unique name (e.g. `dev-my-app-assets-101`).
2. Keep the **"Enable Server-Side Encryption"** checkbox **checked**.
3. Click **"Provision S3 Bucket"**.
4. **What to Observe**: 
   - The Policy Engine validates the request, writes the variables, and triggers `terraform init` and `terraform plan`.
   - The console window will display the real-time, colored streaming logs of Terraform analyzing the workspace.
   - Once complete, the S3 bucket is added to the **Active Services Catalog** at the bottom of the screen!

---

### Test 2: Triggering S3 Security Violation (Fail-State)
1. Fill out the S3 Bucket form.
2. **Uncheck** the **"Enable Server-Side Encryption"** checkbox.
3. Click **"Provision S3 Bucket"**.
4. **What to Observe**:
   - The terminal console instantly logs a red policy violation error:
     `POLICY VIOLATION [Security]: S3 Buckets must have Server-Side Encryption (KMS/AES256) enabled. Unencrypted buckets are prohibited.`
   - No Terraform files are created, and the build process is blocked.

---

### Test 3: Triggering EC2 Cost Violation (Fail-State)
1. Switch to the **EC2 Instance** tab on the form.
2. Select **`m5.large`** or **`c5.xlarge`** under the **"Instance Size"** dropdown.
3. Click **"Provision EC2 VM"**.
4. **What to Observe**:
   - The platform blocks execution immediately, printing:
     `POLICY VIOLATION [Cost Limit]: Instance type 'm5.large' is unauthorized. To prevent unexpected cloud spend, self-service is limited to: [t2.micro, t2.small, t3.micro, t3.small].`
   - The resource is rejected, keeping cloud costs safe.

---

## 🧹 Project Cleanup
The platform backend keeps all dynamic deployment workspaces sandboxed inside the `Project 11/builds/` folder.
*   **To clean a service record and delete its configuration locally**: Click the **Delete** button next to any resource in the **Active Services Catalog** on the dashboard.
