"""
セキュアAIチャット - ユーザーモデル
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
import uuid

from app.core.database import Base
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data

class UserRole(str, enum.Enum):
    """ユーザー役割"""
    TENANT_ADMIN = "tenant_admin"  # テナント管理者
    MANAGER = "manager"            # 部門管理者  
    USER = "user"                 # 一般ユーザー
    VIEWER = "viewer"             # 閲覧専用ユーザー

class UserStatus(str, enum.Enum):
    """ユーザー状態"""
    ACTIVE = "active"        # アクティブ
    INACTIVE = "inactive"    # 非アクティブ
    LOCKED = "locked"        # ロックされた
    PENDING = "pending"      # 承認待ち

class User(Base):
    """ユーザーモデル"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # テナント情報（SaaS対応）
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # 基本情報
    username = Column(String(50), index=True, nullable=False)
    email = Column(String(255), index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # テナント内でユニーク制約（SaaS対応）
    __table_args__ = (
        {"schema": None}
    )
    
    # プロフィール情報（暗号化）
    full_name = Column(Text, nullable=True)  # 暗号化される
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    
    # 役割・権限
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING, nullable=False)
    
    # セキュリティ関連
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # リレーションシップ
    tenant = relationship("Tenant", back_populates="users")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        # 機密情報の暗号化
        if 'full_name' in kwargs and kwargs['full_name']:
            kwargs['full_name'] = encrypt_sensitive_data(kwargs['full_name'])
        
        super().__init__(**kwargs)

    @property
    def decrypted_full_name(self) -> Optional[str]:
        """氏名の復号化"""
        if self.full_name:
            try:
                return decrypt_sensitive_data(self.full_name)
            except:
                return None
        return None

    @property
    def is_tenant_admin(self) -> bool:
        """テナント管理者権限チェック"""
        return self.role == UserRole.TENANT_ADMIN

    @property
    def is_manager(self) -> bool:
        """テナント管理者または部門管理者権限チェック"""
        return self.role in [UserRole.TENANT_ADMIN, UserRole.MANAGER]

    @property
    def can_access_templates(self) -> bool:
        """テンプレート管理権限チェック"""
        return self.role in [UserRole.TENANT_ADMIN, UserRole.MANAGER]
        
    @property
    def can_invite_users(self) -> bool:
        """ユーザー招待権限チェック"""
        return self.role in [UserRole.TENANT_ADMIN, UserRole.MANAGER]
        
    @property
    def can_manage_tenant(self) -> bool:
        """テナント管理権限チェック"""
        return self.role == UserRole.TENANT_ADMIN

    @property
    def is_locked(self) -> bool:
        """アカウントロック状態チェック"""
        if self.status == UserStatus.LOCKED:
            return True
        if self.locked_until and self.locked_until > datetime.now(timezone.utc):
            return True
        return False

    def increment_failed_login(self, max_attempts: int = 5):
        """ログイン失敗回数をインクリメント"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.status = UserStatus.LOCKED
            # 15分間ロック
            self.locked_until = datetime.now(timezone.utc).replace(minute=datetime.now(timezone.utc).minute + 15)

    def reset_failed_login(self):
        """ログイン失敗回数をリセット"""
        self.failed_login_attempts = 0
        self.locked_until = None
        if self.status == UserStatus.LOCKED:
            self.status = UserStatus.ACTIVE

    def update_last_login(self):
        """最終ログイン時刻を更新"""
        self.last_login = datetime.now(timezone.utc)
        self.reset_failed_login()

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"

class Role(Base):
    """役割マスター（将来の拡張用）"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(Text, nullable=True)  # JSON形式で権限を保存
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"