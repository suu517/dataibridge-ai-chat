"""
ユーザー管理・招待 API エンドポイント
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List

from app.core.database import get_db
from app.services.user_service import UserService
from app.models.user import UserRole
from app.schemas.user import (
    UserInvite,
    UserInviteResponse,
    UserAcceptInvitation,
    UserListResponse,
    UserRoleUpdate
)

router = APIRouter(prefix="/users", tags=["ユーザー管理"])

@router.post("/invite", response_model=UserInviteResponse)
async def invite_user(
    invitation: UserInvite,
    tenant_id: str,
    inviter_id: str,  # 実際の実装では認証ミドルウェアから取得
    db: Session = Depends(get_db)
):
    """
    ユーザー招待
    """
    user_service = UserService(db)
    
    result = user_service.invite_user(
        tenant_id=tenant_id,
        inviter_id=inviter_id,
        email=invitation.email,
        role=invitation.role,
        department=invitation.department,
        position=invitation.position
    )
    
    if not result.get("success"):
        error_msg = result.get("error", "招待処理に失敗しました")
        if "権限がありません" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )
        elif "制限に達しています" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=error_msg
            )
        elif "既に登録されています" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
    
    return {
        "success": True,
        "message": "ユーザー招待を送信しました",
        "data": result
    }

@router.post("/accept-invitation")
async def accept_invitation(
    invitation_data: UserAcceptInvitation,
    db: Session = Depends(get_db)
):
    """
    招待受諾・アカウント有効化
    """
    user_service = UserService(db)
    
    result = user_service.accept_invitation(
        invitation_token=invitation_data.invitation_token,
        full_name=invitation_data.full_name,
        new_password=invitation_data.new_password
    )
    
    if not result.get("success"):
        error_msg = result.get("error", "招待受諾に失敗しました")
        if "無効" in error_msg or "期限切れ" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
    
    return {
        "success": True,
        "message": result.get("message"),
        "user": result.get("user")
    }

@router.get("/list/{tenant_id}", response_model=UserListResponse)
async def get_tenant_users(
    tenant_id: str,
    requester_id: str,  # 実際の実装では認証ミドルウェアから取得
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    テナントのユーザー一覧取得
    """
    user_service = UserService(db)
    
    result = user_service.get_tenant_users(
        tenant_id=tenant_id,
        requester_id=requester_id,
        limit=limit,
        offset=offset
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.get("error", "権限がありません")
        )
    
    return result

@router.put("/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_update: UserRoleUpdate,
    tenant_id: str,
    requester_id: str,  # 実際の実装では認証ミドルウェアから取得
    db: Session = Depends(get_db)
):
    """
    ユーザーの役割更新
    """
    user_service = UserService(db)
    
    result = user_service.update_user_role(
        tenant_id=tenant_id,
        requester_id=requester_id,
        user_id=user_id,
        new_role=role_update.role
    )
    
    if not result.get("success"):
        error_msg = result.get("error", "権限更新に失敗しました")
        if "権限が必要" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )
        elif "見つかりません" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    
    return {
        "success": True,
        "message": result.get("message"),
        "user": result.get("user")
    }

@router.delete("/{user_id}")
async def deactivate_user(
    user_id: str,
    tenant_id: str,
    requester_id: str,  # 実際の実装では認証ミドルウェアから取得
    db: Session = Depends(get_db)
):
    """
    ユーザー非アクティブ化
    """
    user_service = UserService(db)
    
    result = user_service.deactivate_user(
        tenant_id=tenant_id,
        requester_id=requester_id,
        user_id=user_id
    )
    
    if not result.get("success"):
        error_msg = result.get("error", "ユーザー無効化に失敗しました")
        if "権限が必要" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )
        elif "見つかりません" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    
    return {
        "success": True,
        "message": result.get("message")
    }