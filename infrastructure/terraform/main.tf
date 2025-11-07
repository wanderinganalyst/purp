# Main Terraform Configuration for Purp
# Supports AWS, Azure, and GCP deployment with production and demo modes

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

# Variables
variable "cloud_provider" {
  description = "Cloud provider to use: aws, azure, or gcp"
  type        = string
  validation {
    condition     = contains(["aws", "azure", "gcp"], var.cloud_provider)
    error_message = "Cloud provider must be aws, azure, or gcp."
  }
}

variable "environment" {
  description = "Environment: production or demo"
  type        = string
  default     = "demo"
  validation {
    condition     = contains(["production", "demo"], var.environment)
    error_message = "Environment must be production or demo."
  }
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "purp"
}

variable "region" {
  description = "Region for deployment"
  type        = string
  default     = ""
}

variable "app_port" {
  description = "Application port"
  type        = number
  default     = 5000
}

# Local variables
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
  
  # Default regions per cloud provider
  default_region = var.region != "" ? var.region : (
    var.cloud_provider == "aws" ? "us-east-1" :
    var.cloud_provider == "azure" ? "eastus" :
    "us-central1" # GCP
  )
  
  # Instance sizes per environment
  instance_size = var.environment == "production" ? {
    aws   = "t3.medium"
    azure = "Standard_B2s"
    gcp   = "e2-medium"
  } : {
    aws   = "t3.micro"
    azure = "Standard_B1s"
    gcp   = "e2-micro"
  }
}

# Provider configurations
provider "aws" {
  region = local.default_region
  
  default_tags {
    tags = local.common_tags
  }
}

provider "azurerm" {
  features {}
}

provider "google" {
  project = var.project_name
  region  = local.default_region
}

# Conditional module deployment based on cloud_provider
module "aws_infrastructure" {
  count  = var.cloud_provider == "aws" ? 1 : 0
  source = "./modules/aws"
  
  project_name  = var.project_name
  environment   = var.environment
  region        = local.default_region
  instance_type = local.instance_size.aws
  app_port      = var.app_port
  tags          = local.common_tags
}

module "azure_infrastructure" {
  count  = var.cloud_provider == "azure" ? 1 : 0
  source = "./modules/azure"
  
  project_name = var.project_name
  environment  = var.environment
  location     = local.default_region
  vm_size      = local.instance_size.azure
  app_port     = var.app_port
  tags         = local.common_tags
}

module "gcp_infrastructure" {
  count  = var.cloud_provider == "gcp" ? 1 : 0
  source = "./modules/gcp"
  
  project_name  = var.project_name
  environment   = var.environment
  region        = local.default_region
  machine_type  = local.instance_size.gcp
  app_port      = var.app_port
  labels        = local.common_tags
}

# Outputs
output "instance_ip" {
  description = "Public IP address of the deployed instance"
  value = (
    var.cloud_provider == "aws" ? try(module.aws_infrastructure[0].instance_ip, null) :
    var.cloud_provider == "azure" ? try(module.azure_infrastructure[0].instance_ip, null) :
    try(module.gcp_infrastructure[0].instance_ip, null)
  )
}

output "instance_url" {
  description = "URL to access the application"
  value = (
    var.cloud_provider == "aws" ? try(module.aws_infrastructure[0].instance_url, null) :
    var.cloud_provider == "azure" ? try(module.azure_infrastructure[0].instance_url, null) :
    try(module.gcp_infrastructure[0].instance_url, null)
  )
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value = (
    var.cloud_provider == "aws" ? try(module.aws_infrastructure[0].ssh_command, null) :
    var.cloud_provider == "azure" ? try(module.azure_infrastructure[0].ssh_command, null) :
    try(module.gcp_infrastructure[0].ssh_command, null)
  )
  sensitive = true
}
