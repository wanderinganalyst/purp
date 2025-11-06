# Quick Start Guide

## Deploy in 5 Minutes

### Step 1: Install Prerequisites

**macOS:**
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install tools
brew install terraform jq
pip install ansible
```

**Linux (Ubuntu/Debian):**
```bash
# Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Others
sudo apt-get update
sudo apt-get install -y jq python3-pip
pip3 install ansible
```

### Step 2: Configure Cloud Credentials

**AWS:**
```bash
export AWS_ACCESS_KEY_ID="your-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

**Azure:**
```bash
az login
```

**GCP:**
```bash
gcloud auth application-default login
```

### Step 3: Deploy

```bash
cd infrastructure/scripts
./deploy.sh
```

### Step 4: Follow Prompts

1. Select cloud provider (1=AWS, 2=Azure, 3=GCP)
2. Select environment (1=Production, 2=Demo)
3. If GCP, enter your project ID
4. Confirm deployment

### Step 5: Access Your App

The script will display:
```
Access your application:
  http://YOUR-IP-ADDRESS
```

## Example Session

```bash
$ cd infrastructure/scripts
$ ./deploy.sh

===================================
BecauseImStuck Deployment Script
===================================

===================================
Checking Prerequisites
===================================

✓ Terraform found: 1.6.0
✓ Ansible found: ansible 2.14.0
✓ jq found
✓ All prerequisites met

===================================
Select Cloud Provider
===================================

Available cloud providers:
  1) AWS
  2) Azure
  3) GCP

Enter your choice (1-3): 1
✓ Selected: AWS

===================================
Select Environment
===================================

Available environments:
  1) Production (larger resources)
  2) Demo (minimal resources)

Enter your choice (1-2): 2
✓ Selected: Demo

===================================
Running Terraform
===================================

[Terraform output...]

✓ Infrastructure provisioned
✓ Instance IP: 54.123.45.67

===================================
Running Ansible Deployment
===================================

[Ansible output...]

✓ Application deployed

===================================
Deployment Complete
===================================

Your application has been deployed successfully!

Cloud Provider:  aws
Environment:     demo
Instance IP:     54.123.45.67

Access your application:
  http://54.123.45.67

SSH into the instance:
  ssh -i /path/to/key.pem ubuntu@54.123.45.67
```

## Destroy Infrastructure

When you're done testing:

```bash
cd infrastructure/scripts
./destroy.sh
```

Type `destroy` when prompted to confirm.

## Need Help?

See the full [README.md](README.md) for:
- Detailed configuration options
- Troubleshooting guide
- Manual deployment steps
- Security considerations
- Cost estimates
