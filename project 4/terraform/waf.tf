# AWS WAFv2 Web ACL for CloudFront Distribution
resource "aws_wafv2_web_acl" "waf" {
  count = var.enable_waf ? 1 : 0

  name        = "${var.project_name}-${var.environment}-waf"
  description = "WAF Web ACL protecting CloudFront static assets CDN"
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # Rule 1: AWS Managed IP Reputation List
  rule {
    name     = "AWS-AWSManagedRulesAmazonIpReputationList"
    priority = 10

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWS-AWSManagedRulesAmazonIpReputationList"
      sampled_requests_enabled   = true
    }
  }

  # Rule 2: AWS Managed Common Rule Set (OWASP Top 10)
  rule {
    name     = "AWS-AWSManagedRulesCommonRuleSet"
    priority = 20

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWS-AWSManagedRulesCommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # Rule 3: Custom IP Rate Limiting Rule
  rule {
    name     = "CustomIPRateLimitRule"
    priority = 30

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.waf_rate_limit_threshold
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CustomIPRateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-${var.environment}-waf-acl"
    sampled_requests_enabled   = true
  }
}
