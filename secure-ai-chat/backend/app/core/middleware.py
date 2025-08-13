"""
認証とテナント分離のミドルウェア
"""

from typing import Optional, Callable
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.config import settings
from app.models.auth import User, UserSession
from app.models.tenant import Tenant

# JWT設定
security = HTTPBearer(auto_error=False)

class TenantContext:
    """テナントコンテキスト"""
    def __init__(self):
        self.tenant_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.user: Optional[User] = None
        self.tenant: Optional[Tenant] = None

# リクエスト毎のテナントコンテキスト
tenant_context = TenantContext()

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """現在のユーザーを取得"""
    if not credentials:
        return None
    
    try:
        # JWTトークンをデコード
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # セッション確認
        session_result = await db.execute(
            select(UserSession).where(
                UserSession.session_token == credentials.credentials,
                UserSession.is_active == True
            )
        )
        session = session_result.scalar_one_or_none()
        
        if not session or session.is_expired():
            return None
        
        # ユーザー取得
        user_result = await db.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        user = user_result.scalar_one_or_none()
        
        if user:
            # テナントコンテキスト設定
            tenant_context.user_id = str(user.id)
            tenant_context.tenant_id = str(user.tenant_id)
            tenant_context.user = user
            
            # セッション使用時間を更新
            session.last_used_at = datetime.utcnow()
            await db.commit()
        
        return user
    
    except jwt.PyJWTError:
        return None

async def require_auth(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """認証必須"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証が必要です",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return current_user

async def require_tenant_admin(
    current_user: User = Depends(require_auth)
) -> User:
    """テナント管理者権限必須"""
    if not current_user.is_tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return current_user

class TenantMiddleware:
    """テナント分離ミドルウェア"""
    
    def __init__(self, app: Callable):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # リクエスト処理前にテナントコンテキストをリセット
        tenant_context.tenant_id = None
        tenant_context.user_id = None
        tenant_context.user = None
        tenant_context.tenant = None
        
        await self.app(scope, receive, send)

def get_tenant_context() -> TenantContext:
    """現在のテナントコンテキストを取得"""
    return tenant_context

async def get_tenant_filter() -> str:
    """テナントIDフィルターを取得"""
    if not tenant_context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="テナント情報が必要です"
        )
    return tenant_context.tenant_id

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """アクセストークンを作成"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def get_tenant_by_domain(domain: str, db: AsyncSession) -> Optional[Tenant]:
    """ドメインからテナントを取得"""
    result = await db.execute(
        select(Tenant).where(
            Tenant.domain == domain,
            Tenant.is_active == True
        )
    )
    return result.scalar_one_or_none()

async def get_tenant_by_subdomain(subdomain: str, db: AsyncSession) -> Optional[Tenant]:
    """サブドメインからテナントを取得"""
    result = await db.execute(
        select(Tenant).where(
            Tenant.subdomain == subdomain,
            Tenant.is_active == True
        )
    )
    return result.scalar_one_or_none()