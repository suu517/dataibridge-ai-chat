"""
セキュアクエリサービス - テナント間データ分離保証
"""

from sqlalchemy.orm import Session, Query
from sqlalchemy import and_
from typing import Type, TypeVar, List, Optional, Dict, Any
from fastapi import HTTPException, status

from app.models.user import User
from app.models.template import PromptTemplate, TemplateCategory
from app.models.tenant import TenantMixin

T = TypeVar('T')

class SecureQueryService:
    """
    テナント間のデータ分離を保証するクエリサービス
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def query_tenant_data(self, model: Type[T]) -> Query:
        """
        テナント限定データクエリを作成
        """
        if not hasattr(model, 'tenant_id'):
            raise ValueError(f"モデル {model.__name__} にtenant_idフィールドがありません")
        
        return self.db.query(model).filter(model.tenant_id == self.tenant_id)
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """テナント内のユーザーを安全に取得"""
        return self.query_tenant_data(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """テナント内のユーザーをメールアドレスで取得"""
        return self.query_tenant_data(User).filter(User.email == email).first()
    
    def get_active_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """テナント内のアクティブユーザー一覧"""
        return self.query_tenant_data(User).filter(
            and_(User.is_active == True, User.status == "active")
        ).offset(offset).limit(limit).all()
    
    def get_user_templates(self, user_id: str, limit: int = 50, offset: int = 0) -> List[PromptTemplate]:
        """ユーザーがアクセス可能なテンプレート一覧"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        # テナント内のテンプレートのみを対象
        query = self.query_tenant_data(PromptTemplate).filter(
            PromptTemplate.status == "active"
        )
        
        # アクセス権限フィルタリング
        accessible_templates = []
        for template in query.offset(offset).limit(limit).all():
            if template.can_access(user):
                accessible_templates.append(template)
        
        return accessible_templates
    
    def get_template_by_id(self, template_id: int, user_id: str) -> Optional[PromptTemplate]:
        """ユーザーがアクセス可能なテンプレートを取得"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        template = self.query_tenant_data(PromptTemplate).filter(
            PromptTemplate.id == template_id
        ).first()
        
        if template and template.can_access(user):
            return template
        
        return None
    
    def get_template_categories(self) -> List[TemplateCategory]:
        """テナント内のテンプレートカテゴリ一覧"""
        return self.query_tenant_data(TemplateCategory).filter(
            TemplateCategory.is_active == True
        ).order_by(TemplateCategory.sort_order).all()
    
    def create_secure_record(self, model: Type[T], **kwargs) -> T:
        """
        テナントIDを自動付与してレコード作成
        """
        if not hasattr(model, 'tenant_id'):
            raise ValueError(f"モデル {model.__name__} にtenant_idフィールドがありません")
        
        kwargs['tenant_id'] = self.tenant_id
        
        record = model(**kwargs)
        self.db.add(record)
        self.db.flush()
        return record
    
    def update_secure_record(self, record: T, **kwargs) -> T:
        """
        テナント所有権を確認してレコード更新
        """
        if not hasattr(record, 'tenant_id'):
            raise ValueError("レコードにtenant_idフィールドがありません")
        
        if str(record.tenant_id) != str(self.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このリソースを更新する権限がありません"
            )
        
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        
        self.db.flush()
        return record
    
    def delete_secure_record(self, record: T) -> bool:
        """
        テナント所有権を確認してレコード削除
        """
        if not hasattr(record, 'tenant_id'):
            raise ValueError("レコードにtenant_idフィールドがありません")
        
        if str(record.tenant_id) != str(self.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このリソースを削除する権限がありません"
            )
        
        self.db.delete(record)
        self.db.flush()
        return True
    
    def count_tenant_records(self, model: Type[T], **filters) -> int:
        """テナント内のレコード数をカウント"""
        query = self.query_tenant_data(model)
        
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)
        
        return query.count()
    
    def search_tenant_records(
        self, 
        model: Type[T], 
        search_fields: List[str], 
        search_term: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[T]:
        """テナント内レコード検索"""
        query = self.query_tenant_data(model)
        
        if search_term:
            conditions = []
            for field in search_fields:
                if hasattr(model, field):
                    field_attr = getattr(model, field)
                    conditions.append(field_attr.ilike(f"%{search_term}%"))
            
            if conditions:
                from sqlalchemy import or_
                query = query.filter(or_(*conditions))
        
        return query.offset(offset).limit(limit).all()
    
    def validate_tenant_access(self, record: Any) -> bool:
        """レコードのテナントアクセス権限確認"""
        if not hasattr(record, 'tenant_id'):
            return False
        
        return str(record.tenant_id) == str(self.tenant_id)
    
    def get_tenant_statistics(self) -> Dict[str, Any]:
        """テナント統計情報"""
        stats = {
            "users": {
                "total": self.count_tenant_records(User),
                "active": self.count_tenant_records(User, is_active=True)
            },
            "templates": {
                "total": self.count_tenant_records(PromptTemplate),
                "active": self.count_tenant_records(PromptTemplate, status="active")
            },
            "categories": {
                "total": self.count_tenant_records(TemplateCategory),
                "active": self.count_tenant_records(TemplateCategory, is_active=True)
            }
        }
        
        return stats

def create_secure_query_service(db: Session, tenant_id: str) -> SecureQueryService:
    """セキュアクエリサービス作成"""
    return SecureQueryService(db, tenant_id)