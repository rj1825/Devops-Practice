# Project 10: Chaos Engineering & Full-Stack Observability Stack

An enterprise-grade, cost-free local **Resilience & Chaos Engineering sandbox** deployed on **Kubernetes (Minikube)**. This project demonstrates active infrastructure monitoring using **Prometheus & Grafana** and controlled fault-injection validation using **Chaos Mesh**.

---

## 🏗️ Architecture Blueprint

```text
       [ User Browser ] ──► [ Frontend NodePort Service (30080) ]
                                      │
                                      ▼
                             [ Frontend Pods ]
                                      │ (Inject 150ms Network Latency here)
                                      ▼
                           [ Backend Service:8000 ]
                                      │
                                      ▼
       [ Redis Cache ] ◄── [ Backend Pods ] (Annotated for Prometheus)
                                   ▲
                                   │ (Randomly Kill Pods here)
                                   ▼
                         [ Chaos Mesh Engine ]
```

---

## 🛠️ Technology Stack & Tools

*   **Orchestration**: Kubernetes (via Minikube)
*   **IaC / Manifests**: Declarative YAML configuration (Namespace, Deployments, Services)
*   **Observability**: Prometheus Operator & Grafana Dashboard (kube-prometheus-stack Helm Chart)
*   **Fault Injection**: Chaos Mesh Engine (PodChaos & NetworkChaos CRDs)

---

## 🚀 Step-by-Step Setup Guide

### 1. Launch the Local Kubernetes Sandbox
Make sure Docker Desktop (or your local container runtime) is running, then start Minikube:
```bash
minikube start --cpus 4 --memory 8192 --disk-size 20g
```

---

### 2. Deploy the Prometheus & Grafana Monitoring Stack
1. Add the official Prometheus Helm repository:
   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   ```
2. Deploy the stack in a dedicated namespace using our custom values file:
   ```bash
   helm install prometheus-stack prometheus-community/kube-prometheus-stack `
     --namespace monitoring --create-namespace `
     -f k8s/monitoring-values.yaml
   ```

---

### 3. Deploy the Chaos Mesh Controller
1. Add the official Chaos Mesh Helm repository:
   ```bash
   helm repo add chaos-mesh https://charts.chaos-mesh.org
   helm repo update
   ```
2. Install Chaos Mesh:
   ```bash
   helm install chaos-mesh chaos-mesh/chaos-mesh `
     --namespace chaos-mesh --create-namespace `
     --set chaosDaemon.runtime=containerd --set chaosDaemon.socketPath=/var/run/containerd/containerd.sock
   ```
3. Check status to ensure all components are active:
   ```bash
   kubectl get pods -n chaos-mesh
   ```

---

### 4. Deploy the Kanban Microservices Application
Deploy the frontend, backend (with Prometheus scrapers active), and Redis database to the cluster:
```bash
kubectl apply -f k8s/app-deployment.yaml
```
Verify that all application pods are successfully running:
```bash
kubectl get pods -n chaos-testing
```

---

## 🧪 Injecting Chaos & Verifying Observability

### Experiment 1: Pod Kill Chaos (Automated Self-Healing)
Verify how Kubernetes maintains system uptime when instances are actively killed:
1. Open a terminal window and watch your pods live:
   ```bash
   kubectl get pods -n chaos-testing -w
   ```
2. In another terminal window, apply the pod-kill experiment:
   ```bash
   kubectl apply -f chaos/pod-kill-experiment.yaml
   ```
3. **Observability Verification**: 
   - You will see Chaos Mesh terminate a random backend pod every 30 seconds.
   - Watch the Kubernetes ReplicaSet controller immediately launch a brand new pod to restore the count to 3. Uptime is preserved!

---

### Experiment 2: Network Latency Injection (Performance Degradation)
Simulate network degradation (e.g., packet delays or zone lag) and watch the alerts trigger:
1. Apply the network latency manifest:
   ```bash
   kubectl apply -f chaos/network-latency-experiment.yaml
   ```
2. Open Grafana and Alertmanager to watch the metrics:
   - **Access Grafana**:
     ```bash
     minikube service prometheus-stack-grafana -n monitoring
     ```
     *Username: `admin` | Password: `admin` (configured in values.yaml)*
   - **Access Alertmanager**:
     ```bash
     minikube service prometheus-stack-kube-prom-alertmanager -n monitoring
     ```
3. **Observability Verification**:
   - In Grafana, search for **Kubernetes / Pod / Networking** or create a custom chart queries for HTTP latency.
   - You will see latency rise by exactly 150ms.
   - Once the high-latency threshold is crossed, Prometheus fires an alert, which will show up as active inside the Alertmanager dashboard!

---

## 🧹 Cleanup
To clean up your local cluster and reclaim system resources:
```bash
kubectl delete -f chaos/pod-kill-experiment.yaml
kubectl delete -f chaos/network-latency-experiment.yaml
kubectl delete -f k8s/app-deployment.yaml
helm uninstall prometheus-stack -n monitoring
helm uninstall chaos-mesh -n chaos-mesh
minikube stop
```
