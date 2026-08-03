# Fetch Ubuntu 22.04 LTS AMI (Canonical Owner ID: 099720109477)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Generate secure random token for k3s cluster joining
resource "random_password" "k3s_token" {
  length  = 32
  special = false
}

# Generate an SSH key pair to authenticate access to the EC2 instances
resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Upload SSH public key to AWS Key Pair registry
resource "aws_key_pair" "ssh_key" {
  key_name   = "key-project6-ssh"
  public_key = tls_private_key.ssh.public_key_openssh
}

# EC2 Instance: k3s Master Node (Control Plane)
resource "aws_instance" "master" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.master_instance_type
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.master_sg.id]
  key_name               = aws_key_pair.ssh_key.key_name

  # Enable resource-oriented public DNS routing
  associate_public_ip_address = true

  # Inject cloud-init template for master installation
  user_data = templatefile("${path.module}/templates/master-init.sh", {
    k3s_token = random_password.k3s_token.result
  })

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name = "vm-k3s-master"
    Role = "k3s-master"
  }
}

# EC2 Instances: k3s Worker Nodes (2 instances)
resource "aws_instance" "worker" {
  count                  = 2
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.worker_instance_type
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.worker_sg.id]
  key_name               = aws_key_pair.ssh_key.key_name

  associate_public_ip_address = true

  # Inject cloud-init template for worker agent installation
  user_data = templatefile("${path.module}/templates/worker-init.sh", {
    k3s_token = random_password.k3s_token.result
    master_ip = aws_instance.master.private_ip
  })

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
  }

  depends_on = [aws_instance.master]

  tags = {
    Name = "vm-k3s-worker-${count.index + 1}"
    Role = "k3s-worker"
  }
}
