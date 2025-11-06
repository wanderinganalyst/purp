# Demo Environment Configuration

cloud_provider = "aws"  # Change to "azure" or "gcp" as needed
environment    = "demo"

# AWS Configuration
aws_region = "us-east-1"

# Azure Configuration
azure_region = "East US"

# GCP Configuration
gcp_region     = "us-east1"
gcp_project_id = "your-gcp-project-id"  # REPLACE WITH YOUR GCP PROJECT ID

# Application Configuration
app_port = 5000

# Tags
tags = {
  Environment = "demo"
  Project     = "BecauseImStuck"
  ManagedBy   = "Terraform"
  Owner       = "DevOps Team"
}
