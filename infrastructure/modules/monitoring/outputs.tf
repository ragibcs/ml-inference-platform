output "prometheus_endpoint" {
  description = "Internal service URL for Prometheus server"
  value       = "http://kube-prometheus-stack-prometheus.${var.monitoring_namespace}.svc.cluster.local:9090"
}

output "grafana_endpoint" {
  description = "Internal service URL for Grafana dashboard UI"
  value       = "http://kube-prometheus-stack-grafana.${var.monitoring_namespace}.svc.cluster.local:80"
}

output "alertmanager_endpoint" {
  description = "Internal service URL for Alertmanager"
  value       = "http://kube-prometheus-stack-alertmanager.${var.monitoring_namespace}.svc.cluster.local:9093"
}
