#!/bin/bash
# Automated Deployment Script for Purp
# Deploys to AWS, Azure, or GCP using Terraform and Ansible

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$INFRA_DIR/terraform"
ANSIBLE_DIR="$INFRA_DIR/ansible"
KEYS_DIR="$INFRA_DIR/keys"

# Functions
print_header() {
    echo -e "\n${BLUE}===================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_tools=()
    
    if ! command -v terraform &> /dev/null; then
        missing_tools+=("terraform")
    else
        print_success "Terraform found: $(terraform version -json | jq -r .terraform_version)"
    fi
    
    if ! command -v ansible &> /dev/null; then
        missing_tools+=("ansible")
    else
        print_success "Ansible found: $(ansible --version | head -n1)"
    fi
    
    if ! command -v jq &> /dev/null; then
        missing_tools+=("jq")
    else
        print_success "jq found"
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        echo ""
        echo "Installation instructions:"
        echo "  Terraform: https://learn.hashicorp.com/tutorials/terraform/install-cli"
        echo "  Ansible:   pip install ansible"
        echo "  jq:        brew install jq (macOS) or apt-get install jq (Ubuntu)"
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Select cloud provider
select_cloud_provider() {
    print_header "Select Cloud Provider"
    
    echo "Available cloud providers:"
    echo "  1) AWS"
    echo "  2) Azure"
    echo "  3) GCP"
    echo ""
    read -p "Enter your choice (1-3): " choice
    
    case $choice in
        1)
            CLOUD_PROVIDER="aws"
            print_success "Selected: AWS"
            ;;
        2)
            CLOUD_PROVIDER="azure"
            print_success "Selected: Azure"
            ;;
        3)
            CLOUD_PROVIDER="gcp"
            print_success "Selected: GCP"
            read -p "Enter your GCP Project ID: " GCP_PROJECT_ID
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

# Select environment
select_environment() {
    print_header "Select Environment"
    
    echo "Available environments:"
    echo "  1) Production (larger resources)"
    echo "  2) Demo (minimal resources)"
    echo ""
    read -p "Enter your choice (1-2): " choice
    
    case $choice in
        1)
            ENVIRONMENT="production"
            print_success "Selected: Production"
            ;;
        2)
            ENVIRONMENT="demo"
            print_success "Selected: Demo"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

# Verify cloud credentials
verify_credentials() {
    print_header "Verifying Cloud Credentials"
    
    case $CLOUD_PROVIDER in
        aws)
            if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
                print_warning "AWS credentials not found in environment"
                print_info "Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
                print_info "Or configure AWS CLI: aws configure"
                exit 1
            fi
            print_success "AWS credentials found"
            ;;
        azure)
            if ! az account show &> /dev/null; then
                print_warning "Not logged in to Azure"
                print_info "Please login: az login"
                exit 1
            fi
            print_success "Azure credentials verified"
            ;;
        gcp)
            if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
                print_warning "GCP credentials not found in environment"
                print_info "Please set GOOGLE_APPLICATION_CREDENTIALS"
                print_info "Or login: gcloud auth application-default login"
                exit 1
            fi
            print_success "GCP credentials found"
            ;;
    esac
}

# Create keys directory
create_keys_dir() {
    mkdir -p "$KEYS_DIR"
    chmod 700 "$KEYS_DIR"
}

# Run Terraform
run_terraform() {
    print_header "Running Terraform"
    
    cd "$TERRAFORM_DIR"
    
    # Initialize Terraform
    print_info "Initializing Terraform..."
    terraform init
    print_success "Terraform initialized"
    
    # Create tfvars file
    TFVARS_FILE="deploy.auto.tfvars"
    cat > "$TFVARS_FILE" <<EOF
cloud_provider = "$CLOUD_PROVIDER"
environment    = "$ENVIRONMENT"
app_port       = 5000
EOF
    
    if [ "$CLOUD_PROVIDER" == "gcp" ]; then
        echo "gcp_project_id = \"$GCP_PROJECT_ID\"" >> "$TFVARS_FILE"
    fi
    
    # Plan
    print_info "Creating Terraform plan..."
    terraform plan -out=tfplan
    print_success "Terraform plan created"
    
    # Apply
    echo ""
    read -p "Do you want to apply this plan? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_warning "Deployment cancelled"
        exit 0
    fi
    
    print_info "Applying Terraform configuration..."
    terraform apply tfplan
    print_success "Infrastructure provisioned"
    
    # Get outputs
    INSTANCE_IP=$(terraform output -raw instance_ip)
    SSH_COMMAND=$(terraform output -raw ssh_command)
    
    print_success "Instance IP: $INSTANCE_IP"
}

# Wait for instance to be ready
wait_for_instance() {
    print_header "Waiting for Instance to be Ready"
    
    print_info "Waiting for SSH to be available on $INSTANCE_IP..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes \
               $(echo $SSH_COMMAND | awk '{for(i=3;i<=NF;i++) printf $i" "}') \
               "echo 'SSH is ready'" &> /dev/null; then
            print_success "SSH connection established"
            return 0
        fi
        
        echo -n "."
        sleep 10
        ((attempt++))
    done
    
    print_error "Instance did not become ready in time"
    exit 1
}

# Run Ansible
run_ansible() {
    print_header "Running Ansible Deployment"
    
    cd "$ANSIBLE_DIR"
    
    # Create inventory file
    cat > inventory.ini <<EOF
[app]
$INSTANCE_IP

[app:vars]
ansible_user=$(echo $SSH_COMMAND | awk -F'@' '{print substr($1, length($1)-length($2)+1)}' | awk '{print $NF}')
ansible_ssh_private_key_file=$KEYS_DIR/$(ls $KEYS_DIR | grep "${CLOUD_PROVIDER}.pem")
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
environment=$ENVIRONMENT
app_port=5000
EOF
    
    # Run playbook
    print_info "Deploying application with Ansible..."
    ansible-playbook -i inventory.ini playbooks/deploy-app.yml
    
    print_success "Application deployed"
}

# Display deployment info
display_deployment_info() {
    print_header "Deployment Complete"
    
    echo -e "${GREEN}Your application has been deployed successfully!${NC}\n"
    echo "Cloud Provider:  $CLOUD_PROVIDER"
    echo "Environment:     $ENVIRONMENT"
    echo "Instance IP:     $INSTANCE_IP"
    echo ""
    echo "Access your application:"
    echo -e "${BLUE}  http://$INSTANCE_IP${NC}"
    echo ""
    echo "SSH into the instance:"
    echo -e "${BLUE}  $SSH_COMMAND${NC}"
    echo ""
    echo "View application logs:"
    echo -e "${BLUE}  ssh [...] 'journalctl -u purp -f'${NC}"
    echo ""
    echo "To destroy the infrastructure:"
    echo -e "${BLUE}  cd $TERRAFORM_DIR && terraform destroy${NC}"
    echo ""
}

# Main execution
main() {
    print_header "Purp Deployment Script"
    
    check_prerequisites
    select_cloud_provider
    select_environment
    verify_credentials
    create_keys_dir
    run_terraform
    wait_for_instance
    run_ansible
    display_deployment_info
}

# Run main function
main
