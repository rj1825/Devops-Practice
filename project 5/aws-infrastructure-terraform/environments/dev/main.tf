provider "aws" {
  region = var.aws_region
}

# 1. VPC Module එක Call කිරීම
module "vpc" {
  source                = "../../modules/vpc"
  environment           = "dev"
  vpc_cidr              = "10.0.0.0/16"
  public_subnet_cidrs   = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs  = ["10.0.11.0/24", "10.0.12.0/24"]
  database_subnet_cidrs = ["10.0.21.0/24", "10.0.22.0/24"]
  availability_zones    = ["us-east-1a", "us-east-1b"]
  enable_nat_gateway    = false # Cost savings for dev sandbox
}

# 2. Security Groups Module එක Call කිරීම
module "security_groups" {
  source      = "../../modules/security_groups"
  vpc_id      = module.vpc.vpc_id
  environment = "dev"
}

# 3. Compute Module (ALB & EC2 Auto Scaling Group) එක Call කිරීම
module "compute" {
  source             = "../../modules/compute"
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  alb_sg_id          = module.security_groups.alb_sg_id
  app_sg_id          = module.security_groups.app_sg_id
  environment        = "dev"
}

# 4. RDS/Database Module එක Call කිරීම
module "rds" {
  source               = "../../modules/rds"
  environment          = "dev"
  vpc_id               = module.vpc.vpc_id
  database_subnet_ids  = module.vpc.database_subnet_ids
  db_security_group_id = module.security_groups.db_sg_id
  db_username          = var.db_username
  db_password          = var.db_password
}