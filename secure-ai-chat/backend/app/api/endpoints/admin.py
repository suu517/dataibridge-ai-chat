"""
セキュアAIチャット - 管理者API
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_database_session
from app.api.dependencies.auth import get_admin_user, log_audit
from app.models.user import User
from app.models.audit import AuditAction, AuditLevel
from app.services.logging_service import logging_service

router = APIRouter()

# Pydantic モデル
class AuditLogFilter(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    level: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None
    success_only: Optional[bool] = None

class AuditLogResponse(BaseModel):
    logs: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

class AuditLogStatistics(BaseModel):
    period_days: int
    total_logs: int
    successful_logs: int
    failed_logs: int
    success_rate: float
    security_related_logs: int
    level_distribution: Dict[str, int]
    top_actions: List[Dict[str, Any]]
    hourly_distribution: List[Dict[str, Any]]

class UserActivitySummary(BaseModel):
    user_id: int
    period_days: int
    total_activities: int
    last_activity: Optional[str]
    action_breakdown: List[Dict[str, Any]]
    security_incidents: int
    average_daily_activities: float

class SuspiciousActivityReport(BaseModel):
    user_id: int
    time_window_minutes: int
    activity_count: int
    failed_login_count: int
    unique_ip_addresses: int
    alerts: List[Dict[str, Any]]
    risk_level: str

class SystemHealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: int
    database_status: str
    ai_service_status: str
    total_users: int
    total_templates: int
    total_chats: int
    recent_activity_count: int

@router.get("/audit-logs", response_model=AuditLogResponse)
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="ユーザーID"),
    action: Optional[str] = Query(None, description="アクション"),
    level: Optional[str] = Query(None, description="ログレベル"),
    resource_type: Optional[str] = Query(None, description="リソースタイプ"),
    start_date: Optional[datetime] = Query(None, description="開始日時"),
    end_date: Optional[datetime] = Query(None, description="終了日時"),
    search: Optional[str] = Query(None, description="検索キーワード"),
    success_only: Optional[bool] = Query(None, description="成功ログのみ"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=200, description="1ページあたりの件数"),
    sort_by: str = Query("timestamp", description="ソート項目"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="ソート順"),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_admin_user)
):
    """監査ログ一覧を取得"""
    
    try:
        # AuditActionとAuditLevelの変換
        action_enum = None
        if action:
            try:
                action_enum = AuditAction(action)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無効なアクション: {action}"
                )
        
        level_enum = None
        if level:
            try:
                level_enum = AuditLevel(level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無効なレベル: {level}"
                )
        
        result = await logging_service.get_audit_logs(
            db=db,
            user_id=user_id,
            action=action_enum,
            level=level_enum,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            search=search,
            success_only=success_only,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"監査ログ取得エラー: {str(e)}"
        )

@router.get("/audit-logs/statistics", response_model=AuditLogStatistics)
async def get_audit_log_statistics(
    days: int = Query(7, ge=1, le=90, description="統計期間（日数）"),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_admin_user)
):
    """監査ログ統計情報を取得"""
    
    try:
        result = await logging_service.get_audit_log_statistics(db, days)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"統計情報取得エラー: {str(e)}"
        )

@router.get("/users/{user_id}/activity", response_model=UserActivitySummary)
async def get_user_activity_summary(
    user_id: int,
    days: int = Query(7, ge=1, le=30, description="活動期間（日数）"),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_admin_user)
):
    """ユーザー活動サマリーを取得"""
    
    try:
        result = await logging_service.get_user_activity_summary(db, user_id, days)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー活動サマリー取得エラー: {str(e)}"
        )

@router.get("/security/suspicious-activity/{user_id}", response_model=SuspiciousActivityReport)
async def detect_suspicious_activity(
    user_id: int,
    time_window_minutes: int = Query(60, ge=10, le=1440, description="監視時間窓（分）"),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_admin_user)
):
    """疑わしい活動を検出"""
    
    try:
        result = await logging_service.detect_suspicious_activity(
            db, user_id, time_window_minutes
        )
        
        # 高リスクの場合は管理者にアラート
        if result["risk_level"] == "high":
            logging_service.log_system_event(
                event_type="security_alert",
                message=f"高リスクユーザー活動検出: User {user_id}",
                level="warning",
                user_id=user_id,
                risk_level=result["risk_level"],
                alerts=result["alerts"]
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"疑わしい活動検出エラー: {str(e)}"
        )

@router.post("/maintenance/cleanup-logs")
async def cleanup_old_audit_logs(
    request: Request,
    retention_days: Optional[int] = Query(None, ge=1, le=365, description="保持日数"),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_admin_user)
):
    """古い監査ログのクリーンアップ"""
    
    try:
        result = await logging_service.cleanup_old_logs(db, retention_days)
        
        # クリーンアップ操作を監査ログに記録
        await log_audit(
            db=db,
            action=AuditAction.SYSTEM_CONFIG_CHANGE,
            description=f"監査ログクリーンアップ実行: {result['deleted_logs']}件削除",
            user_id=current_user.id,
            username=current_user.username,
            user_role=current_user.role.value,
            level=AuditLevel.HIGH,
            resource_type="audit_log",
            ip_address=request.headers.get("X-Forwarded-For", request.client.host if request.client else None),
            user_agent=request.headers.get("user-agent"),
            details=result
        )
        
        return {
            "message": f"クリーンアップ完了: {result['deleted_logs']}件のログを削除しました",
            **result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ログクリーンアップエラー: {str(e)}"
        )

@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_admin_user)
):
    """システムヘルス状態を取得"""
    
    try:
        from sqlalchemy import text
        import time
        import psutil
        
        # システム稼働時間
        uptime_seconds = int(time.time() - psutil.boot_time())
        
        # データベース状態チェック
        try:
            await db.execute(text("SELECT 1"))
            database_status = "healthy"
        except Exception:
            database_status = "unhealthy"
        
        # AI サービス状態チェック
        try:
            from app.services.ai_service import ai_service
            # 簡単なヘルスチェック（実装に応じて調整）
            ai_service_status = "healthy"
        except Exception:
            ai_service_status = "unhealthy"
        
        # 基本統計情報
        user_count_result = await db.execute(text("SELECT COUNT(*) FROM users"))
        total_users = user_count_result.scalar() or 0
        
        template_count_result = await db.execute(text("SELECT COUNT(*) FROM prompt_templates"))
        total_templates = template_count_result.scalar() or 0
        
        chat_count_result = await db.execute(text("SELECT COUNT(*) FROM chats"))
        total_chats = chat_count_result.scalar() or 0
        
        # 最近24時間のアクティビティ
        recent_activity_result = await db.execute(
            text("SELECT COUNT(*) FROM audit_logs WHERE timestamp > NOW() - INTERVAL '24 hours'")
        )
        recent_activity_count = recent_activity_result.scalar() or 0
        
        overall_status = "healthy"
        if database_status != "healthy" or ai_service_status != "healthy":
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime_seconds,
            "database_status": database_status,
            "ai_service_status": ai_service_status,
            "total_users": total_users,
            "total_templates": total_templates,
            "total_chats": total_chats,
            "recent_activity_count": recent_activity_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"システムヘルス取得エラー: {str(e)}"
        )

@router.get("/system/logs")
async def get_system_logs(
    lines: int = Query(100, ge=1, le=1000, description="取得行数"),
    level: Optional[str] = Query(None, description="ログレベル"),
    current_user: User = Depends(get_admin_user)
):
    """システムログを取得"""
    
    try:
        import os
        from pathlib import Path
        
        # ログファイルパスの取得（設定に応じて調整）
        log_file_path = Path("logs/app.log")
        
        if not log_file_path.exists():
            return {
                "logs": [],
                "message": "ログファイルが見つかりません"
            }
        
        # ログファイルから最新のN行を取得
        with open(log_file_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # レベルフィルタリング（オプション）
        if level:
            filtered_lines = [
                line for line in recent_lines 
                if level.upper() in line.upper()
            ]
            recent_lines = filtered_lines
        
        logs = []
        for line in recent_lines:
            try:
                # 構造化ログの場合はJSON解析
                import json
                log_entry = json.loads(line.strip())
                logs.append(log_entry)
            except json.JSONDecodeError:
                # 通常のテキストログの場合
                logs.append({"message": line.strip(), "raw": True})
        
        return {
            "logs": logs,
            "total_lines": len(recent_lines),
            "file_path": str(log_file_path)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"システムログ取得エラー: {str(e)}"
        )

@router.get("/analytics/dashboard")
async def get_analytics_dashboard(
    days: int = Query(7, ge=1, le=90, description="分析期間（日数）"),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_admin_user)
):
    """分析ダッシュボードデータを取得"""
    
    try:
        from sqlalchemy import text
        
        start_date = datetime.now() - timedelta(days=days)
        
        # 基本メトリクス
        metrics_queries = {
            "total_users": "SELECT COUNT(*) FROM users WHERE created_at >= :start_date",
            "total_chats": "SELECT COUNT(*) FROM chats WHERE created_at >= :start_date",
            "total_messages": "SELECT COUNT(*) FROM chat_messages WHERE created_at >= :start_date",
            "total_templates": "SELECT COUNT(*) FROM prompt_templates WHERE created_at >= :start_date",
            "total_ai_requests": "SELECT COUNT(*) FROM audit_logs WHERE action = 'ai_request' AND timestamp >= :start_date"
        }
        
        metrics = {}
        for metric_name, query in metrics_queries.items():
            result = await db.execute(text(query), {"start_date": start_date})
            metrics[metric_name] = result.scalar() or 0
        
        # 日別アクティビティ
        daily_activity_query = text("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as activity_count
            FROM audit_logs 
            WHERE timestamp >= :start_date
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """)
        
        daily_result = await db.execute(daily_activity_query, {"start_date": start_date})
        daily_activity = [
            {"date": row[0].isoformat(), "count": row[1]}
            for row in daily_result.fetchall()
        ]
        
        # 人気のテンプレート
        popular_templates_query = text("""
            SELECT 
                pt.name,
                pt.usage_count,
                tc.name as category_name
            FROM prompt_templates pt
            LEFT JOIN template_categories tc ON pt.category_id = tc.id
            WHERE pt.status = 'active'
            ORDER BY pt.usage_count DESC
            LIMIT 10
        """)
        
        popular_result = await db.execute(popular_templates_query)
        popular_templates = [
            {
                "name": row[0],
                "usage_count": row[1],
                "category": row[2]
            }
            for row in popular_result.fetchall()
        ]
        
        return {
            "period_days": days,
            "metrics": metrics,
            "daily_activity": daily_activity,
            "popular_templates": popular_templates,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析ダッシュボードデータ取得エラー: {str(e)}"
        )