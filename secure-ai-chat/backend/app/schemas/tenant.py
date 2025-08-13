"""
テナント関連のスキーマ定義
"""

from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, EmailStr, validator

from app.models.subscription import PlanType

class TenantCreate(BaseModel):
    """テナント作成スキーマ"""
    name: str
    domain: str
    subdomain: str
    admin_email: EmailStr
    admin_name: str
    admin_password: str
    plan_type: Optional[PlanType] = PlanType.STARTER
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 2:
            raise ValueError('テナント名は2文字以上である必要があります')
        return v
    
    @validator('domain')
    def validate_domain(cls, v):
        if '.' not in v or len(v) < 4:
            raise ValueError('有効なドメイン名を入力してください')
        return v.lower()
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        if len(v) < 3 or not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('サブドメインは3文字以上の英数字である必要があります')
        return v.lower()
    
    @validator('admin_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        return v

class TenantUpdate(BaseModel):
    """テナント更新スキーマ"""
    name: Optional[str] = None
    settings: Optional[Dict] = None

class TenantResponse(BaseModel):
    """テナント応答スキーマ"""
    id: str
    name: str
    domain: str
    subdomain: str
    plan: str
    is_active: bool
    subscription_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserStats(BaseModel):
    """ユーザー統計"""
    total: int
    active: int  
    limit: int

class SubscriptionInfo(BaseModel):
    """サブスクリプション情報"""
    status: str
    plan: str
    trial_end: Optional[str] = None
    next_billing: Optional[str] = None

class TenantStats(BaseModel):
    """テナント統計情報"""
    tenant_id: str
    tenant_name: str
    users: UserStats
    subscription: SubscriptionInfo
    usage: Dict
    created_at: str

class TenantList(BaseModel):
    """テナント一覧レスポンス"""
    tenants: List[TenantResponse]
    total: int
    limit: int
    offset: int