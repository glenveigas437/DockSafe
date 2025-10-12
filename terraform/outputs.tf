# Terraform outputs for DockSafe infrastructure

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.docksafe_vpc.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.docksafe_vpc.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public_subnets[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private_subnets[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.docksafe_igw.id
}

output "security_group_ids" {
  description = "IDs of the security groups"
  value = {
    alb = aws_security_group.docksafe_alb_sg.id
    app = aws_security_group.docksafe_app_sg.id
    db  = aws_security_group.docksafe_db_sg.id
    redis = aws_security_group.docksafe_redis_sg.id
  }
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.docksafe_db.endpoint
  sensitive   = true
}

output "database_port" {
  description = "RDS instance port"
  value       = aws_db_instance.docksafe_db.port
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_replication_group.docksafe_redis.primary_endpoint_address
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = aws_elasticache_replication_group.docksafe_redis.port
}

output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = aws_lb.docksafe_alb.dns_name
}

output "load_balancer_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.docksafe_alb.zone_id
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = aws_lb_target_group.docksafe_tg.arn
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = var.enable_eks ? aws_eks_cluster.docksafe_cluster[0].endpoint : null
}

output "eks_cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = var.enable_eks ? aws_eks_cluster.docksafe_cluster[0].vpc_config[0].cluster_security_group_id : null
}

output "eks_cluster_certificate_authority_data" {
  description = "EKS cluster certificate authority data"
  value       = var.enable_eks ? aws_eks_cluster.docksafe_cluster[0].certificate_authority[0].data : null
  sensitive   = true
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = var.enable_eks ? aws_eks_cluster.docksafe_cluster[0].name : null
}
