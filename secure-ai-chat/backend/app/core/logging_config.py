"""
セキュアAIチャット - 統合ログ設定
"""

import logging
import logging.config
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import traceback

from app.core.config import settings

class JSONFormatter(logging.Formatter):
    """JSON形式のログフォーマッター"""
    
    def format(self, record: logging.LogRecord) -> str:
        # 基本情報
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 追加属性
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'ip_address'):
            log_entry["ip_address"] = record.ip_address
        if hasattr(record, 'session_id'):
            log_entry["session_id"] = record.session_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'event_type'):
            log_entry["event_type"] = record.event_type
        
        # エラー情報
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # スタックトレース
        if record.stack_info:
            log_entry["stack_info"] = record.stack_info
        
        return json.dumps(log_entry, ensure_ascii=False)

class SecurityLogFormatter(logging.Formatter):
    """セキュリティイベント専用フォーマッター"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "severity": self._get_security_severity(record.levelname),
            "event_type": getattr(record, 'event_type', 'unknown'),
            "user_id": getattr(record, 'user_id', None),
            "ip_address": getattr(record, 'ip_address', None),
            "user_agent": getattr(record, 'user_agent', None),
            "session_id": getattr(record, 'session_id', None),
            "request_id": getattr(record, 'request_id', None),
            "message": record.getMessage(),
            "details": getattr(record, 'details', {}),
            "success": getattr(record, 'success', True)
        }
        
        return json.dumps(log_entry, ensure_ascii=False)
    
    def _get_security_severity(self, level: str) -> str:
        """セキュリティイベントの重要度を判定"""
        mapping = {
            "DEBUG": "low",
            "INFO": "medium", 
            "WARNING": "high",
            "ERROR": "critical",
            "CRITICAL": "critical"
        }
        return mapping.get(level, "medium")

def setup_logging():
    """ログ設定の初期化"""
    
    # ログディレクトリの作成
    log_dir = Path(settings.PROJECT_ROOT) / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 設定辞書
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": JSONFormatter
            },
            "security": {
                "()": SecurityLogFormatter
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "standard",
                "stream": sys.stdout
            },
            "console_detailed": {
                "class": "logging.StreamHandler", 
                "level": "DEBUG",
                "formatter": "detailed",
                "stream": sys.stdout
            },
            "file_app": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "json",
                "filename": str(log_dir / "app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json", 
                "filename": str(log_dir / "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "file_security": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "security",
                "filename": str(log_dir / "security.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,  # セキュリティログは多めに保持
                "encoding": "utf-8"
            },
            "file_audit": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(log_dir / "audit.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 30,  # 監査ログは長期保持
                "encoding": "utf-8"
            }
        },
        "loggers": {
            # アプリケーションログ
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file_app", "file_error"],
                "propagate": False
            },
            # セキュリティログ
            "security": {
                "level": "INFO",
                "handlers": ["file_security", "console"],
                "propagate": False
            },
            # 監査ログ
            "audit": {
                "level": "INFO", 
                "handlers": ["file_audit"],
                "propagate": False
            },
            # データベースログ
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["file_app"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "WARNING" if settings.is_production else "INFO",
                "handlers": ["file_app"],
                "propagate": False
            },
            # FastAPIログ
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file_app"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["file_app"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file_app"],
                "propagate": False
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file_app"]
        }
    }
    
    # 開発環境では詳細ログを有効化
    if not settings.is_production:
        config["loggers"]["app"]["handlers"].append("console_detailed")
    
    # 設定を適用
    logging.config.dictConfig(config)
    
    # 初期化メッセージ
    logger = logging.getLogger("app.logging")
    logger.info(f"ログシステム初期化完了 - Level: {settings.LOG_LEVEL}, Environment: {settings.ENVIRONMENT}")

def get_logger(name: str) -> logging.Logger:
    """アプリケーション用ロガー取得"""
    return logging.getLogger(f"app.{name}")

def get_security_logger() -> logging.Logger:
    """セキュリティ用ロガー取得"""
    return logging.getLogger("security")

def get_audit_logger() -> logging.Logger:
    """監査用ロガー取得"""
    return logging.getLogger("audit")

class LogContext:
    """ログコンテキスト管理"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._context: Dict[str, Any] = {}
    
    def set_context(self, **kwargs):
        """コンテキスト情報設定"""
        self._context.update(kwargs)
        return self
    
    def info(self, message: str, **kwargs):
        """INFO レベルログ出力"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """WARNING レベルログ出力"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """ERROR レベルログ出力"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """CRITICAL レベルログ出力"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """ログ出力実行"""
        # コンテキスト情報とキーワード引数をマージ
        extra = {**self._context, **kwargs}
        self.logger.log(level, message, extra=extra)

def create_log_context(logger_name: str) -> LogContext:
    """ログコンテキスト作成"""
    logger = get_logger(logger_name)
    return LogContext(logger)

# セキュリティイベント専用ログ関数
def log_security_event(
    event_type: str,
    message: str,
    user_id: int = None,
    ip_address: str = None,
    user_agent: str = None,
    session_id: str = None,
    request_id: str = None,
    details: Dict[str, Any] = None,
    success: bool = True,
    level: str = "INFO"
):
    """セキュリティイベントログ出力"""
    security_logger = get_security_logger()
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    extra = {
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "session_id": session_id,
        "request_id": request_id,
        "details": details or {},
        "success": success
    }
    
    security_logger.log(log_level, message, extra=extra)

# 監査イベント専用ログ関数
def log_audit_event(
    action: str,
    resource_type: str,
    resource_id: str = None,
    user_id: int = None,
    changes: Dict[str, Any] = None,
    metadata: Dict[str, Any] = None
):
    """監査イベントログ出力"""
    audit_logger = get_audit_logger()
    
    extra = {
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "user_id": user_id,
        "changes": changes or {},
        "metadata": metadata or {}
    }
    
    audit_logger.info(f"監査イベント: {action} - {resource_type}", extra=extra)