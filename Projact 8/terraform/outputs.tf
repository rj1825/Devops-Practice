output "vpc_id" {
  value       = aws_vpc.main.id
  description = "The ID of the created VPC"
}

output "eks_cluster_name" {
  value       = aws_eks_cluster.main.name
  description = "The name of the EKS cluster"
}

output "eks_cluster_endpoint" {
  value       = aws_eks_cluster.main.endpoint
  description = "The endpoint for EKS control plane"
}

output "kubeconfig_update_command" {
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
  description = "Command to configure kubectl to point to this EKS cluster"
}
