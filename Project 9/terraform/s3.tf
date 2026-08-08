# S3 Bucket with intentional security misconfigurations
resource "aws_s3_bucket" "vulnerable_bucket" {
  bucket = "project9-compliance-scan-bucket-test"
  
  # Checkov/tfsec violations:
  # 1. No server-side encryption enabled
  # 2. No public access block resource defined
  # 3. No logging configuration
  # 4. Versioning disabled (default)
}
