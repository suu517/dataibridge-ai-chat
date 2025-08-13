"""
セキュアAIチャット - メインアプリケーション
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import time
import logging

from app.core.config import settings, validate_settings
from app.core.database import create_tables
from app.api.endpoints import templates  # テンプレート機能を有効化
from app.api.endpoints import ai  # AI機能を有効化

# ログ設定
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # 起動時処理
    logger.info("🚀 セキュアAIチャットサービスを起動中...")
    
    try:
        # 設定検証
        if settings.is_production:
            validate_settings()
            logger.info("✅ 本番環境設定の検証完了")
        
        # データベーステーブル作成
        await create_tables()
        logger.info("✅ データベーステーブルの初期化完了")
        
        # AI サービス初期化テスト
        try:
            from app.services.ai_service import ai_service
            # 簡単な初期化テスト
            logger.info("✅ AI サービス初期化完了")
        except Exception as e:
            logger.warning(f"⚠️ AI サービス初期化エラー (続行): {e}")
        
        # その他の初期化処理
        logger.info("✅ アプリケーション初期化完了")
        
    except Exception as e:
        logger.error(f"❌ アプリケーション初期化エラー: {e}")
        raise
    
    yield  # アプリケーション実行
    
    # 終了時処理
    logger.info("🔄 セキュアAIチャットサービスを終了中...")

# FastAPIアプリケーション作成
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="企業専用のセキュアなAIチャットサービス",
    docs_url="/docs" if not settings.is_production else None,  # 本番環境では無効化
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan
)

# セキュリティミドルウェア
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"] if not settings.is_production else ["*.yourdomain.com"]
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# セッション管理
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=settings.SESSION_TIMEOUT_MINUTES * 60,
    same_site="strict",
    https_only=settings.is_production
)

# GZIP圧縮
app.add_middleware(GZipMiddleware, minimum_size=1000)

# テナントコンテキストミドルウェア（SaaS対応）
from app.middleware.tenant_context import TenantContextMiddleware
app.add_middleware(TenantContextMiddleware)

# カスタムミドルウェア
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """セキュリティヘッダーの追加"""
    response = await call_next(request)
    
    # セキュリティヘッダー
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # APIレスポンスヘッダー
    response.headers["X-API-Version"] = settings.APP_VERSION
    response.headers["X-Powered-By"] = "SecureAI-Chat"
    
    return response

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """リクエストログ記録"""
    start_time = time.time()
    
    # リクエスト情報
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    user_agent = request.headers.get("user-agent", "unknown")
    
    try:
        response = await call_next(request)
        
        # 処理時間計算
        process_time = time.time() - start_time
        
        # ログ記録
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.4f}s - "
            f"IP: {client_ip} - "
            f"UA: {user_agent[:100]}"
        )
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"{request.method} {request.url.path} - "
            f"Error: {str(e)} - "
            f"Time: {process_time:.4f}s - "
            f"IP: {client_ip}"
        )
        raise

# グローバル例外ハンドラー
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP例外ハンドラー"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": int(time.time())
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """一般例外ハンドラー"""
    logger.error(f"予期しないエラー: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "内部サーバーエラーが発生しました" if settings.is_production else str(exc),
            "status_code": 500,
            "timestamp": int(time.time())
        }
    )

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": int(time.time())
    }

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": f"🔐 {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs" if not settings.is_production else None,
        "status": "ready"
    }

# API ルーター
app.include_router(templates.router, prefix=f"{settings.API_V1_STR}/templates", tags=["テンプレート管理"])  # テンプレート機能を有効化
app.include_router(ai.router, prefix=f"{settings.API_V1_STR}/ai", tags=["AI統合"])  # AI機能を有効化

# 管理者API（実装完了）
# from app.api.endpoints import admin  # 管理者機能は後で有効化
# app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["管理・監査"])

# SaaS対応API（テナント・ユーザー・管理）
from app.api.routes.tenants import router as tenant_router
from app.api.routes.users import router as user_management_router
from app.api.routes.admin import router as admin_router
from app.api.routes.signup import router as signup_router
from app.api.routes.billing import router as billing_router
from app.api.routes.monitoring import router as monitoring_router
app.include_router(signup_router, prefix=f"{settings.API_V1_STR}", tags=["セルフサービス登録"])
app.include_router(tenant_router, prefix=f"{settings.API_V1_STR}", tags=["テナント管理"])
app.include_router(user_management_router, prefix=f"{settings.API_V1_STR}", tags=["ユーザー招待・管理"])
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}", tags=["管理ダッシュボード"])
app.include_router(billing_router, prefix=f"{settings.API_V1_STR}/billing", tags=["請求・決済管理"])
app.include_router(monitoring_router, prefix=f"{settings.API_V1_STR}/monitoring", tags=["システム監視"])

# メインAPIルーター（実装完了）
from app.api.endpoints import auth, users, chat, websocket
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["認証"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["ユーザー管理"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chats", tags=["チャット"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])

if __name__ == "__main__":
    import uvicorn
    
    # 開発サーバー起動
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production,
        log_level=settings.LOG_LEVEL.lower(),
        ssl_keyfile=settings.SSL_KEY_PATH if settings.is_production else None,
        ssl_certfile=settings.SSL_CERT_PATH if settings.is_production else None,
    )