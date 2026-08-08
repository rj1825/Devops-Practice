# Advanced GitOps & Progressive Delivery Pipeline on AWS

This project sets up a modern, enterprise-grade Continuous Integration and Continuous Delivery (CI/CD) system implementing **GitOps** principles. The system automatically deploys a multi-container Kanban application (Frontend, Backend, Redis) onto an **AWS EKS** cluster using **Terraform** for Infrastructure as Code (IaC) and **ArgoCD** for declarative deployment synchronization.

---

## 🏗️ Architecture Overview

The pipeline implements a **pull-based GitOps deployment model**, which eliminates the security risk of exposing your Kubernetes cluster API to external CI runners.

```mermaid
graph TD
    Developer[Developer] -->|Push Code| GitHub[GitHub Repo]
    subgraph CI Pipeline (GitHub Actions)
        Test[Run Unit Tests] --> Build[Build Docker Images]
        Build --> PushECR[Push to Amazon ECR]
        PushECR --> UpdateHelm[Patch values.yaml Image Tags]
        UpdateHelm --> Commit[Commit & Push Tag to Git]
    end
    GitHub -->|Trigger Workflow| Test
    Commit -->|Update Manifest| GitHub
    
    subgraph Target Infrastructure (AWS)
        subgraph EKS Cluster
            ArgoCD[ArgoCD Controller]
            subgraph Kanban Namespace
                Frontend[Frontend Pods]
                Backend[Backend Pods]
                Redis[Redis Cache]
            end
        end
    end
    
    ArgoCD -->|Poll Config & Sync| GitHub
    ArgoCD -->|Apply Manifests| Kanban Namespace
```

### ⚙️ Component Stack
- **Cloud Provider**: Amazon Web Services (AWS)
- **Infrastructure as Code (IaC)**: Terraform / OpenTofu (VPC, Subnets, EKS, IAM Roles, Security Groups)
- **Container Orchestration**: AWS EKS (Elastic Kubernetes Service)
- **CI System**: GitHub Actions (Pytest, Multi-stage Docker builds, ECR push)
- **GitOps CD Controller**: ArgoCD
- **Packaging & Templating**: Helm (Unified chart definition for local/cloud environments)

---

## 🛠️ Infrastructure Configuration (Terraform)

The infrastructure is provisioned dynamically under the [`terraform/`](file:///c:/Users/Anudeep%20Kuncha/OneDrive/Desktop/Projects/Projact%208/terraform) directory:
- [`vpc.tf`](file:///c:/Users/Anudeep%20Kuncha/OneDrive/Desktop/Projects/Projact%208/terraform/vpc.tf): Sets up a custom VPC with 2 public subnets (exposed to the Internet via IGW) and 2 private subnets (internet routing configured via a NAT Gateway for node security). Subnets are correctly tagged for EKS LoadBalancer discoverability.
- [`eks.tf`](file:///c:/Users/Anudeep%20Kuncha/OneDrive/Desktop/Projects/Projact%208/terraform/eks.tf): Provisions the EKS cluster control plane and an EKS-managed Node Group running `t3.medium` instances in the private subnets. Establishes an **OpenID Connect (OIDC) Provider** to enable IAM Roles for Service Accounts (IRSA).

---

## 🚀 Step-by-Step Deployment Guide

### Prerequisites
- AWS CLI installed and configured with Admin permissions.
- Terraform CLI installed.
- kubectl and helm CLIs installed.

### Step 1: Provision AWS Infrastructure
Navigate to the Terraform folder and initialize:
```bash
cd "Projact 8/terraform"
terraform init
terraform plan
terraform apply -auto-approve
```
*Note: This process takes approximately 10-15 minutes.*

Once completed, configure your local `kubectl` to point to the newly created EKS cluster using the output command:
```bash
aws eks update-kubeconfig --region us-east-1 --name kanban-gitops-cluster
```

### Step 2: Install ArgoCD
Install ArgoCD onto the cluster using Helm:
```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd
```

To access the ArgoCD dashboard:
1. Retrieve the admin password:
   * **On Linux / macOS**:
     ```bash
     kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 --decode
     ```
   * **On Windows (PowerShell)**:
     ```powershell
     [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String((kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}")))
     ```
2. Port-forward the API server:
   ```bash
   kubectl port-forward svc/argocd-server -n argocd 8080:443
   ```
3. Open your browser and navigate to `https://localhost:8080`.

### Step 3: Register the GitOps Application
Apply the declarative ArgoCD application configuration:
```bash
kubectl apply -f "Projact 8/argocd/application.yaml"
```
ArgoCD will immediately scan the `Projact 8/helm/kanban-app` path in this Git repository, automatically create the `kanban` namespace, and deploy the Frontend, Backend, and Redis instances.

---

## 🧠 Architectural Decisions & Best Practices (For Recruiters)

- **Pull-Based CD vs. Push-Based**: Standard pipelines run `kubectl apply` from GitHub Actions, requiring AWS credentials to be configured with direct cluster access. This design uses ArgoCD running *inside* the cluster, polling Git for changes. The cluster credentials never leave the AWS boundary.
- **NAT Gateway & Private Nodes**: Nodes are deployed on private subnets, preventing direct exposure to the public internet. Only the ALB (Application Load Balancer) created by the LoadBalancer service is accessible to clients.
- **OIDC Provider Configuration**: Provisioning the OIDC provider allows Kubernetes pods to assume AWS IAM roles directly via ServiceAccounts, avoiding the anti-pattern of sharing EC2 instance profile access keys.
- **GitOps Auto-Healing**: If a cluster administrator manually alters a Kubernetes resource (e.g., changes backend replicas manually), ArgoCD detects the configuration drift and immediately overwrites it to match the source-of-truth defined in Git.

---

## 🧹 Cleanup
To avoid ongoing AWS charges, destroy the resources when finished:
```bash
cd "Projact 8/terraform"
terraform destroy -auto-approve
```
