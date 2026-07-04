output "s3_bucket_name" {
  value       = aws_s3_bucket.assets.id
  description = "The name of the S3 bucket where static assets should be uploaded."
}

output "s3_bucket_arn" {
  value       = aws_s3_bucket.assets.arn
  description = "The ARN of the S3 bucket."
}

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.cdn.domain_name
  description = "The default URL of the CloudFront distribution (e.g., d111111abcdef8.cloudfront.net)."
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.cdn.id
  description = "The ID of the CloudFront distribution (needed for cache invalidation)."
}

output "cloudfront_arn" {
  value       = aws_cloudfront_distribution.cdn.arn
  description = "The ARN of the CloudFront distribution."
}

output "custom_domain_url" {
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "N/A (No custom domain configured)"
  description = "The custom domain URL for the static assets CDN."
}

output "waf_web_acl_arn" {
  value       = var.enable_waf ? aws_wafv2_web_acl.waf[0].arn : "N/A (WAF Disabled)"
  description = "The ARN of the WAF Web ACL protecting the CloudFront distribution."
}
