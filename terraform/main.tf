# Terraform configuration for DockSafe infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC Configuration
resource "aws_vpc" "docksafe_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "docksafe-vpc"
    Environment = var.environment
  }
}

# Internet Gateway
resource "aws_internet_gateway" "docksafe_igw" {
  vpc_id = aws_vpc.docksafe_vpc.id

  tags = {
    Name        = "docksafe-igw"
    Environment = var.environment
  }
}

# Public Subnets
resource "aws_subnet" "public_subnets" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.docksafe_vpc.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "docksafe-public-subnet-${count.index + 1}"
    Environment = var.environment
    Type        = "public"
  }
}

# Private Subnets
resource "aws_subnet" "private_subnets" {
  count = length(var.private_subnet_cidrs)

  vpc_id            = aws_vpc.docksafe_vpc.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name        = "docksafe-private-subnet-${count.index + 1}"
    Environment = var.environment
    Type        = "private"
  }
}

# Route Table for Public Subnets
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.docksafe_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.docksafe_igw.id
  }

  tags = {
    Name        = "docksafe-public-rt"
    Environment = var.environment
  }
}

# Route Table Association for Public Subnets
resource "aws_route_table_association" "public_rta" {
  count = length(aws_subnet.public_subnets)

  subnet_id      = aws_subnet.public_subnets[count.index].id
  route_table_id = aws_route_table.public_rt.id
}

# Security Groups
resource "aws_security_group" "docksafe_alb_sg" {
  name_prefix = "docksafe-alb-"
  vpc_id      = aws_vpc.docksafe_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "docksafe-alb-sg"
    Environment = var.environment
  }
}

resource "aws_security_group" "docksafe_app_sg" {
  name_prefix = "docksafe-app-"
  vpc_id      = aws_vpc.docksafe_vpc.id

  ingress {
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    security_groups = [aws_security_group.docksafe_alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "docksafe-app-sg"
    Environment = var.environment
  }
}

resource "aws_security_group" "docksafe_db_sg" {
  name_prefix = "docksafe-db-"
  vpc_id      = aws_vpc.docksafe_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.docksafe_app_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "docksafe-db-sg"
    Environment = var.environment
  }
}

# RDS Database
resource "aws_db_subnet_group" "docksafe_db_subnet_group" {
  name       = "docksafe-db-subnet-group"
  subnet_ids = aws_subnet.private_subnets[*].id

  tags = {
    Name        = "docksafe-db-subnet-group"
    Environment = var.environment
  }
}

resource "aws_db_instance" "docksafe_db" {
  identifier = "docksafe-${var.environment}"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "docksafe"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.docksafe_db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.docksafe_db_subnet_group.name

  backup_retention_period = var.db_backup_retention_period
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = var.environment == "dev" ? true : false
  deletion_protection = var.environment == "prod" ? true : false

  tags = {
    Name        = "docksafe-db"
    Environment = var.environment
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "docksafe_redis_subnet_group" {
  name       = "docksafe-redis-subnet-group"
  subnet_ids = aws_subnet.private_subnets[*].id
}

resource "aws_elasticache_replication_group" "docksafe_redis" {
  replication_group_id       = "docksafe-${var.environment}"
  description                = "DockSafe Redis cluster"

  node_type                  = var.redis_node_type
  port                       = 6379
  parameter_group_name       = "default.redis7"

  num_cache_clusters         = var.redis_num_cache_nodes

  subnet_group_name          = aws_elasticache_subnet_group.docksafe_redis_subnet_group.name
  security_group_ids         = [aws_security_group.docksafe_redis_sg.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  tags = {
    Name        = "docksafe-redis"
    Environment = var.environment
  }
}

resource "aws_security_group" "docksafe_redis_sg" {
  name_prefix = "docksafe-redis-"
  vpc_id      = aws_vpc.docksafe_vpc.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.docksafe_app_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "docksafe-redis-sg"
    Environment = var.environment
  }
}

# Application Load Balancer
resource "aws_lb" "docksafe_alb" {
  name               = "docksafe-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.docksafe_alb_sg.id]
  subnets            = aws_subnet.public_subnets[*].id

  enable_deletion_protection = var.environment == "prod" ? true : false

  tags = {
    Name        = "docksafe-alb"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "docksafe_tg" {
  name     = "docksafe-${var.environment}-tg"
  port     = 5000
  protocol = "HTTP"
  vpc_id   = aws_vpc.docksafe_vpc.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
    port                = "traffic-port"
    protocol            = "HTTP"
  }

  tags = {
    Name        = "docksafe-tg"
    Environment = var.environment
  }
}

resource "aws_lb_listener" "docksafe_listener" {
  load_balancer_arn = aws_lb.docksafe_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.docksafe_tg.arn
  }
}

# EKS Cluster (Optional - for Kubernetes deployment)
resource "aws_eks_cluster" "docksafe_cluster" {
  count    = var.enable_eks ? 1 : 0
  name     = "docksafe-${var.environment}"
  role_arn = aws_iam_role.eks_cluster_role[0].arn
  version  = "1.28"

  vpc_config {
    subnet_ids              = aws_subnet.private_subnets[*].id
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy[0],
    aws_iam_role_policy_attachment.eks_vpc_resource_controller[0],
  ]

  tags = {
    Name        = "docksafe-eks"
    Environment = var.environment
  }
}

# IAM Role for EKS Cluster
resource "aws_iam_role" "eks_cluster_role" {
  count = var.enable_eks ? 1 : 0
  name  = "docksafe-eks-cluster-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  count      = var.enable_eks ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role[0].name
}

resource "aws_iam_role_policy_attachment" "eks_vpc_resource_controller" {
  count      = var.enable_eks ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.eks_cluster_role[0].name
}
