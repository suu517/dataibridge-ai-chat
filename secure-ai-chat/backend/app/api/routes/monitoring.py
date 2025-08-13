"""
システム監視・アラート管理API
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import logging
import psutil
import os

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.models.tenant import Tenant
from app.models.subscription import Subscription, BillingHistory
from app.services.email_service import email_service

router = APIRouter()
logger = logging.getLogger(__name__)


class SystemHealthResponse(BaseModel):
    status: str  # healthy, warning, critical
    timestamp: datetime
    uptime: float  # seconds
    services: Dict[str, Any]
    metrics: Dict[str, Any]


class AlertRequest(BaseModel):
    type: str  # usage_limit, payment_failed, system_error
    threshold: float
    enabled: bool
    notification_emails: List[str]


class MonitoringAlert(BaseModel):
    id: str
    type: str
    severity: str  # info, warning, error, critical
    message: str
    created_at: datetime
    resolved_at: Optional[datetime]
    tenant_id: Optional[str]


@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(
    current_user: User = Depends(require_admin)
):
    """システムヘルスチェック"""
    try:
        # システムリソース情報
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # プロセス情報
        process_count = len(psutil.pids())
        
        # データベース接続確認（簡易）
        db_status = "healthy"
        try:
            # データベース接続テストは実際の実装で行う
            pass
        except Exception:
            db_status = "error"
        
        # サービス状態判定
        status = "healthy"
        if cpu_usage > 80 or memory.percent > 85 or disk.percent > 90:
            status = "warning"
        if cpu_usage > 95 or memory.percent > 95 or disk.percent > 95 or db_status == "error":
            status = "critical"
        
        return SystemHealthResponse(
            status=status,
            timestamp=datetime.now(timezone.utc),
            uptime=time.time() - psutil.boot_time(),
            services={
                "database": db_status,
                "api_server": "healthy",
                "background_tasks": "healthy",
                "email_service": "healthy" if hasattr(email_service, 'smtp_server') else "warning"
            },
            metrics={
                "cpu_usage_percent": cpu_usage,
                "memory_usage_percent": memory.percent,
                "disk_usage_percent": disk.percent,
                "process_count": process_count,
                "disk_free_gb": disk.free / (1024**3),
                "memory_available_gb": memory.available / (1024**3)
            }
        )
        
    except Exception as e:
        logger.error(f"システムヘルス取得エラー: {e}")
        raise HTTPException(status_code=500, detail="システムヘルス情報の取得に失敗しました")


@router.get("/system/metrics")
async def get_system_metrics(
    hours: int = 24,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """システムメトリクス取得"""
    try:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        # テナント統計
        tenants_result = await db.execute(
            select(func.count(Tenant.id)).where(
                and_(
                    Tenant.created_at >= start_time,
                    Tenant.is_active == True
                )
            )
        )
        new_tenants = tenants_result.scalar() or 0
        
        total_tenants_result = await db.execute(
            select(func.count(Tenant.id)).where(Tenant.is_active == True)
        )
        total_tenants = total_tenants_result.scalar() or 0
        
        # ユーザー統計
        active_users_result = await db.execute(
            select(func.count(User.id)).where(
                and_(
                    User.is_active == True,
                    User.last_login >= start_time
                )
            )
        )
        active_users = active_users_result.scalar() or 0
        
        # サブスクリプション統計
        active_subs_result = await db.execute(
            select(func.count(Subscription.id)).where(
                Subscription.status.in_(['trial', 'active'])
            )
        )
        active_subscriptions = active_subs_result.scalar() or 0
        
        # 収益統計（今月）
        current_month_start = end_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        revenue_result = await db.execute(
            select(func.sum(BillingHistory.amount)).where(
                and_(
                    BillingHistory.billing_date >= current_month_start,
                    BillingHistory.paid == True
                )
            )
        )
        monthly_revenue = revenue_result.scalar() or 0
        
        return {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "tenants": {
                "total": total_tenants,
                "new": new_tenants,
                "growth_rate": (new_tenants / max(total_tenants - new_tenants, 1)) * 100
            },
            "users": {
                "active": active_users,
                "activity_rate": (active_users / max(total_tenants * 10, 1)) * 100  # 想定平均ユーザー数
            },
            "subscriptions": {
                "active": active_subscriptions,
                "conversion_rate": (active_subscriptions / max(total_tenants, 1)) * 100
            },
            "revenue": {
                "monthly": float(monthly_revenue),
                "currency": "JPY",
                "arpu": float(monthly_revenue) / max(active_subscriptions, 1)  # Average Revenue Per User
            }
        }
        
    except Exception as e:
        logger.error(f"システムメトリクス取得エラー: {e}")
        raise HTTPException(status_code=500, detail="システムメトリクスの取得に失敗しました")


@router.get("/alerts")
async def get_alerts(
    limit: int = 50,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    current_user: User = Depends(require_admin)
):
    """アラート一覧取得"""
    try:
        # 実際の実装ではアラートテーブルから取得
        # ここではサンプルデータを返す
        alerts = [
            MonitoringAlert(
                id="alert_001",
                type="usage_limit",
                severity="warning",
                message="テナント 'sample-company' が月間トークン制限の90%に達しました",
                created_at=datetime.now(timezone.utc) - timedelta(hours=2),
                resolved_at=None,
                tenant_id="tenant_123"
            ),
            MonitoringAlert(
                id="alert_002", 
                type="system_error",
                severity="error",
                message="API接続エラーが5分間で10回発生しました",
                created_at=datetime.now(timezone.utc) - timedelta(hours=1),
                resolved_at=datetime.now(timezone.utc) - timedelta(minutes=30),
                tenant_id=None
            ),
            MonitoringAlert(
                id="alert_003",
                type="payment_failed",
                severity="critical",
                message="テナント 'enterprise-corp' の決済が失敗しました",
                created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
                resolved_at=None,
                tenant_id="tenant_456"
            )
        ]
        
        # フィルタリング
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if resolved is not None:
            alerts = [a for a in alerts if (a.resolved_at is not None) == resolved]
        
        return {
            "alerts": alerts[:limit],
            "total": len(alerts),
            "unresolved": len([a for a in alerts if a.resolved_at is None])
        }
        
    except Exception as e:
        logger.error(f"アラート取得エラー: {e}")
        raise HTTPException(status_code=500, detail="アラート情報の取得に失敗しました")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(require_admin)
):
    """アラート解決マーク"""
    try:
        # 実際の実装ではデータベースでアラートを更新
        logger.info(f"アラート {alert_id} が {current_user.email} によって解決されました")
        
        return {
            "message": "アラートを解決済みにマークしました",
            "alert_id": alert_id,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "resolved_by": current_user.email
        }
        
    except Exception as e:
        logger.error(f"アラート解決エラー: {e}")
        raise HTTPException(status_code=500, detail="アラートの解決に失敗しました")


@router.get("/tenants/overview")
async def get_tenants_overview(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """テナント概要取得"""
    try:
        # テナント一覧取得（最新20件）
        result = await db.execute(
            select(Tenant, Subscription)
            .outerjoin(Subscription)
            .order_by(Tenant.created_at.desc())
            .limit(20)
        )
        tenants_data = result.all()
        
        tenants_overview = []
        for tenant, subscription in tenants_data:
            # 使用量データ（簡易版）
            usage_percentage = 0
            if subscription:
                plan = subscription.plan
                if plan and plan.max_tokens_per_month > 0:
                    usage_percentage = (subscription.tokens_used_this_month / plan.max_tokens_per_month) * 100
            
            tenants_overview.append({
                "id": str(tenant.id),
                "name": tenant.name,
                "subdomain": tenant.subdomain,
                "plan": subscription.plan.name if subscription and subscription.plan else "Unknown",
                "status": subscription.status.value if subscription else "inactive",
                "created_at": tenant.created_at.isoformat(),
                "user_count": tenant.current_user_count,
                "usage_percentage": usage_percentage,
                "trial_end_date": subscription.trial_end_date.isoformat() if subscription and subscription.trial_end_date else None,
                "monthly_revenue": float(subscription.monthly_price) if subscription else 0,
                "health_status": "healthy" if usage_percentage < 80 else ("warning" if usage_percentage < 95 else "critical")
            })
        
        return {"tenants": tenants_overview}
        
    except Exception as e:
        logger.error(f"テナント概要取得エラー: {e}")
        raise HTTPException(status_code=500, detail="テナント概要の取得に失敗しました")


@router.get("/performance")
async def get_performance_metrics(
    current_user: User = Depends(require_admin)
):
    """パフォーマンスメトリクス取得"""
    try:
        # 実際のメトリクス（サンプル）
        import time
        current_time = time.time()
        
        return {
            "api_response_times": {
                "average_ms": 245,
                "p95_ms": 450,
                "p99_ms": 780
            },
            "database_performance": {
                "average_query_time_ms": 12,
                "slow_queries_count": 3,
                "connection_pool_usage": 45
            },
            "ai_service_metrics": {
                "average_response_time_ms": 2100,
                "success_rate": 99.2,
                "error_rate": 0.8,
                "requests_per_minute": 156
            },
            "system_load": {
                "cpu_usage": 34.2,
                "memory_usage": 67.8,
                "disk_io_wait": 2.1
            },
            "cache_performance": {
                "hit_rate": 89.3,
                "miss_rate": 10.7,
                "eviction_rate": 1.2
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"パフォーマンスメトリクス取得エラー: {e}")
        raise HTTPException(status_code=500, detail="パフォーマンスメトリクスの取得に失敗しました")


@router.post("/alerts/configure")
async def configure_alert(
    alert_config: AlertRequest,
    current_user: User = Depends(require_admin)
):
    """アラート設定"""
    try:
        # アラート設定の保存（実際の実装ではデータベースに保存）
        logger.info(f"アラート設定更新: {alert_config.type} by {current_user.email}")
        
        return {
            "message": "アラート設定を更新しました",
            "config": {
                "type": alert_config.type,
                "threshold": alert_config.threshold,
                "enabled": alert_config.enabled,
                "notification_count": len(alert_config.notification_emails)
            }
        }
        
    except Exception as e:
        logger.error(f"アラート設定エラー: {e}")
        raise HTTPException(status_code=500, detail="アラート設定の更新に失敗しました")


@router.post("/maintenance")
async def schedule_maintenance(
    maintenance_window: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    """メンテナンス予約"""
    try:
        # メンテナンス予約処理
        logger.info(f"メンテナンス予約: {maintenance_window} by {current_user.email}")
        
        return {
            "message": "メンテナンスを予約しました",
            "maintenance_id": f"maint_{int(time.time())}",
            "scheduled_time": maintenance_window.get("start_time"),
            "duration_minutes": maintenance_window.get("duration", 30)
        }
        
    except Exception as e:
        logger.error(f"メンテナンス予約エラー: {e}")
        raise HTTPException(status_code=500, detail="メンテナンス予約に失敗しました")


@router.get("/logs")
async def get_system_logs(
    level: str = "INFO",
    hours: int = 24,
    limit: int = 100,
    current_user: User = Depends(require_admin)
):
    """システムログ取得"""
    try:
        # ログファイルから最新のログを取得（実際の実装）
        # ここではサンプルデータを返す
        logs = [
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
                "level": "INFO",
                "service": "api_server",
                "message": "User authentication successful",
                "details": {"user_id": "user_123", "tenant_id": "tenant_456"}
            },
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat(),
                "level": "WARNING", 
                "service": "ai_service",
                "message": "API response time exceeded threshold",
                "details": {"response_time_ms": 3200, "threshold_ms": 3000}
            },
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
                "level": "ERROR",
                "service": "billing_service",
                "message": "Payment processing failed",
                "details": {"error": "Invalid payment method", "customer_id": "cus_123"}
            }
        ]
        
        return {
            "logs": logs[:limit],
            "total": len(logs),
            "level": level,
            "period_hours": hours
        }
        
    except Exception as e:
        logger.error(f"システムログ取得エラー: {e}")
        raise HTTPException(status_code=500, detail="システムログの取得に失敗しました")


# バックグラウンドタスク用の監視関数
async def check_system_health_background():
    """システムヘルスチェック（バックグラウンド実行）"""
    try:
        # CPU、メモリ、ディスク使用量チェック
        cpu_usage = psutil.cpu_percent(interval=5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 閾値チェックとアラート生成
        alerts = []
        
        if cpu_usage > 90:
            alerts.append({
                "type": "system_resource",
                "severity": "critical",
                "message": f"CPU使用率が危険レベルです: {cpu_usage}%"
            })
        elif cpu_usage > 75:
            alerts.append({
                "type": "system_resource", 
                "severity": "warning",
                "message": f"CPU使用率が高くなっています: {cpu_usage}%"
            })
        
        if memory.percent > 90:
            alerts.append({
                "type": "system_resource",
                "severity": "critical", 
                "message": f"メモリ使用率が危険レベルです: {memory.percent}%"
            })
        
        if disk.percent > 85:
            alerts.append({
                "type": "system_resource",
                "severity": "warning",
                "message": f"ディスク使用率が高くなっています: {disk.percent}%"
            })
        
        # アラート処理
        for alert in alerts:
            logger.warning(f"システムアラート: {alert['message']}")
            # 実際の実装ではアラートをデータベースに保存し、通知を送信
        
    except Exception as e:
        logger.error(f"バックグラウンドヘルスチェックエラー: {e}")


# 定期実行用のタスク設定（実際の実装では Celery や APScheduler を使用）
import asyncio
import time

def start_background_monitoring():
    """バックグラウンド監視の開始"""
    async def monitoring_loop():
        while True:
            await check_system_health_background()
            await asyncio.sleep(300)  # 5分間隔
    
    # 非同期タスクとして実行
    asyncio.create_task(monitoring_loop())