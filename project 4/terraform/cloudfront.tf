# Security Response Headers Policy
resource "aws_cloudfront_response_headers_policy" "security_headers" {
  name    = "${var.project_name}-${var.environment}-security-headers-${random_string.suffix.result}"
  comment = "Enforces strict security headers on all CDN responses"

  security_headers_config {
    # HTTP Strict Transport Security (HSTS)
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }

    # Content Security Policy (CSP)
    content_security_policy {
      content_security_policy = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'; object-src 'none';"
      override                = true
    }

    # Prevent MIME Sniffing
    content_type_options {
      override = true
    }

    # Frame Options to prevent Clickjacking
    frame_options {
      frame_option = "DENY"
      override     = true
    }

    # Referrer Policy
    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }

    # Cross-site scripting (XSS) protection
    xss_protection {
      mode_block = true
      protection = true
      override   = true
    }
  }

  custom_headers_config {
    items {
      header   = "X-Content-Delivery"
      value    = "AWS-CloudFront"
      override = true
    }
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "cdn" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CDN for ${var.project_name} - ${var.environment}"
  default_root_object = "index.html"

  # Web ACL association (if WAF is enabled)
  web_acl_id = var.enable_waf ? aws_wafv2_web_acl.waf[0].arn : null

  # Alternate domain names (CNAMEs)
  aliases = var.domain_name != "" ? [var.domain_name] : []

  # Origin definition
  origin {
    domain_name              = aws_s3_bucket.assets.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.assets.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
  }

  # Default Cache Behavior
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.assets.id}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    # Managed CachingOptimized Cache Policy ID
    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6"
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id
  }

  # Ordered Cache Behavior for Images (aggressive caching, compression)
  ordered_cache_behavior {
    path_pattern           = "/images/*"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.assets.id}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    # Managed CachingOptimized
    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6"
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id
  }

  # Ordered Cache Behavior for CSS (compressed, long-lived)
  ordered_cache_behavior {
    path_pattern           = "/css/*"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.assets.id}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    # Managed CachingOptimized
    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6"
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id
  }

  # Ordered Cache Behavior for JS (compressed, long-lived)
  ordered_cache_behavior {
    path_pattern           = "/js/*"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.assets.id}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    # Managed CachingOptimized
    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6"
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id
  }

  # Ordered Cache Behavior for PDFs/Docs
  ordered_cache_behavior {
    path_pattern           = "/docs/*"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.assets.id}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = false

    # Managed CachingOptimized
    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6"
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id
  }

  # Price Class (select based on cost / coverage requirements)
  price_class = "PriceClass_100" # US, Canada, Europe. Use PriceClass_All for global edge coverage.

  # Geographic Restriction Config
  restrictions {
    geo_restriction {
      restriction_type = "none" # Set to whitelist/blacklist if geo-blocking is needed
    }
  }

  # SSL/TLS Viewer Certificate configuration
  viewer_certificate {
    # If no custom domain is used, leverage default CloudFront *.cloudfront.net certificate
    cloudfront_default_certificate = var.domain_name == "" ? true : false

    # If custom domain is used, reference custom SSL certificate
    acm_certificate_arn      = var.domain_name != "" ? aws_acm_certificate.cert[0].arn : null
    ssl_support_method       = var.domain_name != "" ? "sni-only" : null
    minimum_protocol_version = var.domain_name != "" ? "TLSv1.2_2021" : null
  }

  # Custom Error Responses (e.g. standard 404 handler)
  custom_error_response {
    error_code            = 404
    response_code         = 404
    response_page_path    = "/index.html" # Can redirect to a custom 404.html if preferred
    error_caching_min_ttl = 10
  }
}
