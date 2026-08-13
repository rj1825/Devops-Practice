# Query default VPC in the region
data "aws_vpc" "default" {
  default = true
}

# Monitored Security Group acting as our target resource
resource "aws_security_group" "monitored_sg" {
  name        = "compliance-monitored-security-group"
  description = "Hardened security group with auto-drift remediation monitoring"
  vpc_id      = data.aws_vpc.default.id

  # Inbound HTTP Access
  ingress {
    description = "Allow HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Inbound HTTPS Access
  ingress {
    description = "Allow HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound Egress Access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "Compliance-Monitored-Security-Group"
    Environment = "Dev"
    Project     = "Drift-Remediation"
  }
}

output "security_group_id" {
  value       = aws_security_group.monitored_sg.id
  description = "The ID of the security group being monitored for drift compliance"
}
