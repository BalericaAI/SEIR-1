resource "google_compute_instance_template" "template" {
  name_prefix  = "${var.name}-template"
  machine_type = var.machine_type

  disk {
    source_image = "debian-cloud/debian-11"
    auto_delete  = true
    boot         = true
  }

  network_interface {
    subnetwork = var.subnetwork

    # external IP for lab visibility
    access_config {}
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    apt-get update -y
    apt-get install -y nginx git

    systemctl start nginx

    echo "🔥 MIG instance running" > /var/www/html/index.html

    cd /tmp
    git clone https://github.com/BalericaAI/SEIR-1.git
    chmod +x /tmp/SEIR-1/weekly_lessons/weeka/userscripts/supera.sh
    bash /tmp/SEIR-1/weekly_lessons/weeka/userscripts/supera.sh
  EOT

  tags = ["http-server"]
}

resource "google_project_iam_member" "secret_access" {
  role   = "roles/secretmanager.secretAccessor"
  member = "serviceAccount:${google_service_account.kubernetes.email}"
}

# For DB Proxy

#resource "google_project_iam_member" "sql_client" {
#  role   = "roles/cloudsql.client"
#  member = "serviceAccount:${google_service_account.kubernetes.email}"
#}

