# RDS DB Subnet Group
resource "aws_db_subnet_group" "db_subnet_grp" {
  name       = "${var.environment}-db-subnet-group"
  subnet_ids = var.database_subnet_ids

  tags = {
    Name        = "${var.environment}-db-subnet-group"
    Environment = var.environment
  }
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "db" {
  identifier             = "${var.environment}-postgres-db"
  engine                 = "postgres"
  engine_version         = "15"
  instance_class         = var.instance_class
  allocated_storage      = var.allocated_storage
  max_allocated_storage  = 100
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.db_subnet_grp.name
  vpc_security_group_ids = [var.db_security_group_id]
  
  # For dev environments, we turn off Multi-AZ and skip snapshots to minimize costs and deployment time
  multi_az            = false
  publicly_accessible = false
  skip_final_snapshot = true

  tags = {
    Name        = "${var.environment}-db"
    Environment = var.environment
  }
}
