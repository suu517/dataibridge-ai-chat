"""
認証API エンドポイント
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import secrets

from app.core.database import get_db
from app.core.middleware import (
    create_access_token, 
    get_current_user,
    require_auth,
    require_tenant_admin,
    get_tenant_by_domain,
    get_tenant_by_subdomain
)
from app.models.auth import User, UserSession, UserInvitation, UserRole
from app.models.tenant import Tenant

router = APIRouter(prefix="/auth", tags=["認証"])

# リクエスト/レスポンスモデル
class UserRegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    tenant_domain: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_domain: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24時間

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    tenant_id: str
    
    class Config:
        from_attributes = True

class TenantRegisterRequest(BaseModel):
    name: str
    domain: str
    subdomain: str
    admin_email: EmailStr
    admin_name: str
    admin_password: str
    plan: str = "starter"

class InviteUserRequest(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.USER

class AcceptInvitationRequest(BaseModel):
    invitation_token: str
    full_name: str
    password: str

@router.post("/register/tenant", response_model=dict)
async def register_tenant(
    request: TenantRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """テナント新規登録"""
    # ドメイン/サブドメインの重複チェック
    existing_domain = await get_tenant_by_domain(request.domain, db)
    if existing_domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このドメインは既に使用されています"
        )
    
    existing_subdomain = await get_tenant_by_subdomain(request.subdomain, db)
    if existing_subdomain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このサブドメインは既に使用されています"
        )
    
    try:
        # テナント作成
        tenant = Tenant(
            name=request.name,
            domain=request.domain,
            subdomain=request.subdomain,
            plan=request.plan,
            trial_end_date=datetime.utcnow() + timedelta(days=14)  # 14日間トライアル
        )
        db.add(tenant)
        await db.flush()  # IDを取得
        
        # 管理者ユーザー作成
        admin_user = User(
            tenant_id=tenant.id,
            email=request.admin_email,
            full_name=request.admin_name,
            role=UserRole.TENANT_ADMIN,
            is_active=True,
            is_verified=True
        )
        admin_user.set_password(request.admin_password)
        
        db.add(admin_user)
        await db.commit()
        await db.refresh(tenant)
        await db.refresh(admin_user)
        
        return {
            "message": "テナント登録が完了しました",
            "tenant_id": str(tenant.id),
            "admin_user_id": str(admin_user.id)
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登録に失敗しました: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """ユーザーログイン"""
    # テナント特定
    tenant = None
    if request.tenant_domain:
        tenant = await get_tenant_by_domain(request.tenant_domain, db)
        if not tenant:
            tenant = await get_tenant_by_subdomain(request.tenant_domain, db)
    
    # ユーザー検索
    query = select(User).where(User.email == request.email, User.is_active == True)
    if tenant:
        query = query.where(User.tenant_id == tenant.id)
    
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not user.verify_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが間違っています"
        )
    
    # セッション作成
    session = UserSession.create_session(
        user_id=str(user.id),
        ip_address="127.0.0.1",  # TODO: 実際のIPアドレスを取得
        user_agent="User-Agent"  # TODO: 実際のUser-Agentを取得
    )
    db.add(session)
    
    # ログイン情報更新
    user.update_login()
    
    await db.commit()
    
    # JWTトークン生成
    access_token = create_access_token(
        data={"sub": str(user.id), "tenant_id": str(user.tenant_id)}
    )
    
    return TokenResponse(access_token=access_token)

@router.post("/logout")
async def logout(
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """ログアウト"""
    # 現在のセッションを無効化
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        )
    )
    sessions = result.scalars().all()
    
    for session in sessions:
        session.revoke()
    
    await db.commit()
    
    return {"message": "ログアウトしました"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(require_auth)
):
    """現在のユーザー情報取得"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        tenant_id=str(current_user.tenant_id)
    )

@router.post("/invite")
async def invite_user(
    request: InviteUserRequest,
    current_user: User = Depends(require_tenant_admin),
    db: AsyncSession = Depends(get_db)
):
    """ユーザー招待"""
    # 既存ユーザーチェック
    existing_user = await db.execute(
        select(User).where(
            User.email == request.email,
            User.tenant_id == current_user.tenant_id
        )
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に登録されています"
        )
    
    # 既存の招待チェック
    existing_invitation = await db.execute(
        select(UserInvitation).where(
            UserInvitation.email == request.email,
            UserInvitation.tenant_id == current_user.tenant_id,
            UserInvitation.is_accepted == False
        )
    )
    if existing_invitation.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスに既に招待が送信されています"
        )
    
    # 招待作成
    invitation = UserInvitation.create_invitation(
        tenant_id=str(current_user.tenant_id),
        email=request.email,
        role=request.role,
        invited_by=str(current_user.id)
    )
    
    db.add(invitation)
    await db.commit()
    
    # TODO: メール送信処理
    
    return {
        "message": "招待を送信しました",
        "invitation_token": invitation.invitation_token
    }

@router.post("/accept-invitation", response_model=TokenResponse)
async def accept_invitation(
    request: AcceptInvitationRequest,
    db: AsyncSession = Depends(get_db)
):
    """招待承認"""
    # 招待確認
    result = await db.execute(
        select(UserInvitation).where(
            UserInvitation.invitation_token == request.invitation_token,
            UserInvitation.is_accepted == False
        )
    )
    invitation = result.scalar_one_or_none()
    
    if not invitation or invitation.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無効または期限切れの招待です"
        )
    
    # ユーザー作成
    user = User(
        tenant_id=invitation.tenant_id,
        email=invitation.email,
        full_name=request.full_name,
        role=invitation.role,
        is_active=True,
        is_verified=True
    )
    user.set_password(request.password)
    
    db.add(user)
    
    # 招待を承認済みに
    invitation.accept()
    
    await db.commit()
    await db.refresh(user)
    
    # セッション作成とトークン生成
    session = UserSession.create_session(
        user_id=str(user.id),
        ip_address="127.0.0.1",
        user_agent="User-Agent"
    )
    db.add(session)
    await db.commit()
    
    access_token = create_access_token(
        data={"sub": str(user.id), "tenant_id": str(user.tenant_id)}
    )
    
    return TokenResponse(access_token=access_token)