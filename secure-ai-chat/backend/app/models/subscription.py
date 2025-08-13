"""
SaaS向け課金・サブスクリプション管理モデル
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
import uuid

from app.core.database import Base

class PlanType(str, enum.Enum):
    """料金プラン"""
    STARTER = "starter"           # スタータープラン
    STANDARD = "standard"         # スタンダードプラン
    PROFESSIONAL = "professional" # プロフェッショナルプラン
    ENTERPRISE = "enterprise"     # エンタープライズプラン

class SubscriptionStatus(str, enum.Enum):
    """サブスクリプション状態"""
    ACTIVE = "active"         # アクティブ
    TRIAL = "trial"           # 試用期間中
    EXPIRED = "expired"       # 期限切れ
    CANCELLED = "cancelled"   # キャンセル済み
    SUSPENDED = "suspended"   # 一時停止

class Plan(Base):
    """料金プランマスター"""
    __tablename__ = "plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)  # プラン名
    plan_type = Column(Enum(PlanType), nullable=False, unique=True)
    
    # 制限値
    max_users = Column(Integer, nullable=False, default=10)
    max_tokens_per_month = Column(Integer, nullable=False, default=100000)
    max_templates = Column(Integer, nullable=False, default=10)
    max_storage_gb = Column(Integer, nullable=False, default=5)
    
    # 料金
    monthly_price = Column(Numeric(10, 2), nullable=False, default=0)
    annual_price = Column(Numeric(10, 2), nullable=True)
    
    # 機能フラグ
    has_api_access = Column(Boolean, default=False)
    has_custom_branding = Column(Boolean, default=False)
    has_priority_support = Column(Boolean, default=False)
    has_advanced_analytics = Column(Boolean, default=False)
    
    # プラン説明
    description = Column(Text)
    features = Column(Text)  # JSON形式で機能一覧
    
    # メタデータ
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # リレーションシップ
    subscriptions = relationship("Subscription", back_populates="plan")
    
    def __str__(self):
        return f"<Plan {self.name} (¥{self.monthly_price}/月)>"

class Subscription(Base):
    """テナントのサブスクリプション"""
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    
    # サブスクリプション状態
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.TRIAL)
    
    # 期間
    start_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    end_date = Column(DateTime(timezone=True), nullable=True)
    trial_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # 課金情報
    monthly_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="JPY")
    
    # 使用状況
    current_users = Column(Integer, default=0)
    tokens_used_this_month = Column(Integer, default=0)
    storage_used_gb = Column(Numeric(10, 3), default=0)
    
    # 請求情報
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    last_billing_date = Column(DateTime(timezone=True), nullable=True)
    
    # メタデータ
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # リレーションシップ
    tenant = relationship("Tenant", back_populates="subscription")
    plan = relationship("Plan", back_populates="subscriptions")
    billing_history = relationship("BillingHistory", back_populates="subscription")
    
    @property
    def is_active(self) -> bool:
        """アクティブ状態チェック"""
        return self.status == SubscriptionStatus.ACTIVE
    
    @property
    def is_trial(self) -> bool:
        """トライアル期間中チェック"""
        return self.status == SubscriptionStatus.TRIAL
    
    @property
    def days_remaining(self) -> Optional[int]:
        """残り日数"""
        if self.end_date:
            remaining = self.end_date - datetime.now(timezone.utc)
            return max(0, remaining.days)
        return None
    
    @property
    def usage_percentage(self) -> dict:
        """使用率"""
        return {
            "users": (self.current_users / self.plan.max_users) * 100 if self.plan.max_users > 0 else 0,
            "tokens": (self.tokens_used_this_month / self.plan.max_tokens_per_month) * 100 if self.plan.max_tokens_per_month > 0 else 0,
            "storage": (float(self.storage_used_gb) / self.plan.max_storage_gb) * 100 if self.plan.max_storage_gb > 0 else 0,
        }
    
    def can_add_user(self) -> bool:
        """ユーザー追加可能チェック"""
        return self.current_users < self.plan.max_users
    
    def can_use_tokens(self, required_tokens: int) -> bool:
        """トークン使用可能チェック"""
        return (self.tokens_used_this_month + required_tokens) <= self.plan.max_tokens_per_month

class BillingHistory(Base):
    """請求履歴"""
    __tablename__ = "billing_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False)
    
    # 請求情報
    billing_date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="JPY")
    
    # 期間
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # 使用量詳細
    users_billed = Column(Integer, nullable=False)
    tokens_used = Column(Integer, nullable=False)
    
    # 支払い状況
    paid = Column(Boolean, default=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # メタデータ
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # リレーションシップ
    subscription = relationship("Subscription", back_populates="billing_history")
    
    def __str__(self):
        return f"<BillingHistory {self.billing_date.strftime('%Y-%m')} ¥{self.amount}>"