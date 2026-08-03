variable "aws_region" {
  type        = string
  description = "The AWS region to deploy resources"
  default     = "us-east-1"
}

variable "admin_username" {
  type        = string
  description = "The admin username for all EC2 instances"
  default     = "ubuntu"
}

variable "master_instance_type" {
  type        = string
  description = "The instance type for the k3s Master node"
  default     = "t3.small" # Free Tier eligible on this account (2GB RAM)
}

variable "worker_instance_type" {
  type        = string
  description = "The instance type for the k3s Worker nodes"
  default     = "t3.small" # Free Tier eligible on this account (2GB RAM)
}

variable "ecr_name" {
  type        = string
  description = "The name of the AWS ECR Repository"
  default     = "project6-sample-web-app"
}
