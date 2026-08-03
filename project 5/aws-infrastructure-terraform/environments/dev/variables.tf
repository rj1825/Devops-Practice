variable "aws_region" {
  type        = string
  description = "AWS Region to deploy resources"
  default     = "us-east-1"
}

variable "db_username" {
  type        = string
  description = "Database administrator username"
  default     = "postgresadmin"
}

variable "db_password" {
  type        = string
  description = "Database administrator password"
  sensitive   = true
  default     = "Project5PasswordSecure!"
}