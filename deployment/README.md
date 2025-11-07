# deployment/

This directory contains all deployment-related files for Purp.

## Structure

```
deployment/
├── deploy-aws.sh           # Automated AWS deployment script
├── terraform/              # Infrastructure as Code
│   ├── main.tf            # Main Terraform configuration
│   ├── variables.tf       # Input variables
│   ├── outputs.tf         # Output values
│   ├── user-data.sh       # EC2 initialization script
│   └── terraform.tfvars.example  # Configuration template
└── README.md              # This file
```

## Quick Start

### AWS Deployment

1. **Prerequisites**
   ```bash
   # Install AWS CLI and Terraform
   brew install awscli terraform
   
   # Configure AWS credentials
   aws configure
   
   # Create SSH key
   aws ec2 create-key-pair --key-name purp-key \
     --query 'KeyMaterial' --output text > ~/.ssh/purp-key.pem
   chmod 400 ~/.ssh/purp-key.pem
   ```

2. **Deploy**
   ```bash
   # Automated deployment
   ./deployment/deploy-aws.sh
   
   # OR Manual deployment
   cd deployment/terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   terraform init
   terraform apply
   ```

3. **Access**
   ```bash
   # Get application URL
   terraform output application_url
   ```

## Files

### deploy-aws.sh

Automated deployment script that:
- Generates secure secrets
- Configures Terraform
- Provisions AWS infrastructure
- Deploys application code
- Configures web server

Usage:
```bash
./deployment/deploy-aws.sh
```

### Terraform Configuration

Infrastructure as Code files for AWS:

- `main.tf`: Defines VPC, EC2, RDS, security groups
- `variables.tf`: Configurable parameters
- `outputs.tf`: Resource information (IPs, endpoints)
- `user-data.sh`: EC2 bootstrap script
- `terraform.tfvars.example`: Template for your configuration

### user-data.sh

EC2 initialization script that runs on first boot:
- Installs system dependencies
- Creates application user
- Clones repository
- Configures Python environment
- Sets up systemd service
- Configures Nginx
- Initializes database

## Configuration

### Required Variables

Edit `terraform.tfvars`:

```hcl
# AWS
aws_region = "us-east-1"
key_name   = "purp-key"

# Database
db_password = "SECURE_PASSWORD_HERE"

# Flask
secret_key = "SECURE_SECRET_HERE"

# Network
allowed_ssh_cidr = ["YOUR_IP/32"]
```

Generate secrets:
```bash
# SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# DB_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Infrastructure

### AWS Resources Created

- **VPC** (10.0.0.0/16)
  - 2 Public subnets
  - 2 Private subnets
  - Internet Gateway
  - Route tables

- **EC2 Instance**
  - Ubuntu 22.04 LTS
  - t3.small (2 vCPU, 2 GB RAM)
  - 30 GB encrypted EBS
  - Elastic IP

- **RDS PostgreSQL**
  - PostgreSQL 15.4
  - db.t3.micro (2 vCPU, 1 GB RAM)
  - 20 GB encrypted storage
  - Automated backups (7 days)

- **Security Groups**
  - App: HTTP (80), HTTPS (443), SSH (22)
  - DB: PostgreSQL (5432) from app

- **IAM**
  - EC2 instance role
  - CloudWatch permissions

### Cost Estimate

Monthly costs (us-east-1):
- EC2 t3.small: ~$15
- RDS db.t3.micro: ~$13
- EBS Storage: ~$3
- RDS Storage: ~$2
- **Total**: ~$33/month

## Operations

### View Outputs

```bash
cd deployment/terraform

# All outputs
terraform output

# Specific output
terraform output ec2_public_ip
terraform output database_url
```

### Update Application

```bash
# SSH to instance
ssh -i ~/.ssh/purp-key.pem ubuntu@$(terraform output -raw ec2_public_ip)

# Update code
cd /opt/purp
sudo -u purp git pull
sudo -u purp .venv/bin/pip install -r requirements-production.txt

# Restart
sudo systemctl restart purp
```

### Scale Infrastructure

```bash
# Edit terraform.tfvars
instance_type = "t3.medium"
db_instance_class = "db.t3.small"

# Apply changes
terraform apply
```

### Destroy Infrastructure

```bash
# Backup first
aws rds create-db-snapshot \
  --db-instance-identifier purp-production-db \
  --db-snapshot-identifier purp-final-backup

# Destroy
terraform destroy
```

## Troubleshooting

### Connection Issues

```bash
# Test SSH
ssh -i ~/.ssh/purp-key.pem ubuntu@<IP>

# Check security group
aws ec2 describe-security-groups --group-ids <SG_ID>

# Check instance status
aws ec2 describe-instance-status --instance-ids <INSTANCE_ID>
```

### Application Issues

```bash
# SSH to instance
ssh -i ~/.ssh/purp-key.pem ubuntu@<IP>

# Check service
sudo systemctl status purp

# View logs
sudo journalctl -u purp -n 100
sudo tail -f /var/log/purp/app.log

# Restart
sudo systemctl restart purp
```

### Database Issues

```bash
# Check RDS status
aws rds describe-db-instances --db-instance-identifier purp-production-db

# Test connection from EC2
psql -h <RDS_ENDPOINT> -U purp_admin -d purp

# View RDS logs
aws rds download-db-log-file-portion \
  --db-instance-identifier purp-production-db \
  --log-file-name error/postgresql.log
```

## Documentation

See [docs/deployment/aws.md](../../docs/deployment/aws.md) for full deployment guide.

## Security

- Never commit `terraform.tfvars` (contains secrets)
- Use strong passwords (20+ characters)
- Restrict SSH to your IP
- Enable SSL with Certbot
- Regular security updates
- Monitor CloudWatch logs

## Next Steps

1. Configure domain name
2. Setup SSL certificate
3. Configure monitoring
4. Setup log aggregation
5. Configure automated backups
6. Load testing
