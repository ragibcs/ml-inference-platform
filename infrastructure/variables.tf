variable "aws_region" {
  type        = string
  description = "AWS region for infrastructure provisioning"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, production)"
  default     = "dev"
}

variable "cluster_name" {
  type        = string
  description = "EKS / Kubernetes cluster name identifier"
  default     = "ml-inference-eks"
}

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes control plane version"
  default     = "1.30"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block allocation for the VPC"
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  description = "List of availability zones for multi-AZ deployment"
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "node_instance_types" {
  type        = list(string)
  description = "EC2 instance types for EKS worker nodes"
  default     = ["t3.medium"]
}

variable "min_node_count" {
  type        = number
  description = "Minimum number of worker nodes in EKS managed node group"
  default     = 2
}

variable "max_node_count" {
  type        = number
  description = "Maximum number of worker nodes in EKS managed node group"
  default     = 10
}

variable "desired_node_count" {
  type        = number
  description = "Desired baseline number of worker nodes"
  default     = 3
}

variable "enable_monitoring" {
  type        = bool
  description = "Enable Prometheus and Grafana monitoring stack"
  default     = true
}
