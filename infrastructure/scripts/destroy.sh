#!/bin/bash
# Script to destroy infrastructure created by deploy.sh

set -e

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")/terraform"

echo -e "${BLUE}===================================${NC}"
echo -e "${BLUE}Infrastructure Destruction${NC}"
echo -e "${BLUE}===================================${NC}\n"

echo -e "${RED}WARNING: This will destroy all infrastructure!${NC}"
echo -e "${YELLOW}This action cannot be undone.${NC}\n"

read -p "Are you absolutely sure? Type 'destroy' to confirm: " confirm

if [ "$confirm" != "destroy" ]; then
    echo -e "${YELLOW}Destruction cancelled${NC}"
    exit 0
fi

cd "$TERRAFORM_DIR"

echo -e "\n${BLUE}Running terraform destroy...${NC}\n"
terraform destroy

echo -e "\n${BLUE}Cleaning up local files...${NC}"
rm -f deploy.auto.tfvars
rm -f tfplan
rm -rf ../keys/*

echo -e "\n${BLUE}Infrastructure destroyed successfully${NC}\n"
