"""
管理ダッシュボード関連のスキーマ定義
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class SystemStats(BaseModel):
    """システム統計情報"""
    total_users: int
    active_users: int
    total_tenants: int
    active_tenants: int
    active_subscriptions: int
    monthly_revenue: float
    monthly_tokens: int
    user_growth_rate: float
    last_updated: str

class TenantSummary(BaseModel):
    """テナント概要"""
    id: str
    name: str
    domain: str
    subdomain: str
    plan: str
    user_count: int
    max_users: int
    is_active: bool
    subscription_status: str
    created_at: str
    trial_end_date: Optional[str] = None

class TenantListResponse(BaseModel):
    """テナント一覧レスポンス"""
    tenants: List[TenantSummary]
    total: int
    limit: int
    offset: int

class UserSummary(BaseModel):
    """ユーザー概要"""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    status: str
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: bool
    last_login: Optional[str] = None
    created_at: str
    tenant: Dict[str, str]

class UserListResponse(BaseModel):
    """ユーザー一覧レスポンス"""
    users: List[UserSummary]
    total: int
    limit: int
    offset: int

class PlanBreakdown(BaseModel):
    """プラン別統計"""
    plan_name: str
    subscription_count: int
    monthly_revenue: float

class StatusBreakdown(BaseModel):
    """状態別統計"""
    status: str
    count: int

class SubscriptionStats(BaseModel):
    """サブスクリプション統計"""
    total_subscriptions: int
    active_subscriptions: int
    monthly_recurring_revenue: float
    churn_rate: float
    plan_breakdown: List[PlanBreakdown]
    status_breakdown: List[StatusBreakdown]

class UsageAnalytics(BaseModel):
    """使用状況分析"""
    period: str
    start_date: str
    token_usage: Dict[str, Any]
    storage_usage: Dict[str, Any]

class AdminAction(BaseModel):
    """管理者アクション"""
    action_type: str
    target_id: str
    target_type: str  # tenant, user, subscription
    reason: Optional[str] = None
    performed_at: str
    performed_by: str

class SecurityAlert(BaseModel):
    """セキュリティアラート"""
    id: str
    type: str  # failed_login, suspicious_activity, data_breach
    severity: str  # low, medium, high, critical
    description: str
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: str
    resolved: bool = False
    resolved_at: Optional[str] = None

class SystemHealth(BaseModel):
    """システム健全性"""
    database_status: str
    api_response_time: float
    error_rate: float
    uptime: str
    last_backup: Optional[str] = None
    disk_usage: float
    memory_usage: float
    cpu_usage: float