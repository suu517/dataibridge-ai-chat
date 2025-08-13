"""
管理ダッシュボード API エンドポイント
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.models.user import User, UserStatus
from app.models.tenant import Tenant
from app.models.subscription import Subscription, Plan
from app.services.auth_service import require_tenant_admin
from app.schemas.admin import (
    SystemStats,
    TenantListResponse,
    UserListResponse,
    SubscriptionStats
)

router = APIRouter(prefix="/admin", tags=["管理ダッシュボード"])

@router.get("/stats/overview", response_model=SystemStats)
async def get_system_overview(
    current_user: User = Depends(require_tenant_admin()),
    db: Session = Depends(get_db)
):
    """
    システム全体の統計情報取得
    """
    # 現在の日付
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 基本統計
    total_users = db.query(User).count()
    active_users = db.query(User).filter(
        and_(User.is_active == True, User.status == UserStatus.ACTIVE)
    ).count()
    
    total_tenants = db.query(Tenant).count()
    active_tenants = db.query(Tenant).filter(Tenant.is_active == True).count()
    
    # サブスクリプション統計
    active_subscriptions = db.query(Subscription).filter(
        Subscription.status == "active"
    ).count()
    
    # 月間収益計算
    monthly_revenue = db.query(func.sum(Subscription.monthly_price)).filter(
        and_(
            Subscription.status == "active",
            Subscription.start_date >= month_start
        )
    ).scalar() or 0
    
    # 月間トークン使用量
    monthly_tokens = db.query(func.sum(Subscription.tokens_used_this_month)).filter(
        Subscription.status == "active"
    ).scalar() or 0
    
    # 成長率計算（前月比）
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
    prev_month_end = month_start - timedelta(seconds=1)
    
    prev_month_users = db.query(User).filter(
        User.created_at.between(prev_month_start, prev_month_end)
    ).count()
    
    current_month_users = db.query(User).filter(
        User.created_at >= month_start
    ).count()
    
    user_growth_rate = (
        ((current_month_users - prev_month_users) / prev_month_users * 100) 
        if prev_month_users > 0 else 0
    )
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "active_subscriptions": active_subscriptions,
        "monthly_revenue": float(monthly_revenue),
        "monthly_tokens": int(monthly_tokens),
        "user_growth_rate": round(user_growth_rate, 1),
        "last_updated": now.isoformat()
    }

@router.get("/tenants", response_model=TenantListResponse)
async def get_all_tenants(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_tenant_admin()),
    db: Session = Depends(get_db)
):
    """
    全テナント一覧取得
    """
    query = db.query(Tenant)
    
    # 検索フィルター
    if search:
        query = query.filter(
            or_(
                Tenant.name.ilike(f"%{search}%"),
                Tenant.domain.ilike(f"%{search}%"),
                Tenant.subdomain.ilike(f"%{search}%")
            )
        )
    
    # 状態フィルター
    if status:
        if status == "active":
            query = query.filter(Tenant.is_active == True)
        elif status == "inactive":
            query = query.filter(Tenant.is_active == False)
    
    total = query.count()
    tenants = query.offset(offset).limit(limit).all()
    
    tenant_list = []
    for tenant in tenants:
        # ユーザー数取得
        user_count = db.query(User).filter(User.tenant_id == tenant.id).count()
        
        # サブスクリプション情報取得
        subscription = tenant.subscription
        
        tenant_list.append({
            "id": str(tenant.id),
            "name": tenant.name,
            "domain": tenant.domain,
            "subdomain": tenant.subdomain,
            "plan": subscription.plan.name if subscription else tenant.plan,
            "user_count": user_count,
            "max_users": subscription.plan.max_users if subscription else tenant.max_users,
            "is_active": tenant.is_active,
            "subscription_status": tenant.subscription_status,
            "created_at": tenant.created_at.isoformat(),
            "trial_end_date": tenant.trial_end_date.isoformat() if tenant.trial_end_date else None
        })
    
    return {
        "tenants": tenant_list,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/users", response_model=UserListResponse)
async def get_all_users(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    tenant_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_tenant_admin()),
    db: Session = Depends(get_db)
):
    """
    全ユーザー一覧取得
    """
    query = db.query(User).join(Tenant)
    
    # 検索フィルター
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    
    # テナントフィルター
    if tenant_id:
        query = query.filter(User.tenant_id == tenant_id)
    
    # 状態フィルター
    if status:
        query = query.filter(User.status == status)
    
    total = query.count()
    users = query.offset(offset).limit(limit).all()
    
    user_list = []
    for user in users:
        tenant = user.tenant
        
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
            "created_at": user.created_at.isoformat(),
            "tenant": {
                "id": str(tenant.id),
                "name": tenant.name,
                "domain": tenant.domain
            }
        })
    
    return {
        "users": user_list,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/subscriptions/stats", response_model=SubscriptionStats)
async def get_subscription_stats(
    current_user: User = Depends(require_tenant_admin()),
    db: Session = Depends(get_db)
):
    """
    サブスクリプション統計情報
    """
    # プラン別統計
    plan_stats = db.query(
        Plan.name,
        func.count(Subscription.id).label('count'),
        func.sum(Subscription.monthly_price).label('revenue')
    ).join(Subscription).filter(
        Subscription.status == "active"
    ).group_by(Plan.name).all()
    
    plan_breakdown = []
    for stat in plan_stats:
        plan_breakdown.append({
            "plan_name": stat.name,
            "subscription_count": stat.count,
            "monthly_revenue": float(stat.revenue)
        })
    
    # 状態別統計
    status_stats = db.query(
        Subscription.status,
        func.count(Subscription.id).label('count')
    ).group_by(Subscription.status).all()
    
    status_breakdown = []
    for stat in status_stats:
        status_breakdown.append({
            "status": stat.status,
            "count": stat.count
        })
    
    # 総収益
    total_revenue = db.query(func.sum(Subscription.monthly_price)).filter(
        Subscription.status == "active"
    ).scalar() or 0
    
    # MRR (Monthly Recurring Revenue)
    mrr = total_revenue
    
    # 解約率計算（簡易版）
    total_subscriptions = db.query(Subscription).count()
    cancelled_subscriptions = db.query(Subscription).filter(
        Subscription.status == "cancelled"
    ).count()
    
    churn_rate = (
        (cancelled_subscriptions / total_subscriptions * 100) 
        if total_subscriptions > 0 else 0
    )
    
    return {
        "total_subscriptions": total_subscriptions,
        "active_subscriptions": len([p for p in plan_breakdown]),
        "monthly_recurring_revenue": float(mrr),
        "churn_rate": round(churn_rate, 2),
        "plan_breakdown": plan_breakdown,
        "status_breakdown": status_breakdown
    }

@router.get("/usage/analytics")
async def get_usage_analytics(
    period: str = "month",
    current_user: User = Depends(require_tenant_admin()),
    db: Session = Depends(get_db)
):
    """
    使用状況分析
    """
    now = datetime.now(timezone.utc)
    
    if period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    else:
        start_date = now - timedelta(days=30)
    
    # トークン使用量統計
    token_usage = db.query(
        func.sum(Subscription.tokens_used_this_month).label('total_tokens'),
        func.avg(Subscription.tokens_used_this_month).label('avg_tokens')
    ).filter(
        and_(
            Subscription.status == "active",
            Subscription.start_date >= start_date
        )
    ).first()
    
    # ストレージ使用量
    storage_usage = db.query(
        func.sum(Subscription.storage_used_gb).label('total_storage'),
        func.avg(Subscription.storage_used_gb).label('avg_storage')
    ).filter(
        Subscription.status == "active"
    ).first()
    
    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "token_usage": {
            "total": int(token_usage.total_tokens or 0),
            "average": float(token_usage.avg_tokens or 0)
        },
        "storage_usage": {
            "total": float(storage_usage.total_storage or 0),
            "average": float(storage_usage.avg_storage or 0)
        }
    }

@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    current_user: User = Depends(require_tenant_admin()),
    db: Session = Depends(get_db)
):
    """
    テナント一時停止
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テナントが見つかりません"
        )
    
    tenant.is_active = False
    
    # サブスクリプションも一時停止
    if tenant.subscription:
        tenant.subscription.status = "suspended"
    
    db.commit()
    
    return {"success": True, "message": f"テナント {tenant.name} を一時停止しました"}

@router.post("/tenants/{tenant_id}/reactivate")
async def reactivate_tenant(
    tenant_id: str,
    current_user: User = Depends(require_tenant_admin()),
    db: Session = Depends(get_db)
):
    """
    テナント再アクティブ化
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テナントが見つかりません"
        )
    
    tenant.is_active = True
    
    # サブスクリプションも再開
    if tenant.subscription:
        tenant.subscription.status = "active"
    
    db.commit()
    
    return {"success": True, "message": f"テナント {tenant.name} を再アクティブ化しました"}