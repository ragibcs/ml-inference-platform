module "root" {
  source = "../../"

  aws_region          = var.aws_region
  environment         = var.environment
  cluster_name        = var.cluster_name
  kubernetes_version  = var.kubernetes_version
  vpc_cidr            = var.vpc_cidr
  availability_zones  = var.availability_zones
  node_instance_types = var.node_instance_types
  min_node_count      = var.min_node_count
  max_node_count      = var.max_node_count
  desired_node_count  = var.desired_node_count
  enable_monitoring   = var.enable_monitoring
}
