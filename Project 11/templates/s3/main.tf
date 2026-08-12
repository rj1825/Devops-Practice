variable "bucket_name" {
  type        = string
  description = "The name of the S3 bucket to provision"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
}

variable "encrypted" {
  type        = bool
  description = "Enable AES256 server-side encryption"
  default     = true
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "bucket" {
  bucket = var.bucket_name

  tags = {
    Environment = var.environment
    Provisioned = "IDP-Self-Service"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "encryption" {
  count  = var.encrypted ? 1 : 0
  bucket = aws_s3_bucket.bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
