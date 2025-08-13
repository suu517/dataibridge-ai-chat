"""
セキュアAIチャット - 認証依存関係
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_database_session
from app.core.security import verify_token, login_rate_limiter
from app.models.user import User, UserStatus
from app.models.session import UserSession
from app.models.audit import AuditLog, AuditAction, AuditLevel
from app.models.tenant import Tenant

# HTTPベアラートークン認証
security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_database_session)
) -> User:
    """現在のユーザーを取得"""
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証トークンが必要です",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # トークン検証
    payload = verify_token(credentials.credentials)
    if not payload:
        # 監査ログ記録
        await log_audit(
            db=db,
            action=AuditAction.UNAUTHORIZED_ACCESS,
            description="無効なJWTトークンでのアクセス試行",
            level=AuditLevel.HIGH,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent")
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効な認証トークンです",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ユーザーID取得
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンにユーザー情報がありません",
        )
    
    # ユーザーをテナント情報と一緒に取得（eager loading）
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(User)
        .options(selectinload(User.tenant))
        .where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません",
        )
    
    # ユーザー状態チェック
    if not user.is_active or user.status != UserStatus.ACTIVE:
        await log_audit(
            db=db,
            action=AuditAction.UNAUTHORIZED_ACCESS,
            description=f"非アクティブユーザーによるアクセス試行: {user.username}",
            level=AuditLevel.MEDIUM,
            user_id=user.id,
            username=user.username,
            ip_address=get_client_ip(request)
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アカウントが無効です",
        )
    
    # アカウントロックチェック
    if user.is_locked:
        await log_audit(
            db=db,
            action=AuditAction.UNAUTHORIZED_ACCESS,
            description=f"ロックされたアカウントによるアクセス試行: {user.username}",
            level=AuditLevel.HIGH,
            user_id=user.id,
            username=user.username,
            ip_address=get_client_ip(request)
        )
        
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="アカウントがロックされています",
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """現在のアクティブユーザーを取得"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="非アクティブなユーザーです"
        )
    return current_user

async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """管理者権限が必要な操作用"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return current_user

async def get_manager_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """管理者またはマネージャー権限が必要な操作用"""
    if not current_user.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者またはマネージャー権限が必要です"
        )
    return current_user

def check_rate_limit(request: Request, identifier: Optional[str] = None):
    """レート制限チェック"""
    if identifier is None:
        identifier = get_client_ip(request)
    
    if not login_rate_limiter.is_allowed(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="リクエストが多すぎます。しばらく時間をおいてから再試行してください。"
        )

def get_client_ip(request: Request) -> str:
    """クライアントIPアドレスを取得"""
    # プロキシ経由の場合のヘッダーもチェック
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"

async def log_audit(
    db: AsyncSession,
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
    success: bool = True,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    **kwargs
):
    """監査ログを記録"""
    audit_log = AuditLog.create_log(
        action=action,
        description=description,
        user_id=user_id,
        username=username,
        user_role=user_role,
        level=level,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        endpoint=endpoint,
        http_method=http_method,
        success=success,
        error_code=error_code,
        error_message=error_message,
        **kwargs
    )
    
    db.add(audit_log)
    await db.commit()

class RequirePermissions:
    """権限チェッククラス"""
    
    def __init__(self, *permissions: str):
        self.permissions = permissions
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        # 管理者は全権限を持つ
        if current_user.is_admin:
            return current_user
        
        # 権限チェック実装（将来的にはより詳細な権限システム）
        # 現在は役割ベースの簡易チェック
        for permission in self.permissions:
            if permission == "manage_templates" and not current_user.can_access_templates:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"'{permission}' 権限が必要です"
                )
        
        return current_user

# 権限チェック用のインスタンス
require_template_management = RequirePermissions("manage_templates")
require_user_management = RequirePermissions("manage_users")
require_system_management = RequirePermissions("manage_system")