# ==============================================================================
# Security and Compliance Configuration
# ==============================================================================

# AWS Config for compliance monitoring
resource "aws_config_configuration_recorder" "main" {
  name     = "${var.cluster_name}-config-recorder"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }

  depends_on = [aws_config_delivery_channel.main]
}

resource "aws_config_delivery_channel" "main" {
  name           = "${var.cluster_name}-config-delivery-channel"
  s3_bucket_name = aws_s3_bucket.config.bucket
  s3_key_prefix  = "config"

  snapshot_delivery_properties {
    delivery_frequency = "TwentyFour_Hours"
  }
}

# S3 bucket for AWS Config
resource "aws_s3_bucket" "config" {
  bucket        = "${var.cluster_name}-aws-config"
  force_destroy = false

  tags = {
    Name = "${var.cluster_name}-aws-config"
  }
}

resource "aws_s3_bucket_policy" "config" {
  bucket = aws_s3_bucket.config.id
  policy = data.aws_iam_policy_document.config_bucket_policy.json
}

data "aws_iam_policy_document" "config_bucket_policy" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }
    actions   = ["s3:GetBucketAcl"]
    resources = [aws_s3_bucket.config.arn]
    
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }

  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.config.arn]
    
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }

  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.config.arn}/config/AWSLogs/${data.aws_caller_identity.current.account_id}/Config/*"]
    
    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
    
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_s3_bucket_versioning" "config" {
  bucket = aws_s3_bucket.config.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "config" {
  bucket = aws_s3_bucket.config.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "config" {
  bucket = aws_s3_bucket.config.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM role for AWS Config
resource "aws_iam_role" "config" {
  name = "${var.cluster_name}-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.cluster_name}-config-role"
  }
}

resource "aws_iam_role_policy_attachment" "config" {
  role       = aws_iam_role.config.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/ConfigRole"
}

# ==============================================================================
# AWS Config Rules for Security Compliance
# ==============================================================================

# Check if RDS instances are encrypted
resource "aws_config_config_rule" "rds_encrypted" {
  name = "${var.cluster_name}-rds-encrypted"

  source {
    owner             = "AWS"
    source_identifier = "RDS_STORAGE_ENCRYPTED"
  }

  depends_on = [aws_config_configuration_recorder.main]

  tags = {
    Name = "${var.cluster_name}-rds-encrypted"
  }
}

# Check if S3 buckets are encrypted
resource "aws_config_config_rule" "s3_encrypted" {
  name = "${var.cluster_name}-s3-encrypted"

  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_SERVER_SIDE_ENCRYPTION_ENABLED"
  }

  depends_on = [aws_config_configuration_recorder.main]

  tags = {
    Name = "${var.cluster_name}-s3-encrypted"
  }
}

# Check if EBS volumes are encrypted
resource "aws_config_config_rule" "ebs_encrypted" {
  name = "${var.cluster_name}-ebs-encrypted"

  source {
    owner             = "AWS"
    source_identifier = "ENCRYPTED_VOLUMES"
  }

  depends_on = [aws_config_configuration_recorder.main]

  tags = {
    Name = "${var.cluster_name}-ebs-encrypted"
  }
}

# Check if security groups allow unrestricted access
resource "aws_config_config_rule" "sg_ssh_restricted" {
  name = "${var.cluster_name}-sg-ssh-restricted"

  source {
    owner             = "AWS"
    source_identifier = "INCOMING_SSH_DISABLED"
  }

  depends_on = [aws_config_configuration_recorder.main]

  tags = {
    Name = "${var.cluster_name}-sg-ssh-restricted"
  }
}

# ==============================================================================
# CloudTrail for audit logging
# ==============================================================================

resource "aws_cloudtrail" "main" {
  name           = "${var.cluster_name}-cloudtrail"
  s3_bucket_name = aws_s3_bucket.cloudtrail.bucket
  s3_key_prefix  = "cloudtrail"

  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging               = true

  event_selector {
    read_write_type                 = "All"
    include_management_events       = true
    exclude_management_event_sources = []

    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::${aws_s3_bucket.static_assets.bucket}/*"]
    }
  }

  insight_selector {
    insight_type = "ApiCallRateInsight"
  }

  tags = {
    Name = "${var.cluster_name}-cloudtrail"
  }
}

# S3 bucket for CloudTrail logs
resource "aws_s3_bucket" "cloudtrail" {
  bucket        = "${var.cluster_name}-cloudtrail"
  force_destroy = false

  tags = {
    Name = "${var.cluster_name}-cloudtrail"
  }
}

resource "aws_s3_bucket_policy" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id
  policy = data.aws_iam_policy_document.cloudtrail_bucket_policy.json
}

data "aws_iam_policy_document" "cloudtrail_bucket_policy" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.cloudtrail.arn}/cloudtrail/AWSLogs/${data.aws_caller_identity.current.account_id}/*"]
    
    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
  }

  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    actions   = ["s3:GetBucketAcl"]
    resources = [aws_s3_bucket.cloudtrail.arn]
  }
}

resource "aws_s3_bucket_versioning" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ==============================================================================
# GuardDuty for threat detection
# ==============================================================================

resource "aws_guardduty_detector" "main" {
  enable = true

  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = true
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }

  tags = {
    Name = "${var.cluster_name}-guardduty"
  }
}

# ==============================================================================
# Security Hub for centralized security findings
# ==============================================================================

resource "aws_securityhub_account" "main" {
  enable_default_standards = true
}

# Enable AWS Config, CloudTrail, and GuardDuty findings
resource "aws_securityhub_product_subscription" "aws_config" {
  product_arn = "arn:aws:securityhub:${var.aws_region}::product/aws/config"
}

resource "aws_securityhub_product_subscription" "aws_guardduty" {
  product_arn = "arn:aws:securityhub:${var.aws_region}::product/aws/guardduty"
}

resource "aws_securityhub_product_subscription" "aws_inspector" {
  product_arn = "arn:aws:securityhub:${var.aws_region}::product/aws/inspector"
}

# ==============================================================================
# VPC Flow Logs for network monitoring
# ==============================================================================

resource "aws_flow_log" "vpc" {
  iam_role_arn    = aws_iam_role.flow_log.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_log.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = {
    Name = "${var.cluster_name}-vpc-flow-log"
  }
}

resource "aws_cloudwatch_log_group" "vpc_flow_log" {
  name              = "/aws/vpc/${var.cluster_name}/flowlogs"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${var.cluster_name}-vpc-flow-log"
  }
}

resource "aws_iam_role" "flow_log" {
  name = "${var.cluster_name}-flow-log-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.cluster_name}-flow-log-role"
  }
}

resource "aws_iam_role_policy" "flow_log" {
  name = "${var.cluster_name}-flow-log-policy"
  role = aws_iam_role.flow_log.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# ==============================================================================
# Inspector V2 for vulnerability scanning
# ==============================================================================

resource "aws_inspector2_enabler" "main" {
  account_ids    = [data.aws_caller_identity.current.account_id]
  resource_types = ["ECR", "EC2"]
}

# ==============================================================================
# Systems Manager for patch management
# ==============================================================================

# Patch group for EKS nodes
resource "aws_ssm_patch_group" "eks_nodes" {
  baseline_id = aws_ssm_patch_baseline.eks_nodes.id
  patch_group = "${var.cluster_name}-eks-nodes"
}

resource "aws_ssm_patch_baseline" "eks_nodes" {
  name             = "${var.cluster_name}-eks-nodes-baseline"
  description      = "Patch baseline for EKS worker nodes"
  operating_system = "AMAZON_LINUX_2"

  approval_rule {
    approve_after_days  = 7
    compliance_level    = "HIGH"
    enable_non_security = false

    patch_filter {
      key    = "CLASSIFICATION"
      values = ["Security", "Bugfix", "Critical"]
    }

    patch_filter {
      key    = "SEVERITY"
      values = ["Critical", "Important"]
    }
  }

  tags = {
    Name = "${var.cluster_name}-eks-nodes-baseline"
  }
}

# Maintenance window for patching
resource "aws_ssm_maintenance_window" "eks_patching" {
  name     = "${var.cluster_name}-eks-patching"
  schedule = "cron(0 2 ? * SUN *)" # Weekly on Sunday at 2 AM
  duration = 4                     # 4 hours
  cutoff   = 1                     # 1 hour before end

  tags = {
    Name = "${var.cluster_name}-eks-patching"
  }
}

# ==============================================================================
# Secrets encryption with Customer Managed Keys
# ==============================================================================

resource "aws_kms_key" "secrets" {
  description             = "Secrets encryption key for ${var.cluster_name}"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow use of the key"
        Effect = "Allow"
        Principal = {
          Service = ["secretsmanager.amazonaws.com", "rds.amazonaws.com"]
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name = "${var.cluster_name}-secrets-key"
  }
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/${var.cluster_name}-secrets"
  target_key_id = aws_kms_key.secrets.key_id
}

# ==============================================================================
# Network Access Control Lists (NACLs)
# ==============================================================================

resource "aws_network_acl" "private" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.private[*].id

  # Allow inbound HTTPS
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 443
    to_port    = 443
  }

  # Allow inbound HTTP
  ingress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 80
    to_port    = 80
  }

  # Allow PostgreSQL
  ingress {
    protocol   = "tcp"
    rule_no    = 120
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 5432
    to_port    = 5432
  }

  # Allow Redis
  ingress {
    protocol   = "tcp"
    rule_no    = 130
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 6379
    to_port    = 6379
  }

  # Allow ephemeral ports
  ingress {
    protocol   = "tcp"
    rule_no    = 140
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  # Allow all outbound
  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  tags = {
    Name = "${var.cluster_name}-private-nacl"
  }
}

# ==============================================================================
# Outputs
# ==============================================================================

output "security_hub_account_id" {
  description = "Security Hub account ID"
  value       = aws_securityhub_account.main.id
}

output "guardduty_detector_id" {
  description = "GuardDuty detector ID"
  value       = aws_guardduty_detector.main.id
}

output "cloudtrail_arn" {
  description = "CloudTrail ARN"
  value       = aws_cloudtrail.main.arn
}

output "config_recorder_name" {
  description = "AWS Config recorder name"
  value       = aws_config_configuration_recorder.main.name
}

output "secrets_kms_key_arn" {
  description = "KMS key ARN for secrets encryption"
  value       = aws_kms_key.secrets.arn
}