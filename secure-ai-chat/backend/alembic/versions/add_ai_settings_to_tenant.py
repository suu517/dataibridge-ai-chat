"""Add AI settings to tenant

Revision ID: add_ai_settings_to_tenant
Revises: dbf98a6d5391
Create Date: 2025-08-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_ai_settings_to_tenant'
down_revision = 'dbf98a6d5391'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # AI設定関連のカラムをtenantsテーブルに追加
    op.add_column('tenants', sa.Column('ai_provider', sa.String(50), nullable=True, default='system_default'))
    op.add_column('tenants', sa.Column('use_system_default', sa.Boolean(), nullable=True, default=True))
    op.add_column('tenants', sa.Column('azure_openai_settings', sa.Text(), nullable=True))
    op.add_column('tenants', sa.Column('openai_settings', sa.Text(), nullable=True))
    
    # デフォルト値を設定
    op.execute("UPDATE tenants SET ai_provider = 'system_default' WHERE ai_provider IS NULL")
    op.execute("UPDATE tenants SET use_system_default = true WHERE use_system_default IS NULL")
    
    # NOT NULL制約を追加
    op.alter_column('tenants', 'ai_provider', nullable=False)
    op.alter_column('tenants', 'use_system_default', nullable=False)


def downgrade() -> None:
    # AI設定関連のカラムを削除
    op.drop_column('tenants', 'openai_settings')
    op.drop_column('tenants', 'azure_openai_settings')
    op.drop_column('tenants', 'use_system_default')
    op.drop_column('tenants', 'ai_provider')