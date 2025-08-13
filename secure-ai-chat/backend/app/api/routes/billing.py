"""
請求・決済管理API
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.models.tenant import Tenant
from app.models.subscription import Subscription, Plan, PlanType
from app.services.billing_service import billing_service, format_currency
from app.services.email_service import send_trial_reminder_email

router = APIRouter()
logger = logging.getLogger(__name__)


class SubscriptionResponse(BaseModel):
    id: str
    tenant_id: str
    plan: dict
    status: str
    trial_end_date: Optional[datetime]
    next_billing_date: Optional[datetime]
    monthly_price: float
    usage: dict
    stripe_customer_portal_url: Optional[str] = None


class PlanChangeRequest(BaseModel):
    new_plan: str  # starter, standard, professional, enterprise
    billing_interval: str = "monthly"  # monthly, yearly


class PaymentMethodRequest(BaseModel):
    payment_method_id: str


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription_details(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """現在のサブスクリプション詳細取得"""
    try:
        # テナントのサブスクリプション取得
        result = await db.execute(
            select(Subscription)
            .join(Tenant)
            .where(Tenant.id == current_user.tenant_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="サブスクリプションが見つかりません")
        
        # プラン情報取得
        plan_result = await db.execute(
            select(Plan).where(Plan.id == subscription.plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        
        # 使用量取得
        usage_data = subscription.usage_percentage
        
        # Stripe顧客ポータルURL生成（管理者のみ）
        portal_url = None
        if current_user.role == 'admin' and subscription.stripe_customer_id:
            portal_url = await billing_service.generate_billing_portal_url(
                subscription.stripe_customer_id,
                f"https://{current_user.tenant.domain}/dashboard"
            )
        
        return SubscriptionResponse(
            id=str(subscription.id),
            tenant_id=str(subscription.tenant_id),
            plan={
                "id": plan.plan_type.value if plan else "unknown",
                "name": plan.name if plan else "Unknown",
                "max_users": plan.max_users if plan else 0,
                "max_tokens_per_month": plan.max_tokens_per_month if plan else 0,
                "monthly_price": float(plan.monthly_price) if plan else 0,
                "features": {
                    "api_access": plan.has_api_access if plan else False,
                    "custom_branding": plan.has_custom_branding if plan else False,
                    "priority_support": plan.has_priority_support if plan else False,
                    "advanced_analytics": plan.has_advanced_analytics if plan else False
                }
            },
            status=subscription.status.value,
            trial_end_date=subscription.trial_end_date,
            next_billing_date=subscription.next_billing_date,
            monthly_price=float(subscription.monthly_price),
            usage={
                "users": {
                    "current": subscription.current_users,
                    "limit": plan.max_users if plan else 0,
                    "percentage": usage_data.get("users", 0)
                },
                "tokens": {
                    "current": subscription.tokens_used_this_month,
                    "limit": plan.max_tokens_per_month if plan else 0,
                    "percentage": usage_data.get("tokens", 0)
                },
                "storage": {
                    "current": float(subscription.storage_used_gb),
                    "limit": plan.max_storage_gb if plan else 0,
                    "percentage": usage_data.get("storage", 0)
                }
            },
            stripe_customer_portal_url=portal_url
        )
        
    except Exception as e:
        logger.error(f"サブスクリプション取得エラー: {e}")
        raise HTTPException(status_code=500, detail="サブスクリプション情報の取得に失敗しました")


@router.get("/plans")
async def get_available_plans():
    """利用可能なプラン一覧取得"""
    plans = [
        {
            "id": "starter",
            "name": "Starter",
            "description": "小規模チーム向けの基本プラン",
            "monthly_price": 29800,
            "yearly_price": 298000,  # 年払い17%オフ
            "max_users": 10,
            "max_tokens_per_month": 100000,
            "max_templates": 10,
            "max_storage_gb": 5,
            "features": {
                "ai_chat": True,
                "templates": True,
                "basic_analytics": True,
                "email_support": True,
                "api_access": False,
                "custom_branding": False,
                "priority_support": False,
                "advanced_analytics": False
            },
            "trial_days": 14,
            "popular": False
        },
        {
            "id": "standard",
            "name": "Standard",
            "description": "中規模企業向けの推奨プラン",
            "monthly_price": 49800,
            "yearly_price": 498000,  # 年払い17%オフ
            "max_users": 50,
            "max_tokens_per_month": 500000,
            "max_templates": 50,
            "max_storage_gb": 25,
            "features": {
                "ai_chat": True,
                "templates": True,
                "basic_analytics": True,
                "email_support": True,
                "api_access": True,
                "custom_api_settings": True,
                "custom_branding": False,
                "priority_support": False,
                "advanced_analytics": True
            },
            "trial_days": 14,
            "popular": True
        },
        {
            "id": "professional",
            "name": "Professional", 
            "description": "大企業向けの高機能プラン",
            "monthly_price": 98000,
            "yearly_price": 980000,  # 年払い17%オフ
            "max_users": 200,
            "max_tokens_per_month": 2000000,
            "max_templates": 200,
            "max_storage_gb": 100,
            "features": {
                "ai_chat": True,
                "templates": True,
                "basic_analytics": True,
                "email_support": True,
                "api_access": True,
                "custom_api_settings": True,
                "custom_branding": True,
                "priority_support": True,
                "advanced_analytics": True,
                "phone_support": True
            },
            "trial_days": 30,
            "popular": False
        },
        {
            "id": "enterprise",
            "name": "Enterprise",
            "description": "大規模組織向けのエンタープライズプラン",
            "monthly_price": 198000,
            "yearly_price": 1980000,  # 年払い17%オフ
            "max_users": 9999,
            "max_tokens_per_month": 10000000,
            "max_templates": 9999,
            "max_storage_gb": 1000,
            "features": {
                "ai_chat": True,
                "templates": True,
                "basic_analytics": True,
                "email_support": True,
                "api_access": True,
                "custom_api_settings": True,
                "custom_branding": True,
                "priority_support": True,
                "advanced_analytics": True,
                "phone_support": True,
                "dedicated_support": True,
                "custom_integrations": True,
                "sla_99_9": True
            },
            "trial_days": 30,
            "popular": False,
            "contact_sales": True
        }
    ]
    
    return {"plans": plans}


@router.post("/change-plan")
async def change_subscription_plan(
    plan_change: PlanChangeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """サブスクリプションプラン変更"""
    try:
        # 現在のサブスクリプション取得
        result = await db.execute(
            select(Subscription)
            .join(Tenant)
            .where(Tenant.id == current_user.tenant_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="サブスクリプションが見つかりません")
        
        # 新しいプラン情報取得
        plans = await get_available_plans()
        new_plan_info = None
        for plan in plans["plans"]:
            if plan["id"] == plan_change.new_plan:
                new_plan_info = plan
                break
        
        if not new_plan_info:
            raise HTTPException(status_code=400, detail="無効なプランが指定されました")
        
        # プラン変更処理
        success = await billing_service.update_subscription_plan(
            db,
            subscription,
            plan_change.new_plan,
            {
                'name': new_plan_info['name'],
                'max_users': new_plan_info['max_users'],
                'max_tokens_per_month': new_plan_info['max_tokens_per_month'],
                'price_monthly': new_plan_info['yearly_price'] // 12 if plan_change.billing_interval == 'yearly' else new_plan_info['monthly_price']
            }
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="プラン変更に失敗しました")
        
        # 成功通知メール送信（バックグラウンド）
        # background_tasks.add_task(send_plan_change_notification, current_user.email, plan_change.new_plan)
        
        return {
            "message": f"プランを {new_plan_info['name']} に変更しました",
            "new_plan": plan_change.new_plan,
            "billing_interval": plan_change.billing_interval,
            "effective_date": "即座に反映" if new_plan_info['monthly_price'] > subscription.monthly_price else "次回更新時"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"プラン変更エラー: {e}")
        raise HTTPException(status_code=500, detail="プラン変更中にエラーが発生しました")


@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """サブスクリプション解約"""
    try:
        # 現在のサブスクリプション取得
        result = await db.execute(
            select(Subscription)
            .join(Tenant)
            .where(Tenant.id == current_user.tenant_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="サブスクリプションが見つかりません")
        
        if subscription.status.value == 'cancelled':
            raise HTTPException(status_code=400, detail="既に解約済みです")
        
        # 解約処理
        success = await billing_service.cancel_subscription(
            db,
            subscription,
            "ユーザーによる解約"
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="解約処理に失敗しました")
        
        return {
            "message": "サブスクリプションを解約しました",
            "effective_date": subscription.current_period_end.isoformat() if subscription.current_period_end else "即座に反映",
            "data_retention": "データは90日間保持されます"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"サブスクリプション解約エラー: {e}")
        raise HTTPException(status_code=500, detail="解約処理中にエラーが発生しました")


@router.get("/usage-history")
async def get_usage_history(
    months: int = 6,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """使用量履歴取得"""
    try:
        # 使用量サマリー取得
        current_month_data = await billing_service.get_usage_summary(
            db, 
            current_user.tenant_id
        )
        
        # 過去の月次データ（ダミーデータ - 実際の実装では履歴テーブルから取得）
        history = []
        current_date = datetime.now(timezone.utc)
        
        for i in range(months):
            month = current_date.replace(month=current_date.month - i) if current_date.month > i else \
                   current_date.replace(year=current_date.year - 1, month=12 - (i - current_date.month))
            
            history.append({
                "month": month.strftime("%Y-%m"),
                "tokens_used": current_month_data.get('usage', {}).get('tokens_used', 0) * (0.8 + i * 0.1),  # ダミー変動
                "users_active": current_month_data.get('usage', {}).get('users_active', 0),
                "cost": current_month_data.get('costs', {}).get('total_cost', 0),
                "plan": current_month_data.get('subscription', {}).get('plan', 'Unknown')
            })
        
        return {
            "current_month": current_month_data,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"使用量履歴取得エラー: {e}")
        raise HTTPException(status_code=500, detail="使用量履歴の取得に失敗しました")


@router.get("/invoices")
async def get_invoices(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """請求書一覧取得"""
    try:
        # サブスクリプション取得
        result = await db.execute(
            select(Subscription)
            .join(Tenant)
            .where(Tenant.id == current_user.tenant_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return {"invoices": []}
        
        # 請求履歴取得（最新のもの）
        from app.models.subscription import BillingHistory
        invoices_result = await db.execute(
            select(BillingHistory)
            .where(BillingHistory.subscription_id == subscription.id)
            .order_by(BillingHistory.billing_date.desc())
            .limit(limit)
        )
        invoices = invoices_result.scalars().all()
        
        invoice_list = []
        for invoice in invoices:
            invoice_list.append({
                "id": str(invoice.id),
                "billing_date": invoice.billing_date.isoformat(),
                "amount": float(invoice.amount),
                "currency": invoice.currency,
                "period_start": invoice.period_start.isoformat(),
                "period_end": invoice.period_end.isoformat(),
                "paid": invoice.paid,
                "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
                "users_billed": invoice.users_billed,
                "tokens_used": invoice.tokens_used,
                "status": "paid" if invoice.paid else ("overdue" if invoice.billing_date < datetime.now(timezone.utc) else "pending")
            })
        
        return {"invoices": invoice_list}
        
    except Exception as e:
        logger.error(f"請求書一覧取得エラー: {e}")
        raise HTTPException(status_code=500, detail="請求書一覧の取得に失敗しました")


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Stripe Webhook エンドポイント"""
    try:
        payload = await request.body()
        signature = request.headers.get('stripe-signature')
        
        if not signature:
            raise HTTPException(status_code=400, detail="Stripe署名がありません")
        
        # バックグラウンドでWebhook処理
        background_tasks.add_task(
            billing_service.handle_webhook,
            payload.decode(),
            signature
        )
        
        return {"received": True}
        
    except Exception as e:
        logger.error(f"Stripe Webhook エラー: {e}")
        raise HTTPException(status_code=500, detail="Webhook処理に失敗しました")


@router.get("/trial-status")
async def get_trial_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """トライアル状況取得"""
    try:
        result = await db.execute(
            select(Subscription)
            .join(Tenant)
            .where(Tenant.id == current_user.tenant_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return {"is_trial": False}
        
        is_trial = subscription.is_trial
        days_remaining = subscription.days_remaining if subscription.trial_end_date else None
        
        return {
            "is_trial": is_trial,
            "trial_end_date": subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
            "days_remaining": days_remaining,
            "status": subscription.status.value,
            "upgrade_required": is_trial and days_remaining is not None and days_remaining <= 3
        }
        
    except Exception as e:
        logger.error(f"トライアル状況取得エラー: {e}")
        raise HTTPException(status_code=500, detail="トライアル状況の取得に失敗しました")