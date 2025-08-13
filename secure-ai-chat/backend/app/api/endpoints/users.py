"""
ユーザー管理APIエンドポイント
ユーザープロフィール管理、権限管理
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.endpoints.auth import get_current_active_user, get_current_user
from app.models.user import User
from app.models.audit import AuditLog
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic モデル
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None

class UserList(BaseModel):
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

class UserStats(BaseModel):
    total_users: int
    active_users: int
    new_users_today: int
    new_users_week: int

class UserActivity(BaseModel):
    date: str
    login_count: int
    chat_count: int

# ユーザー管理エンドポイント
@router.get("/profile", response_model=UserList)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """現在のユーザープロフィール取得"""
    return UserList(
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

@router.put("/profile", response_model=UserList)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """ユーザープロフィール更新"""
    
    # 更新可能なフィールドのみ更新
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.department is not None:
        current_user.department = user_update.department
    
    if user_update.position is not None:
        current_user.position = user_update.position
    
    current_user.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(current_user)
    
    logger.info(f"ユーザープロフィール更新: {current_user.email}")
    
    return UserList(
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

@router.get("/list", response_model=List[UserList])
async def get_users_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, min_length=1),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """ユーザーリスト取得（管理者のみ）"""
    
    # 管理者権限チェック
    if not current_user.is_admin and not current_user.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です"
        )
    
    # クエリ構築
    query = select(User)
    
    # 検索条件
    filters = []
    
    if search:
        search_term = f"%{search}%"
        filters.append(
            func.or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term),
                User.department.ilike(search_term),
                User.position.ilike(search_term)
            )
        )
    
    if role:
        filters.append(User.role == role)
    
    if is_active is not None:
        filters.append(User.is_active == is_active)
    
    if filters:
        query = query.where(and_(*filters))
    
    # 結果取得
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [
        UserList(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.decrypted_full_name,
            department=user.department,
            position=user.position,
            role=user.role.value,
            status=user.status.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            last_login=user.last_login.isoformat() if user.last_login else None
        )
        for user in users
    ]

@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """ユーザー統計取得（管理者のみ）"""
    
    # 管理者権限チェック
    if not current_user.is_admin and not current_user.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です"
        )
    
    # 現在の日時
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    
    # 統計クエリ
    # 総ユーザー数
    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar()
    
    # アクティブユーザー数
    active_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_result.scalar()
    
    # 今日の新規ユーザー数
    today_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )
    new_users_today = today_result.scalar()
    
    # 週間新規ユーザー数
    week_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_start)
    )
    new_users_week = week_result.scalar()
    
    return UserStats(
        total_users=total_users,
        active_users=active_users,
        new_users_today=new_users_today,
        new_users_week=new_users_week
    )

@router.get("/activity", response_model=List[UserActivity])
async def get_user_activity(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """ユーザーアクティビティ取得（管理者のみ）"""
    
    # 管理者権限チェック
    if not current_user.is_admin and not current_user.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です"
        )
    
    # 過去N日間のアクティビティ取得
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days-1)
    
    activity_data = []
    current_date = start_date
    
    while current_date <= end_date:
        date_start = datetime.combine(current_date, datetime.min.time())
        date_end = date_start + timedelta(days=1)
        
        # ログイン数取得
        login_result = await db.execute(
            select(func.count(AuditLog.id)).where(
                and_(
                    AuditLog.event_type == "login_success",
                    AuditLog.timestamp >= date_start,
                    AuditLog.timestamp < date_end
                )
            )
        )
        login_count = login_result.scalar() or 0
        
        # チャット数取得（将来実装）
        chat_count = 0  # 暫定的に0
        
        activity_data.append(UserActivity(
            date=current_date.isoformat(),
            login_count=login_count,
            chat_count=chat_count
        ))
        
        current_date += timedelta(days=1)
    
    return activity_data

@router.put("/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """ユーザー権限変更（管理者のみ）"""
    
    # 管理者権限チェック
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です"
        )
    
    # 有効なロールチェック
    from app.models.user import UserRole
    valid_roles = [role.value for role in UserRole]
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"無効な権限です。有効な権限: {valid_roles}"
        )
    
    # 対象ユーザー取得
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )
    
    # 自分自身の権限変更を防ぐ
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="自分自身の権限を変更することはできません"
        )
    
    # 権限更新
    old_role = target_user.role.value
    target_user.role = UserRole(role)
    target_user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"ユーザー権限変更: {target_user.email} ({old_role} -> {role}) by {current_user.email}")
    
    return {"message": "権限が更新されました"}

@router.put("/{user_id}/status")
async def toggle_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """ユーザーステータス変更（管理者のみ）"""
    
    # 管理者権限チェック
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です"
        )
    
    # 対象ユーザー取得
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )
    
    # 自分自身のステータス変更を防ぐ
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="自分自身のステータスを変更することはできません"
        )
    
    # ステータス更新
    old_status = target_user.is_active
    target_user.is_active = is_active
    target_user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"ユーザーステータス変更: {target_user.email} ({old_status} -> {is_active}) by {current_user.email}")
    
    return {"message": f"ユーザーステータスが{'有効' if is_active else '無効'}に更新されました"}