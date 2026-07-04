# SSL/TLS Certificate with ACM (AWS Certificate Manager)
# CloudFront requires ACM certificates to be deployed in the us-east-1 region.
resource "aws_acm_certificate" "cert" {
  count = var.domain_name != "" ? 1 : 0

  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# Route 53 Record for DNS Validation of the ACM Certificate
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in(var.domain_name != "" ? aws_acm_certificate.cert[0].domain_validation_options : []) : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.route53_zone_id
}

# Triggers ACM Certificate validation flow using the Route 53 DNS records
resource "aws_acm_certificate_validation" "cert" {
  count = var.domain_name != "" ? 1 : 0

  certificate_arn         = aws_acm_certificate.cert[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# Route 53 Alias Record pointing the Custom Domain to the CloudFront Distribution URL
resource "aws_route53_record" "cdn_alias" {
  count = (var.domain_name != "" && var.route53_zone_id != "") ? 1 : 0

  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.cdn.domain_name
    zone_id                = aws_cloudfront_distribution.cdn.hosted_zone_id
    evaluate_target_health = false
  }
}
