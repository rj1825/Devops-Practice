variable "vpc_id" {
  type        = string
  description = "The ID of the VPC"
}

variable "environment" {
  type        = string
  description = "Deployment environment name (e.g., dev, prod)"
}
