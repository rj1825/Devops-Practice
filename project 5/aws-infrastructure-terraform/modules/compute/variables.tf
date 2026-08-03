variable "vpc_id" {
  type        = string
  description = "The ID of the VPC"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "List of public subnet IDs for the ALB"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs for application EC2 instances"
}

variable "alb_sg_id" {
  type        = string
  description = "Security Group ID for the ALB"
}

variable "app_sg_id" {
  type        = string
  description = "Security Group ID for the application EC2 instances"
}

variable "environment" {
  type        = string
  description = "Deployment environment name (e.g., dev, prod)"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  default     = "t3.micro"
}
