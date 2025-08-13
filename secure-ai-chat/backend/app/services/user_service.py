"""
ユーザー管理・招待サービス
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user import User, UserRole, UserStatus
from app.models.tenant import Tenant
from app.core.security import get_password_hash, create_access_token
import uuid
import secrets

class UserService:
    """ユーザー管理サービス"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def invite_user(
        self,
        tenant_id: str,
        inviter_id: str,
        email: str,
        role: UserRole = UserRole.USER,
        department: Optional[str] = None,
        position: Optional[str] = None
    ) -> Dict:
        """
        ユーザー招待
        """
        try:
            # 1. 招待者の権限チェック
            inviter = self.db.query(User).filter(
                and_(User.id == inviter_id, User.tenant_id == tenant_id)
            ).first()
            
            if not inviter or not inviter.can_invite_users:
                return {"success": False, "error": "招待権限がありません"}
            
            # 2. テナントの制限チェック
            tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant or not tenant.can_add_user:
                return {"success": False, "error": "ユーザー追加制限に達しています"}
            
            # 3. 既存ユーザーチェック
            existing_user = self.db.query(User).filter(
                and_(User.email == email, User.tenant_id == tenant_id)
            ).first()
            
            if existing_user:
                return {"success": False, "error": "このメールアドレスは既に登録されています"}
            
            # 4. 仮パスワード生成
            temp_password = secrets.token_urlsafe(12)
            
            # 5. ユーザー作成（PENDING状態）
            new_user = User(
                tenant_id=tenant_id,
                username=email.split('@')[0] + f"_{tenant.subdomain}",
                email=email,
                hashed_password=get_password_hash(temp_password),
                role=role,
                status=UserStatus.PENDING,
                department=department,
                position=position,
                is_active=False,
                is_verified=False
            )
            
            self.db.add(new_user)
            self.db.flush()
            
            # 6. 招待トークン生成
            invitation_token = create_access_token(
                data={"user_id": str(new_user.id), "type": "invitation"},
                expires_delta=timedelta(days=7)  # 7日間有効
            )
            
            self.db.commit()
            
            return {
                "success": True,
                "user": {
                    "id": str(new_user.id),
                    "email": new_user.email,
                    "username": new_user.username,
                    "role": new_user.role.value,
                    "status": new_user.status.value
                },
                "invitation_token": invitation_token,
                "temp_password": temp_password,
                "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def accept_invitation(
        self,
        invitation_token: str,
        full_name: str,
        new_password: str
    ) -> Dict:
        """
        招待を受諾してアカウントを有効化
        """
        try:
            # トークン検証とユーザー取得は認証ミドルウェアで行われると仮定
            # ここでは簡易実装
            from jose import jwt
            from app.core.config import settings
            
            payload = jwt.decode(
                invitation_token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
            
            user_id = payload.get("user_id")
            token_type = payload.get("type")
            
            if token_type != "invitation":
                return {"success": False, "error": "無効な招待トークンです"}
            
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or user.status != UserStatus.PENDING:
                return {"success": False, "error": "無効または期限切れの招待です"}
            
            # アカウント有効化
            user.full_name = full_name
            user.hashed_password = get_password_hash(new_password)
            user.status = UserStatus.ACTIVE
            user.is_active = True
            user.is_verified = True
            user.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            return {
                "success": True,
                "message": "アカウントが正常に有効化されました",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.decrypted_full_name,
                    "role": user.role.value
                }
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def get_tenant_users(
        self,
        tenant_id: str,
        requester_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """
        テナントのユーザー一覧取得
        """
        # 権限チェック
        requester = self.db.query(User).filter(
            and_(User.id == requester_id, User.tenant_id == tenant_id)
        ).first()
        
        if not requester or not requester.is_manager:
            return {"success": False, "error": "権限がありません"}
        
        # ユーザー一覧取得
        users = self.db.query(User).filter(
            User.tenant_id == tenant_id
        ).offset(offset).limit(limit).all()
        
        total_count = self.db.query(User).filter(User.tenant_id == tenant_id).count()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.decrypted_full_name,
                "role": user.role.value,
                "status": user.status.value,
                "department": user.department,
                "position": user.position,
                "is_active": user.is_active,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat()
            })
        
        return {
            "success": True,
            "users": user_list,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    
    def update_user_role(
        self,
        tenant_id: str,
        requester_id: str,
        user_id: str,
        new_role: UserRole
    ) -> Dict:
        """
        ユーザーの役割を更新
        """
        try:
            # 権限チェック
            requester = self.db.query(User).filter(
                and_(User.id == requester_id, User.tenant_id == tenant_id)
            ).first()
            
            if not requester or not requester.is_tenant_admin:
                return {"success": False, "error": "テナント管理者権限が必要です"}
            
            # 対象ユーザー取得
            target_user = self.db.query(User).filter(
                and_(User.id == user_id, User.tenant_id == tenant_id)
            ).first()
            
            if not target_user:
                return {"success": False, "error": "ユーザーが見つかりません"}
            
            # 自分自身の権限は変更不可
            if str(requester.id) == str(user_id):
                return {"success": False, "error": "自分自身の権限は変更できません"}
            
            # 権限更新
            old_role = target_user.role
            target_user.role = new_role
            target_user.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"ユーザーの権限を {old_role.value} から {new_role.value} に変更しました",
                "user": {
                    "id": str(target_user.id),
                    "email": target_user.email,
                    "old_role": old_role.value,
                    "new_role": new_role.value
                }
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def deactivate_user(
        self,
        tenant_id: str,
        requester_id: str,
        user_id: str
    ) -> Dict:
        """
        ユーザーを非アクティブ化
        """
        try:
            # 権限チェック
            requester = self.db.query(User).filter(
                and_(User.id == requester_id, User.tenant_id == tenant_id)
            ).first()
            
            if not requester or not requester.is_manager:
                return {"success": False, "error": "管理者権限が必要です"}
            
            # 対象ユーザー取得
            target_user = self.db.query(User).filter(
                and_(User.id == user_id, User.tenant_id == tenant_id)
            ).first()
            
            if not target_user:
                return {"success": False, "error": "ユーザーが見つかりません"}
            
            # 自分自身は無効化不可
            if str(requester.id) == str(user_id):
                return {"success": False, "error": "自分自身を無効化することはできません"}
            
            # 無効化
            target_user.is_active = False
            target_user.status = UserStatus.INACTIVE
            target_user.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"ユーザー {target_user.email} を非アクティブ化しました"
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}