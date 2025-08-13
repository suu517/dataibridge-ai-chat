# Secure AI Chat - AWS Infrastructure

This Terraform configuration deploys a production-ready, scalable infrastructure for the Secure AI Chat SaaS application on AWS.

## Architecture Overview

```
Internet → CloudFront → WAF → ALB → EKS Cluster
                      ↓
                   S3 (Static Assets)
                      ↓
            RDS PostgreSQL & Redis ElastiCache
```

### Key Components

1. **Amazon EKS Cluster** - Kubernetes orchestration
2. **Application Load Balancer** - Traffic distribution
3. **CloudFront CDN** - Global content delivery
4. **Route53** - DNS management
5. **ACM SSL Certificates** - HTTPS encryption
6. **RDS PostgreSQL** - Primary database
7. **ElastiCache Redis** - Caching and sessions
8. **WAF v2** - Web application firewall
9. **S3** - Static asset storage
10. **Secrets Manager** - Secure credential storage

## Prerequisites

### 1. AWS CLI Configuration
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

### 2. Terraform Installation
```bash
# macOS
brew install terraform

# Verify installation
terraform version
```

### 3. kubectl Installation
```bash
# macOS
brew install kubectl

# Verify installation
kubectl version --client
```

### 4. SSH Key Pair
```bash
# Generate SSH key for EKS node access
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
```

## Deployment Instructions

### 1. Clone and Navigate
```bash
cd /path/to/secure-ai-chat/terraform
```

### 2. Configure Variables
```bash
# Copy example file
cp terraform.tfvars.example terraform.tfvars

# Edit variables
vi terraform.tfvars
```

### 3. Initialize Terraform
```bash
terraform init
```

### 4. Plan Deployment
```bash
terraform plan
```

### 5. Deploy Infrastructure
```bash
terraform apply
```

### 6. Configure kubectl
```bash
# Update kubeconfig
aws eks update-kubeconfig --region ap-northeast-1 --name secure-ai-chat-prod
```

## Configuration Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `aws_region` | AWS region for deployment | `ap-northeast-1` | No |
| `environment` | Environment name | `production` | No |
| `cluster_name` | EKS cluster name | `secure-ai-chat-prod` | No |
| `domain_name` | Primary domain name | `secure-ai-chat.com` | Yes |
| `vpc_cidr` | VPC CIDR block | `10.0.0.0/16` | No |
| `node_instance_types` | EKS node instance types | `["t3.large", "t3.xlarge"]` | No |
| `db_instance_class` | RDS instance class | `db.t3.medium` | No |
| `redis_node_type` | Redis node type | `cache.t3.micro` | No |

## Post-Deployment Steps

### 1. Domain Configuration
```bash
# Get name servers from output
terraform output route53_name_servers

# Update your domain registrar's DNS settings with these name servers
```

### 2. SSL Certificate Validation
The SSL certificate will be automatically validated via DNS. Monitor the certificate status:
```bash
aws acm describe-certificate --certificate-arn $(terraform output certificate_arn)
```

### 3. Database Setup
```bash
# Get database connection info
terraform output db_secret_arn

# Retrieve credentials from Secrets Manager
aws secretsmanager get-secret-value --secret-id $(terraform output db_secret_arn)
```

### 4. Deploy Application
```bash
# Apply Kubernetes manifests
kubectl apply -f ../k8s/
```

## Security Features

### Network Security
- **Private Subnets**: Application and database in private subnets
- **Security Groups**: Restrictive ingress/egress rules
- **NACLs**: Additional network-level protection

### Data Protection
- **Encryption at Rest**: RDS, Redis, and S3 encryption
- **Encryption in Transit**: TLS 1.2+ everywhere
- **Secrets Management**: AWS Secrets Manager for credentials

### WAF Protection
- **Rate Limiting**: 2000 requests per 5-minute period
- **AWS Managed Rules**: Core rule set and known bad inputs
- **Custom Rules**: Application-specific protection

### Access Control
- **IAM Roles**: Least privilege principle
- **EKS RBAC**: Kubernetes role-based access control
- **VPC Endpoints**: Secure AWS service access

## Monitoring and Logging

### CloudWatch Integration
- **EKS Cluster Logs**: API server, audit, authenticator
- **Application Logs**: Centralized logging
- **Metrics**: Custom and AWS metrics

### Performance Insights
- **RDS Monitoring**: Database performance analysis
- **Redis Metrics**: Cache performance monitoring

## Backup and Disaster Recovery

### Automated Backups
- **RDS**: 7-day backup retention
- **EKS**: Persistent volume snapshots
- **Configuration**: Terraform state backup

### High Availability
- **Multi-AZ Deployment**: Database and cache clusters
- **Auto Scaling**: EKS nodes and application pods
- **Load Balancing**: Traffic distribution across AZs

## Cost Optimization

### Resource Tagging
All resources are tagged for cost tracking:
```hcl
tags = {
  Project     = "secure-ai-chat"
  Environment = var.environment
  ManagedBy   = "terraform"
}
```

### Scaling Policies
- **EKS Nodes**: Auto-scaling based on demand
- **RDS**: Burstable instances for cost efficiency
- **CloudFront**: Regional edge caching

## Troubleshooting

### Common Issues

#### 1. EKS Cluster Access
```bash
# Check kubectl context
kubectl config current-context

# Update kubeconfig
aws eks update-kubeconfig --region ap-northeast-1 --name secure-ai-chat-prod
```

#### 2. Domain Resolution
```bash
# Check DNS propagation
dig secure-ai-chat.com
nslookup secure-ai-chat.com
```

#### 3. SSL Certificate Issues
```bash
# Check certificate status
aws acm describe-certificate --certificate-arn $(terraform output certificate_arn)
```

#### 4. Application Load Balancer Health
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn $(terraform output target_group_arn)
```

### Logs and Debugging

#### EKS Cluster Logs
```bash
# View cluster logs in CloudWatch
aws logs describe-log-groups --log-group-name-prefix "/aws/eks/secure-ai-chat-prod"
```

#### Application Logs
```bash
# View pod logs
kubectl logs -l app=secure-ai-chat -n default
```

## Cleanup

### Destroy Infrastructure
```bash
# Remove Kubernetes resources first
kubectl delete -f ../k8s/

# Destroy Terraform resources
terraform destroy
```

**Warning**: This will permanently delete all resources and data. Ensure you have backups before proceeding.

## Support and Maintenance

### Regular Updates
- **Terraform Providers**: Keep AWS provider updated
- **EKS Version**: Regular Kubernetes version updates
- **Security Patches**: Monitor and apply security updates

### Monitoring
- **CloudWatch Alarms**: Set up alerts for critical metrics
- **Cost Alerts**: Monitor spending and usage
- **Security Scanning**: Regular security assessments

## Additional Resources

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AWS Security Best Practices](https://aws.amazon.com/security/security-learning/)

## License

This infrastructure code is part of the Secure AI Chat project. See the main project README for licensing information.