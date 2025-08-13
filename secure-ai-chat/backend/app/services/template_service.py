"""
セキュアAIチャット - プロンプトテンプレートサービス
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload

from app.models.template import PromptTemplate, TemplateCategory, TemplateStatus, TemplateAccessLevel
from app.models.user import User
from app.models.audit import AuditLog, AuditAction, AuditLevel
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data

class TemplateService:
    """プロンプトテンプレート管理サービス"""

    @staticmethod
    async def get_categories(
        db: AsyncSession,
        active_only: bool = True
    ) -> List[TemplateCategory]:
        """カテゴリ一覧を取得"""
        query = select(TemplateCategory)
        
        if active_only:
            query = query.where(TemplateCategory.is_active == True)
        
        query = query.order_by(TemplateCategory.sort_order, TemplateCategory.name)
        
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_category(
        db: AsyncSession,
        name: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        sort_order: int = 0
    ) -> TemplateCategory:
        """カテゴリを作成"""
        category = TemplateCategory(
            name=name,
            description=description,
            icon=icon,
            color=color,
            sort_order=sort_order
        )
        
        db.add(category)
        await db.commit()
        await db.refresh(category)
        
        return category

    @staticmethod
    async def get_templates(
        db: AsyncSession,
        user: User,
        category_id: Optional[int] = None,
        status: Optional[TemplateStatus] = None,
        access_level: Optional[TemplateAccessLevel] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 50,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """テンプレート一覧を取得（ページング対応）"""
        
        # ベースクエリ
        query = select(PromptTemplate).options(
            selectinload(PromptTemplate.category),
            selectinload(PromptTemplate.creator)
        )
        
        # アクセス権限フィルタ
        if not user.is_admin:
            access_conditions = [
                PromptTemplate.access_level == TemplateAccessLevel.PUBLIC,
                PromptTemplate.created_by == user.id
            ]
            
            if user.department:
                access_conditions.append(
                    and_(
                        PromptTemplate.access_level == TemplateAccessLevel.DEPARTMENT,
                        PromptTemplate.allowed_departments.contains(user.department)
                    )
                )
            
            access_conditions.append(
                and_(
                    PromptTemplate.access_level == TemplateAccessLevel.ROLE,
                    PromptTemplate.allowed_roles.contains(user.role.value)
                )
            )
            
            query = query.where(or_(*access_conditions))
        
        # フィルタ条件
        if category_id:
            query = query.where(PromptTemplate.category_id == category_id)
        
        if status:
            query = query.where(PromptTemplate.status == status)
        elif not user.is_admin:
            # 一般ユーザーはアクティブなテンプレートのみ表示
            query = query.where(PromptTemplate.status == TemplateStatus.ACTIVE)
        
        if access_level:
            query = query.where(PromptTemplate.access_level == access_level)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    PromptTemplate.name.ilike(search_term),
                    PromptTemplate.description.ilike(search_term),
                    PromptTemplate.tags.ilike(search_term)
                )
            )
        
        if tags:
            for tag in tags:
                query = query.where(PromptTemplate.tags.contains(tag))
        
        # ソート
        sort_column = getattr(PromptTemplate, sort_by, PromptTemplate.updated_at)
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
        templates = result.scalars().all()
        
        # 復号化（必要な場合）
        decrypted_templates = []
        for template in templates:
            template_dict = {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "template_content": template.decrypted_template_content if user.can_access_templates else None,
                "category_id": template.category_id,
                "category": template.category,
                "created_by": template.created_by,
                "creator": template.creator,
                "access_level": template.access_level,
                "allowed_departments": template.allowed_department_list,
                "allowed_roles": template.allowed_role_list,
                "parameters": template.parameter_list,
                "default_model": template.default_model,
                "default_temperature": template.default_temperature,
                "default_max_tokens": template.default_max_tokens,
                "system_message": template.decrypted_system_message if user.can_access_templates else None,
                "usage_count": template.usage_count,
                "last_used_at": template.last_used_at,
                "status": template.status,
                "version": template.version,
                "sort_order": template.sort_order,
                "tags": template.tag_list,
                "created_at": template.created_at,
                "updated_at": template.updated_at,
                "can_edit": template.created_by == user.id or user.is_admin
            }
            decrypted_templates.append(template_dict)
        
        return {
            "templates": decrypted_templates,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
            "has_next": page * limit < total,
            "has_prev": page > 1
        }

    @staticmethod
    async def get_template_by_id(
        db: AsyncSession,
        template_id: int,
        user: User
    ) -> Optional[PromptTemplate]:
        """IDでテンプレートを取得"""
        query = select(PromptTemplate).options(
            selectinload(PromptTemplate.category),
            selectinload(PromptTemplate.creator)
        ).where(PromptTemplate.id == template_id)
        
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            return None
        
        # アクセス権限チェック
        if not template.can_access(user):
            return None
        
        return template

    @staticmethod
    async def create_template(
        db: AsyncSession,
        user: User,
        name: str,
        description: Optional[str],
        template_content: str,
        category_id: Optional[int] = None,
        access_level: TemplateAccessLevel = TemplateAccessLevel.PUBLIC,
        allowed_departments: Optional[List[str]] = None,
        allowed_roles: Optional[List[str]] = None,
        parameters: Optional[List[Dict]] = None,
        default_model: Optional[str] = None,
        default_temperature: Optional[str] = None,
        default_max_tokens: Optional[int] = None,
        system_message: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_order: int = 0
    ) -> PromptTemplate:
        """テンプレートを作成"""
        
        # 権限チェック
        if not user.can_access_templates:
            raise ValueError("テンプレート作成権限がありません")
        
        template = PromptTemplate(
            name=name,
            description=description,
            template_content=encrypt_sensitive_data(template_content),
            category_id=category_id,
            created_by=user.id,
            access_level=access_level,
            allowed_departments=",".join(allowed_departments) if allowed_departments else None,
            allowed_roles=",".join(allowed_roles) if allowed_roles else None,
            parameters=parameters,
            default_model=default_model,
            default_temperature=default_temperature,
            default_max_tokens=default_max_tokens,
            system_message=encrypt_sensitive_data(system_message) if system_message else None,
            sort_order=sort_order,
            tags=",".join(tags) if tags else None
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        # 監査ログ
        audit_log = AuditLog.create_log(
            action=AuditAction.TEMPLATE_CREATE,
            description=f"プロンプトテンプレート作成: {name}",
            user_id=user.id,
            username=user.username,
            user_role=user.role.value,
            level=AuditLevel.MEDIUM,
            resource_type="template",
            resource_id=str(template.id),
            details={"template_name": name, "access_level": access_level.value}
        )
        db.add(audit_log)
        await db.commit()
        
        return template

    @staticmethod
    async def update_template(
        db: AsyncSession,
        template_id: int,
        user: User,
        name: Optional[str] = None,
        description: Optional[str] = None,
        template_content: Optional[str] = None,
        category_id: Optional[int] = None,
        access_level: Optional[TemplateAccessLevel] = None,
        allowed_departments: Optional[List[str]] = None,
        allowed_roles: Optional[List[str]] = None,
        parameters: Optional[List[Dict]] = None,
        default_model: Optional[str] = None,
        default_temperature: Optional[str] = None,
        default_max_tokens: Optional[int] = None,
        system_message: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_order: Optional[int] = None,
        status: Optional[TemplateStatus] = None
    ) -> PromptTemplate:
        """テンプレートを更新"""
        
        template = await TemplateService.get_template_by_id(db, template_id, user)
        if not template:
            raise ValueError("テンプレートが見つかりません")
        
        # 編集権限チェック
        if template.created_by != user.id and not user.is_admin:
            raise ValueError("テンプレート編集権限がありません")
        
        # 更新
        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if template_content is not None:
            template.template_content = encrypt_sensitive_data(template_content)
        if category_id is not None:
            template.category_id = category_id
        if access_level is not None:
            template.access_level = access_level
        if allowed_departments is not None:
            template.allowed_departments = ",".join(allowed_departments) if allowed_departments else None
        if allowed_roles is not None:
            template.allowed_roles = ",".join(allowed_roles) if allowed_roles else None
        if parameters is not None:
            template.parameters = parameters
        if default_model is not None:
            template.default_model = default_model
        if default_temperature is not None:
            template.default_temperature = default_temperature
        if default_max_tokens is not None:
            template.default_max_tokens = default_max_tokens
        if system_message is not None:
            template.system_message = encrypt_sensitive_data(system_message) if system_message else None
        if tags is not None:
            template.tags = ",".join(tags) if tags else None
        if sort_order is not None:
            template.sort_order = sort_order
        if status is not None:
            template.status = status
        
        await db.commit()
        await db.refresh(template)
        
        # 監査ログ
        audit_log = AuditLog.create_log(
            action=AuditAction.TEMPLATE_UPDATE,
            description=f"プロンプトテンプレート更新: {template.name}",
            user_id=user.id,
            username=user.username,
            user_role=user.role.value,
            level=AuditLevel.MEDIUM,
            resource_type="template",
            resource_id=str(template.id)
        )
        db.add(audit_log)
        await db.commit()
        
        return template

    @staticmethod
    async def delete_template(
        db: AsyncSession,
        template_id: int,
        user: User
    ) -> bool:
        """テンプレートを削除"""
        
        template = await TemplateService.get_template_by_id(db, template_id, user)
        if not template:
            return False
        
        # 削除権限チェック
        if template.created_by != user.id and not user.is_admin:
            raise ValueError("テンプレート削除権限がありません")
        
        template_name = template.name
        
        await db.delete(template)
        await db.commit()
        
        # 監査ログ
        audit_log = AuditLog.create_log(
            action=AuditAction.TEMPLATE_DELETE,
            description=f"プロンプトテンプレート削除: {template_name}",
            user_id=user.id,
            username=user.username,
            user_role=user.role.value,
            level=AuditLevel.HIGH,
            resource_type="template",
            resource_id=str(template_id)
        )
        db.add(audit_log)
        await db.commit()
        
        return True

    @staticmethod
    async def use_template(
        db: AsyncSession,
        template_id: int,
        user: User,
        parameters: Dict[str, Any]
    ) -> str:
        """テンプレートを使用してプロンプトを生成"""
        
        template = await TemplateService.get_template_by_id(db, template_id, user)
        if not template:
            raise ValueError("テンプレートが見つかりません")
        
        if not template.is_active:
            raise ValueError("このテンプレートは使用できません")
        
        # 使用回数をインクリメント
        template.increment_usage()
        await db.commit()
        
        # プロンプトをレンダリング
        rendered_prompt = template.render_template(parameters)
        
        # 監査ログ
        audit_log = AuditLog.create_log(
            action=AuditAction.TEMPLATE_USE,
            description=f"プロンプトテンプレート使用: {template.name}",
            user_id=user.id,
            username=user.username,
            user_role=user.role.value,
            level=AuditLevel.LOW,
            resource_type="template",
            resource_id=str(template.id)
        )
        db.add(audit_log)
        await db.commit()
        
        return rendered_prompt

    @staticmethod
    async def get_popular_templates(
        db: AsyncSession,
        user: User,
        limit: int = 10
    ) -> List[PromptTemplate]:
        """人気のテンプレートを取得"""
        
        query = select(PromptTemplate).options(
            selectinload(PromptTemplate.category)
        ).where(
            PromptTemplate.status == TemplateStatus.ACTIVE
        ).order_by(desc(PromptTemplate.usage_count)).limit(limit)
        
        # アクセス権限フィルタ
        if not user.is_admin:
            access_conditions = [
                PromptTemplate.access_level == TemplateAccessLevel.PUBLIC,
                PromptTemplate.created_by == user.id
            ]
            
            if user.department:
                access_conditions.append(
                    and_(
                        PromptTemplate.access_level == TemplateAccessLevel.DEPARTMENT,
                        PromptTemplate.allowed_departments.contains(user.department)
                    )
                )
            
            access_conditions.append(
                and_(
                    PromptTemplate.access_level == TemplateAccessLevel.ROLE,
                    PromptTemplate.allowed_roles.contains(user.role.value)
                )
            )
            
            query = query.where(or_(*access_conditions))
        
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_recent_templates(
        db: AsyncSession,
        user: User,
        limit: int = 10
    ) -> List[PromptTemplate]:
        """最近のテンプレートを取得"""
        
        query = select(PromptTemplate).options(
            selectinload(PromptTemplate.category)
        ).where(
            PromptTemplate.status == TemplateStatus.ACTIVE
        ).order_by(desc(PromptTemplate.created_at)).limit(limit)
        
        # アクセス権限フィルタ
        if not user.is_admin:
            access_conditions = [
                PromptTemplate.access_level == TemplateAccessLevel.PUBLIC,
                PromptTemplate.created_by == user.id
            ]
            
            if user.department:
                access_conditions.append(
                    and_(
                        PromptTemplate.access_level == TemplateAccessLevel.DEPARTMENT,
                        PromptTemplate.allowed_departments.contains(user.department)
                    )
                )
            
            access_conditions.append(
                and_(
                    PromptTemplate.access_level == TemplateAccessLevel.ROLE,
                    PromptTemplate.allowed_roles.contains(user.role.value)
                )
            )
            
            query = query.where(or_(*access_conditions))
        
        result = await db.execute(query)
        return result.scalars().all()