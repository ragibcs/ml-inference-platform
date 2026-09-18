variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "monitoring_namespace" {
  type        = string
  description = "Kubernetes namespace for Prometheus and Grafana stack"
  default     = "monitoring"
}

variable "prometheus_metrics_retention" {
  type        = string
  description = "Prometheus data retention period"
  default     = "15d"
}

variable "grafana_admin_password" {
  type        = string
  description = "Admin password for Grafana dashboard access"
  default     = "admin-prom-grafana-secure"
  sensitive   = true
}
