# Secure Security Group restricting port 22 SSH ingress
resource "aws_security_group" "secured_sg" {
  name        = "project9-secured-sg"
  description = "Security group with restricted ingress"
  vpc_id      = "vpc-123456"

  # Resolve Checkov violation: Limit SSH access to a secure private subnet range instead of 0.0.0.0/0
  ingress {
    description = "Allow SSH only from secure admin subnet"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"] 
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
