# ==============================================================================
# Secure AI Chat Infrastructure Makefile
# ==============================================================================

.PHONY: help init plan apply destroy validate format check-deps clean

# Default values
ENVIRONMENT ?= production
REGION ?= ap-northeast-1
DOMAIN ?= secure-ai-chat.com

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Display this help message
	@echo "$(GREEN)Secure AI Chat Infrastructure Management$(NC)"
	@echo ""
	@echo "$(YELLOW)Usage:$(NC)"
	@echo "  make [target] [ENVIRONMENT=production] [REGION=ap-northeast-1] [DOMAIN=secure-ai-chat.com]"
	@echo ""
	@echo "$(YELLOW)Targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check-deps: ## Check required dependencies
	@echo "$(YELLOW)Checking dependencies...$(NC)"
	@command -v terraform >/dev/null 2>&1 || { echo "$(RED)Terraform is required but not installed.$(NC)" >&2; exit 1; }
	@command -v aws >/dev/null 2>&1 || { echo "$(RED)AWS CLI is required but not installed.$(NC)" >&2; exit 1; }
	@command -v kubectl >/dev/null 2>&1 || { echo "$(RED)kubectl is required but not installed.$(NC)" >&2; exit 1; }
	@echo "$(GREEN)All dependencies are installed.$(NC)"

validate-vars: ## Validate required variables
	@echo "$(YELLOW)Validating configuration...$(NC)"
	@if [ ! -f terraform.tfvars ]; then \
		echo "$(RED)terraform.tfvars not found. Please copy terraform.tfvars.example and configure it.$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f ~/.ssh/id_rsa.pub ]; then \
		echo "$(RED)SSH public key not found at ~/.ssh/id_rsa.pub. Please generate SSH keys.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Configuration validated.$(NC)"

init: check-deps validate-vars ## Initialize Terraform
	@echo "$(YELLOW)Initializing Terraform...$(NC)"
	terraform init
	@echo "$(GREEN)Terraform initialized successfully.$(NC)"

format: ## Format Terraform files
	@echo "$(YELLOW)Formatting Terraform files...$(NC)"
	terraform fmt -recursive .
	@echo "$(GREEN)Terraform files formatted.$(NC)"

validate: format ## Validate Terraform configuration
	@echo "$(YELLOW)Validating Terraform configuration...$(NC)"
	terraform validate
	@echo "$(GREEN)Terraform configuration is valid.$(NC)"

plan: validate ## Plan Terraform deployment
	@echo "$(YELLOW)Planning Terraform deployment...$(NC)"
	terraform plan -var="environment=$(ENVIRONMENT)" -var="aws_region=$(REGION)" -var="domain_name=$(DOMAIN)" -out=tfplan
	@echo "$(GREEN)Terraform plan completed. Review the changes above.$(NC)"

apply: ## Apply Terraform configuration
	@echo "$(YELLOW)Applying Terraform configuration...$(NC)"
	@if [ -f tfplan ]; then \
		terraform apply tfplan; \
	else \
		echo "$(RED)No plan file found. Run 'make plan' first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Infrastructure deployed successfully!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "1. Configure DNS with the following name servers:"
	@terraform output route53_name_servers
	@echo "2. Wait for SSL certificate validation (may take up to 30 minutes)"
	@echo "3. Update kubeconfig:"
	@echo "   aws eks update-kubeconfig --region $(REGION) --name $(shell terraform output -raw cluster_id 2>/dev/null || echo 'secure-ai-chat-prod')"
	@echo "4. Deploy applications:"
	@echo "   kubectl apply -f ../k8s/"

quick-deploy: init plan apply ## Quick deployment (init + plan + apply)

destroy-plan: ## Plan destruction of infrastructure
	@echo "$(YELLOW)Planning infrastructure destruction...$(NC)"
	@echo "$(RED)WARNING: This will plan the destruction of ALL infrastructure!$(NC)"
	@read -p "Are you sure you want to continue? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	terraform plan -destroy -var="environment=$(ENVIRONMENT)" -var="aws_region=$(REGION)" -var="domain_name=$(DOMAIN)" -out=destroy-plan
	@echo "$(YELLOW)Destruction plan completed. Review the changes above.$(NC)"

destroy: destroy-plan ## Destroy infrastructure (requires confirmation)
	@echo "$(RED)WARNING: This will PERMANENTLY DESTROY all infrastructure!$(NC)"
	@echo "$(RED)This action cannot be undone!$(NC)"
	@read -p "Type 'DESTROY' to confirm: " confirm && [ "$$confirm" = "DESTROY" ]
	terraform apply destroy-plan
	@echo "$(RED)Infrastructure destroyed.$(NC)"

clean: ## Clean temporary files
	@echo "$(YELLOW)Cleaning temporary files...$(NC)"
	rm -f tfplan destroy-plan ebs_snapshot.zip
	rm -rf .terraform.lock.hcl
	@echo "$(GREEN)Cleanup completed.$(NC)"

status: ## Show infrastructure status
	@echo "$(YELLOW)Infrastructure Status:$(NC)"
	@if [ -f terraform.tfstate ]; then \
		terraform show -json | jq -r '.values.root_module.resources[] | select(.type == "aws_eks_cluster") | .values.status // "Unknown"'; \
	else \
		echo "$(RED)No state file found. Infrastructure may not be deployed.$(NC)"; \
	fi

outputs: ## Show Terraform outputs
	@echo "$(YELLOW)Terraform Outputs:$(NC)"
	@terraform output

kubeconfig: ## Update kubectl configuration
	@echo "$(YELLOW)Updating kubeconfig...$(NC)"
	aws eks update-kubeconfig --region $(REGION) --name $(shell terraform output -raw cluster_id 2>/dev/null || echo 'secure-ai-chat-prod')
	@echo "$(GREEN)kubeconfig updated.$(NC)"

check-health: ## Check infrastructure health
	@echo "$(YELLOW)Checking infrastructure health...$(NC)"
	@echo "EKS Cluster Status:"
	@aws eks describe-cluster --region $(REGION) --name $(shell terraform output -raw cluster_id 2>/dev/null || echo 'secure-ai-chat-prod') --query 'cluster.status' --output text 2>/dev/null || echo "Cluster not found"
	@echo ""
	@echo "RDS Instance Status:"
	@aws rds describe-db-instances --region $(REGION) --db-instance-identifier $(shell terraform output -raw cluster_id 2>/dev/null || echo 'secure-ai-chat-prod')-db --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null || echo "Database not found"
	@echo ""
	@echo "CloudFront Distribution Status:"
	@aws cloudfront list-distributions --query 'DistributionList.Items[?Comment==`$(shell terraform output -raw cluster_id 2>/dev/null || echo 'secure-ai-chat-prod')-cloudfront`].Status' --output text 2>/dev/null || echo "Distribution not found"

backup-state: ## Backup Terraform state
	@echo "$(YELLOW)Backing up Terraform state...$(NC)"
	@if [ -f terraform.tfstate ]; then \
		cp terraform.tfstate terraform.tfstate.backup.$(shell date +%Y%m%d_%H%M%S); \
		echo "$(GREEN)State backed up.$(NC)"; \
	else \
		echo "$(RED)No state file found.$(NC)"; \
	fi

security-scan: ## Run security scan on Terraform files
	@echo "$(YELLOW)Running security scan...$(NC)"
	@if command -v tfsec >/dev/null 2>&1; then \
		tfsec .; \
	else \
		echo "$(YELLOW)tfsec not installed. Install it for security scanning: https://github.com/aquasecurity/tfsec$(NC)"; \
	fi

cost-estimate: ## Estimate infrastructure costs
	@echo "$(YELLOW)Estimating infrastructure costs...$(NC)"
	@if command -v infracost >/dev/null 2>&1; then \
		infracost breakdown --path .; \
	else \
		echo "$(YELLOW)infracost not installed. Install it for cost estimation: https://www.infracost.io/$(NC)"; \
	fi

docs: ## Generate documentation
	@echo "$(YELLOW)Generating documentation...$(NC)"
	@if command -v terraform-docs >/dev/null 2>&1; then \
		terraform-docs markdown table --output-file TERRAFORM_DOCS.md .; \
		echo "$(GREEN)Documentation generated in TERRAFORM_DOCS.md$(NC)"; \
	else \
		echo "$(YELLOW)terraform-docs not installed. Install it for documentation generation: https://terraform-docs.io/$(NC)"; \
	fi

upgrade: ## Upgrade Terraform providers
	@echo "$(YELLOW)Upgrading Terraform providers...$(NC)"
	terraform init -upgrade
	@echo "$(GREEN)Providers upgraded.$(NC)"

# Development targets
dev-init: ## Initialize for development environment
	@$(MAKE) init ENVIRONMENT=development REGION=ap-northeast-1 DOMAIN=dev.secure-ai-chat.com

dev-deploy: ## Deploy development environment
	@$(MAKE) quick-deploy ENVIRONMENT=development REGION=ap-northeast-1 DOMAIN=dev.secure-ai-chat.com

dev-destroy: ## Destroy development environment
	@$(MAKE) destroy ENVIRONMENT=development REGION=ap-northeast-1 DOMAIN=dev.secure-ai-chat.com

# Staging targets
staging-init: ## Initialize for staging environment
	@$(MAKE) init ENVIRONMENT=staging REGION=ap-northeast-1 DOMAIN=staging.secure-ai-chat.com

staging-deploy: ## Deploy staging environment
	@$(MAKE) quick-deploy ENVIRONMENT=staging REGION=ap-northeast-1 DOMAIN=staging.secure-ai-chat.com

staging-destroy: ## Destroy staging environment
	@$(MAKE) destroy ENVIRONMENT=staging REGION=ap-northeast-1 DOMAIN=staging.secure-ai-chat.com

# Production targets
prod-init: ## Initialize for production environment
	@$(MAKE) init ENVIRONMENT=production REGION=ap-northeast-1 DOMAIN=secure-ai-chat.com

prod-deploy: ## Deploy production environment
	@$(MAKE) quick-deploy ENVIRONMENT=production REGION=ap-northeast-1 DOMAIN=secure-ai-chat.com

prod-destroy: ## Destroy production environment
	@$(MAKE) destroy ENVIRONMENT=production REGION=ap-northeast-1 DOMAIN=secure-ai-chat.com