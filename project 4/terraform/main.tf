terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
  # Note: A real production system would store state in a remote backend (e.g. S3 with DynamoDB locking).
  # We leave this commented out as default to run locally out-of-the-box.
  # backend "s3" {
  #   bucket         = "my-company-terraform-state"
  #   key            = "cdn-platform/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-lock-table"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# Generate a random suffix to ensure S3 bucket name global uniqueness
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

locals {
  bucket_name = "${var.project_name}-${var.environment}-${random_string.suffix.result}"
}
