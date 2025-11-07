# Infrastructure Testing Checklist

## Pre-Deployment Tests

### ✅ Prerequisites Check
- [ ] Terraform installed (>= 1.0)
- [ ] Ansible installed (>= 2.9)
- [ ] jq installed
- [ ] Python 3 installed
- [ ] Git installed

### ✅ Cloud Credentials
- [ ] AWS credentials configured (if using AWS)
- [ ] Azure CLI logged in (if using Azure)
- [ ] GCP credentials configured (if using GCP)

### ✅ Code Validation
```bash
# Terraform validation
cd infrastructure/terraform
terraform init
terraform validate

# Ansible syntax check
cd ../ansible
ansible-playbook --syntax-check playbooks/deploy-app.yml
```

## Deployment Tests

### Demo Environment (Recommended First)

#### AWS Demo
- [ ] Deploy: `./scripts/deploy.sh` → Select AWS → Select Demo
- [ ] Instance created successfully
- [ ] SSH key generated in `keys/`
- [ ] Can SSH to instance
- [ ] Application responds on port 80
- [ ] Application responds on port 5000
- [ ] Nginx is running
- [ ] Gunicorn is running
- [ ] Systemd service is active
- [ ] Logs are accessible via journalctl
- [ ] Destroy: `./scripts/destroy.sh`
- [ ] Resources cleaned up

#### Azure Demo
- [ ] Deploy: `./scripts/deploy.sh` → Select Azure → Select Demo
- [ ] Resource group created
- [ ] VM created successfully
- [ ] SSH key generated in `keys/`
- [ ] Can SSH to instance
- [ ] Application responds on port 80
- [ ] Application responds on port 5000
- [ ] Nginx is running
- [ ] Gunicorn is running
- [ ] Systemd service is active
- [ ] Logs are accessible via journalctl
- [ ] Destroy: `./scripts/destroy.sh`
- [ ] Resources cleaned up

#### GCP Demo
- [ ] Deploy: `./scripts/deploy.sh` → Select GCP → Select Demo
- [ ] Enter project ID
- [ ] Compute instance created
- [ ] SSH key generated in `keys/`
- [ ] Can SSH to instance
- [ ] Application responds on port 80
- [ ] Application responds on port 5000
- [ ] Nginx is running
- [ ] Gunicorn is running
- [ ] Systemd service is active
- [ ] Logs are accessible via journalctl
- [ ] Destroy: `./scripts/destroy.sh`
- [ ] Resources cleaned up

### Production Environment

#### AWS Production
- [ ] Deploy: `./scripts/deploy.sh` → Select AWS → Select Production
- [ ] Instance type is t3.medium
- [ ] Disk size is 30GB
- [ ] All services running
- [ ] Application accessible
- [ ] Performance is acceptable
- [ ] Destroy: `./scripts/destroy.sh`

#### Azure Production
- [ ] Deploy: `./scripts/deploy.sh` → Select Azure → Select Production
- [ ] VM size is Standard_B2s
- [ ] Disk size is 30GB
- [ ] All services running
- [ ] Application accessible
- [ ] Performance is acceptable
- [ ] Destroy: `./scripts/destroy.sh`

#### GCP Production
- [ ] Deploy: `./scripts/deploy.sh` → Select GCP → Select Production
- [ ] Machine type is e2-medium
- [ ] Disk size is 30GB
- [ ] All services running
- [ ] Application accessible
- [ ] Performance is acceptable
- [ ] Destroy: `./scripts/destroy.sh`

## Functional Tests

### Application Tests (Run on deployed instance)

```bash
# SSH into instance
ssh -i keys/purp-*-*.pem ubuntu@<INSTANCE-IP>

# Check systemd service
sudo systemctl status purp
# Should show: Active: active (running)

# Check nginx
sudo systemctl status nginx
# Should show: Active: active (running)

# Check application logs
sudo journalctl -u purp -n 50
# Should show Flask/Gunicorn logs

# Check processes
ps aux | grep gunicorn
# Should show 4 worker processes

# Check listening ports
sudo netstat -tlnp | grep -E '(80|5000)'
# Should show nginx on :80 and gunicorn on :5000

# Test database
cd /home/appuser/purp
source .venv/bin/activate
python -c "from models import db; print('DB OK')"

# Check disk space
df -h
# Should show available space

# Check memory
free -h
# Should show available memory
```

### HTTP Tests (Run from local machine)

```bash
# Replace <INSTANCE-IP> with your instance IP

# Test HTTP connection
curl -I http://<INSTANCE-IP>
# Should return: HTTP/1.1 200 OK

# Test application response
curl http://<INSTANCE-IP>
# Should return HTML

# Test direct application port
curl http://<INSTANCE-IP>:5000
# Should return HTML

# Test health endpoint (if configured)
curl http://<INSTANCE-IP>/health
# Should return: OK

# Test with browser
open http://<INSTANCE-IP>  # macOS
# or visit in browser
```

### Security Tests

```bash
# Test SSH key authentication
ssh -i keys/purp-*-*.pem ubuntu@<INSTANCE-IP> "echo 'SSH works'"
# Should print: SSH works

# Verify no password authentication
ssh ubuntu@<INSTANCE-IP>
# Should fail without key

# Check firewall rules (AWS example)
aws ec2 describe-security-groups --group-ids <SG-ID>
# Should show ports 22, 80, 443, 5000

# Check file permissions
ssh -i keys/purp-*-*.pem ubuntu@<INSTANCE-IP> "ls -la ~/purp/.env"
# Should show: -rw------- (600)

# Verify SSH key permissions
ls -la keys/
# Should show: -rw------- (600) for .pem files
```

## Idempotency Tests

### Re-run Terraform
```bash
cd infrastructure/terraform
terraform apply
# Should show: No changes. Infrastructure is up-to-date.
```

### Re-run Ansible
```bash
cd infrastructure/ansible
ansible-playbook -i inventory.ini playbooks/deploy-app.yml
# Should complete with "ok" changes, minimal "changed"
```

### Re-run Deploy Script
```bash
cd infrastructure/scripts
./deploy.sh
# Should succeed with minimal changes
```

## Cleanup Tests

### Destroy Infrastructure
```bash
cd infrastructure/scripts
./destroy.sh
# Type: destroy
# Should remove all cloud resources
```

### Verify Cleanup
```bash
# AWS
aws ec2 describe-instances --filters "Name=tag:Project,Values=Purp"
# Should show no running instances

# Azure
az vm list -g purp-*-rg
# Should show empty array

# GCP
gcloud compute instances list --filter="labels.project=purp"
# Should show no instances

# Check local files cleaned
ls infrastructure/terraform/
# Should not contain: tfplan, deploy.auto.tfvars

ls infrastructure/keys/
# Should be empty
```

## Error Handling Tests

### Invalid Cloud Provider
```bash
# Manually edit main.tf to set cloud_provider = "invalid"
terraform plan
# Should show: Invalid value for variable
```

### Missing Credentials
```bash
# Unset cloud credentials
unset AWS_ACCESS_KEY_ID
./deploy.sh
# Should show: AWS credentials not found
```

### SSH Connection Failure
```bash
# Deploy but block SSH in firewall
# Deploy should timeout with helpful message
```

### Ansible Failure
```bash
# Deploy but modify playbook to have syntax error
# Should fail with clear error message
```

## Performance Tests

### Application Response Time
```bash
# Install Apache Bench
brew install httpd  # macOS
sudo apt-get install apache2-utils  # Linux

# Run load test (100 requests, 10 concurrent)
ab -n 100 -c 10 http://<INSTANCE-IP>/
# Check: Requests per second, Time per request
```

### Database Performance
```bash
# SSH to instance
ssh -i keys/purp-*-*.pem ubuntu@<INSTANCE-IP>

# Run Python performance test
cd /home/appuser/purp
source .venv/bin/activate
python -c "
import time
from models import db, User
start = time.time()
for i in range(100):
    user = User(username=f'test{i}', email=f'test{i}@example.com')
    db.session.add(user)
db.session.commit()
print(f'100 inserts: {time.time()-start:.2f}s')
"
```

## Cost Verification

### AWS Cost
```bash
# Check estimated cost
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://filter.json
```

### Azure Cost
```bash
# Check cost analysis
az consumption usage list \
  --start-date 2024-01-01 \
  --end-date 2024-01-31
```

### GCP Cost
```bash
# Check billing
gcloud billing accounts list
gcloud billing budgets list
```

## Documentation Tests

### README Accuracy
- [ ] All prerequisites listed are actually needed
- [ ] Installation commands work
- [ ] Example outputs match actual outputs
- [ ] Troubleshooting steps are helpful
- [ ] Links are valid

### Code Comments
- [ ] Terraform modules are well-commented
- [ ] Ansible playbooks explain each task
- [ ] Scripts have helpful error messages

## Compatibility Tests

### Terraform Versions
- [ ] Works with Terraform 1.0.x
- [ ] Works with Terraform 1.5.x
- [ ] Works with Terraform 1.6.x

### Ansible Versions
- [ ] Works with Ansible 2.9
- [ ] Works with Ansible 2.14
- [ ] Works with Ansible 2.15

### Python Versions
- [ ] Works with Python 3.8
- [ ] Works with Python 3.10
- [ ] Works with Python 3.11

### OS Tests
- [ ] macOS (local machine)
- [ ] Linux (local machine)
- [ ] Ubuntu 22.04 (deployed instance)

## Final Checklist

- [ ] All demo deployments work (AWS, Azure, GCP)
- [ ] All production deployments work
- [ ] Application is accessible
- [ ] All services are running
- [ ] Logs are available
- [ ] Destroy works cleanly
- [ ] No sensitive data in Git
- [ ] Documentation is complete
- [ ] Error messages are helpful
- [ ] Performance is acceptable

## Test Results Template

```
Date: ___________
Tester: _________

Environment: [ ] Demo [ ] Production
Cloud: [ ] AWS [ ] Azure [ ] GCP

Pre-Deployment:
  Prerequisites: [ ] Pass [ ] Fail
  Credentials: [ ] Pass [ ] Fail
  Validation: [ ] Pass [ ] Fail

Deployment:
  Terraform: [ ] Pass [ ] Fail
  Ansible: [ ] Pass [ ] Fail
  Time taken: _____ minutes

Functionality:
  HTTP 80: [ ] Pass [ ] Fail
  HTTP 5000: [ ] Pass [ ] Fail
  SSH: [ ] Pass [ ] Fail
  Systemd: [ ] Pass [ ] Fail
  Nginx: [ ] Pass [ ] Fail
  Gunicorn: [ ] Pass [ ] Fail
  Database: [ ] Pass [ ] Fail

Cleanup:
  Destroy: [ ] Pass [ ] Fail
  Verification: [ ] Pass [ ] Fail

Issues Found:
_________________________________
_________________________________
_________________________________

Notes:
_________________________________
_________________________________
_________________________________

Overall: [ ] Pass [ ] Fail
```

## Automated Testing Script

Save as `test-infrastructure.sh`:

```bash
#!/bin/bash
# Automated infrastructure testing

set -e

echo "Starting infrastructure tests..."

# Test 1: Check prerequisites
echo "Test 1: Prerequisites"
command -v terraform >/dev/null 2>&1 && echo "✓ Terraform" || echo "✗ Terraform"
command -v ansible >/dev/null 2>&1 && echo "✓ Ansible" || echo "✗ Ansible"
command -v jq >/dev/null 2>&1 && echo "✓ jq" || echo "✗ jq"

# Test 2: Validate Terraform
echo "Test 2: Terraform validation"
cd terraform
terraform init > /dev/null 2>&1
terraform validate && echo "✓ Valid" || echo "✗ Invalid"
cd ..

# Test 3: Ansible syntax
echo "Test 3: Ansible syntax"
ansible-playbook --syntax-check ansible/playbooks/deploy-app.yml && \
  echo "✓ Valid" || echo "✗ Invalid"

# Test 4: Check documentation
echo "Test 4: Documentation"
[ -f README.md ] && echo "✓ README exists" || echo "✗ Missing README"
[ -f QUICKSTART.md ] && echo "✓ QUICKSTART exists" || echo "✗ Missing QUICKSTART"

echo "Tests complete!"
```
