output "vpc_id" {
  description = "Dev VPC ID"
  value       = module.root.vpc_id
}

output "cluster_name" {
  description = "Dev EKS Cluster Name"
  value       = module.root.cluster_name
}

output "cluster_endpoint" {
  description = "Dev EKS Cluster Endpoint"
  value       = module.root.cluster_endpoint
}

output "ecr_repository_url" {
  description = "ECR Container Registry URL"
  value       = module.root.ecr_repository_url
}
