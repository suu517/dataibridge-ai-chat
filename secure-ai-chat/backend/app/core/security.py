"""
セキュアAIチャット - セキュリティ機能
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Dict
import secrets
import hashlib
import hmac

from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from app.core.config import settings

# パスワードハッシュ化設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SecurityManager:
    """セキュリティ管理クラス"""
    
    def __init__(self):
        self._encryption_key = None
    
    @property
    def encryption_key(self) -> bytes:
        """データ暗号化キーの生成・取得"""
        if self._encryption_key is None:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'secure_ai_chat_salt',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(settings.DB_ENCRYPT_KEY.encode()))
            self._encryption_key = key
        return self._encryption_key

# グローバルセキュリティマネージャー
security_manager = SecurityManager()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワード検証"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """パスワードハッシュ化"""
    return pwd_context.hash(password)

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """JWTアクセストークン生成"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(16)  # JWT ID
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(subject: str) -> str:
    """JWTリフレッシュトークン生成"""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(16)
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str, is_refresh_token: bool = False) -> Optional[Dict[str, Any]]:
    """JWTトークン検証"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # トークンタイプチェック
        expected_type = "refresh" if is_refresh_token else "access"
        if payload.get("type") != expected_type:
            return None
            
        return payload
    
    except JWTError:
        return None

def encrypt_sensitive_data(data: str) -> str:
    """機密データ暗号化"""
    f = Fernet(security_manager.encryption_key)
    encrypted_data = f.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted_data).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """機密データ復号化"""
    try:
        f = Fernet(security_manager.encryption_key)
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception:
        raise ValueError("データの復号化に失敗しました")

def generate_secure_token(length: int = 32) -> str:
    """セキュアなトークン生成"""
    return secrets.token_urlsafe(length)

def hash_data(data: str, salt: Optional[str] = None) -> str:
    """データのハッシュ化（監査ログ等で使用）"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    return hashlib.pbkdf2_hmac(
        'sha256',
        data.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()

def verify_signature(data: str, signature: str, key: str) -> bool:
    """HMAC署名検証"""
    expected_signature = hmac.new(
        key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def create_signature(data: str, key: str) -> str:
    """HMAC署名作成"""
    return hmac.new(
        key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()

class RateLimiter:
    """レート制限クラス"""
    
    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes
        self.attempts = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """レート制限チェック"""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=self.window_minutes)
        
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        # 古い試行を削除
        self.attempts[identifier] = [
            attempt for attempt in self.attempts[identifier]
            if attempt > window_start
        ]
        
        # 制限チェック
        if len(self.attempts[identifier]) >= self.max_attempts:
            return False
        
        # 新しい試行を記録
        self.attempts[identifier].append(now)
        return True
    
    def reset_attempts(self, identifier: str):
        """試行回数リセット"""
        if identifier in self.attempts:
            del self.attempts[identifier]

# 便利なエイリアス
encrypt_data = encrypt_sensitive_data
decrypt_data = decrypt_sensitive_data

# グローバルレート制限インスタンス
login_rate_limiter = RateLimiter(
    max_attempts=settings.MAX_LOGIN_ATTEMPTS,
    window_minutes=settings.ACCOUNT_LOCKOUT_MINUTES
)