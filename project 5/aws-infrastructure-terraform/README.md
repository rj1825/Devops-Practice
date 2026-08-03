# Production-Grade Multi-Tier AWS Infrastructure via Terraform

[![Terraform](https://img.shields.io/badge/Terraform-%235C4EE5.svg?style=flat&logo=terraform&logoColor=white)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=flat&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-ready, modular, and secure multi-tier infrastructure deployed on AWS using Terraform. This repository demonstrates infrastructure automation best practices, focusing on modular design, separation of environments, strict security principles, and remote state management.

## 🏗️ Architecture Overview

This project provisions a highly available, secure multi-tier network architecture spanning multiple Availability Zones (AZs). 


![Architecture Diagram]([diagram link](https://app.diagrams.net/#G1bwZkYOT2SnAgqPs-9UDJfx5z_rvqWnc8#%7B%22pageId%22%3A%22r3wQHY7XBgxDhBP5ijPV%22%7D))

### Core Components Provisioned:
*   **Networking (VPC Module):** Custom VPC with highly available Public, Private (Application), and Isolated (Database) subnets distributed across 2+ Availability Zones. Features NAT Gateways for secure private internet egress.
*   **Compute & Scaling:** Auto Scaling Groups (ASG) integrated with an Application Load Balancer (ALB) to route traffic, ensuring automated scale-up/scale-down capabilities.
*   **Database Tier (RDS Module):** Multi-AZ Amazon RDS instances tucked securely inside isolated database subnets, restricted by strict security group ingress rules.
*   **Security & Identity:** IAM Roles enforced with the Principle of Least Privilege, AWS Key Management Service (KMS) for data encryption at rest, and zero wide-open (`0.0.0.0/0`) ingress security groups.

---

## 🛠️ Repository Structure

This repository adheres to a modular, reusable pattern separating core infrastructure logic from environment runtime configurations.

```text
aws-infrastructure-terraform/
├── modules/                  # Reusable, standalone infrastructure blueprints
│   ├── vpc/                  # Core networking logic (Subnets, IGW, NAT, Routes)
│   ├── security_groups/      # Consolidated firewall rules 
│   ├── compute/              # ALB, Auto Scaling Groups, EC2 setups
│   └── rds/                  # Multi-AZ database topology
└── environments/             # Live environment environments (decoupled states)
    └── dev/                  # Development sandbox config
        ├── backend.tf        # S3 Remote State configuration with DynamoDB locking
        ├── main.tf           # Instantiates and wires modules together
        ├── outputs.tf        # Root level outputs
        ├── variables.tf      # Dynamic configuration inputs
        └── terraform.tfvars  # Environment-specific values (e.g. Instance classes, CIDRs)