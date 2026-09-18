variable "aws_region" {
  type        = string
  description = "AWS region"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Environment identifier"
  default     = "production"
}

variable "cluster_name" {
  type        = string
  description = "EKS Cluster Name"
  default     = "ml-platform-prod-eks"
}

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes Version"
  default     = "1.30"
}

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR block"
  default     = "10.20.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  description = "Availability zones"
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "node_instance_types" {
  type        = list(string)
  description = "EC2 instance types for worker nodes"
  default     = ["t3.large"]
}

variable "min_node_count" {
  type        = number
  description = "Minimum node count"
  default     = 3
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

variable "enable_monitoring" {
  type        = bool
  description = "Enable Prometheus & Grafana stack"
  default     = true
}
