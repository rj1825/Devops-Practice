# S3 Bucket for Static Assets
resource "aws_s3_bucket" "assets" {
  bucket        = local.bucket_name
  force_destroy = true # Convenient for sandbox cleanups; typically false in strict prod environments
}

# Block all public access at the S3 bucket level
resource "aws_s3_bucket_public_access_block" "assets_public_block" {
  bucket = aws_s3_bucket.assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable server-side encryption with AWS managed S3 key
resource "aws_s3_bucket_server_side_encryption_configuration" "assets_encryption" {
  bucket = aws_s3_bucket.assets.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Define Bucket Policy allowing read-only access to CloudFront Origin Access Control (OAC)
resource "aws_s3_bucket_policy" "cloudfront_oac_read" {
  bucket = aws_s3_bucket.assets.id

  # Ensure the policy is only created after public access block settings are in place
  depends_on = [aws_s3_bucket_public_access_block.assets_public_block]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipalReadOnly"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.assets.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.cdn.arn
          }
        }
      }
    ]
  })
}

# CORS configuration to allow cross-origin requests for web assets (e.g. fonts, AJAX)
resource "aws_s3_bucket_cors_configuration" "assets_cors" {
  bucket = aws_s3_bucket.assets.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"] # Adjust to specific domains in strict production setups
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Origin Access Control (OAC) for securing the S3 origin
resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "${var.project_name}-${var.environment}-oac"
  description                       = "OAC for static assets bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}
