"""
SaaS セルフサービス登録API
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import re

from app.core.database import get_db
from app.core.security import get_password_hash, create_access_token
from app.models.tenant import Tenant
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionStatus, PlanType, Plan
from app.services.email_service import send_welcome_email, send_confirmation_email

router = APIRouter()


class SignupRequest(BaseModel):
    # 会社情報
    company_name: str
    subdomain: str
    
    # 管理者情報
    admin_email: EmailStr
    admin_name: str
    admin_password: str
    
    # プラン情報
    plan: str = "starter"  # starter, standard, professional, enterprise
    
    # オプション
    use_system_default: bool = True
    
    @validator('company_name')
    def validate_company_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('会社名は2文字以上で入力してください')
        if len(v.strip()) > 100:
            raise ValueError('会社名は100文字以内で入力してください')
        return v.strip()
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        if not v:
            raise ValueError('サブドメインは必須です')
        
        # 英数字とハイフンのみ許可
        if not re.match(r'^[a-z0-9-]+$', v.lower()):
            raise ValueError('サブドメインは英数字とハイフン(-)のみ使用できます')
        
        if len(v) < 3:
            raise ValueError('サブドメインは3文字以上で入力してください')
        if len(v) > 20:
            raise ValueError('サブドメインは20文字以内で入力してください')
        
        # 予約語チェック
        reserved = ['www', 'api', 'admin', 'app', 'mail', 'support', 'help', 'docs', 'blog']
        if v.lower() in reserved:
            raise ValueError(f'"{v}" は予約されているため使用できません')
        
        return v.lower()
    
    @validator('admin_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上で入力してください')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('パスワードには英字を含めてください')
        if not re.search(r'[0-9]', v):
            raise ValueError('パスワードには数字を含めてください')
        return v
    
    @validator('plan')
    def validate_plan(cls, v):
        valid_plans = ['starter', 'standard', 'professional', 'enterprise']
        if v.lower() not in valid_plans:
            raise ValueError(f'有効なプラン: {", ".join(valid_plans)}')
        return v.lower()


class SignupResponse(BaseModel):
    tenant_id: str
    admin_user_id: str
    company_name: str
    subdomain: str
    plan: str
    domain: str
    access_token: str
    trial_end_date: Optional[datetime]
    message: str


async def check_subdomain_availability(db: AsyncSession, subdomain: str) -> bool:
    """サブドメインの利用可能性チェック"""
    result = await db.execute(
        select(Tenant).where(Tenant.subdomain == subdomain.lower())
    )
    return result.scalar_one_or_none() is None


async def check_email_availability(db: AsyncSession, email: str) -> bool:
    """メールアドレスの利用可能性チェック"""
    result = await db.execute(
        select(User).where(User.email == email.lower())
    )
    return result.scalar_one_or_none() is None


def get_plan_details(plan: str) -> dict:
    """プラン詳細情報取得"""
    plan_configs = {
        'starter': {
            'name': 'Starter',
            'max_users': 10,
            'max_tokens_per_month': 100000,
            'price_monthly': 29800,
            'trial_days': 14
        },
        'standard': {
            'name': 'Standard', 
            'max_users': 50,
            'max_tokens_per_month': 500000,
            'price_monthly': 49800,
            'trial_days': 14
        },
        'professional': {
            'name': 'Professional',
            'max_users': 200,
            'max_tokens_per_month': 2000000,
            'price_monthly': 98000,
            'trial_days': 30
        },
        'enterprise': {
            'name': 'Enterprise',
            'max_users': 9999,
            'max_tokens_per_month': 10000000,
            'price_monthly': 198000,
            'trial_days': 30
        }
    }
    return plan_configs.get(plan, plan_configs['starter'])


async def provision_tenant(
    db: AsyncSession, 
    signup_data: SignupRequest,
    background_tasks: BackgroundTasks
) -> tuple[Tenant, User]:
    """テナントとユーザーの自動プロビジョニング"""
    
    # プラン詳細取得
    plan_details = get_plan_details(signup_data.plan)
    
    # 1. テナント作成
    tenant_id = uuid.uuid4()
    tenant = Tenant(
        id=tenant_id,
        name=signup_data.company_name,
        domain=f"{signup_data.subdomain}.secure-ai-chat.com",
        subdomain=signup_data.subdomain,
        plan=signup_data.plan,
        max_users=plan_details['max_users'],
        max_tokens_per_month=plan_details['max_tokens_per_month'],
        ai_provider="system_default",
        use_system_default=signup_data.use_system_default,
        is_active=True,
        trial_end_date=datetime.utcnow() + timedelta(days=plan_details['trial_days'])
    )
    
    db.add(tenant)
    await db.flush()
    
    # 2. 管理者ユーザー作成
    admin_user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=signup_data.admin_email.lower(),
        username=signup_data.admin_name,
        full_name=signup_data.admin_name,
        hashed_password=get_password_hash(signup_data.admin_password),
        role="admin",
        is_active=True,
        is_verified=False,  # メール確認が必要
        created_at=datetime.utcnow()
    )
    
    db.add(admin_user)
    await db.flush()
    
    # 3. プラン取得
    from sqlalchemy import select
    plan_result = await db.execute(
        select(Plan).where(Plan.plan_type == PlanType(signup_data.plan))
    )
    plan = plan_result.scalar_one_or_none()
    
    # プランが存在しない場合はデフォルトプラン作成
    if not plan:
        plan = Plan(
            id=uuid.uuid4(),
            name=plan_details['name'],
            plan_type=PlanType(signup_data.plan),
            max_users=plan_details['max_users'],
            max_tokens_per_month=plan_details['max_tokens_per_month'],
            monthly_price=plan_details['price_monthly']
        )
        db.add(plan)
        await db.flush()
    
    # サブスクリプション作成
    subscription = Subscription(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        plan_id=plan.id,
        status=SubscriptionStatus.TRIAL,
        start_date=datetime.utcnow(),
        trial_end_date=tenant.trial_end_date,
        monthly_price=plan_details['price_monthly']
    )
    
    db.add(subscription)
    
    # 4. データベースに保存
    await db.commit()
    await db.refresh(tenant)
    await db.refresh(admin_user)
    
    # 5. バックグラウンドタスク（メール送信）
    background_tasks.add_task(
        send_welcome_email,
        admin_user.email,
        {
            'name': admin_user.full_name,
            'company': tenant.name,
            'domain': tenant.domain,
            'plan': plan_details['name'],
            'trial_days': plan_details['trial_days']
        }
    )
    
    background_tasks.add_task(
        send_confirmation_email,
        admin_user.email,
        admin_user.id
    )
    
    return tenant, admin_user


@router.post("/signup", response_model=SignupResponse)
async def signup_saas_customer(
    signup_data: SignupRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """SaaS顧客セルフサインアップ"""
    
    # 1. バリデーション
    if not await check_subdomain_availability(db, signup_data.subdomain):
        raise HTTPException(
            status_code=400,
            detail=f"サブドメイン '{signup_data.subdomain}' は既に使用されています"
        )
    
    if not await check_email_availability(db, signup_data.admin_email):
        raise HTTPException(
            status_code=400,
            detail=f"メールアドレス '{signup_data.admin_email}' は既に登録されています"
        )
    
    try:
        # 2. テナント・ユーザープロビジョニング
        tenant, admin_user = await provision_tenant(db, signup_data, background_tasks)
        
        # 3. アクセストークン生成
        access_token = create_access_token(
            data={
                "sub": str(admin_user.id),
                "tenant_id": str(tenant.id),
                "role": admin_user.role,
                "email": admin_user.email
            }
        )
        
        # 4. レスポンス生成
        return SignupResponse(
            tenant_id=str(tenant.id),
            admin_user_id=str(admin_user.id),
            company_name=tenant.name,
            subdomain=tenant.subdomain,
            plan=tenant.plan,
            domain=tenant.domain,
            access_token=access_token,
            trial_end_date=tenant.trial_end_date,
            message=f"🎉 {tenant.name} のアカウントが正常に作成されました！"
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"アカウント作成中にエラーが発生しました: {str(e)}"
        )


@router.get("/check-subdomain/{subdomain}")
async def check_subdomain_available(
    subdomain: str,
    db: AsyncSession = Depends(get_db)
):
    """サブドメイン利用可能性チェック"""
    
    # 基本バリデーション
    if not re.match(r'^[a-z0-9-]+$', subdomain.lower()):
        return {
            "available": False,
            "message": "サブドメインは英数字とハイフン(-)のみ使用できます"
        }
    
    if len(subdomain) < 3 or len(subdomain) > 20:
        return {
            "available": False,
            "message": "サブドメインは3-20文字で入力してください"
        }
    
    # 予約語チェック
    reserved = ['www', 'api', 'admin', 'app', 'mail', 'support', 'help', 'docs', 'blog']
    if subdomain.lower() in reserved:
        return {
            "available": False,
            "message": f"'{subdomain}' は予約されているため使用できません"
        }
    
    # データベースチェック
    available = await check_subdomain_availability(db, subdomain)
    
    return {
        "available": available,
        "message": "利用可能です" if available else "既に使用されています",
        "domain": f"{subdomain.lower()}.secure-ai-chat.com" if available else None
    }


@router.get("/plans")
async def get_available_plans():
    """利用可能なプラン一覧取得"""
    
    plans = []
    for plan_id in ['starter', 'standard', 'professional', 'enterprise']:
        details = get_plan_details(plan_id)
        plans.append({
            "id": plan_id,
            "name": details['name'],
            "max_users": details['max_users'],
            "max_tokens_per_month": details['max_tokens_per_month'],
            "price_monthly": details['price_monthly'],
            "trial_days": details['trial_days'],
            "recommended": plan_id == 'standard'  # おすすめプラン
        })
    
    return {"plans": plans}