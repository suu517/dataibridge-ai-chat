"""
セキュアAIチャット - ユーザーセッション管理モデル
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
import json
import secrets

from app.core.database import Base

class UserSession(Base):
    """ユーザーセッションモデル"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    
    # ユーザー情報
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # セッション情報
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), nullable=True)
    
    # デバイス・ブラウザ情報
    ip_address = Column(String(45), nullable=True)  # IPv6対応
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # 位置情報（オプション）
    location_country = Column(String(100), nullable=True)
    location_city = Column(String(100), nullable=True)
    
    # セッション状態
    is_active = Column(Boolean, default=True, nullable=False)
    is_mobile = Column(Boolean, default=False, nullable=False)
    
    # セキュリティ情報
    login_method = Column(String(50), default="password", nullable=False)  # "password", "sso", "api_key"
    two_factor_verified = Column(Boolean, default=False, nullable=False)
    suspicious_activity_count = Column(Integer, default=0, nullable=False)
    
    # メタデータ
    extra_metadata = Column(JSON, nullable=True)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # リレーションシップ
    user = relationship("User", back_populates="sessions")

    def __init__(self, **kwargs):
        if 'session_id' not in kwargs:
            kwargs['session_id'] = self.generate_session_id()
        
        if 'expires_at' not in kwargs:
            # デフォルトで24時間後に期限切れ
            kwargs['expires_at'] = datetime.now(timezone.utc) + timedelta(hours=24)
        
        super().__init__(**kwargs)

    @staticmethod
    def generate_session_id() -> str:
        """セキュアなセッションID生成"""
        return f"sess_{secrets.token_urlsafe(32)}_{int(datetime.now().timestamp())}"

    @property
    def extra_metadata_dict(self) -> Dict[str, Any]:
        """メタデータの辞書形式取得"""
        if self.extra_metadata:
            try:
                return json.loads(self.extra_metadata) if isinstance(self.extra_metadata, str) else self.extra_metadata
            except:
                return {}
        return {}

    @property
    def is_expired(self) -> bool:
        """セッション期限切れチェック"""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """セッション有効性チェック"""
        return self.is_active and not self.is_expired

    @property
    def time_remaining(self) -> timedelta:
        """残り時間"""
        if self.is_expired:
            return timedelta(0)
        return self.expires_at - datetime.now(timezone.utc)

    @property
    def duration(self) -> timedelta:
        """セッション継続時間"""
        return self.last_activity_at - self.created_at

    @property
    def is_suspicious(self) -> bool:
        """不審なセッションかどうか"""
        return self.suspicious_activity_count > 0

    def update_activity(self, extend_session: bool = True):
        """アクティビティを更新"""
        self.last_activity_at = datetime.now(timezone.utc)
        
        if extend_session:
            # セッション期限を延長（現在時刻から24時間後）
            self.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    def extend_expiration(self, hours: int = 24):
        """セッション期限を延長"""
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
        self.last_activity_at = datetime.now(timezone.utc)

    def invalidate(self):
        """セッション無効化"""
        self.is_active = False
        self.expires_at = datetime.now(timezone.utc)

    def mark_suspicious(self, reason: str = ""):
        """不審な活動としてマーク"""
        self.suspicious_activity_count += 1
        
        metadata = self.extra_metadata_dict
        if 'suspicious_activities' not in metadata:
            metadata['suspicious_activities'] = []
        
        metadata['suspicious_activities'].append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'reason': reason
        })
        
        self.extra_metadata = metadata

    def add_metadata(self, key: str, value: Any):
        """メタデータに項目を追加"""
        metadata = self.extra_metadata_dict
        metadata[key] = value
        self.extra_metadata = metadata

    def get_browser_info(self) -> Dict[str, str]:
        """ブラウザ情報を解析して返す"""
        if not self.user_agent:
            return {"browser": "Unknown", "os": "Unknown"}
        
        # 簡易的なUser-Agent解析
        user_agent = self.user_agent.lower()
        
        # ブラウザ判定
        if 'chrome' in user_agent:
            browser = "Chrome"
        elif 'firefox' in user_agent:
            browser = "Firefox"
        elif 'safari' in user_agent:
            browser = "Safari"
        elif 'edge' in user_agent:
            browser = "Edge"
        else:
            browser = "Other"
        
        # OS判定
        if 'windows' in user_agent:
            os = "Windows"
        elif 'macintosh' in user_agent or 'mac os' in user_agent:
            os = "macOS"
        elif 'linux' in user_agent:
            os = "Linux"
        elif 'iphone' in user_agent or 'ipad' in user_agent:
            os = "iOS"
        elif 'android' in user_agent:
            os = "Android"
        else:
            os = "Other"
        
        return {"browser": browser, "os": os}

    @classmethod
    def create_session(
        cls,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        login_method: str = "password",
        session_duration_hours: int = 24
    ) -> "UserSession":
        """新しいセッションを作成"""
        
        expires_at = datetime.now(timezone.utc) + timedelta(hours=session_duration_hours)
        
        # モバイルデバイス判定
        is_mobile = False
        if user_agent:
            user_agent_lower = user_agent.lower()
            mobile_indicators = ['mobile', 'android', 'iphone', 'ipad', 'tablet']
            is_mobile = any(indicator in user_agent_lower for indicator in mobile_indicators)
        
        return cls(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            login_method=login_method,
            is_mobile=is_mobile,
            expires_at=expires_at
        )

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, session_id='{self.session_id[:20]}...', active={self.is_active})>"