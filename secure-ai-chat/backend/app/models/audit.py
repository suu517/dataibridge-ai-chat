"""
セキュアAIチャット - 監査ログモデル
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
import enum
import json

from app.core.database import Base

class AuditAction(str, enum.Enum):
    """監査アクション"""
    # 認証関連
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    ACCOUNT_LOCKED = "account_locked"
    
    # チャット関連
    CHAT_CREATE = "chat_create"
    CHAT_UPDATE = "chat_update"
    CHAT_DELETE = "chat_delete"
    CHAT_ARCHIVE = "chat_archive"
    MESSAGE_SEND = "message_send"
    MESSAGE_DELETE = "message_delete"
    
    # テンプレート関連
    TEMPLATE_CREATED = "template_created"
    TEMPLATE_UPDATED = "template_updated"
    TEMPLATE_DELETED = "template_deleted"
    TEMPLATE_USE = "template_use"
    TEMPLATE_ACCESS_DENIED = "template_access_denied"
    
    # AI API関連
    AI_REQUEST = "ai_request"
    AI_RESPONSE = "ai_response"
    AI_ERROR = "ai_error"
    
    # システム関連
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    ROLE_CHANGED = "role_changed"
    DATA_ACCESS = "data_access"
    UNKNOWN = "unknown"
    
    # セキュリティ関連
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"

class AuditLevel(str, enum.Enum):
    """監査レベル"""
    LOW = "low"        # 一般的な操作
    MEDIUM = "medium"  # 重要な操作
    HIGH = "high"      # 機密操作
    CRITICAL = "critical"  # 最重要操作

class AuditLog(Base):
    """監査ログモデル"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # ユーザー情報
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # システム操作の場合はNULL
    username = Column(String(50), nullable=True)  # ユーザー削除後も記録を保持
    user_role = Column(String(20), nullable=True)
    
    # アクション情報
    action = Column(Enum(AuditAction), nullable=False, index=True)
    level = Column(Enum(AuditLevel), default=AuditLevel.LOW, nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # リソース情報
    resource_type = Column(String(50), nullable=True)  # "chat", "template", "user" など
    resource_id = Column(String(100), nullable=True)
    
    # リクエスト情報
    ip_address = Column(String(45), nullable=True)  # IPv6対応
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True)
    http_method = Column(String(10), nullable=True)
    
    # 詳細情報
    details = Column(JSON, nullable=True)  # 追加詳細をJSON形式で保存
    
    # 結果情報
    success = Column(String(10), nullable=False, default="true")  # "true", "false", "partial"
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # セキュリティ情報
    session_id = Column(String(255), nullable=True)
    correlation_id = Column(String(100), nullable=True)  # 関連する一連の操作を紐付け
    
    # タイムスタンプ
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # データ保持期間管理
    retention_until = Column(DateTime(timezone=True), nullable=True)
    
    # リレーションシップ
    user = relationship("User", back_populates="audit_logs")

    @classmethod
    def create_log(
        cls,
        action: AuditAction,
        description: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        user_role: Optional[str] = None,
        level: AuditLevel = AuditLevel.LOW,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        http_method: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> "AuditLog":
        """監査ログエントリを作成"""
        
        # 保持期間の計算（90日後）
        retention_until = datetime.now(timezone.utc).replace(day=datetime.now(timezone.utc).day + 90)
        
        return cls(
            user_id=user_id,
            username=username,
            user_role=user_role,
            action=action,
            level=level,
            description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            http_method=http_method,
            details=details,
            success="true" if success else "false",
            error_code=error_code,
            error_message=error_message,
            session_id=session_id,
            correlation_id=correlation_id,
            retention_until=retention_until
        )

    @property
    def details_dict(self) -> Dict[str, Any]:
        """詳細情報の辞書形式取得"""
        if self.details:
            try:
                return json.loads(self.details) if isinstance(self.details, str) else self.details
            except:
                return {}
        return {}

    @property
    def is_success(self) -> bool:
        """成功判定"""
        return self.success == "true"

    @property
    def is_security_related(self) -> bool:
        """セキュリティ関連の操作かどうか"""
        security_actions = [
            AuditAction.LOGIN_FAILED,
            AuditAction.ACCOUNT_LOCKED,
            AuditAction.SUSPICIOUS_ACTIVITY,
            AuditAction.RATE_LIMIT_EXCEEDED,
            AuditAction.UNAUTHORIZED_ACCESS,
            AuditAction.TEMPLATE_ACCESS_DENIED
        ]
        return self.action in security_actions

    @property
    def is_high_risk(self) -> bool:
        """高リスク操作かどうか"""
        return self.level in [AuditLevel.HIGH, AuditLevel.CRITICAL]

    def add_detail(self, key: str, value: Any):
        """詳細情報に項目を追加"""
        details = self.details_dict
        details[key] = value
        self.details = details

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action.value}', user_id={self.user_id}, timestamp={self.timestamp})>"