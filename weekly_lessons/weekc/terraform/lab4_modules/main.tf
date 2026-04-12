module "vpc" {
  source = "./modules/vpc"

  network_name = local.network_name
  subnet_name  = local.subnet_name
  region       = var.region
}

module "gke" {
  source = "./modules/gke"

  cluster_name = local.cluster_name
  zone         = var.zone
  project_id   = var.project_id

  network    = module.vpc.network_id
  subnetwork = module.vpc.subnet_id
}

module "lb" {
  source = "./modules/lb"

  name           = "${local.prefix}-${var.environment}-lb"
  region         = var.region
  instance_group = module.mig.instance_group

# domain_name = "www.chewbacca-snacks.com"
# enable_waf  = true
# allowed_ips = ["YOUR_IP/32"]

}


module "waf" {
  source = "./modules/waf"

  name = "${local.prefix}-${var.environment}"

  enable_geo_blocking  = true
  blocked_region_codes = ["RU", "CN", "KP"]

  enable_rate_limit       = true
  rate_limit_count        = 100
  rate_limit_interval_sec = 60

  enable_waf_rules      = true
  enable_bot_management = false
}


module "postgres" {
  source = "./modules/postgres"

  name     = "${local.prefix}-${var.environment}"
  region   = var.region
  network  = module.vpc.network_id

  db_name     = "chewbacca"
  db_user     = "chewie"
  db_password = "supersecret123"
}
