# Pre-Deployment Checklist

## ✅ **Domain Safety Verification**

### Existing Website Protection
- [x] Configuration uses **chat.dataibridge.com** subdomain
- [x] Existing **dataibridge.com** website will remain untouched
- [x] No changes to root domain DNS required

### Subdomain Structure
```
dataibridge.com              → Existing website (UNCHANGED)
chat.dataibridge.com         → Secure AI Chat main app
api.dataibridge.com          → API endpoints
admin.dataibridge.com        → Admin interface
static.dataibridge.com       → Static assets (CDN)
```

## 🔧 **Technical Prerequisites**

### Local Tools (✅ Completed)
- [x] Terraform v1.5.7 installed
- [x] AWS CLI v2.28.8 installed
- [x] kubectl v1.30.5 installed
- [x] Docker v27.4.0 installed
- [x] SSH keys generated (~/.ssh/id_rsa)

## ⚙️ **Configuration Updates Required**

### 1. Update Email Addresses
Edit `terraform.tfvars` and replace:
```hcl
alert_email_addresses = [
  "your-actual-admin@dataibridge.com",    # Replace with real email
  "your-actual-tech@dataibridge.com"      # Replace with real email
]
```

### 2. AWS Account Setup
```bash
# Configure AWS credentials (after AWS account creation)
aws configure
# Enter: Access Key ID, Secret Access Key, Region (ap-northeast-1)
```

### 3. Verify Route53 Hosted Zone
Ensure `dataibridge.com` hosted zone exists in AWS Route53:
```bash
# After AWS setup, verify existing zone
aws route53 list-hosted-zones-by-name --dns-name dataibridge.com
```

## 💰 **Cost Estimates**

### Optimized Configuration
- **EKS Cluster**: ~$73/month
- **RDS t3.micro**: ~$15/month
- **Redis t3.micro**: ~$15/month
- **ALB**: ~$20/month
- **CloudFront**: ~$5/month
- **Data Transfer**: ~$10/month
- **Monitoring**: ~$10/month

**Total Estimated**: ~$150/month

### Scale-up Options (Later)
- Increase instance sizes as traffic grows
- Enable Performance Insights
- Add more EKS nodes
- Upgrade database instance

## 🔐 **Security Notes**

### Enabled Security Features
- WAF with rate limiting
- SSL/TLS encryption everywhere
- VPC with private subnets
- Security Groups with minimal access
- CloudTrail audit logging
- GuardDuty threat detection
- Encrypted storage (RDS, S3, EBS)

### Initial Settings (Development-friendly)
- `enable_deletion_protection = false` (for easy cleanup)
- Smaller instances for cost optimization
- Performance Insights disabled initially

## 🚀 **Deployment Commands**

### Quick Deployment
```bash
cd Desktop/secure-ai-chat/terraform

# Initialize Terraform
make init

# Review deployment plan
make plan

# Deploy infrastructure
make apply

# Update kubectl config
make kubeconfig

# Deploy applications
kubectl apply -f ../k8s/
```

### Environment-Specific Deployment
```bash
# Development environment
make dev-deploy

# Production environment
make prod-deploy
```

## 📋 **Post-Deployment Verification**

### 1. Check DNS Resolution
```bash
# Wait 30-60 minutes for SSL certificate validation
dig chat.dataibridge.com
nslookup api.dataibridge.com
```

### 2. Verify Services
```bash
# Check EKS cluster
kubectl get nodes
kubectl get pods -A

# Check endpoints
curl -k https://chat.dataibridge.com/health
curl -k https://api.dataibridge.com/health
```

### 3. Monitor Costs
- AWS Cost Explorer
- CloudWatch billing alarms
- Resource tagging for cost tracking

## ⚠️ **Safety Reminders**

1. **Existing Website**: Configuration designed to NOT impact dataibridge.com
2. **Gradual Rollout**: Start with small instances, scale as needed
3. **Monitoring**: Email alerts configured for all critical metrics
4. **Backups**: Automatic daily backups enabled
5. **Security**: All AWS security best practices implemented

## 🆘 **Rollback Plan**

If needed, complete infrastructure removal:
```bash
# Remove applications first
kubectl delete -f ../k8s/

# Destroy infrastructure
make destroy

# Confirm: No impact on existing dataibridge.com website
```

---
**Ready for deployment when AWS account is set up and email addresses are updated!**