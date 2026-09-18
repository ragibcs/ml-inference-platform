variable "cluster_name" {
  type        = string
  description = "EKS Cluster Name"
}

variable "cluster_version" {
  type        = string
  description = "Kubernetes Version"
  default     = "1.30"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where cluster is hosted"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for worker node group"
}

variable "control_plane_subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for EKS control plane ENIs"
}

variable "node_instance_types" {
  type        = list(string)
  description = "EC2 instance types for worker nodes"
  default     = ["t3.medium"]
}

variable "min_node_count" {
  type        = number
  description = "Minimum node count"
  default     = 2
}

variable "max_node_count" {
  type        = number
  description = "Maximum node count"
  default     = 10
}

variable "desired_node_count" {
  type        = number
  description = "Desired node count"
  default     = 3
}

variable "install_argocd" {
  type        = bool
  description = "Install ArgoCD using Helm"
  default     = true
}
