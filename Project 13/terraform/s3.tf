resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "aws_s3_bucket" "target_bucket" {
  bucket        = "compliance-test-bucket-${random_string.suffix.result}"
  force_destroy = true

  tags = {
    Name        = "Compliance-Monitoring-Target"
    Environment = "Dev"
  }
}

resource "aws_s3_bucket_public_access_block" "target_bucket_block" {
  bucket = aws_s3_bucket.target_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "target_bucket_name" {
  value       = aws_s3_bucket.target_bucket.id
  description = "The name of the S3 bucket created for compliance testing"
}
