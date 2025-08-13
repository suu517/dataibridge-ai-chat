"""
ユーザー関連のスキーマ定義
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator

from app.models.user import UserRole, UserStatus

class UserInvite(BaseModel):
    """ユーザー招待スキーマ"""
    email: EmailStr
    role: UserRole = UserRole.USER
    department: Optional[str] = None
    position: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()

class UserAcceptInvitation(BaseModel):
    """招待受諾スキーマ"""
    invitation_token: str
    full_name: str
    new_password: str
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('氏名は2文字以上である必要があります')
        return v.strip()
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        return v

class UserRoleUpdate(BaseModel):
    """ユーザー権限更新スキーマ"""
    role: UserRole

class UserResponse(BaseModel):
    """ユーザー情報レスポンス"""
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
    
    class Config:
        from_attributes = True

class UserInviteResponse(BaseModel):
    """招待レスポンス"""
    success: bool
    message: str
    data: Optional[dict] = None

class UserListResponse(BaseModel):
    """ユーザー一覧レスポンス"""
    success: bool
    users: List[UserResponse]
    total: int
    limit: int
    offset: int

class UserProfile(BaseModel):
    """ユーザープロフィール"""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    department: Optional[str] = None
    position: Optional[str] = None
    tenant_name: str
    last_login: Optional[str] = None
    created_at: str

class UserSettings(BaseModel):
    """ユーザー設定"""
    theme: Optional[str] = "light"
    language: Optional[str] = "ja"
    notifications_enabled: bool = True
    email_notifications: bool = True