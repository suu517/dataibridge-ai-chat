"""
テナント管理 API エンドポイント
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.core.database import get_db, get_async_db
from app.services.tenant_service import TenantService
from app.services.ai_service import ai_service
from app.models.subscription import PlanType
from app.models.tenant import Tenant
from app.models.user import User
from app.api.dependencies.auth import get_current_user
from app.schemas.tenant import (
    TenantCreate, 
    TenantResponse, 
    TenantStats,
    TenantUpdate
)

# AI設定用スキーマ
class AzureOpenAISettings(BaseModel):
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_version: str = "2024-02-01"
    deployment_name: str = "gpt-4"

class OpenAISettings(BaseModel):
    api_key: Optional[str] = None
    model: str = "gpt-4"

class AISettingsRequest(BaseModel):
    provider: str  # system_default, azure_openai, openai
    azure_settings: Optional[AzureOpenAISettings] = None
    openai_settings: Optional[OpenAISettings] = None

class AISettingsResponse(BaseModel):
    ai_provider: str
    use_system_default: bool
    azure_settings: Optional[Dict] = None
    openai_settings: Optional[Dict] = None

class UsageStatsResponse(BaseModel):
    daily_tokens: int
    monthly_tokens: int
    monthly_limit: int
    remaining_tokens: int

class ConnectionTestRequest(BaseModel):
    provider: str
    azure_settings: Optional[AzureOpenAISettings] = None
    openai_settings: Optional[OpenAISettings] = None

router = APIRouter(prefix="/tenants", tags=["テナント管理"])

@router.post("/register", response_model=Dict)
async def register_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db)
):
    """
    新規テナント登録
    - テナント、管理者ユーザー、サブスクリプションを一括作成
    """
    tenant_service = TenantService(db)
    
    result = tenant_service.create_tenant(
        name=tenant_data.name,
        domain=tenant_data.domain,
        subdomain=tenant_data.subdomain,
        admin_email=tenant_data.admin_email,
        admin_name=tenant_data.admin_name,
        admin_password=tenant_data.admin_password,
        plan_type=tenant_data.plan_type or PlanType.STARTER
    )
    
    if not result.get("success"):
        if "Domain already exists" in result.get("error", ""):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="指定されたドメインは既に使用されています"
            )
        elif "Subdomain already taken" in result.get("error", ""):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="指定されたサブドメインは既に使用されています"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"テナント作成に失敗しました: {result.get('error')}"
            )
    
    return {
        "success": True,
        "message": "テナントが正常に作成されました",
        "data": result
    }

@router.get("/{tenant_id}/stats", response_model=TenantStats)
async def get_tenant_stats(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """
    テナント統計情報取得
    """
    tenant_service = TenantService(db)
    stats = tenant_service.get_tenant_stats(tenant_id)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テナントが見つかりません"
        )
    
    return stats

@router.get("/domain/{domain}")
async def get_tenant_by_domain(
    domain: str,
    db: Session = Depends(get_db)
):
    """
    ドメインからテナント情報取得
    """
    tenant_service = TenantService(db)
    tenant = tenant_service.get_tenant_by_domain(domain)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたドメインのテナントが見つかりません"
        )
    
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "domain": tenant.domain,
        "subdomain": tenant.subdomain,
        "is_active": tenant.is_active,
        "subscription_status": tenant.subscription_status
    }

@router.get("/subdomain/{subdomain}")
async def get_tenant_by_subdomain(
    subdomain: str,
    db: Session = Depends(get_db)
):
    """
    サブドメインからテナント情報取得
    """
    tenant_service = TenantService(db)
    tenant = tenant_service.get_tenant_by_subdomain(subdomain)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたサブドメインのテナントが見つかりません"
        )
    
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "domain": tenant.domain,  
        "subdomain": tenant.subdomain,
        "is_active": tenant.is_active,
        "subscription_status": tenant.subscription_status
    }

@router.put("/{tenant_id}/settings")
async def update_tenant_settings(
    tenant_id: str,
    settings: Dict,
    db: Session = Depends(get_db)
):
    """
    テナント設定更新
    """
    tenant_service = TenantService(db)
    success = tenant_service.update_tenant_settings(tenant_id, settings)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テナントが見つかりません"
        )
    
    return {"success": True, "message": "設定が更新されました"}

@router.get("/", response_model=List[Dict])
async def list_tenants(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    テナント一覧取得（システム管理者用）
    """
    tenant_service = TenantService(db)
    tenants = tenant_service.list_tenants(limit=limit, offset=offset)
    
    return tenants

# AI設定管理エンドポイント

@router.get("/ai-settings", response_model=AISettingsResponse)
async def get_ai_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    現在のテナントのAI設定を取得
    """
    if not current_user.tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テナントが見つかりません"
        )
    
    tenant = current_user.tenant
    
    # Azure設定の安全な表示（APIキーをマスク）
    azure_settings = None
    if tenant.get_azure_openai_settings():
        settings = tenant.get_azure_openai_settings()
        azure_settings = {
            "endpoint": settings.get("endpoint"),
            "api_version": settings.get("api_version"),
            "deployment_name": settings.get("deployment_name"),
            "has_api_key": bool(settings.get("api_key"))
        }
    
    # OpenAI設定の安全な表示（APIキーをマスク）
    openai_settings = None
    if tenant.get_openai_settings():
        settings = tenant.get_openai_settings()
        openai_settings = {
            "model": settings.get("model"),
            "has_api_key": bool(settings.get("api_key"))
        }
    
    return AISettingsResponse(
        ai_provider=tenant.ai_provider,
        use_system_default=tenant.use_system_default,
        azure_settings=azure_settings,
        openai_settings=openai_settings
    )

@router.post("/ai-settings")
async def update_ai_settings(
    settings: AISettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    テナントのAI設定を更新
    """
    if not current_user.tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テナントが見つかりません"
        )
    
    # テナント管理者のみ許可
    if not current_user.is_tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作にはテナント管理者権限が必要です"
        )
    
    tenant = current_user.tenant
    
    try:
        if settings.provider == "system_default":
            tenant.use_default_ai_settings()
        
        elif settings.provider == "azure_openai":
            if not settings.azure_settings:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Azure OpenAI設定が必要です"
                )
            
            try:
                tenant.set_azure_openai_settings(
                    endpoint=settings.azure_settings.endpoint,
                    api_key=settings.azure_settings.api_key,
                    api_version=settings.azure_settings.api_version,
                    deployment_name=settings.azure_settings.deployment_name
                )
            except ValueError as ve:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Azure OpenAI設定エラー: {str(ve)}"
                )
        
        elif settings.provider == "openai":
            if not settings.openai_settings or not settings.openai_settings.api_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="OpenAI APIキーが必要です"
                )
            
            try:
                tenant.set_openai_settings(
                    api_key=settings.openai_settings.api_key,
                    model=settings.openai_settings.model
                )
            except ValueError as ve:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"OpenAI設定エラー: {str(ve)}"
                )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不正なプロバイダーです"
            )
        
        # データベースに保存
        db.commit()
        db.refresh(tenant)
        
        return {
            "success": True,
            "message": "AI設定が正常に更新されました"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"設定の更新に失敗しました: {str(e)}"
        )

@router.post("/test-ai-connection")
async def test_ai_connection(
    test_data: ConnectionTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    AI API接続をテスト
    """
    if not current_user.tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テナントが見つかりません"
        )
    
    try:
        # 一時的なテナントオブジェクトを作成してテスト
        temp_tenant = Tenant(
            id=current_user.tenant.id,
            name=current_user.tenant.name,
            ai_provider=test_data.provider,
            use_system_default=(test_data.provider == "system_default")
        )
        
        if test_data.provider == "azure_openai" and test_data.azure_settings:
            temp_tenant.set_azure_openai_settings(
                endpoint=test_data.azure_settings.endpoint,
                api_key=test_data.azure_settings.api_key,
                api_version=test_data.azure_settings.api_version,
                deployment_name=test_data.azure_settings.deployment_name
            )
        elif test_data.provider == "openai" and test_data.openai_settings:
            temp_tenant.set_openai_settings(
                api_key=test_data.openai_settings.api_key,
                model=test_data.openai_settings.model
            )
        
        # 接続テスト実行
        test_messages = [
            {"role": "user", "content": "こんにちは"}
        ]
        
        result = await ai_service.generate_completion(
            messages=test_messages,
            tenant=temp_tenant,
            user_id=current_user.id,
            db=db
        )
        
        return {
            "success": True,
            "message": "接続テストが成功しました",
            "response_preview": result.get("content", "")[:100] + "..." if len(result.get("content", "")) > 100 else result.get("content", "")
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"接続テストに失敗しました: {str(e)}"
        }

@router.get("/usage-stats", response_model=UsageStatsResponse)
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    テナントの使用量統計を取得
    """
    if not current_user.tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テナントが見つかりません"
        )
    
    tenant = current_user.tenant
    
    try:
        # 今日の使用量
        daily_tokens = await ai_service.count_tenant_tokens_today(db, str(tenant.id))
        
        # 過去30日間の使用量を取得
        monthly_tokens = await ai_service.count_tenant_tokens_monthly(db, str(tenant.id))
        
        # 月間制限
        monthly_limit = tenant.max_tokens_per_month
        
        # 残りトークン数
        remaining_tokens = max(0, monthly_limit - monthly_tokens)
        
        return UsageStatsResponse(
            daily_tokens=daily_tokens,
            monthly_tokens=monthly_tokens,
            monthly_limit=monthly_limit,
            remaining_tokens=remaining_tokens
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"使用量統計の取得に失敗しました: {str(e)}"
        )