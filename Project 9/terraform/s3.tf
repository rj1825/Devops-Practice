# Hardened, compliant S3 bucket configuration
resource "aws_s3_bucket" "secured_bucket" {
  bucket = "project9-compliance-scan-bucket-test"
}

# 1. Enable Server-Side Encryption (SSE-S3)
resource "aws_s3_bucket_server_side_encryption_configuration" "secured_bucket_sse" {
  bucket = aws_s3_bucket.secured_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# 2. Block all public access at the bucket level
resource "aws_s3_bucket_public_access_block" "secured_bucket_public_access" {
  bucket = aws_s3_bucket.secured_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 3. Enable bucket versioning for backup/restore resilience
resource "aws_s3_bucket_versioning" "secured_bucket_versioning" {
  bucket = aws_s3_bucket.secured_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}
