"""
認証・ユーザー管理のモデル
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from passlib.context import CryptContext
import uuid
import enum

from app.models.base import BaseModel
from app.models.tenant import TenantMixin

# パスワードハッシュ化
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(enum.Enum):
    """ユーザーロール"""
    TENANT_ADMIN = "tenant_admin"  # テナント管理者
    MANAGER = "manager"            # マネージャー
    USER = "user"                  # 一般ユーザー
    VIEWER = "viewer"              # 閲覧のみ


class User(BaseModel, TenantMixin):
    """ユーザーモデル"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # 基本情報
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # 権限
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # 最終アクセス
    last_login_at = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # メタデータ
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    tenant = relationship("Tenant", back_populates="users")
    sessions = relationship("UserSession", back_populates="user")
    
    def set_password(self, password: str):
        """パスワードをハッシュ化して設定"""
        self.hashed_password = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """パスワードを検証"""
        return pwd_context.verify(password, self.hashed_password)
    
    def update_login(self):
        """ログイン情報を更新"""
        self.last_login_at = datetime.utcnow()
        self.login_count += 1
    
    @property
    def is_tenant_admin(self) -> bool:
        return self.role == UserRole.TENANT_ADMIN
    
    def __str__(self):
        return f"<User {self.email} ({self.full_name})>"


class UserSession(BaseModel):
    """ユーザーセッション管理"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # セッション情報
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False)
    
    # IPアドレスとUser-Agent（セキュリティ用）
    ip_address = Column(String(45))  # IPv6対応
    user_agent = Column(Text)
    
    # 有効期限
    expires_at = Column(DateTime, nullable=False)
    refresh_expires_at = Column(DateTime, nullable=False)
    
    # ステータス
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime)
    
    # メタデータ
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_used_at = Column(DateTime, default=datetime.utcnow)
    
    # リレーションシップ
    user = relationship("User", back_populates="sessions")
    
    @classmethod
    def create_session(cls, user_id: str, ip_address: str = None, user_agent: str = None):
        """新しいセッションを作成"""
        import secrets
        
        session_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        
        return cls(
            user_id=user_id,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(hours=24),  # 24時間
            refresh_expires_at=datetime.utcnow() + timedelta(days=30)  # 30日
        )
    
    def is_expired(self) -> bool:
        """セッションが期限切れかチェック"""
        return datetime.utcnow() > self.expires_at or not self.is_active
    
    def revoke(self):
        """セッションを無効化"""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
    
    def __str__(self):
        return f"<UserSession {self.session_token[:8]}... for user {self.user_id}>"


class UserInvitation(BaseModel):
    """ユーザー招待"""
    __tablename__ = "user_invitations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 招待情報
    email = Column(String(255), nullable=False, index=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    invitation_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # ステータス
    is_accepted = Column(Boolean, default=False)
    accepted_at = Column(DateTime)
    expires_at = Column(DateTime, nullable=False)
    
    # メタデータ
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    @classmethod
    def create_invitation(cls, tenant_id: str, email: str, role: UserRole, invited_by: str):
        """招待を作成"""
        import secrets
        
        invitation_token = secrets.token_urlsafe(32)
        
        return cls(
            tenant_id=tenant_id,
            email=email,
            role=role,
            invited_by=invited_by,
            invitation_token=invitation_token,
            expires_at=datetime.utcnow() + timedelta(days=7)  # 7日間有効
        )
    
    def is_expired(self) -> bool:
        """招待が期限切れかチェック"""
        return datetime.utcnow() > self.expires_at or self.is_accepted
    
    def accept(self):
        """招待を承認"""
        self.is_accepted = True
        self.accepted_at = datetime.utcnow()