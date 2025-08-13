"""
認証・認可サービス（テナント対応）
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User, UserStatus
from app.models.tenant import Tenant
from app.services.secure_query_service import SecureQueryService

security = HTTPBearer()

class AuthService:
    """認証・認可サービス"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, email: str, password: str, tenant_id: str) -> Optional[User]:
        """
        テナント内でのユーザー認証
        """
        # テナント内のユーザーのみ検索
        user = self.db.query(User).filter(
            User.email == email,
            User.tenant_id == tenant_id
        ).first()
        
        if not user:
            return None
        
        # アカウント状態チェック
        if user.status in [UserStatus.LOCKED, UserStatus.INACTIVE]:
            return None
        
        # パスワード検証
        if not verify_password(password, user.hashed_password):
            user.increment_failed_login()
            self.db.commit()
            return None
        
        # ログイン成功処理
        user.update_last_login()
        self.db.commit()
        
        return user
    
    def create_access_token(self, user: User) -> Dict[str, Any]:
        """アクセストークン作成"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
            "role": user.role.value,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_at": expire.isoformat(),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.decrypted_full_name,
                "role": user.role.value,
                "tenant_id": str(user.tenant_id)
            }
        }
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """トークン検証"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            token_type = payload.get("type", "access")
            
            if user_id is None or tenant_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="無効なトークンです"
                )
            
            # ユーザー存在確認
            user = self.db.query(User).filter(
                User.id == user_id,
                User.tenant_id == tenant_id
            ).first()
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="ユーザーが無効です"
                )
            
            return {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "role": payload.get("role"),
                "token_type": token_type,
                "user": user
            }
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="トークンの検証に失敗しました"
            )
    
    def get_current_user(self, token: str) -> User:
        """現在のユーザーを取得"""
        token_data = self.verify_token(token)
        return token_data["user"]

class AuthDependency:
    """認証依存性注入クラス"""
    
    def __init__(self, require_active: bool = True):
        self.require_active = require_active
    
    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> User:
        """認証済みユーザーを取得"""
        auth_service = AuthService(db)
        
        try:
            user = auth_service.get_current_user(credentials.credentials)
            
            # テナントコンテキストとの整合性チェック
            if hasattr(request.state, 'tenant_id'):
                if str(user.tenant_id) != request.state.tenant_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="テナントアクセス権限がありません"
                    )
            
            # アクティブユーザーチェック
            if self.require_active and (not user.is_active or user.status != UserStatus.ACTIVE):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="アカウントが無効です"
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"認証エラー: {str(e)}"
            )

class RoleBasedAuth:
    """役割ベース認証"""
    
    def __init__(self, required_roles: list):
        self.required_roles = required_roles
    
    async def __call__(
        self,
        user: User = Depends(AuthDependency())
    ) -> User:
        """必要な権限をチェック"""
        if user.role.value not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"この操作には {', '.join(self.required_roles)} の権限が必要です"
            )
        
        return user

# 依存性注入用のファクトリー関数
def get_current_user():
    """現在のユーザーを取得"""
    return AuthDependency()

def get_current_active_user():
    """現在のアクティブユーザーを取得"""
    return AuthDependency(require_active=True)

def require_tenant_admin():
    """テナント管理者権限が必要"""
    return RoleBasedAuth(["tenant_admin"])

def require_manager():
    """マネージャー以上の権限が必要"""
    return RoleBasedAuth(["tenant_admin", "manager"])

def require_user():
    """一般ユーザー以上の権限が必要"""
    return RoleBasedAuth(["tenant_admin", "manager", "user"])

# 認証ヘルパー関数
async def login_user(
    email: str,
    password: str,
    tenant_id: str,
    db: Session
) -> Dict[str, Any]:
    """ユーザーログイン処理"""
    auth_service = AuthService(db)
    
    # ユーザー認証
    user = auth_service.authenticate_user(email, password, tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが間違っています"
        )
    
    # トークン作成
    return auth_service.create_access_token(user)

from app.core.database import get_db