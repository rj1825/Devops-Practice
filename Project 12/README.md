# Project 12: Zero-Trust Kubernetes Security & Service Mesh

A hands-on implementation of a **Zero-Trust Kubernetes Security Architecture** deployed on a local cluster. This project demonstrates service-to-service encryption using a **Service Mesh (Linkerd)**, strict traffic segmentation using **Kubernetes NetworkPolicies**, and container hardening enforcement using an **Admission Controller (Kyverno)**.

---

## 🏗️ Architecture Blueprint

```text
                             [ External User Traffic ]
                                         │
                                         ▼ (Exposed via NodePort 32080)
                              [ Frontend App Pods ]
                                         │
                 (mTLS Tunnel)           │ (Only Allowed Connection)
                       │                 ▼
                       └────────► [ Backend App Pods ]
                                         │
                 (mTLS Tunnel)           │ (Only Allowed Connection)
                       │                 ▼
                       └────────► [ Redis Database ]
```

---

## 🔒 Implemented Security Controls

1.  **Mutual TLS (mTLS)**: Enforced via **Linkerd**. Linkerd proxies run as sidecars alongside every pod, intercepting all TCP traffic and transparently encrypting it using mutual TLS.
2.  **Traffic Isolation**: Declared in [`network-policies.yaml`](file:///c:/Users/Anudeep%20Kuncha/OneDrive/Desktop/Projects/Project%2012/k8s/network-policies.yaml). Blocks all traffic in the namespace by default, then selectively permits ONLY the required service flow (Ingress -> Frontend -> Backend -> Redis).
3.  **Pod Admission Guardrails**: Enforced via **Kyverno** in [`kyverno-policies.yaml`](file:///c:/Users/Anudeep%20Kuncha/OneDrive/Desktop/Projects/Project%2012/k8s/kyverno-policies.yaml). Validates configurations at resource creation, blocking any pod that tries to run as root (`runAsNonRoot: false`) or allows privilege escalation.

---

## 🚀 Setup & Deployment Guide

Ensure your local Kubernetes cluster (Docker Desktop or Minikube) is running.

### 1. Install Kyverno (Admission Controller)
Run these commands to deploy Kyverno to your cluster via Helm:
```bash
helm repo add kyverno https://kyverno.github.io/kyverno/
helm repo update
helm install kyverno kyverno/kyverno --namespace kyverno --create-namespace
```
Verify Kyverno pods are running:
```bash
kubectl get pods -n kyverno
```

---

### 2. Install Linkerd Service Mesh
1.  **Download the Linkerd CLI**:
    -   *On Windows (via Winget)*:
        ```bash
        winget install Linkerd.Linkerd
        ```
    -   *On Windows (via PowerShell)*:
        ```powershell
        Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://run.linkerd.io/install-cli.ps1'))
        ```
2.  **Validate EKS/Local Cluster Compatibility**:
    ```bash
    linkerd check --pre
    ```
3.  **Install Linkerd CRDs**:
    ```bash
    linkerd install --crds | kubectl apply -f -
    ```
4.  **Install the Control Plane**:
    ```bash
    linkerd install | kubectl apply -f -
    ```
5.  **Run Final Checks**:
    ```bash
    linkerd check
    ```

---

### 3. Deploy the Hardened Stack
1.  Apply the Kyverno policies to enforce non-root runtime environments:
    ```bash
    kubectl apply -f k8s/kyverno-policies.yaml
    ```
2.  Deploy the frontend, backend, and Redis cache workloads (Linkerd automatically injects proxies into these deployments because the namespace is annotated with `linkerd.io/inject: enabled`):
    ```bash
    kubectl apply -f k8s/app-deployments.yaml
    ```
3.  Lock down the network using our microservice-specific isolation rules:
    ```bash
    kubectl apply -f k8s/network-policies.yaml
    ```

---

## 🧪 Testing and Verifying the Zero-Trust Environment

### Test 1: Verify Kyverno Blocks Privileged Containers (Admission Gate)
Try to deploy a standard alpine container that runs as root:
```bash
kubectl run root-hacker --image=alpine -n secure-zone --overrides='{ "spec": { "containers": [ { "name": "alpine", "image": "alpine", "command": ["sleep", "3600"] } ] } }'
```
👉 **Expected Output**: Kyverno will block the deployment with a policy violation error:
`Error from server (Forbidden): admission webhook "validate.kyverno.svc-fail" denied the request: restrict-root-execution: check-run-as-non-root: SECURITY ERROR: Containers in the 'secure-zone' must run as non-root. Please set securityContext.runAsNonRoot = true.`

---

### Test 2: Verify Network Segmentation (Isolation Gate)
1.  Verify the app works normally at: **[http://localhost:32080](http://localhost:32080)**. (The frontend service can communicate with the backend, which connects to Redis).
2.  Now, try to run a separate container inside the namespace and curl the Redis service directly:
    ```bash
    kubectl run network-tester -n secure-zone --image=curlimages/curl -it --rm --restart=Never --overrides='{ "spec": { "securityContext": { "runAsNonRoot": true, "runAsUser": 1000 } } }' -- sh
    ```
3.  Inside the container shell, try to query the backend or redis service:
    ```bash
    curl http://redis-service:6379 --connect-timeout 5
    ```
    👉 **Expected Output**: The connection will time out. Although the container is in the same namespace, our `network-policies.yaml` blocks all direct traffic to Redis unless it originates from a backend pod!

---

### Test 3: Verify Traffic is Encrypted (mTLS check)
Check if all inter-pod traffic is encrypted:
1.  Install the Linkerd Viz dashboard tool:
    ```bash
    linkerd viz install | kubectl apply -f -
    ```
2.  Open the dashboard:
    ```bash
    linkerd viz dashboard
    ```
3.  Check connection edges:
    - Under the **secure-zone** namespace, verify that the edge lines connecting `frontend -> backend` and `backend -> redis` display the green shield icon, denoting that mutual TLS is active and traffic is fully encrypted.
