output "vpc_id" {
  description = "The ID of the provisioned VPC"
  value       = module.network.vpc_id
}

output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = module.network.private_subnets
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = module.network.public_subnets
}

output "cluster_name" {
  description = "The name of the Kubernetes / EKS cluster"
  value       = module.kubernetes.cluster_name
}

output "cluster_endpoint" {
  description = "The endpoint URL for the Kubernetes control plane"
  value       = module.kubernetes.cluster_endpoint
}

output "ecr_repository_url" {
  description = "The URL of the ECR container repository"
  value       = module.kubernetes.ecr_repository_url
}

output "argocd_server_url" {
  description = "The URL or service name for ArgoCD server"
  value       = module.kubernetes.argocd_server_endpoint
}
