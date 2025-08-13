"""
セキュアAIチャット - 認証・認可機能
"""

from fastapi import Depends, HTTPException, status, WebSocket, WebSocketException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User

# HTTP Bearer認証
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """現在のユーザーを取得（HTTP用）"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報が無効です",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # JWTトークン検証
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        # ユーザーID取得
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # ユーザー情報取得
        stmt = select(User).where(User.id == int(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user is None:
            raise credentials_exception
            
        # ユーザーがアクティブかチェック
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="非アクティブなユーザーです"
            )
            
        return user
        
    except HTTPException:
        raise
    except Exception:
        raise credentials_exception

async def get_current_user_ws(token: str) -> User:
    """現在のユーザーを取得（WebSocket用）"""
    
    try:
        # JWTトークン検証
        payload = verify_token(token)
        if payload is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        
        # ユーザーID取得
        user_id: str = payload.get("sub")
        if user_id is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload")
        
        # データベースセッション取得
        from app.core.database import async_session
        async with async_session() as db:
            # ユーザー情報取得
            stmt = select(User).where(User.id == int(user_id))
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user is None:
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
                
            # ユーザーがアクティブかチェック
            if not user.is_active:
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Inactive user")
                
            return user
            
    except WebSocketException:
        raise
    except Exception as e:
        raise WebSocketException(code=status.WS_1011_INTERNAL_ERROR, reason=f"Authentication error: {str(e)}")

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

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """現在の管理者ユーザーを取得"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return current_user

class PermissionChecker:
    """権限チェッククラス"""
    
    def __init__(self, required_permission: str):
        self.required_permission = required_permission
    
    async def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """権限をチェック"""
        
        # 管理者は全権限を持つ
        if current_user.is_admin:
            return current_user
        
        # TODO: 個別の権限システムを実装
        # 現在は簡易版として管理者のみアクセス許可
        if self.required_permission in ["admin", "manage_users", "manage_templates"]:
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"権限 '{self.required_permission}' が必要です"
                )
        
        return current_user

# 権限チェッカーのインスタンス
RequirePermission = PermissionChecker