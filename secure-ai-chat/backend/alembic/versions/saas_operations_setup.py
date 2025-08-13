"""SaaS運営に必要な追加テーブル作成

Revision ID: saas_operations_001
Revises: add_ai_settings_to_tenant
Create Date: 2025-01-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'saas_operations_001'
down_revision = 'add_ai_settings_to_tenant'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Plans テーブル作成
    op.create_table(
        'plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('plan_type', sa.Enum('STARTER', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE', name='plantype'), nullable=False),
        sa.Column('max_users', sa.Integer(), nullable=False, default=10),
        sa.Column('max_tokens_per_month', sa.Integer(), nullable=False, default=100000),
        sa.Column('max_templates', sa.Integer(), nullable=False, default=10),
        sa.Column('max_storage_gb', sa.Integer(), nullable=False, default=5),
        sa.Column('monthly_price', sa.Numeric(precision=10, scale=2), nullable=False, default=0),
        sa.Column('annual_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('has_api_access', sa.Boolean(), default=False),
        sa.Column('has_custom_branding', sa.Boolean(), default=False),
        sa.Column('has_priority_support', sa.Boolean(), default=False),
        sa.Column('has_advanced_analytics', sa.Boolean(), default=False),
        sa.Column('description', sa.Text()),
        sa.Column('features', sa.Text()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_type')
    )
    
    # Subscriptions テーブル作成
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'TRIAL', 'EXPIRED', 'CANCELLED', 'SUSPENDED', name='subscriptionstatus'), nullable=False, default='TRIAL'),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('monthly_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, default='JPY'),
        sa.Column('current_users', sa.Integer(), default=0),
        sa.Column('tokens_used_this_month', sa.Integer(), default=0),
        sa.Column('storage_used_gb', sa.Numeric(precision=10, scale=3), default=0),
        sa.Column('next_billing_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_billing_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id']),
        sa.Index('ix_subscriptions_tenant_id', 'tenant_id'),
        sa.Index('ix_subscriptions_stripe_subscription_id', 'stripe_subscription_id'),
        sa.Index('ix_subscriptions_stripe_customer_id', 'stripe_customer_id')
    )
    
    # BillingHistory テーブル作成
    op.create_table(
        'billing_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('billing_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, default='JPY'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('users_billed', sa.Integer(), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=False),
        sa.Column('paid', sa.Boolean(), default=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id']),
        sa.Index('ix_billing_history_subscription_id', 'subscription_id'),
        sa.Index('ix_billing_history_billing_date', 'billing_date')
    )
    
    # UsageRecords テーブル作成
    op.create_table(
        'usage_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('record_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tokens_used', sa.Integer(), default=0),
        sa.Column('api_calls', sa.Integer(), default=0),
        sa.Column('feature_used', sa.String(length=100), nullable=True),
        sa.Column('cost_cents', sa.Integer(), default=0),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.Index('ix_usage_records_tenant_id', 'tenant_id'),
        sa.Index('ix_usage_records_record_date', 'record_date'),
        sa.Index('ix_usage_records_user_id', 'user_id')
    )
    
    # SystemAlerts テーブル作成
    op.create_table(
        'system_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.Enum('INFO', 'WARNING', 'ERROR', 'CRITICAL', name='alertseverity'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('resolved', sa.Boolean(), default=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id']),
        sa.Index('ix_system_alerts_tenant_id', 'tenant_id'),
        sa.Index('ix_system_alerts_created_at', 'created_at'),
        sa.Index('ix_system_alerts_severity', 'severity'),
        sa.Index('ix_system_alerts_resolved', 'resolved')
    )
    
    # Tenantsテーブルにsubscriptionリレーションのための更新は不要
    # （既存のテーブル構造で対応可能）
    
    # デフォルトプランデータの挿入
    op.execute("""
        INSERT INTO plans (id, name, plan_type, max_users, max_tokens_per_month, max_templates, max_storage_gb, 
                          monthly_price, annual_price, has_api_access, has_custom_branding, has_priority_support, 
                          has_advanced_analytics, description, features, is_active, display_order, created_at, updated_at)
        VALUES 
            ('11111111-1111-1111-1111-111111111111', 'Starter', 'STARTER', 10, 100000, 10, 5, 
             29800, 298000, false, false, false, false, 
             '小規模チーム向けの基本プラン', '{"ai_chat": true, "templates": true, "basic_analytics": true, "email_support": true}', 
             true, 1, NOW(), NOW()),
            ('22222222-2222-2222-2222-222222222222', 'Standard', 'STANDARD', 50, 500000, 50, 25, 
             49800, 498000, true, false, false, true, 
             '中規模企業向けの推奨プラン', '{"ai_chat": true, "templates": true, "api_access": true, "custom_api_settings": true, "advanced_analytics": true, "email_support": true}', 
             true, 2, NOW(), NOW()),
            ('33333333-3333-3333-3333-333333333333', 'Professional', 'PROFESSIONAL', 200, 2000000, 200, 100, 
             98000, 980000, true, true, true, true, 
             '大企業向けの高機能プラン', '{"ai_chat": true, "templates": true, "api_access": true, "custom_branding": true, "priority_support": true, "phone_support": true, "advanced_analytics": true}', 
             true, 3, NOW(), NOW()),
            ('44444444-4444-4444-4444-444444444444', 'Enterprise', 'ENTERPRISE', 9999, 10000000, 9999, 1000, 
             198000, 1980000, true, true, true, true, 
             '大規模組織向けのエンタープライズプラン', '{"ai_chat": true, "templates": true, "api_access": true, "custom_branding": true, "priority_support": true, "dedicated_support": true, "custom_integrations": true, "sla_99_9": true}', 
             true, 4, NOW(), NOW());
    """)


def downgrade() -> None:
    # テーブル削除（逆順）
    op.drop_table('system_alerts')
    op.drop_table('usage_records')
    op.drop_table('billing_history')
    op.drop_table('subscriptions')
    op.drop_table('plans')
    
    # Enumタイプ削除
    op.execute("DROP TYPE IF EXISTS alertseverity")
    op.execute("DROP TYPE IF EXISTS subscriptionstatus")
    op.execute("DROP TYPE IF EXISTS plantype")