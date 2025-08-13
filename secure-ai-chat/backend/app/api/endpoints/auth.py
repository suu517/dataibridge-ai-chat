"""
認証・認可APIエンドポイント
JWT + OAuth2による安全な認証システム
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token, 
    create_refresh_token,
    verify_password, 
    get_password_hash,
    verify_token
)
from app.models.user import User
from app.services.logging_service import log_security_event
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Pydantic モデル
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    department: Optional[str] = None
    position: Optional[str] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    refresh_token: str

class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    department: Optional[str]
    position: Optional[str]
    role: str
    status: str
    is_active: bool
    created_at: str
    last_login: Optional[str]

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

# 認証依存性
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """現在のユーザーを取得"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報を確認できません",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    # ユーザー取得
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="アカウントが無効化されています"
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """アクティブなユーザーを取得"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="アカウントが無効化されています"
        )
    return current_user

# エンドポイント
@router.post("/register", response_model=UserProfile)
async def register(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """新規ユーザー登録"""
    
    # 既存ユーザーチェック（メール）
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に登録されています"
        )
    
    # 既存ユーザーチェック（ユーザー名）
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このユーザー名は既に使用されています"
        )
    
    # パスワードハッシュ化
    hashed_password = get_password_hash(user_data.password)
    
    # 新しいユーザー作成
    from app.models.user import UserRole, UserStatus
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        department=user_data.department,
        position=user_data.position,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_active=True
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # セキュリティログ
    await log_security_event(
        db=db,
        event_type="user_register",
        user_id=new_user.id,
        ip_address=request.client.host if request.client else "unknown",
        details={"email": user_data.email}
    )
    
    logger.info(f"新規ユーザー登録: {user_data.email}")
    
    return UserProfile(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.decrypted_full_name,
        department=new_user.department,
        position=new_user.position,
        role=new_user.role.value,
        status=new_user.status.value,
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat(),
        last_login=new_user.last_login.isoformat() if new_user.last_login else None
    )

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """ユーザーログイン"""
    
    # ユーザー認証（ユーザー名またはメールアドレスで認証）
    result = await db.execute(
        select(User).where(
            (User.username == form_data.username) | (User.email == form_data.username)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        # セキュリティログ（失敗）
        await log_security_event(
            db=db,
            event_type="login_failed",
            user_id=user.id if user else None,
            ip_address=request.client.host if request and request.client else "unknown",
            details={"email": form_data.username}
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが間違っています",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="アカウントが無効化されています"
        )
    
    # トークン生成
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(subject=str(user.id))
    
    # 最終ログイン時刻更新
    user.update_last_login()
    await db.commit()
    
    # セキュリティログ（成功）
    await log_security_event(
        db=db,
        event_type="login_success",
        user_id=user.id,
        ip_address=request.client.host if request and request.client else "unknown",
        details={"email": user.email}
    )
    
    logger.info(f"ユーザーログイン成功: {user.email}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """トークン更新"""
    try:
        payload = verify_token(token_data.refresh_token, is_refresh_token=True)
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なリフレッシュトークンです"
            )
        
        # ユーザー存在確認
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ユーザーが見つからないか、アカウントが無効です"
            )
        
        # 新しいトークン生成
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        new_refresh_token = create_refresh_token(data={"sub": user.email})
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    except Exception as e:
        logger.error(f"トークン更新エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンの更新に失敗しました"
        )

@router.get("/me", response_model=UserProfile)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """現在のユーザー情報取得"""
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.decrypted_full_name,
        department=current_user.department,
        position=current_user.position,
        role=current_user.role.value,
        status=current_user.status.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None
    )

@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """パスワード変更"""
    
    # 現在のパスワード確認
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="現在のパスワードが間違っています"
        )
    
    # 新しいパスワードハッシュ化
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    # セキュリティログ
    await log_security_event(
        db=db,
        event_type="password_changed",
        user_id=current_user.id,
        ip_address=request.client.host if request and request.client else "unknown",
        details={"email": current_user.email}
    )
    
    logger.info(f"パスワード変更: {current_user.email}")

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_active_user),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """ユーザーログアウト"""
    
    # セキュリティログ
    await log_security_event(
        db=db,
        event_type="logout",
        user_id=current_user.id,
        ip_address=request.client.host if request and request.client else "unknown",
        details={"email": current_user.email}
    )
    
    logger.info(f"ユーザーログアウト: {current_user.email}")
    
    # NOTE: JWTはステートレスなため、クライアント側でトークンを削除する必要あり
    # 本格的な実装では、トークンブラックリスト機能を追加可能