"""
セキュアAIチャット - アプリケーション設定
"""

from typing import List, Optional
from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings
import secrets
from pathlib import Path

class Settings(BaseSettings):
    """アプリケーション設定クラス"""
    
    # アプリケーション基本設定
    APP_NAME: str = "Secure AI Chat"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # セキュリティ設定
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    
    # レート制限設定
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # データベース設定
    DATABASE_URL: str = "postgresql://chatuser:securepassword@localhost:5432/secure_ai_chat"
    DB_ENCRYPT_KEY: str = secrets.token_urlsafe(32)
    
    # Redis設定
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI API設定
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4"
    
    # OpenAI API（代替）
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    
    # CORS設定
    ALLOWED_ORIGINS: List[str] = ["https://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # ログ設定
    LOG_LEVEL: str = "INFO"
    ENABLE_AUDIT_LOG: bool = True
    
    # SSL/TLS設定
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None
    
    # セッション設定
    SESSION_TIMEOUT_MINUTES: int = 60
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15
    
    # ファイルアップロード設定
    MAX_FILE_SIZE_MB: int = 10
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "txt", "docx", "xlsx"]
    
    # 監査ログ設定
    AUDIT_LOG_RETENTION_DAYS: int = 90
    ENABLE_USER_ACTIVITY_TRACKING: bool = True
    
    # API設定
    API_V1_STR: str = "/api/v1"
    
    # プロジェクトルート
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def use_azure_openai(self) -> bool:
        return bool(self.AZURE_OPENAI_ENDPOINT and self.AZURE_OPENAI_API_KEY)
    
    @property
    def database_url_async(self) -> str:
        """非同期用データベースURL"""
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

# グローバル設定インスタンス
settings = Settings()

# 設定検証
def validate_settings():
    """設定の妥当性チェック"""
    errors = []
    
    if not settings.use_azure_openai and not settings.OPENAI_API_KEY:
        errors.append("AI APIキー（Azure OpenAI または OpenAI）が設定されていません")
    
    if settings.is_production:
        if settings.SECRET_KEY == "your-super-secret-key-change-this-in-production":
            errors.append("本番環境でデフォルトのSECRET_KEYを使用しています")
        
        if not settings.SSL_CERT_PATH or not settings.SSL_KEY_PATH:
            errors.append("本番環境でSSL証明書が設定されていません")
    
    if errors:
        raise ValueError(f"設定エラー: {', '.join(errors)}")

# 起動時の設定検証
if settings.is_production:
    validate_settings()