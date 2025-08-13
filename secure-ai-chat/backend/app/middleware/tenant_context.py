"""
テナントコンテキストミドルウェア - データ分離とセキュリティ強化
"""

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
import re
from typing import Optional

from app.core.database import get_db
from app.models.tenant import Tenant
from app.models.user import User

class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    テナントコンテキスト管理ミドルウェア
    - サブドメインまたはドメインからテナントを特定
    - リクエストにテナント情報を注入
    - テナント間のデータ分離を保証
    """
    
    def __init__(self, app):
        super().__init__(app)
        # テナント特定が不要なパス（パブリックAPI、ヘルスチェックなど）
        self.public_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/tenants/register",  # テナント登録は除外
            "/static",
            "/"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # パブリックパスの場合はスキップ
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        try:
            # テナント特定
            tenant = await self._identify_tenant(request)
            
            if tenant:
                # リクエストにテナント情報を注入
                request.state.tenant = tenant
                request.state.tenant_id = str(tenant.id)
                
                # テナントの状態チェック
                if not tenant.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="テナントが無効化されています"
                    )
                
                # サブスクリプション状態チェック
                if tenant.subscription_status in ["expired", "cancelled", "suspended"]:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail="サブスクリプションの更新が必要です"
                    )
            
            response = await call_next(request)
            
            # レスポンスにテナント情報ヘッダーを追加
            if tenant:
                response.headers["X-Tenant-ID"] = str(tenant.id)
                response.headers["X-Tenant-Name"] = tenant.name
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"テナント処理エラー: {str(e)}"
            )
    
    def _is_public_path(self, path: str) -> bool:
        """パブリックパス判定"""
        for public_path in self.public_paths:
            if path.startswith(public_path):
                return True
        return False
    
    async def _identify_tenant(self, request: Request) -> Optional[Tenant]:
        """テナント特定"""
        db = next(get_db())
        
        try:
            # 1. サブドメインから特定
            host = request.headers.get("host", "")
            if "." in host:
                subdomain = host.split(".")[0]
                if subdomain not in ["www", "api"]:
                    tenant = db.query(Tenant).filter(Tenant.subdomain == subdomain).first()
                    if tenant:
                        return tenant
            
            # 2. カスタムドメインから特定
            domain = host.replace("www.", "")
            tenant = db.query(Tenant).filter(Tenant.domain == domain).first()
            if tenant:
                return tenant
            
            # 3. ヘッダーから特定（開発・テスト用）
            tenant_id = request.headers.get("X-Tenant-ID")
            if tenant_id:
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                if tenant:
                    return tenant
            
            # 4. クエリパラメータから特定（開発・テスト用）
            tenant_id = request.query_params.get("tenant_id")
            if tenant_id:
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                if tenant:
                    return tenant
            
            return None
            
        finally:
            db.close()

class DataIsolationMixin:
    """
    データ分離を保証するミックスイン
    SQLAlchemy クエリに自動的にテナントフィルターを追加
    """
    
    @classmethod
    def filter_by_tenant(cls, query, tenant_id: str):
        """テナントフィルターを適用"""
        return query.filter(cls.tenant_id == tenant_id)
    
    @classmethod
    def get_tenant_data(cls, db: Session, tenant_id: str, **filters):
        """テナント限定データ取得"""
        query = db.query(cls).filter(cls.tenant_id == tenant_id)
        
        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.filter(getattr(cls, key) == value)
        
        return query
    
    def ensure_tenant_access(self, current_tenant_id: str) -> bool:
        """テナントアクセス権限確認"""
        return str(self.tenant_id) == str(current_tenant_id)

def get_current_tenant(request: Request) -> Tenant:
    """現在のテナント取得"""
    if not hasattr(request.state, "tenant") or request.state.tenant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="テナントコンテキストが見つかりません"
        )
    return request.state.tenant

def get_current_tenant_id(request: Request) -> str:
    """現在のテナントID取得"""
    tenant = get_current_tenant(request)
    return str(tenant.id)

def require_tenant_access(obj, request: Request):
    """テナントアクセス権限チェック"""
    if not hasattr(obj, 'tenant_id'):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="オブジェクトにテナントIDがありません"
        )
    
    current_tenant_id = get_current_tenant_id(request)
    if str(obj.tenant_id) != current_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このリソースにアクセスする権限がありません"
        )