variable "instance_name" {
  type        = string
  description = "The name tag of the EC2 instance"
}

variable "instance_type" {
  type        = string
  description = "The EC2 instance type (e.g. t3.micro)"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
}

provider "aws" {
  region = "us-east-1"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_instance" "vm" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  tags = {
    Name        = var.instance_name
    Environment = var.environment
    Provisioned = "IDP-Self-Service"
  }
}
