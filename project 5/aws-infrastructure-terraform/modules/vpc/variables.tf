variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR block"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "Public Subnets CIDR blocks"
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "Private Subnets CIDR blocks"
  default     = []
}

variable "database_subnet_cidrs" {
  type        = list(string)
  description = "Database Subnets CIDR blocks"
  default     = []
}

variable "availability_zones" {
  type        = list(string)
  description = "List of Availability Zones"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev/prod)"
}

variable "enable_nat_gateway" {
  type        = bool
  description = "Enable NAT Gateway for private subnets (costs apply)"
  default     = false
}