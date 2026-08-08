# Security Group with open SSH ingress
resource "aws_security_group" "vulnerable_sg" {
  name        = "project9-vulnerable-sg"
  description = "Security group with wide open ingress"
  vpc_id      = "vpc-123456" # placeholder for scanning

  # Checkov/tfsec violation: Ingress from 0.0.0.0/0 on sensitive port 22 (SSH)
  ingress {
    description = "Allow SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
