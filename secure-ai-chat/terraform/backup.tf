# ==============================================================================
# AWS Backup Configuration
# ==============================================================================

# IAM Role for AWS Backup
resource "aws_iam_role" "backup_role" {
  name = "${var.cluster_name}-backup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.cluster_name}-backup-role"
  }
}

resource "aws_iam_role_policy_attachment" "backup_policy" {
  role       = aws_iam_role.backup_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "restore_policy" {
  role       = aws_iam_role.backup_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

# KMS Key for Backup Encryption
resource "aws_kms_key" "backup" {
  description             = "Backup encryption key for ${var.cluster_name}"
  deletion_window_in_days = 7

  tags = {
    Name = "${var.cluster_name}-backup-key"
  }
}

resource "aws_kms_alias" "backup" {
  name          = "alias/${var.cluster_name}-backup"
  target_key_id = aws_kms_key.backup.key_id
}

# Backup Vault
resource "aws_backup_vault" "main" {
  name        = "${var.cluster_name}-backup-vault"
  kms_key_arn = aws_kms_key.backup.arn

  tags = {
    Name = "${var.cluster_name}-backup-vault"
  }
}

# Backup Plan for Daily Backups
resource "aws_backup_plan" "daily" {
  name = "${var.cluster_name}-daily-backup"

  rule {
    rule_name                = "daily_backup_rule"
    target_vault_name        = aws_backup_vault.main.name
    schedule                 = "cron(0 2 * * ? *)" # Daily at 2 AM UTC
    start_window             = 60                   # 1 hour
    completion_window        = 180                  # 3 hours
    enable_continuous_backup = true

    lifecycle {
      cold_storage_after = 30   # Move to cold storage after 30 days
      delete_after       = 365  # Delete after 1 year
    }

    recovery_point_tags = {
      BackupType = "Daily"
      Project    = var.cluster_name
    }
  }

  tags = {
    Name = "${var.cluster_name}-daily-backup"
  }
}

# Backup Plan for Weekly Backups
resource "aws_backup_plan" "weekly" {
  name = "${var.cluster_name}-weekly-backup"

  rule {
    rule_name         = "weekly_backup_rule"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 1 ? * SUN *)" # Weekly on Sunday at 1 AM UTC
    start_window      = 60                    # 1 hour
    completion_window = 300                   # 5 hours

    lifecycle {
      cold_storage_after = 30    # Move to cold storage after 30 days
      delete_after       = 2555  # Delete after 7 years
    }

    recovery_point_tags = {
      BackupType = "Weekly"
      Project    = var.cluster_name
    }
  }

  tags = {
    Name = "${var.cluster_name}-weekly-backup"
  }
}

# Backup Selection for RDS
resource "aws_backup_selection" "rds_daily" {
  iam_role_arn = aws_iam_role.backup_role.arn
  name         = "${var.cluster_name}-rds-daily"
  plan_id      = aws_backup_plan.daily.id

  resources = [
    aws_db_instance.main.arn
  ]

  condition {
    string_equals {
      key   = "aws:ResourceTag/Project"
      value = "secure-ai-chat"
    }
  }
}

resource "aws_backup_selection" "rds_weekly" {
  iam_role_arn = aws_iam_role.backup_role.arn
  name         = "${var.cluster_name}-rds-weekly"
  plan_id      = aws_backup_plan.weekly.id

  resources = [
    aws_db_instance.main.arn
  ]

  condition {
    string_equals {
      key   = "aws:ResourceTag/Project"
      value = "secure-ai-chat"
    }
  }
}

# ==============================================================================
# EBS Volume Backup (for EKS persistent volumes)
# ==============================================================================

# IAM Role for EBS Snapshot automation
resource "aws_iam_role" "ebs_snapshot_role" {
  name = "${var.cluster_name}-ebs-snapshot-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.cluster_name}-ebs-snapshot-role"
  }
}

resource "aws_iam_role_policy" "ebs_snapshot_policy" {
  name = "${var.cluster_name}-ebs-snapshot-policy"
  role = aws_iam_role.ebs_snapshot_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateSnapshot",
          "ec2:DeleteSnapshot",
          "ec2:DescribeSnapshots",
          "ec2:DescribeVolumes",
          "ec2:CreateTags"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda function for EBS snapshot automation
resource "aws_lambda_function" "ebs_snapshot" {
  filename         = "ebs_snapshot.zip"
  function_name    = "${var.cluster_name}-ebs-snapshot"
  role            = aws_iam_role.ebs_snapshot_role.arn
  handler         = "index.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300

  depends_on = [data.archive_file.ebs_snapshot_zip]

  environment {
    variables = {
      CLUSTER_NAME = var.cluster_name
    }
  }

  tags = {
    Name = "${var.cluster_name}-ebs-snapshot"
  }
}

# Create the Lambda deployment package
data "archive_file" "ebs_snapshot_zip" {
  type        = "zip"
  output_path = "ebs_snapshot.zip"
  
  source {
    content = <<EOF
import boto3
import json
import datetime
import os

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    cluster_name = os.environ['CLUSTER_NAME']
    
    # Get all EBS volumes tagged with the cluster name
    volumes = ec2.describe_volumes(
        Filters=[
            {
                'Name': 'tag:kubernetes.io/cluster/' + cluster_name,
                'Values': ['owned']
            },
            {
                'Name': 'state',
                'Values': ['in-use']
            }
        ]
    )
    
    # Create snapshots for each volume
    for volume in volumes['Volumes']:
        volume_id = volume['VolumeId']
        
        # Create snapshot
        snapshot = ec2.create_snapshot(
            VolumeId=volume_id,
            Description=f'Automated snapshot for {volume_id} - {cluster_name}'
        )
        
        # Tag the snapshot
        ec2.create_tags(
            Resources=[snapshot['SnapshotId']],
            Tags=[
                {'Key': 'Name', 'Value': f'{cluster_name}-{volume_id}-snapshot'},
                {'Key': 'Project', 'Value': 'secure-ai-chat'},
                {'Key': 'AutomatedBackup', 'Value': 'true'},
                {'Key': 'CreatedDate', 'Value': str(datetime.datetime.now())},
                {'Key': 'VolumeId', 'Value': volume_id}
            ]
        )
        
        print(f'Created snapshot {snapshot["SnapshotId"]} for volume {volume_id}')
    
    # Clean up old snapshots (older than 7 days)
    snapshots = ec2.describe_snapshots(
        OwnerIds=['self'],
        Filters=[
            {
                'Name': 'tag:Project',
                'Values': ['secure-ai-chat']
            },
            {
                'Name': 'tag:AutomatedBackup',
                'Values': ['true']
            }
        ]
    )
    
    for snapshot in snapshots['Snapshots']:
        # Calculate age
        start_time = snapshot['StartTime'].replace(tzinfo=None)
        age = datetime.datetime.now() - start_time
        
        if age.days > 7:
            print(f'Deleting old snapshot {snapshot["SnapshotId"]}')
            ec2.delete_snapshot(SnapshotId=snapshot['SnapshotId'])
    
    return {
        'statusCode': 200,
        'body': json.dumps('EBS snapshot automation completed successfully')
    }
EOF
    filename = "index.py"
  }
}

# CloudWatch Event Rule for daily EBS snapshots
resource "aws_cloudwatch_event_rule" "ebs_snapshot_schedule" {
  name                = "${var.cluster_name}-ebs-snapshot-schedule"
  description         = "Trigger EBS snapshot Lambda daily"
  schedule_expression = "cron(0 3 * * ? *)" # Daily at 3 AM UTC

  tags = {
    Name = "${var.cluster_name}-ebs-snapshot-schedule"
  }
}

resource "aws_cloudwatch_event_target" "ebs_snapshot_target" {
  rule      = aws_cloudwatch_event_rule.ebs_snapshot_schedule.name
  target_id = "EBSSnapshotTarget"
  arn       = aws_lambda_function.ebs_snapshot.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_ebs" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ebs_snapshot.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ebs_snapshot_schedule.arn
}

# ==============================================================================
# Disaster Recovery Documentation
# ==============================================================================

# S3 Bucket for DR documentation and scripts
resource "aws_s3_bucket" "dr_documentation" {
  bucket = "${var.cluster_name}-dr-documentation"

  tags = {
    Name = "${var.cluster_name}-dr-documentation"
  }
}

resource "aws_s3_bucket_versioning" "dr_documentation" {
  bucket = aws_s3_bucket.dr_documentation.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "dr_documentation" {
  bucket = aws_s3_bucket.dr_documentation.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "dr_documentation" {
  bucket = aws_s3_bucket.dr_documentation.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Upload DR runbook
resource "aws_s3_object" "dr_runbook" {
  bucket = aws_s3_bucket.dr_documentation.id
  key    = "disaster-recovery-runbook.md"
  content = <<EOF
# Disaster Recovery Runbook

## Overview
This document outlines the disaster recovery procedures for the Secure AI Chat application.

## Recovery Time Objective (RTO): 4 hours
## Recovery Point Objective (RPO): 1 hour

## Pre-requisites
- AWS CLI configured with appropriate permissions
- Terraform installed and configured
- kubectl installed and configured
- Access to AWS Backup console
- Emergency contact information

## Database Recovery

### RDS Recovery from Backup
1. Navigate to AWS Backup console
2. Select the latest recovery point for the RDS instance
3. Choose "Restore" and configure the new instance
4. Update application configuration with new endpoint

### Point-in-Time Recovery
```bash
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier ${var.cluster_name}-db \
  --target-db-instance-identifier ${var.cluster_name}-db-restored \
  --restore-time 2023-01-01T00:00:00.000Z
```

## EKS Cluster Recovery

### Full Cluster Recreation
```bash
# Navigate to terraform directory
cd terraform/

# Destroy existing cluster (if accessible)
terraform destroy -target=aws_eks_cluster.main

# Recreate cluster
terraform apply -target=aws_eks_cluster.main
terraform apply -target=aws_eks_node_group.main

# Update kubeconfig
aws eks update-kubeconfig --region ${var.aws_region} --name ${var.cluster_name}
```

### Application Deployment Recovery
```bash
# Redeploy applications
kubectl apply -f ../k8s/

# Verify deployment
kubectl get pods -A
kubectl get services -A
```

## Storage Recovery

### EBS Volume Recovery
```bash
# List available snapshots
aws ec2 describe-snapshots \
  --owner-ids self \
  --filters "Name=tag:Project,Values=secure-ai-chat"

# Create volume from snapshot
aws ec2 create-volume \
  --snapshot-id snap-xxxxxxxxx \
  --availability-zone ${var.aws_region}a \
  --volume-type gp3
```

## Network Recovery

### VPC and Networking
If the entire VPC needs to be recreated:
```bash
terraform destroy -target=aws_vpc.main
terraform apply -target=aws_vpc.main
terraform apply
```

## DNS and CDN Recovery

### Route53 Recovery
- Verify name servers are correctly configured
- Check DNS propagation: `dig secure-ai-chat.com`

### CloudFront Recovery
- Check distribution status in AWS console
- Invalidate cache if needed: `aws cloudfront create-invalidation`

## Monitoring Recovery

### CloudWatch Alarms
```bash
# Recreate monitoring resources
terraform apply -target=aws_cloudwatch_metric_alarm
```

## Testing Recovery

### Application Health Check
```bash
# Test application endpoints
curl -k https://secure-ai-chat.com/health
curl -k https://api.secure-ai-chat.com/health
```

### Database Connectivity
```bash
# Test database connection
kubectl exec -it <pod-name> -- psql -h <db-endpoint> -U postgres -d secureaichat
```

## Post-Recovery Tasks

1. Verify all services are operational
2. Check data integrity
3. Update monitoring dashboards
4. Notify stakeholders
5. Document lessons learned
6. Update this runbook if necessary

## Emergency Contacts

- AWS Support: [Support Case URL]
- On-call Engineer: [Phone Number]
- Team Lead: [Phone Number]
- Management: [Phone Number]

## Related Documentation

- [AWS Backup Console](https://console.aws.amazon.com/backup/)
- [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/)
- [EKS Console](https://console.aws.amazon.com/eks/)
EOF

  tags = {
    Name = "${var.cluster_name}-dr-runbook"
  }
}

# ==============================================================================
# Outputs
# ==============================================================================

output "backup_vault_arn" {
  description = "AWS Backup vault ARN"
  value       = aws_backup_vault.main.arn
}

output "backup_kms_key_arn" {
  description = "KMS key ARN for backup encryption"
  value       = aws_kms_key.backup.arn
}

output "dr_documentation_bucket" {
  description = "S3 bucket for disaster recovery documentation"
  value       = aws_s3_bucket.dr_documentation.bucket
}