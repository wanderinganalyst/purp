# Makefile for Infrastructure Management

.PHONY: help install check deploy destroy plan clean

help:
	@echo "BecauseImStuck Infrastructure Management"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install required tools (Ansible)"
	@echo "  make check      - Check prerequisites"
	@echo "  make deploy     - Deploy infrastructure and application"
	@echo "  make plan       - Show Terraform plan only"
	@echo "  make destroy    - Destroy infrastructure"
	@echo "  make clean      - Clean temporary files"
	@echo ""

install:
	@echo "Installing Ansible..."
	pip install -r ansible/requirements.txt
	@echo "✓ Ansible installed"
	@echo ""
	@echo "Please install Terraform manually:"
	@echo "  https://learn.hashicorp.com/tutorials/terraform/install-cli"

check:
	@echo "Checking prerequisites..."
	@command -v terraform >/dev/null 2>&1 || { echo "✗ Terraform not found"; exit 1; }
	@echo "✓ Terraform: $$(terraform version -json | jq -r .terraform_version)"
	@command -v ansible >/dev/null 2>&1 || { echo "✗ Ansible not found"; exit 1; }
	@echo "✓ Ansible: $$(ansible --version | head -n1)"
	@command -v jq >/dev/null 2>&1 || { echo "✗ jq not found"; exit 1; }
	@echo "✓ jq installed"
	@echo ""
	@echo "All prerequisites met!"

deploy:
	@./scripts/deploy.sh

plan:
	@cd terraform && terraform init && terraform plan

destroy:
	@./scripts/destroy.sh

clean:
	@echo "Cleaning temporary files..."
	@rm -f terraform/tfplan
	@rm -f terraform/deploy.auto.tfvars
	@rm -f ansible/inventory.ini
	@echo "✓ Cleaned"
