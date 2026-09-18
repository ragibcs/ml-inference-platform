# Network Module (VPC, Subnets, Gateways, Routing)
module "network" {
  source = "./modules/network"

  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  environment        = var.environment
  cluster_name       = var.cluster_name
}

# Kubernetes / EKS Module (Cluster, Managed Node Group, IAM, ECR, ArgoCD)
module "kubernetes" {
  source = "./modules/kubernetes"

  cluster_name             = var.cluster_name
  cluster_version          = var.kubernetes_version
  environment              = var.environment
  vpc_id                   = module.network.vpc_id
  subnet_ids               = module.network.private_subnets
  control_plane_subnet_ids = concat(module.network.public_subnets, module.network.private_subnets)
  node_instance_types      = var.node_instance_types
  min_node_count           = var.min_node_count
  max_node_count           = var.max_node_count
  desired_node_count       = var.desired_node_count
  install_argocd           = true
}

# Monitoring Stack Module (Prometheus, Grafana, Alertmanager)
module "monitoring" {
  source = "./modules/monitoring"

  count       = var.enable_monitoring ? 1 : 0
  environment = var.environment

  depends_on = [module.kubernetes]
}
