# Infrastructure Documentation

## Overview

This infrastructure-as-code (IaC) setup allows you to deploy the BecauseImStuck application to AWS, Azure, or GCP with a single command. It uses:

- **Terraform** for infrastructure provisioning
- **Ansible** for application deployment and configuration
- **Bash scripts** for automation

## Features

- **Multi-cloud support**: Deploy to AWS, Azure, or GCP
- **Environment modes**: Production (larger resources) or Demo (minimal resources)
- **Automated deployment**: Single command to provision and deploy
- **SSH key management**: Automatic generation and secure storage
- **Nginx reverse proxy**: Production-ready web server configuration
- **Systemd service**: Application runs as a managed service
- **Idempotent**: Safe to run multiple times

## Prerequisites

### Required Tools

1. **Terraform** (>= 1.0)
   ```bash
   # macOS
   brew install terraform
   
   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

2. **Ansible** (>= 2.9)
   ```bash
   pip install ansible
   ```

3. **jq** (JSON processor)
   ```bash
   # macOS
   brew install jq
   
   # Linux
   sudo apt-get install jq
   ```

### Cloud Provider Credentials

#### AWS
```bash
# Set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# Or configure AWS CLI
aws configure
```

#### Azure
```bash
# Login to Azure
az login

# Set subscription (if you have multiple)
az account set --subscription "your-subscription-id"
```

#### GCP
```bash
# Login
gcloud auth application-default login

# Set project
gcloud config set project your-project-id

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## Directory Structure

```
infrastructure/
├── terraform/
│   ├── main.tf                    # Main Terraform configuration
│   ├── modules/
│   │   ├── aws/main.tf           # AWS-specific resources
│   │   ├── azure/main.tf         # Azure-specific resources
│   │   └── gcp/main.tf           # GCP-specific resources
│   └── environments/
│       ├── production.tfvars     # Production configuration
│       └── demo.tfvars           # Demo configuration
├── ansible/
│   └── playbooks/
│       ├── deploy-app.yml        # Application deployment playbook
│       └── templates/
│           ├── env.j2            # Environment file template
│           ├── becauseimstuck.service.j2  # Systemd service
│           └── nginx.conf.j2     # Nginx configuration
├── scripts/
│   ├── deploy.sh                 # Main deployment script
│   └── destroy.sh                # Infrastructure destruction script
├── keys/                         # SSH keys (auto-generated)
└── README.md                     # This file
```

## Quick Start

### 1. Deploy the Application

```bash
cd infrastructure/scripts
./deploy.sh
```

The script will:
1. Check prerequisites
2. Ask you to select a cloud provider (AWS/Azure/GCP)
3. Ask you to select an environment (Production/Demo)
4. Verify cloud credentials
5. Provision infrastructure with Terraform
6. Deploy the application with Ansible
7. Display access information

### 2. Access Your Application

After deployment completes, you'll see:
```
Your application has been deployed successfully!

Cloud Provider:  aws
Environment:     production
Instance IP:     54.123.45.67

Access your application:
  http://54.123.45.67
```

### 3. Destroy Infrastructure

When you're done:
```bash
cd infrastructure/scripts
./destroy.sh
```

## Manual Deployment

If you prefer manual control:

### Terraform

```bash
cd infrastructure/terraform

# Initialize
terraform init

# Plan (AWS example)
terraform plan \
  -var="cloud_provider=aws" \
  -var="environment=production" \
  -var="app_port=5000" \
  -out=tfplan

# Apply
terraform apply tfplan

# Get outputs
terraform output instance_ip
terraform output ssh_command
```

### Ansible

```bash
cd infrastructure/ansible

# Create inventory
cat > inventory.ini <<EOF
[app]
54.123.45.67

[app:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=../keys/becauseimstuck-production-aws.pem
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
environment=production
app_port=5000
EOF

# Run playbook
ansible-playbook -i inventory.ini playbooks/deploy-app.yml
```

## Configuration

### Environment Variables

Edit `terraform/environments/production.tfvars` or `demo.tfvars`:

```hcl
cloud_provider = "aws"  # "aws", "azure", or "gcp"
environment    = "production"  # "production" or "demo"

# AWS Configuration
aws_region = "us-east-1"

# Azure Configuration
azure_region = "East US"

# GCP Configuration
gcp_region     = "us-east1"
gcp_project_id = "your-project-id"

# Application
app_port = 5000

# Tags
tags = {
  Environment = "production"
  Project     = "BecauseImStuck"
}
```

### Instance Sizes

#### Production
- **AWS**: t3.medium (2 vCPU, 4GB RAM)
- **Azure**: Standard_B2s (2 vCPU, 4GB RAM)
- **GCP**: e2-medium (2 vCPU, 4GB RAM)
- **Disk**: 30GB

#### Demo
- **AWS**: t3.micro (2 vCPU, 1GB RAM)
- **Azure**: Standard_B1s (1 vCPU, 1GB RAM)
- **GCP**: e2-micro (2 vCPU, 1GB RAM)
- **Disk**: 10GB

## Architecture

### AWS
- **VPC**: 10.0.0.0/16
- **Subnet**: 10.0.1.0/24 (public)
- **Security Group**: Allows SSH (22), HTTP (80), HTTPS (443), App port (5000)
- **EC2 Instance**: Ubuntu 22.04 LTS
- **SSH Key**: Auto-generated RSA 4096-bit

### Azure
- **Resource Group**: Dedicated resource group
- **VNet**: 10.0.0.0/16
- **Subnet**: 10.0.1.0/24
- **NSG**: Allows SSH (22), HTTP (80), HTTPS (443), App port (5000)
- **VM**: Ubuntu 22.04 LTS
- **Public IP**: Static

### GCP
- **VPC Network**: Custom network
- **Subnet**: 10.0.1.0/24 (regional)
- **Firewall Rules**: Allows SSH (22), HTTP (80), HTTPS (443), App port (5000)
- **Compute Instance**: Ubuntu 22.04 LTS
- **External IP**: Ephemeral

## Application Deployment

### What Ansible Installs

1. **System packages**: Python 3, pip, venv, git, curl, nginx, Docker
2. **Application**: Cloned to `/home/appuser/becauseimstuck`
3. **Python environment**: Virtual environment with all dependencies
4. **Gunicorn**: WSGI server with 4 workers
5. **Systemd service**: Manages application lifecycle
6. **Nginx**: Reverse proxy on port 80

### Application Structure

```
/home/appuser/becauseimstuck/
├── .venv/              # Virtual environment
├── .env                # Environment configuration
├── app.py              # Flask application
├── models.py           # Database models
├── routes/             # Route blueprints
├── utils/              # Utility functions
├── static/             # Static files
├── templates/          # Jinja2 templates
└── instance/           # SQLite database
```

## Troubleshooting

### Check Application Status

```bash
# SSH into instance
ssh -i ../keys/becauseimstuck-production-aws.pem ubuntu@54.123.45.67

# Check service status
sudo systemctl status becauseimstuck

# View logs
sudo journalctl -u becauseimstuck -f

# Check nginx status
sudo systemctl status nginx

# Test nginx config
sudo nginx -t
```

### Common Issues

#### 1. Terraform apply fails
- Check cloud credentials
- Verify quota limits in cloud provider
- Check for existing resources with same name

#### 2. Ansible fails to connect
- Wait longer for instance to boot
- Check security group/firewall rules
- Verify SSH key permissions (should be 0600)

#### 3. Application won't start
- Check logs: `sudo journalctl -u becauseimstuck`
- Verify Python dependencies: `source .venv/bin/activate && pip list`
- Check .env file: `cat /home/appuser/becauseimstuck/.env`

#### 4. Can't access application
- Check security group allows inbound on port 80
- Verify nginx is running: `sudo systemctl status nginx`
- Check application is listening: `sudo netstat -tlnp | grep 5000`

### Debug Mode

Enable Ansible verbose output:
```bash
ansible-playbook -vvv -i inventory.ini playbooks/deploy-app.yml
```

Enable Terraform debug:
```bash
export TF_LOG=DEBUG
terraform apply
```

## Security Considerations

1. **SSH Keys**: Stored in `infrastructure/keys/` - add to `.gitignore`
2. **Secrets**: Never commit credentials to Git
3. **Firewall**: Consider restricting SSH to your IP
4. **HTTPS**: Add SSL certificate in production (not included)
5. **Database**: Use managed database service for production
6. **Backups**: Configure automated backups

## Cost Estimation

### AWS (us-east-1)
- **Production**: ~$30-40/month (t3.medium + 30GB storage + transfer)
- **Demo**: ~$5-10/month (t3.micro + 10GB storage + transfer)

### Azure (East US)
- **Production**: ~$35-45/month (Standard_B2s + 30GB storage + transfer)
- **Demo**: ~$10-15/month (Standard_B1s + 10GB storage + transfer)

### GCP (us-east1)
- **Production**: ~$25-35/month (e2-medium + 30GB storage + transfer)
- **Demo**: ~$5-10/month (e2-micro + 10GB storage + transfer)

*Costs are estimates and may vary based on usage and region*

## Next Steps

1. **Domain Name**: Point DNS to instance IP
2. **SSL Certificate**: Use Let's Encrypt with Certbot
3. **CI/CD**: Integrate with GitHub Actions
4. **Monitoring**: Add CloudWatch/Azure Monitor/Stackdriver
5. **Scaling**: Use load balancer + auto-scaling group
6. **Database**: Migrate to RDS/Azure SQL/Cloud SQL

## Support

For issues or questions:
- Check logs: `sudo journalctl -u becauseimstuck -f`
- Terraform docs: https://registry.terraform.io/
- Ansible docs: https://docs.ansible.com/
