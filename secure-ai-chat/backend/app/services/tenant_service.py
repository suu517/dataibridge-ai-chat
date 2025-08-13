"""
テナント管理サービス
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.tenant import Tenant
from app.models.user import User, UserRole, UserStatus
from app.models.subscription import Subscription, Plan, PlanType, SubscriptionStatus
from app.core.security import get_password_hash
import uuid

class TenantService:
    """テナント管理サービス"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_tenant(
        self,
        name: str,
        domain: str,
        subdomain: str,
        admin_email: str,
        admin_name: str,
        admin_password: str,
        plan_type: PlanType = PlanType.STARTER
    ) -> Dict:
        """
        テナント作成（管理者ユーザーとサブスクリプションも同時作成）
        """
        try:
            # 1. ドメイン・サブドメイン重複チェック
            existing_domain = self.db.query(Tenant).filter(
                Tenant.domain == domain
            ).first()
            
            if existing_domain:
                return {"success": False, "error": "Domain already exists"}
            
            existing_subdomain = self.db.query(Tenant).filter(
                Tenant.subdomain == subdomain
            ).first()
            
            if existing_subdomain:
                return {"success": False, "error": "Subdomain already taken"}
            
            # 2. テナント作成
            tenant = Tenant(
                name=name,
                domain=domain,
                subdomain=subdomain,
                plan=plan_type.value,
                is_active=True,
                trial_end_date=datetime.now(timezone.utc) + timedelta(days=14)  # 14日間トライアル
            )
            self.db.add(tenant)
            self.db.flush()
            
            # 3. プラン取得
            plan = self.db.query(Plan).filter(Plan.plan_type == plan_type).first()
            if not plan:
                # デフォルトプランがない場合は作成
                plan = self._create_default_plan(plan_type)
            
            # 4. サブスクリプション作成（トライアル状態）
            subscription = Subscription(
                tenant_id=tenant.id,
                plan_id=plan.id,
                status=SubscriptionStatus.TRIAL,
                start_date=datetime.now(timezone.utc),
                trial_end_date=datetime.now(timezone.utc) + timedelta(days=14),
                monthly_price=plan.monthly_price,
                current_users=1  # 管理者ユーザー
            )
            self.db.add(subscription)
            self.db.flush()
            
            # 5. 管理者ユーザー作成
            admin_user = User(
                tenant_id=tenant.id,
                username=admin_email.split('@')[0],  # メールアドレスの@前を使用
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                full_name=admin_name,
                role=UserRole.TENANT_ADMIN,
                status=UserStatus.ACTIVE,
                is_active=True,
                is_verified=True
            )
            self.db.add(admin_user)
            
            # 6. 変更をコミット
            self.db.commit()
            
            return {
                "success": True,
                "tenant": {
                    "id": str(tenant.id),
                    "name": tenant.name,
                    "domain": tenant.domain,
                    "subdomain": tenant.subdomain,
                    "trial_end_date": tenant.trial_end_date.isoformat(),
                },
                "admin_user": {
                    "id": str(admin_user.id),
                    "email": admin_user.email,
                    "username": admin_user.username,
                }
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """ドメインからテナント取得"""
        return self.db.query(Tenant).filter(Tenant.domain == domain).first()
    
    def get_tenant_by_subdomain(self, subdomain: str) -> Optional[Tenant]:
        """サブドメインからテナント取得"""
        return self.db.query(Tenant).filter(Tenant.subdomain == subdomain).first()
    
    def update_tenant_settings(self, tenant_id: str, settings: Dict) -> bool:
        """テナント設定更新"""
        try:
            tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                return False
            
            # 設定を JSON として保存
            import json
            tenant.settings = json.dumps(settings)
            tenant.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            return True
        except:
            self.db.rollback()
            return False
    
    def get_tenant_stats(self, tenant_id: str) -> Dict:
        """テナント統計情報"""
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return {}
        
        # ユーザー統計
        total_users = self.db.query(User).filter(User.tenant_id == tenant_id).count()
        active_users = self.db.query(User).filter(
            and_(User.tenant_id == tenant_id, User.is_active == True)
        ).count()
        
        # サブスクリプション情報
        subscription = tenant.subscription
        
        return {
            "tenant_id": str(tenant_id),
            "tenant_name": tenant.name,
            "users": {
                "total": total_users,
                "active": active_users,
                "limit": subscription.plan.max_users if subscription else tenant.max_users
            },
            "subscription": {
                "status": subscription.status.value if subscription else "inactive",
                "plan": subscription.plan.name if subscription else tenant.plan,
                "trial_end": subscription.trial_end_date.isoformat() if subscription and subscription.trial_end_date else None,
                "next_billing": subscription.next_billing_date.isoformat() if subscription and subscription.next_billing_date else None,
            },
            "usage": subscription.usage_percentage if subscription else {},
            "created_at": tenant.created_at.isoformat()
        }
    
    def _create_default_plan(self, plan_type: PlanType) -> Plan:
        """デフォルトプラン作成"""
        plan_configs = {
            PlanType.STARTER: {
                "name": "スタータープラン",
                "max_users": 10,
                "max_tokens_per_month": 100000,
                "max_templates": 10,
                "max_storage_gb": 5,
                "monthly_price": 29800,
                "features": ["基本AI機能", "メールサポート", "標準テンプレート"]
            },
            PlanType.STANDARD: {
                "name": "スタンダードプラン", 
                "max_users": 50,
                "max_tokens_per_month": 500000,
                "max_templates": 50,
                "max_storage_gb": 20,
                "monthly_price": 49800,
                "features": ["全AI機能", "電話サポート", "カスタムテンプレート", "レポート機能"]
            },
            PlanType.PROFESSIONAL: {
                "name": "プロフェッショナルプラン",
                "max_users": 200,
                "max_tokens_per_month": 2000000,
                "max_templates": -1,  # 無制限
                "max_storage_gb": 100,
                "monthly_price": 98000,
                "features": ["全機能", "専用サポート", "カスタムブランディング", "API access"]
            }
        }
        
        config = plan_configs.get(plan_type, plan_configs[PlanType.STARTER])
        
        plan = Plan(
            plan_type=plan_type,
            name=config["name"],
            max_users=config["max_users"],
            max_tokens_per_month=config["max_tokens_per_month"],
            max_templates=config["max_templates"],
            max_storage_gb=config["max_storage_gb"],
            monthly_price=config["monthly_price"],
            features=str(config["features"])  # JSON文字列として保存
        )
        
        self.db.add(plan)
        self.db.flush()
        return plan
    
    def list_tenants(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """テナント一覧取得（システム管理用）"""
        tenants = self.db.query(Tenant).offset(offset).limit(limit).all()
        
        result = []
        for tenant in tenants:
            result.append({
                "id": str(tenant.id),
                "name": tenant.name,
                "domain": tenant.domain,
                "subdomain": tenant.subdomain,
                "plan": tenant.plan,
                "is_active": tenant.is_active,
                "user_count": len(tenant.users),
                "created_at": tenant.created_at.isoformat(),
                "subscription_status": tenant.subscription_status
            })
        
        return result