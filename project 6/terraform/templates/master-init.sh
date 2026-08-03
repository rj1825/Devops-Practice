#!/bin/bash
# Log stdout/stderr to a file for debugging
exec > >(tee -i /var/log/k3s-master-setup.log) 2>&1

echo "=== Starting k3s Master & ArgoCD Installation ==="

# Update package repository
apt-get update -y
apt-get install -y curl apt-transport-https ca-certificates gnupg

# Download and install k3s master
# - K3S_TOKEN: the shared secret token to allow agents to join
# - --write-kubeconfig-mode 644: makes /etc/rancher/k3s/k3s.yaml readable by non-root users
export K3S_TOKEN="${k3s_token}"
curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644 --disable traefik --disable metrics-server

# Export kubeconfig path globally for root
echo "export KUBECONFIG=/etc/rancher/k3s/k3s.yaml" >> /etc/environment
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Wait for control plane node to be ready
echo "Waiting for k3s cluster API to be ready..."
until kubectl get nodes; do
  sleep 5
done

echo "=== Installing ArgoCD ==="
# Create namespace
kubectl create namespace argocd

# Apply official ArgoCD installation manifests
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD CRDs and deployments to be ready
echo "Waiting for ArgoCD controller to be established..."
kubectl wait --namespace argocd --for=condition=available --timeout=600s deployment/argocd-repo-server
kubectl wait --namespace argocd --for=condition=available --timeout=600s deployment/argocd-server

# Patch ArgoCD service to LoadBalancer so it is reachable on the VM's public IP
echo "Exposing ArgoCD server via LoadBalancer..."
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

echo "=== Installation Finished ==="
