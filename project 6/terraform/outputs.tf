output "aws_region" {
  value       = var.aws_region
  description = "The AWS deployment region"
}

output "master_public_ip" {
  value       = aws_instance.master.public_ip
  description = "The public IP address of the k3s Master EC2 instance"
}

output "ecr_registry_url" {
  value       = aws_ecr_repository.ecr.repository_url
  description = "The repository URL for the Amazon ECR registry"
}

output "ecr_name" {
  value       = aws_ecr_repository.ecr.name
  description = "The repository name for Amazon ECR"
}

output "ssh_private_key" {
  value       = tls_private_key.ssh.private_key_pem
  description = "The generated private key for SSH access to EC2 instances"
  sensitive   = true
}

output "k3s_token" {
  value       = random_password.k3s_token.result
  description = "The random cluster join token used for k3s cluster setup"
  sensitive   = true
}
