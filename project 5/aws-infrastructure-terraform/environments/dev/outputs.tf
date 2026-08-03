output "alb_dns_name" {
  description = "The public DNS name of the Application Load Balancer"
  value       = module.compute.alb_dns_name
}

output "db_endpoint" {
  description = "The connection endpoint for the RDS instance"
  value       = module.rds.db_instance_endpoint
}
