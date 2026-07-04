variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "The AWS Region to deploy resources into. Note: CloudFront Web ACLs and ACM Certificates for CloudFront must be in us-east-1."
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Deployment environment name (e.g., development, staging, production)."
}

variable "project_name" {
  type        = string
  default     = "enterprise-cdn"
  description = "Project name to prefix resources."
}

variable "domain_name" {
  type        = string
  default     = ""
  description = "Custom domain name for the CDN (e.g., assets.mycompany.com). Leave blank to use default CloudFront domain."
}

variable "route53_zone_id" {
  type        = string
  default     = ""
  description = "Route 53 hosted zone ID for the custom domain. Required if domain_name is specified."
}

variable "enable_waf" {
  type        = bool
  default     = true
  description = "Toggle to enable/disable AWS WAF Web ACL association with CloudFront."
}

variable "waf_rate_limit_threshold" {
  type        = number
  default     = 500
  description = "Number of requests allowed from a single IP address in a 5-minute rolling window before rate-limiting triggers."
}

variable "tags" {
  type = map(string)
  default = {
    Project     = "EnterpriseStaticAssetDelivery"
    ManagedBy   = "Terraform"
    Environment = "production"
  }
  description = "Common tags to apply to all taggable resources."
}
