"""
マルチテナント対応のモデル定義
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import json
from typing import Optional

from app.core.database import Base
from app.core.security import encrypt_data, decrypt_data


class Tenant(Base):
    """テナント（組織）モデル"""
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)  # example.com
    subdomain = Column(String(100), unique=True, nullable=False, index=True)  # company
    
    # 契約情報
    plan = Column(String(50), nullable=False, default="starter")  # starter, business, enterprise
    max_users = Column(Integer, default=10)
    max_tokens_per_month = Column(Integer, default=100000)
    
    # 設定
    settings = Column(Text)  # JSON形式の設定
    
    # AI API設定
    ai_provider = Column(String(50), default="system_default")  # system_default, azure_openai, openai
    use_system_default = Column(Boolean, default=True)
    
    # Azure OpenAI設定（暗号化されたJSON）
    azure_openai_settings = Column(Text)
    
    # OpenAI設定（暗号化されたJSON）
    openai_settings = Column(Text)
    
    # ステータス
    is_active = Column(Boolean, default=True)
    trial_end_date = Column(DateTime)
    
    # メタデータ
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    users = relationship("User", back_populates="tenant")
    # templates = relationship("Template", back_populates="tenant")  # 将来実装
    subscription = relationship("Subscription", back_populates="tenant", uselist=False)
    
    @property
    def current_user_count(self) -> int:
        """現在のユーザー数"""
        return len([user for user in self.users if user.is_active])
    
    @property
    def can_add_user(self) -> bool:
        """ユーザー追加可能チェック"""
        if self.subscription:
            return self.subscription.can_add_user()
        return self.current_user_count < self.max_users
    
    @property
    def is_trial(self) -> bool:
        """トライアル期間中チェック"""
        if self.subscription:
            return self.subscription.is_trial
        return self.trial_end_date and self.trial_end_date > datetime.utcnow()
    
    @property
    def subscription_status(self) -> str:
        """サブスクリプション状態"""
        if self.subscription:
            return self.subscription.status.value
        return "inactive"
    
    def set_azure_openai_settings(self, endpoint: str, api_key: str, api_version: str = "2024-02-01", deployment_name: str = "gpt-4"):
        """Azure OpenAI設定を暗号化して保存"""
        # バリデーション
        if not endpoint or not endpoint.strip():
            raise ValueError("エンドポイントURLが必要です")
        if not api_key or not api_key.strip():
            raise ValueError("APIキーが必要です")
        if not deployment_name or not deployment_name.strip():
            raise ValueError("デプロイメント名が必要です")
        
        # URL形式チェック
        if not (endpoint.startswith("https://") and "openai.azure.com" in endpoint):
            raise ValueError("有効なAzure OpenAIエンドポイントURLを指定してください")
        
        # APIキーの長さチェック（基本的な検証）
        if len(api_key.strip()) < 10:
            raise ValueError("APIキーが短すぎます")
        
        settings = {
            "endpoint": endpoint.strip(),
            "api_key": api_key.strip(),
            "api_version": api_version,
            "deployment_name": deployment_name.strip()
        }
        self.azure_openai_settings = encrypt_data(json.dumps(settings))
        self.ai_provider = "azure_openai"
        self.use_system_default = False
    
    def get_azure_openai_settings(self) -> Optional[dict]:
        """Azure OpenAI設定を復号化して取得"""
        if not self.azure_openai_settings:
            return None
        try:
            decrypted = decrypt_data(self.azure_openai_settings)
            return json.loads(decrypted)
        except Exception:
            return None
    
    def set_openai_settings(self, api_key: str, model: str = "gpt-4"):
        """OpenAI設定を暗号化して保存"""
        # バリデーション
        if not api_key or not api_key.strip():
            raise ValueError("OpenAI APIキーが必要です")
        if not model or not model.strip():
            raise ValueError("モデル名が必要です")
        
        # APIキーの形式チェック
        api_key_clean = api_key.strip()
        if not api_key_clean.startswith("sk-"):
            raise ValueError("有効なOpenAI APIキー形式ではありません（sk-で始まる必要があります）")
        if len(api_key_clean) < 20:
            raise ValueError("APIキーが短すぎます")
        
        # モデル名の基本チェック
        valid_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]
        if model.strip() not in valid_models:
            raise ValueError(f"サポートされていないモデルです。有効なモデル: {', '.join(valid_models)}")
        
        settings = {
            "api_key": api_key_clean,
            "model": model.strip()
        }
        self.openai_settings = encrypt_data(json.dumps(settings))
        self.ai_provider = "openai"
        self.use_system_default = False
    
    def get_openai_settings(self) -> Optional[dict]:
        """OpenAI設定を復号化して取得"""
        if not self.openai_settings:
            return None
        try:
            decrypted = decrypt_data(self.openai_settings)
            return json.loads(decrypted)
        except Exception:
            return None
    
    def use_default_ai_settings(self):
        """システムデフォルトのAI設定を使用"""
        self.ai_provider = "system_default"
        self.use_system_default = True
        self.azure_openai_settings = None
        self.openai_settings = None
    
    def get_ai_settings(self) -> dict:
        """現在有効なAI設定を取得"""
        if self.use_system_default:
            from app.core.config import settings
            return {
                "provider": "system_default",
                "use_azure": settings.use_azure_openai,
                "azure_endpoint": settings.AZURE_OPENAI_ENDPOINT if settings.use_azure_openai else None,
                "azure_api_key": settings.AZURE_OPENAI_API_KEY if settings.use_azure_openai else None,
                "azure_api_version": settings.AZURE_OPENAI_API_VERSION if settings.use_azure_openai else None,
                "azure_deployment": settings.AZURE_OPENAI_DEPLOYMENT_NAME if settings.use_azure_openai else None,
                "openai_api_key": settings.OPENAI_API_KEY if not settings.use_azure_openai else None,
                "openai_model": settings.OPENAI_MODEL if not settings.use_azure_openai else None
            }
        elif self.ai_provider == "azure_openai":
            azure_settings = self.get_azure_openai_settings()
            if azure_settings:
                return {
                    "provider": "azure_openai",
                    "use_azure": True,
                    "azure_endpoint": azure_settings.get("endpoint"),
                    "azure_api_key": azure_settings.get("api_key"),
                    "azure_api_version": azure_settings.get("api_version"),
                    "azure_deployment": azure_settings.get("deployment_name")
                }
        elif self.ai_provider == "openai":
            openai_settings = self.get_openai_settings()
            if openai_settings:
                return {
                    "provider": "openai",
                    "use_azure": False,
                    "openai_api_key": openai_settings.get("api_key"),
                    "openai_model": openai_settings.get("model")
                }
        
        # フォールバック：システムデフォルト
        return self.get_ai_settings() if not self.use_system_default else {}

    def __str__(self):
        return f"<Tenant {self.name} ({self.domain})>"


class TenantMixin:
    """テナント対応のためのMixin"""
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    @classmethod
    def get_by_tenant(cls, db_session, tenant_id, **filters):
        """テナント別のデータ取得"""
        query = db_session.query(cls).filter(cls.tenant_id == tenant_id)
        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.filter(getattr(cls, key) == value)
        return query
        
    @classmethod
    def create_for_tenant(cls, db_session, tenant_id, **kwargs):
        """テナント用レコード作成"""
        kwargs['tenant_id'] = tenant_id
        instance = cls(**kwargs)
        db_session.add(instance)
        db_session.commit()
        db_session.refresh(instance)
        return instance