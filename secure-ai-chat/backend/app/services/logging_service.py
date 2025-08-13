"""
セキュアAIチャット - ログ管理・監査サービス
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc, text
from sqlalchemy.orm import selectinload
import structlog
import logging
import traceback

from app.models.audit import AuditLog, AuditAction, AuditLevel
from app.models.user import User
from app.core.config import settings

# 構造化ログの設定
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

class LoggingService:
    """ログ管理・監査サービス"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        
    async def get_audit_logs(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        action: Optional[AuditAction] = None,
        level: Optional[AuditLevel] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None,
        success_only: Optional[bool] = None,
        page: int = 1,
        limit: int = 50,
        sort_by: str = "timestamp",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """監査ログの取得（フィルタリング・ページング対応）"""
        
        # ベースクエリ
        query = select(AuditLog).options(
            selectinload(AuditLog.user)
        )
        
        # フィルタ条件の構築
        conditions = []
        
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
            
        if action:
            conditions.append(AuditLog.action == action)
            
        if level:
            conditions.append(AuditLog.level == level)
            
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
            
        if start_date:
            conditions.append(AuditLog.timestamp >= start_date)
            
        if end_date:
            conditions.append(AuditLog.timestamp <= end_date)
            
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    AuditLog.description.ilike(search_term),
                    AuditLog.username.ilike(search_term),
                    AuditLog.ip_address.ilike(search_term),
                    AuditLog.error_message.ilike(search_term)
                )
            )
            
        if success_only is not None:
            if success_only:
                conditions.append(AuditLog.success == "true")
            else:
                conditions.append(AuditLog.success != "true")
        
        # 条件を適用
        if conditions:
            query = query.where(and_(*conditions))
        
        # ソート
        sort_column = getattr(AuditLog, sort_by, AuditLog.timestamp)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        # カウント
        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()
        
        # ページング
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # レスポンス構築
        log_data = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username,
                "user_role": log.user_role,
                "action": log.action.value,
                "level": log.level.value,
                "description": log.description,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "endpoint": log.endpoint,
                "http_method": log.http_method,
                "details": log.details_dict,
                "success": log.is_success,
                "error_code": log.error_code,
                "error_message": log.error_message,
                "session_id": log.session_id,
                "correlation_id": log.correlation_id,
                "timestamp": log.timestamp.isoformat(),
                "is_security_related": log.is_security_related,
                "is_high_risk": log.is_high_risk,
                "user": {
                    "id": log.user.id,
                    "username": log.user.username,
                    "role": log.user.role.value
                } if log.user else None
            }
            log_data.append(log_dict)
        
        return {
            "logs": log_data,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
            "has_next": page * limit < total,
            "has_prev": page > 1
        }
    
    async def get_audit_log_statistics(
        self,
        db: AsyncSession,
        days: int = 7
    ) -> Dict[str, Any]:
        """監査ログ統計情報の取得"""
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # 基本統計
        total_query = select(func.count(AuditLog.id)).where(
            AuditLog.timestamp >= start_date
        )
        total_result = await db.execute(total_query)
        total_logs = total_result.scalar() or 0
        
        # 成功・失敗統計
        success_query = select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.success == "true"
            )
        )
        success_result = await db.execute(success_query)
        successful_logs = success_result.scalar() or 0
        
        failed_logs = total_logs - successful_logs
        
        # レベル別統計
        level_stats = {}
        for level in AuditLevel:
            level_query = select(func.count(AuditLog.id)).where(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.level == level
                )
            )
            level_result = await db.execute(level_query)
            level_stats[level.value] = level_result.scalar() or 0
        
        # アクション別統計
        action_query = select(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).where(
            AuditLog.timestamp >= start_date
        ).group_by(AuditLog.action).order_by(desc('count')).limit(10)
        
        action_result = await db.execute(action_query)
        action_stats = [
            {"action": row[0].value, "count": row[1]} 
            for row in action_result.fetchall()
        ]
        
        # セキュリティ関連ログ
        security_query = select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.timestamp >= start_date,
                or_(
                    AuditLog.action == AuditAction.LOGIN_FAILED,
                    AuditLog.action == AuditAction.UNAUTHORIZED_ACCESS,
                    AuditLog.action == AuditAction.SUSPICIOUS_ACTIVITY,
                    AuditLog.action == AuditAction.RATE_LIMIT_EXCEEDED
                )
            )
        )
        security_result = await db.execute(security_query)
        security_logs = security_result.scalar() or 0
        
        # 時間別分布（過去24時間）
        hourly_stats = await self._get_hourly_statistics(db, start_date)
        
        return {
            "period_days": days,
            "total_logs": total_logs,
            "successful_logs": successful_logs,
            "failed_logs": failed_logs,
            "success_rate": (successful_logs / total_logs * 100) if total_logs > 0 else 0,
            "security_related_logs": security_logs,
            "level_distribution": level_stats,
            "top_actions": action_stats,
            "hourly_distribution": hourly_stats
        }
    
    async def _get_hourly_statistics(
        self,
        db: AsyncSession,
        start_date: datetime
    ) -> List[Dict[str, Any]]:
        """時間別ログ統計の取得"""
        
        # 過去24時間の時間別統計
        hourly_query = text("""
            SELECT 
                DATE_TRUNC('hour', timestamp) as hour,
                COUNT(*) as total,
                COUNT(CASE WHEN success = 'true' THEN 1 END) as successful,
                COUNT(CASE WHEN success != 'true' THEN 1 END) as failed
            FROM audit_logs 
            WHERE timestamp >= :start_date
            GROUP BY hour
            ORDER BY hour DESC
            LIMIT 24
        """)
        
        result = await db.execute(hourly_query, {"start_date": start_date})
        rows = result.fetchall()
        
        return [
            {
                "hour": row[0].isoformat(),
                "total": row[1],
                "successful": row[2],
                "failed": row[3]
            }
            for row in rows
        ]
    
    async def get_user_activity_summary(
        self,
        db: AsyncSession,
        user_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """ユーザー活動サマリーの取得"""
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # 基本活動統計
        total_query = select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= start_date
            )
        )
        total_result = await db.execute(total_query)
        total_activities = total_result.scalar() or 0
        
        # 最終活動時刻
        last_activity_query = select(func.max(AuditLog.timestamp)).where(
            AuditLog.user_id == user_id
        )
        last_activity_result = await db.execute(last_activity_query)
        last_activity = last_activity_result.scalar()
        
        # アクション別統計
        action_query = select(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= start_date
            )
        ).group_by(AuditLog.action).order_by(desc('count'))
        
        action_result = await db.execute(action_query)
        action_breakdown = [
            {"action": row[0].value, "count": row[1]} 
            for row in action_result.fetchall()
        ]
        
        # セキュリティ関連活動
        security_query = select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= start_date,
                or_(
                    AuditLog.level == AuditLevel.HIGH,
                    AuditLog.level == AuditLevel.CRITICAL,
                    AuditLog.success != "true"
                )
            )
        )
        security_result = await db.execute(security_query)
        security_incidents = security_result.scalar() or 0
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_activities": total_activities,
            "last_activity": last_activity.isoformat() if last_activity else None,
            "action_breakdown": action_breakdown,
            "security_incidents": security_incidents,
            "average_daily_activities": total_activities / days if days > 0 else 0
        }
    
    async def detect_suspicious_activity(
        self,
        db: AsyncSession,
        user_id: int,
        time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """疑わしい活動の検出"""
        
        start_time = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
        
        # 高頻度アクセスチェック
        high_frequency_query = select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= start_time
            )
        )
        high_frequency_result = await db.execute(high_frequency_query)
        activity_count = high_frequency_result.scalar() or 0
        
        # 失敗ログイン試行チェック
        failed_login_query = select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.action == AuditAction.LOGIN_FAILED,
                AuditLog.timestamp >= start_time
            )
        )
        failed_login_result = await db.execute(failed_login_query)
        failed_logins = failed_login_result.scalar() or 0
        
        # 異常なIPアドレスチェック
        ip_query = select(
            AuditLog.ip_address,
            func.count(AuditLog.id).label('count')
        ).where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= start_time,
                AuditLog.ip_address.isnot(None)
            )
        ).group_by(AuditLog.ip_address)
        
        ip_result = await db.execute(ip_query)
        ip_addresses = [
            {"ip": row[0], "count": row[1]} 
            for row in ip_result.fetchall()
        ]
        
        # 疑わしい活動の判定
        alerts = []
        
        if activity_count > 100:  # 1時間で100回以上のアクセス
            alerts.append({
                "type": "high_frequency_access",
                "severity": "medium",
                "message": f"高頻度アクセス検出: {activity_count}回/{time_window_minutes}分",
                "value": activity_count
            })
        
        if failed_logins > 5:  # 1時間で5回以上のログイン失敗
            alerts.append({
                "type": "multiple_failed_logins",
                "severity": "high", 
                "message": f"複数回のログイン失敗: {failed_logins}回",
                "value": failed_logins
            })
        
        if len(ip_addresses) > 3:  # 1時間で3つ以上の異なるIPアドレス
            alerts.append({
                "type": "multiple_ip_addresses",
                "severity": "medium",
                "message": f"複数IPアドレスからのアクセス: {len(ip_addresses)}個",
                "value": len(ip_addresses),
                "details": ip_addresses
            })
        
        return {
            "user_id": user_id,
            "time_window_minutes": time_window_minutes,
            "activity_count": activity_count,
            "failed_login_count": failed_logins,
            "unique_ip_addresses": len(ip_addresses),
            "alerts": alerts,
            "risk_level": "high" if any(alert["severity"] == "high" for alert in alerts) else 
                         "medium" if any(alert["severity"] == "medium" for alert in alerts) else "low"
        }
    
    async def cleanup_old_logs(
        self,
        db: AsyncSession,
        retention_days: int = None
    ) -> Dict[str, int]:
        """古いログのクリーンアップ"""
        
        if retention_days is None:
            retention_days = settings.AUDIT_LOG_RETENTION_DAYS
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        # 削除対象のログ数を取得
        count_query = select(func.count(AuditLog.id)).where(
            AuditLog.timestamp < cutoff_date
        )
        count_result = await db.execute(count_query)
        logs_to_delete = count_result.scalar() or 0
        
        if logs_to_delete > 0:
            # 古いログを削除
            delete_query = text("""
                DELETE FROM audit_logs 
                WHERE timestamp < :cutoff_date
            """)
            await db.execute(delete_query, {"cutoff_date": cutoff_date})
            await db.commit()
            
            # 削除完了ログ
            self.logger.info(
                "audit_logs_cleanup_completed",
                deleted_count=logs_to_delete,
                retention_days=retention_days,
                cutoff_date=cutoff_date.isoformat()
            )
        
        return {
            "deleted_logs": logs_to_delete,
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    def log_system_event(
        self,
        event_type: str,
        message: str,
        level: str = "info",
        **kwargs
    ):
        """システムイベントのログ出力"""
        
        log_data = {
            "event_type": event_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs
        }
        
        if level == "error":
            self.logger.error(message, **log_data)
        elif level == "warning":
            self.logger.warning(message, **log_data)
        elif level == "debug":
            self.logger.debug(message, **log_data)
        else:
            self.logger.info(message, **log_data)
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "ms",
        **kwargs
    ):
        """パフォーマンスメトリクスのログ出力"""
        
        self.logger.info(
            "performance_metric",
            metric_name=metric_name,
            value=value,
            unit=unit,
            timestamp=datetime.now(timezone.utc).isoformat(),
            **kwargs
        )

async def log_security_event(
    db: AsyncSession,
    event_type: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    endpoint: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    session_id: Optional[str] = None,
    correlation_id: Optional[str] = None
):
    """セキュリティイベントの監査ログ記録"""
    
    # イベントタイプに基づくアクションとレベルのマッピング
    event_mapping = {
        "login_success": (AuditAction.LOGIN_SUCCESS, AuditLevel.LOW),
        "login_failed": (AuditAction.LOGIN_FAILED, AuditLevel.MEDIUM),
        "logout": (AuditAction.LOGOUT, AuditLevel.LOW),
        "user_register": (AuditAction.USER_CREATED, AuditLevel.LOW),
        "password_changed": (AuditAction.PASSWORD_CHANGED, AuditLevel.MEDIUM),
        "unauthorized_access": (AuditAction.UNAUTHORIZED_ACCESS, AuditLevel.HIGH),
        "suspicious_activity": (AuditAction.SUSPICIOUS_ACTIVITY, AuditLevel.HIGH),
        "rate_limit_exceeded": (AuditAction.RATE_LIMIT_EXCEEDED, AuditLevel.MEDIUM),
        "ai_request": (AuditAction.AI_REQUEST, AuditLevel.LOW),
        "ai_error": (AuditAction.AI_ERROR, AuditLevel.MEDIUM),
        "template_created": (AuditAction.TEMPLATE_CREATED, AuditLevel.LOW),
        "template_updated": (AuditAction.TEMPLATE_UPDATED, AuditLevel.LOW),
        "template_deleted": (AuditAction.TEMPLATE_DELETED, AuditLevel.MEDIUM),
        "data_access": (AuditAction.DATA_ACCESS, AuditLevel.LOW),
        "data_export": (AuditAction.DATA_EXPORT, AuditLevel.MEDIUM),
        "system_config_changed": (AuditAction.SYSTEM_CONFIG_CHANGED, AuditLevel.HIGH)
    }
    
    action, level = event_mapping.get(event_type, (AuditAction.UNKNOWN, AuditLevel.MEDIUM))
    
    # ユーザー情報の取得
    user = None
    username = None
    user_role = None
    
    if user_id:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            username = user.username
            user_role = user.role.value
    
    # 監査ログエントリの作成
    audit_log = AuditLog.create_log(
        action=action,
        description=f"Security event: {event_type}",
        user_id=user_id,
        username=username,
        user_role=user_role,
        level=level,
        ip_address=ip_address,
        user_agent=user_agent,
        endpoint=endpoint,
        success=success,
        error_message=error_message,
        details=details or {},
        session_id=session_id,
        correlation_id=correlation_id
    )
    
    db.add(audit_log)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        # ログ記録に失敗した場合は構造化ログに出力
        logging_service.log_system_event(
            event_type="audit_log_failed",
            message=f"Failed to record security event: {event_type}",
            level="error",
            user_id=user_id,
            error=str(e)
        )
        raise

# グローバルログサービスインスタンス
logging_service = LoggingService()