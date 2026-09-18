output "cluster_name" {
  description = "Kubernetes EKS Cluster Name"
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane API server"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.main.certificate_authority[0].data
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

output "ecr_repository_url" {
  description = "URL of the ECR container repository"
  value       = aws_ecr_repository.app.repository_url
}

output "ecr_repository_arn" {
  description = "ARN of the ECR container repository"
  value       = aws_ecr_repository.app.arn
}

output "oidc_provider_arn" {
  description = "ARN of the IAM OIDC Provider for Service Accounts"
  value       = aws_iam_openid_connect_provider.cluster.arn
}

output "argocd_server_endpoint" {
  description = "Internal service endpoint for ArgoCD API Server"
  value       = "http://argocd-server.argocd.svc.cluster.local:80"
}
