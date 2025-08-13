"""
セキュアAIチャット - テンプレート管理API
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator

from app.core.database import get_database_session
from app.api.dependencies.auth import get_current_active_user, get_manager_user, log_audit
from app.models.user import User
from app.models.template import TemplateStatus, TemplateAccessLevel
from app.models.audit import AuditAction, AuditLevel
from app.services.template_service import TemplateService

router = APIRouter()

# Pydantic モデル
class TemplateParameterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    type: str = Field(..., pattern="^(text|textarea|number|select|boolean)$")
    label: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    required: bool = Field(default=True)
    default_value: Optional[Any] = None
    options: Optional[List[str]] = None
    validation: Optional[Dict[str, Any]] = None

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)
    sort_order: int = Field(default=0, ge=0)

class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    template_content: str = Field(..., min_length=1, max_length=10000)
    category_id: Optional[int] = Field(None, gt=0)
    access_level: TemplateAccessLevel = Field(default=TemplateAccessLevel.PUBLIC)
    allowed_departments: Optional[List[str]] = None
    allowed_roles: Optional[List[str]] = None
    parameters: Optional[List[TemplateParameterCreate]] = None
    default_model: Optional[str] = Field(None, max_length=50)
    default_temperature: Optional[str] = Field(None, pattern="^[0-2](\.[0-9])?$")
    default_max_tokens: Optional[int] = Field(None, gt=0, le=4000)
    system_message: Optional[str] = Field(None, max_length=5000)
    tags: Optional[List[str]] = None
    sort_order: int = Field(default=0, ge=0)

    @validator('tags')
    def validate_tags(cls, v):
        if v and len(v) > 10:
            raise ValueError('タグは最大10個まで設定できます')
        return v

class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    template_content: Optional[str] = Field(None, min_length=1, max_length=10000)
    category_id: Optional[int] = Field(None, gt=0)
    access_level: Optional[TemplateAccessLevel] = None
    allowed_departments: Optional[List[str]] = None
    allowed_roles: Optional[List[str]] = None
    parameters: Optional[List[TemplateParameterCreate]] = None
    default_model: Optional[str] = Field(None, max_length=50)
    default_temperature: Optional[str] = Field(None, pattern="^[0-2](\.[0-9])?$")
    default_max_tokens: Optional[int] = Field(None, gt=0, le=4000)
    system_message: Optional[str] = Field(None, max_length=5000)
    tags: Optional[List[str]] = None
    sort_order: Optional[int] = Field(None, ge=0)
    status: Optional[TemplateStatus] = None

class TemplateUse(BaseModel):
    parameters: Dict[str, Any] = Field(default_factory=dict)

class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    template_content: Optional[str]
    category_id: Optional[int]
    category: Optional[Dict[str, Any]]
    created_by: int
    creator: Optional[Dict[str, Any]]
    access_level: str
    allowed_departments: Optional[List[str]]
    allowed_roles: Optional[List[str]]
    parameters: Optional[List[Dict[str, Any]]]
    default_model: Optional[str]
    default_temperature: Optional[str]
    default_max_tokens: Optional[int]
    system_message: Optional[str]
    usage_count: int
    last_used_at: Optional[str]
    status: str
    version: str
    sort_order: int
    tags: Optional[List[str]]
    created_at: str
    updated_at: str
    can_edit: bool

# API エンドポイント

@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_categories(
    active_only: bool = Query(True, description="アクティブなカテゴリのみ取得"),
    db: AsyncSession = Depends(get_database_session)
):
    """テンプレートカテゴリ一覧を取得"""
    categories = await TemplateService.get_categories(db, active_only=active_only)
    return [
        {
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "icon": cat.icon,
            "color": cat.color,
            "sort_order": cat.sort_order,
            "is_active": cat.is_active,
            "created_at": cat.created_at.isoformat(),
            "updated_at": cat.updated_at.isoformat()
        }
        for cat in categories
    ]

@router.post("/categories", response_model=Dict[str, Any])
async def create_category(
    category_data: CategoryCreate,
    request: Request,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_manager_user)
):
    """テンプレートカテゴリを作成"""
    try:
        category = await TemplateService.create_category(
            db=db,
            name=category_data.name,
            description=category_data.description,
            icon=category_data.icon,
            color=category_data.color,
            sort_order=category_data.sort_order
        )
        
        # 監査ログ
        await log_audit(
            db=db,
            action=AuditAction.TEMPLATE_CREATE,
            description=f"テンプレートカテゴリ作成: {category.name}",
            user_id=current_user.id,
            username=current_user.username,
            user_role=current_user.role.value,
            level=AuditLevel.MEDIUM,
            resource_type="template_category",
            resource_id=str(category.id),
            ip_address=request.headers.get("X-Forwarded-For", request.client.host if request.client else None),
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "icon": category.icon,
            "color": category.color,
            "sort_order": category.sort_order,
            "is_active": category.is_active,
            "created_at": category.created_at.isoformat(),
            "updated_at": category.updated_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"カテゴリ作成エラー: {str(e)}"
        )

@router.get("/", response_model=Dict[str, Any])
async def get_templates(
    category_id: Optional[int] = Query(None, description="カテゴリID"),
    status_filter: Optional[TemplateStatus] = Query(None, alias="status", description="ステータス"),
    access_level: Optional[TemplateAccessLevel] = Query(None, description="アクセスレベル"),
    search: Optional[str] = Query(None, description="検索キーワード"),
    tags: Optional[str] = Query(None, description="タグ（カンマ区切り）"),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(50, ge=1, le=100, description="1ページあたりの件数"),
    sort_by: str = Query("updated_at", description="ソート項目"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="ソート順"),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_active_user)
):
    """テンプレート一覧を取得"""
    tag_list = tags.split(",") if tags else None
    
    result = await TemplateService.get_templates(
        db=db,
        user=current_user,
        category_id=category_id,
        status=status_filter,
        access_level=access_level,
        search=search,
        tags=tag_list,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return result

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_active_user)
):
    """特定のテンプレートを取得"""
    template = await TemplateService.get_template_by_id(db, template_id, current_user)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="テンプレートが見つかりません"
        )
    
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "template_content": template.decrypted_template_content if current_user.can_access_templates else None,
        "category_id": template.category_id,
        "category": {
            "id": template.category.id,
            "name": template.category.name,
            "icon": template.category.icon,
            "color": template.category.color
        } if template.category else None,
        "created_by": template.created_by,
        "creator": {
            "id": template.creator.id,
            "username": template.creator.username,
            "full_name": template.creator.decrypted_full_name
        } if template.creator else None,
        "access_level": template.access_level.value,
        "allowed_departments": template.allowed_department_list,
        "allowed_roles": template.allowed_role_list,
        "parameters": template.parameter_list,
        "default_model": template.default_model,
        "default_temperature": template.default_temperature,
        "default_max_tokens": template.default_max_tokens,
        "system_message": template.decrypted_system_message if current_user.can_access_templates else None,
        "usage_count": template.usage_count,
        "last_used_at": template.last_used_at.isoformat() if template.last_used_at else None,
        "status": template.status.value,
        "version": template.version,
        "sort_order": template.sort_order,
        "tags": template.tag_list,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat(),
        "can_edit": template.created_by == current_user.id or current_user.is_admin
    }

@router.post("/", response_model=Dict[str, Any])
async def create_template(
    template_data: TemplateCreate,
    request: Request,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_manager_user)
):
    """新しいテンプレートを作成"""
    try:
        # パラメータをディクショナリ形式に変換
        parameters_dict = [param.dict() for param in template_data.parameters] if template_data.parameters else None
        
        template = await TemplateService.create_template(
            db=db,
            user=current_user,
            name=template_data.name,
            description=template_data.description,
            template_content=template_data.template_content,
            category_id=template_data.category_id,
            access_level=template_data.access_level,
            allowed_departments=template_data.allowed_departments,
            allowed_roles=template_data.allowed_roles,
            parameters=parameters_dict,
            default_model=template_data.default_model,
            default_temperature=template_data.default_temperature,
            default_max_tokens=template_data.default_max_tokens,
            system_message=template_data.system_message,
            tags=template_data.tags,
            sort_order=template_data.sort_order
        )
        
        return {
            "id": template.id,
            "name": template.name,
            "message": "テンプレートが作成されました"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"テンプレート作成エラー: {str(e)}"
        )

@router.put("/{template_id}", response_model=Dict[str, Any])
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    request: Request,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_active_user)
):
    """テンプレートを更新"""
    try:
        # パラメータをディクショナリ形式に変換
        parameters_dict = [param.dict() for param in template_data.parameters] if template_data.parameters else None
        
        template = await TemplateService.update_template(
            db=db,
            template_id=template_id,
            user=current_user,
            name=template_data.name,
            description=template_data.description,
            template_content=template_data.template_content,
            category_id=template_data.category_id,
            access_level=template_data.access_level,
            allowed_departments=template_data.allowed_departments,
            allowed_roles=template_data.allowed_roles,
            parameters=parameters_dict,
            default_model=template_data.default_model,
            default_temperature=template_data.default_temperature,
            default_max_tokens=template_data.default_max_tokens,
            system_message=template_data.system_message,
            tags=template_data.tags,
            sort_order=template_data.sort_order,
            status=template_data.status
        )
        
        return {
            "id": template.id,
            "name": template.name,
            "message": "テンプレートが更新されました"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"テンプレート更新エラー: {str(e)}"
        )

@router.delete("/{template_id}", response_model=Dict[str, str])
async def delete_template(
    template_id: int,
    request: Request,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_active_user)
):
    """テンプレートを削除"""
    try:
        success = await TemplateService.delete_template(
            db=db,
            template_id=template_id,
            user=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="テンプレートが見つかりません"
            )
        
        return {"message": "テンプレートが削除されました"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"テンプレート削除エラー: {str(e)}"
        )

@router.post("/{template_id}/use", response_model=Dict[str, str])
async def use_template(
    template_id: int,
    use_data: TemplateUse,
    request: Request,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_active_user)
):
    """テンプレートを使用してプロンプトを生成"""
    try:
        rendered_prompt = await TemplateService.use_template(
            db=db,
            template_id=template_id,
            user=current_user,
            parameters=use_data.parameters
        )
        
        return {"rendered_prompt": rendered_prompt}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"テンプレート使用エラー: {str(e)}"
        )

@router.get("/popular/list", response_model=List[Dict[str, Any]])
async def get_popular_templates(
    limit: int = Query(10, ge=1, le=50, description="取得件数"),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_active_user)
):
    """人気のテンプレートを取得"""
    templates = await TemplateService.get_popular_templates(db, current_user, limit)
    
    return [
        {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": {
                "id": template.category.id,
                "name": template.category.name,
                "icon": template.category.icon,
                "color": template.category.color
            } if template.category else None,
            "usage_count": template.usage_count,
            "last_used_at": template.last_used_at.isoformat() if template.last_used_at else None,
            "tags": template.tag_list,
            "created_at": template.created_at.isoformat()
        }
        for template in templates
    ]

@router.get("/recent/list", response_model=List[Dict[str, Any]])
async def get_recent_templates(
    limit: int = Query(10, ge=1, le=50, description="取得件数"),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_active_user)
):
    """最近のテンプレートを取得"""
    templates = await TemplateService.get_recent_templates(db, current_user, limit)
    
    return [
        {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": {
                "id": template.category.id,
                "name": template.category.name,
                "icon": template.category.icon,
                "color": template.category.color
            } if template.category else None,
            "usage_count": template.usage_count,
            "tags": template.tag_list,
            "created_at": template.created_at.isoformat()
        }
        for template in templates
    ]