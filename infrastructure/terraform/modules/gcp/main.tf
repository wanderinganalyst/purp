# GCP Infrastructure Module for Purp

variable "project_name" { type = string }
variable "environment" { type = string }
variable "region" { type = string }
variable "instance_type" { type = string }
variable "app_port" { type = number }
variable "tags" { type = map(string) }
variable "gcp_project_id" { type = string }

# VPC Network
resource "google_compute_network" "main" {
  name                    = "${var.project_name}-${var.environment}-vpc"
  auto_create_subnetworks = false
  project                 = var.gcp_project_id
}

# Subnet
resource "google_compute_subnetwork" "main" {
  name          = "${var.project_name}-${var.environment}-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.main.id
  project       = var.gcp_project_id
}

# Firewall Rules
resource "google_compute_firewall" "ssh" {
  name    = "${var.project_name}-${var.environment}-fw-ssh"
  network = google_compute_network.main.name
  project = var.gcp_project_id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["${var.project_name}-${var.environment}"]
}

resource "google_compute_firewall" "app" {
  name    = "${var.project_name}-${var.environment}-fw-app"
  network = google_compute_network.main.name
  project = var.gcp_project_id

  allow {
    protocol = "tcp"
    ports    = [var.app_port]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["${var.project_name}-${var.environment}"]
}

resource "google_compute_firewall" "http" {
  name    = "${var.project_name}-${var.environment}-fw-http"
  network = google_compute_network.main.name
  project = var.gcp_project_id

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["${var.project_name}-${var.environment}"]
}

resource "google_compute_firewall" "https" {
  name    = "${var.project_name}-${var.environment}-fw-https"
  network = google_compute_network.main.name
  project = var.gcp_project_id

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["${var.project_name}-${var.environment}"]
}

# SSH Key
resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Save private key locally
resource "local_file" "private_key" {
  content         = tls_private_key.ssh.private_key_pem
  filename        = "${path.root}/../../keys/${var.project_name}-${var.environment}-gcp.pem"
  file_permission = "0600"
}

# Compute Instance
resource "google_compute_instance" "app" {
  name         = "${var.project_name}-${var.environment}-instance"
  machine_type = var.instance_type
  zone         = "${var.region}-a"
  project      = var.gcp_project_id

  tags = ["${var.project_name}-${var.environment}"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = var.environment == "production" ? 30 : 10
      type  = "pd-standard"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.main.id

    access_config {
      # Ephemeral public IP
    }
  }

  metadata = {
    ssh-keys = "ubuntu:${tls_private_key.ssh.public_key_openssh}"
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y python3 python3-pip python3-venv git
    
    # Create app user
    useradd -m -s /bin/bash appuser
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker appuser
    
    # Signal ready for Ansible
    touch /tmp/cloud-init-done
    EOF

  labels = var.tags
}

# Outputs
output "instance_id" {
  value = google_compute_instance.app.id
}

output "instance_ip" {
  value = google_compute_instance.app.network_interface[0].access_config[0].nat_ip
}

output "instance_url" {
  value = "http://${google_compute_instance.app.network_interface[0].access_config[0].nat_ip}:${var.app_port}"
}

output "ssh_command" {
  value = "ssh -i ${local_file.private_key.filename} ubuntu@${google_compute_instance.app.network_interface[0].access_config[0].nat_ip}"
}

output "instance_dns" {
  value = google_compute_instance.app.network_interface[0].access_config[0].nat_ip
}
