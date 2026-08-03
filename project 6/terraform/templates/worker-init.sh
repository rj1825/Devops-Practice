#!/bin/bash
# Log stdout/stderr to a file for debugging
exec > >(tee -i /var/log/k3s-worker-setup.log) 2>&1

echo "=== Starting k3s Worker Installation ==="

# Update package repository
apt-get update -y
apt-get install -y curl apt-transport-https ca-certificates gnupg

# Download and install k3s agent
# - K3S_TOKEN: the shared secret token to allow agents to join
# - K3S_URL: the address of the master node control plane API
export K3S_TOKEN="${k3s_token}"
export K3S_URL="https://${master_ip}:6443"

echo "Joining cluster at $K3S_URL..."
curl -sfL https://get.k3s.io | sh -

echo "=== Worker Node Joined Successfully ==="
