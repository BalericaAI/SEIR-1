locals {
  prefix = "seir"

  # Environment-aware naming
  network_name = "${local.prefix}-${var.environment}-vpc"
  subnet_name  = "${local.prefix}-${var.environment}-subnet"
  cluster_name = "${local.prefix}-${var.environment}-gke"

  workload_pool = "${var.project_id}.svc.id.goog"

  # Environment-based sizing
  node_config = {
    dev = {
      machine_type = "e2-standard-2"
      node_count   = 1
    }

    stage = {
      machine_type = "e2-standard-4"
      node_count   = 2
    }

    prod = {
      machine_type = "n2-standard-8"
      node_count   = 3
    }
  }

  selected_node_config = local.node_config[var.environment]
}
