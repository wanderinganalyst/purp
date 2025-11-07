#!/bin/bash
# AWS Deployment Script for Purp
# This script helps deploy Purp to AWS EC2 with RDS PostgreSQL

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}   Purp AWS Deployment Script${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: Terraform is not installed${NC}"
    echo "Install it from: https://www.terraform.io/downloads"
    exit 1
fi

# Configuration
read -p "AWS Region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

read -p "Environment name (default: production): " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-production}

read -p "EC2 Instance Type (default: t3.small): " INSTANCE_TYPE
INSTANCE_TYPE=${INSTANCE_TYPE:-t3.small}

read -p "RDS Instance Type (default: db.t3.micro): " DB_INSTANCE_TYPE
DB_INSTANCE_TYPE=${DB_INSTANCE_TYPE:-db.t3.micro}

echo ""
echo -e "${YELLOW}Deployment Configuration:${NC}"
echo "  Region: $AWS_REGION"
echo "  Environment: $ENVIRONMENT"
echo "  EC2 Instance: $INSTANCE_TYPE"
echo "  RDS Instance: $DB_INSTANCE_TYPE"
echo ""

read -p "Continue with deployment? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo -e "${GREEN}Step 1: Generating secrets${NC}"
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo "  ✓ Generated SECRET_KEY"
echo "  ✓ Generated DB_PASSWORD"

echo ""
echo -e "${GREEN}Step 2: Creating Terraform configuration${NC}"

# Create Terraform variables file
cat > deployment/terraform/terraform.tfvars <<EOF
aws_region = "$AWS_REGION"
environment = "$ENVIRONMENT"
instance_type = "$INSTANCE_TYPE"
db_instance_class = "$DB_INSTANCE_TYPE"
db_password = "$DB_PASSWORD"
secret_key = "$SECRET_KEY"
EOF

echo "  ✓ Created terraform.tfvars"

echo ""
echo -e "${GREEN}Step 3: Initializing Terraform${NC}"
cd deployment/terraform
terraform init

echo ""
echo -e "${GREEN}Step 4: Planning infrastructure${NC}"
terraform plan -out=tfplan

echo ""
read -p "Review the plan above. Apply changes? (yes/no): " APPLY
if [ "$APPLY" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo -e "${GREEN}Step 5: Creating infrastructure${NC}"
terraform apply tfplan

# Get outputs
EC2_IP=$(terraform output -raw ec2_public_ip)
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)

echo ""
echo -e "${GREEN}Step 6: Waiting for instance to be ready${NC}"
sleep 30

echo ""
echo -e "${GREEN}Step 7: Deploying application${NC}"

# Create deployment package
cd ../..
tar -czf purp-deploy.tar.gz \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='instance' \
    --exclude='deployment' \
    .

# Copy to EC2
echo "  Copying files to EC2..."
scp -i ~/.ssh/purp-key.pem purp-deploy.tar.gz ubuntu@$EC2_IP:/tmp/

# Deploy on EC2
echo "  Installing application..."
ssh -i ~/.ssh/purp-key.pem ubuntu@$EC2_IP << 'ENDSSH'
cd /opt/purp
sudo tar -xzf /tmp/purp-deploy.tar.gz
sudo chown -R purp:purp /opt/purp

# Install dependencies
sudo -u purp /opt/purp/.venv/bin/pip install -r requirements-production.txt

# Run migrations
sudo -u purp /opt/purp/.venv/bin/python init_db.py

# Restart service
sudo systemctl restart purp
sudo systemctl restart nginx

# Check status
sudo systemctl status purp --no-pager
ENDSSH

echo ""
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}   Deployment Complete!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""
echo "Application URL: http://$EC2_IP"
echo "Database Endpoint: $RDS_ENDPOINT"
echo ""
echo "Credentials have been saved to: deployment/terraform/terraform.tfvars"
echo -e "${YELLOW}Important: Keep this file secure and do not commit it!${NC}"
echo ""
echo "Next steps:"
echo "  1. Configure DNS to point to $EC2_IP"
echo "  2. Set up SSL certificate"
echo "  3. Configure monitoring and backups"
echo ""
