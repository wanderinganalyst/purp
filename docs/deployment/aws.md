# Deploying Purp to AWS

This guide walks you through deploying Purp to AWS using Terraform for infrastructure and automated deployment scripts.

## Architecture Overview

The production deployment consists of:
- **EC2 Instance** (t3.small): Runs the Flask application with Gunicorn and Nginx
- **RDS PostgreSQL** (db.t3.micro): Managed database service
- **VPC**: Isolated network with public and private subnets
- **Security Groups**: Firewall rules for EC2 and RDS
- **Elastic IP**: Static IP address for the application
- **IAM Role**: Permissions for CloudWatch logging

## Prerequisites

### 1. AWS Account Setup
- Active AWS account with billing enabled
- AWS CLI installed and configured
- IAM user with permissions for EC2, RDS, VPC, and IAM

### 2. Install Required Tools
```bash
# AWS CLI
brew install awscli

# Terraform
brew install terraform

# Configure AWS credentials
aws configure
```

### 3. Create EC2 Key Pair
```bash
# Create SSH key
aws ec2 create-key-pair --key-name purp-key \
  --query 'KeyMaterial' --output text > ~/.ssh/purp-key.pem

# Set permissions
chmod 400 ~/.ssh/purp-key.pem
```

## Quick Deployment

### Option 1: Automated Script

```bash
# Run the deployment script
./deployment/deploy-aws.sh
```

The script will:
1. Generate secure secrets (SECRET_KEY, DB_PASSWORD)
2. Create Terraform configuration
3. Initialize and apply infrastructure
4. Deploy the application code
5. Configure Nginx and systemd

### Option 2: Manual Deployment

#### Step 1: Configure Terraform

```bash
cd deployment/terraform

# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

Required changes in `terraform.tfvars`:
- `db_password`: Strong database password
- `secret_key`: Flask session secret (generate with `python3 -c "import secrets; print(secrets.token_hex(32))"`)
- `allowed_ssh_cidr`: Your IP address for SSH access

#### Step 2: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply configuration
terraform apply
```

This creates:
- VPC with public/private subnets
- EC2 instance with application installed
- RDS PostgreSQL database
- Security groups and networking

#### Step 3: Access Your Application

```bash
# Get the public IP
terraform output ec2_public_ip

# SSH to instance
terraform output -raw ssh_command | bash

# View application
terraform output application_url
```

## Post-Deployment Configuration

### 1. Configure DNS (Optional)

If you have a domain name:

```bash
# Get Elastic IP
ELASTIC_IP=$(terraform output -raw ec2_public_ip)

# Create DNS A record pointing to $ELASTIC_IP
```

### 2. Setup SSL Certificate

```bash
# SSH to instance
ssh -i ~/.ssh/purp-key.pem ubuntu@<EC2_IP>

# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

### 3. Verify Deployment

```bash
# Check application status
curl http://<EC2_IP>/health

# Check systemd service
ssh ubuntu@<EC2_IP> "sudo systemctl status purp"

# View logs
ssh ubuntu@<EC2_IP> "sudo journalctl -u purp -n 50"
```

## Monitoring and Maintenance

### Application Logs

```bash
# Application logs
sudo tail -f /var/log/purp/app.log

# Nginx access logs
sudo tail -f /var/log/nginx/purp-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/purp-error.log

# System logs
sudo journalctl -u purp -f
```

### Database Backups

Automated backups are enabled by default:
- **Frequency**: Daily
- **Retention**: 7 days (configurable)
- **Backup Window**: 3:00-4:00 AM UTC

To create manual backup:
```bash
cd deployment/terraform
terraform apply -var="backup_retention_days=30"
```

### Health Checks

A health check runs every 5 minutes and automatically restarts the application if unhealthy:
```bash
# View health check cron
sudo crontab -l

# Manual health check
/usr/local/bin/purp-health-check
```

### Updating the Application

```bash
# SSH to instance
ssh -i ~/.ssh/purp-key.pem ubuntu@<EC2_IP>

# Pull latest code
cd /opt/purp
sudo -u purp git pull origin main

# Install dependencies
sudo -u purp .venv/bin/pip install -r requirements-production.txt

# Run migrations
sudo -u purp .venv/bin/python init_db.py

# Restart service
sudo systemctl restart purp
```

### Scaling Up

To increase capacity:

```bash
# Edit terraform.tfvars
instance_type = "t3.medium"      # More CPU/RAM
db_instance_class = "db.t3.small" # Larger database

# Apply changes
terraform apply
```

## Troubleshooting

### Application Won't Start

```bash
# Check service status
sudo systemctl status purp

# View recent errors
sudo journalctl -u purp -n 100 --no-pager

# Check environment variables
sudo cat /etc/purp/.env.production

# Test Gunicorn manually
cd /opt/purp
sudo -u purp .venv/bin/gunicorn -c gunicorn_config.py wsgi:app
```

### Database Connection Issues

```bash
# Test database connectivity
psql -h <RDS_ENDPOINT> -U purp_admin -d purp

# Check security group rules
aws ec2 describe-security-groups --group-ids <DB_SG_ID>

# Verify DATABASE_URL format
# Should be: postgresql://username:password@host:5432/database
```

### Nginx Issues

```bash
# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Check error logs
sudo tail -f /var/log/nginx/error.log
```

### High Memory Usage

```bash
# Check running processes
top

# Adjust Gunicorn workers in /etc/purp/.env.production
GUNICORN_WORKERS=2  # Reduce if needed

# Restart application
sudo systemctl restart purp
```

## Cost Optimization

**Estimated Monthly Costs** (us-east-1):
- EC2 t3.small (730 hours): ~$15
- RDS db.t3.micro (730 hours): ~$13
- EBS Storage (30 GB): ~$3
- RDS Storage (20 GB): ~$2
- Data Transfer (minimal): ~$1
- **Total**: ~$34/month

To reduce costs:
1. Use smaller instance types for testing
2. Stop instances when not in use (development)
3. Enable RDS snapshots and delete instance
4. Use Reserved Instances for production

## Destroying Infrastructure

**Warning**: This deletes all resources including the database.

```bash
cd deployment/terraform

# Backup database first
aws rds create-db-snapshot \
  --db-instance-identifier purp-production-db \
  --db-snapshot-identifier purp-final-backup

# Destroy infrastructure
terraform destroy
```

## Security Checklist

- [ ] Changed SECRET_KEY from default
- [ ] Set strong DB_PASSWORD (20+ characters)
- [ ] Restricted SSH access to your IP in `allowed_ssh_cidr`
- [ ] Enabled SSL certificate with Certbot
- [ ] Configured Fail2Ban for SSH protection
- [ ] Set up CloudWatch alarms for monitoring
- [ ] Enabled RDS encryption
- [ ] Regular security updates: `sudo apt-get update && sudo apt-get upgrade`

## Next Steps

1. **Configure Domain**: Point DNS to Elastic IP
2. **Enable SSL**: Use Certbot for HTTPS
3. **Setup Monitoring**: Configure CloudWatch dashboards
4. **Enable Backups**: Verify RDS backup schedule
5. **Load Testing**: Test application under load
6. **Documentation**: Document custom configurations

## Support

For issues or questions:
- Review logs in `/var/log/purp/`
- Check Terraform state: `terraform show`
- AWS Console: Monitor EC2 and RDS dashboards
- GitHub Issues: Report bugs or request features
