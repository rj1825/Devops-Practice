variable "vpc_id" {
  type        = string
  description = "The ID of the VPC"
}

variable "database_subnet_ids" {
  type        = list(string)
  description = "List of isolated database subnet IDs"
}

variable "db_security_group_id" {
  type        = string
  description = "Security Group ID allowed to access the database"
}

variable "environment" {
  type        = string
  description = "Deployment environment name (e.g., dev, prod)"
}

variable "db_name" {
  type        = string
  description = "Database name"
  default     = "project5db"
}

variable "db_username" {
  type        = string
  description = "Database administrator username"
}

variable "db_password" {
  type        = string
  description = "Database administrator password"
  sensitive   = true
}

variable "instance_class" {
  type        = string
  description = "RDS DB instance class"
  default     = "db.t4g.micro"
}

variable "allocated_storage" {
  type        = number
  description = "Allocated database storage (in GB)"
  default     = 20
}
