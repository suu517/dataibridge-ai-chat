"""
セキュアAIチャット - プロンプトテンプレートモデル
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
import json
import uuid

from app.core.database import Base
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data
from app.models.tenant import TenantMixin

class TemplateStatus(str, enum.Enum):
    """テンプレート状態"""
    DRAFT = "draft"        # 下書き
    ACTIVE = "active"      # アクティブ
    INACTIVE = "inactive"  # 非アクティブ
    ARCHIVED = "archived"  # アーカイブ済み

class TemplateAccessLevel(str, enum.Enum):
    """テンプレートアクセスレベル"""
    PUBLIC = "public"      # 全員アクセス可
    DEPARTMENT = "department"  # 部署限定
    ROLE = "role"         # 役職限定
    PRIVATE = "private"   # 作成者のみ

class TemplateCategory(Base, TenantMixin):
    """プロンプトテンプレートカテゴリ"""
    __tablename__ = "template_categories"

    id = Column(Integer, primary_key=True, index=True)
    
    # 基本情報
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # アイコン名
    color = Column(String(20), nullable=True)  # カラーコード
    
    # 並び順
    sort_order = Column(Integer, default=0, nullable=False)
    
    # 状態
    is_active = Column(Boolean, default=True, nullable=False)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # リレーションシップ
    templates = relationship("PromptTemplate", back_populates="category")

    def __repr__(self):
        return f"<TemplateCategory(id={self.id}, name='{self.name}')>"

class PromptTemplate(Base, TenantMixin):
    """プロンプトテンプレートモデル"""
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    # 基本情報
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    template_content = Column(Text, nullable=False)  # 暗号化される
    
    # カテゴリ
    category_id = Column(Integer, ForeignKey("template_categories.id"), nullable=True)
    
    # 作成者情報
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # アクセス制御
    access_level = Column(Enum(TemplateAccessLevel), default=TemplateAccessLevel.PUBLIC, nullable=False)
    allowed_departments = Column(Text, nullable=True)  # カンマ区切り部署リスト
    allowed_roles = Column(Text, nullable=True)  # カンマ区切り役職リスト
    
    # パラメータ定義
    parameters = Column(JSON, nullable=True)  # テンプレートパラメータのJSON定義
    
    # AI設定
    default_model = Column(String(50), nullable=True, default="gpt-4")
    default_temperature = Column(String(10), nullable=True, default="0.7")
    default_max_tokens = Column(Integer, nullable=True)
    system_message = Column(Text, nullable=True)  # 暗号化される
    
    # 統計情報
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # 状態
    status = Column(Enum(TemplateStatus), default=TemplateStatus.DRAFT, nullable=False)
    version = Column(String(20), default="1.0", nullable=False)
    
    # 並び順・分類
    sort_order = Column(Integer, default=0, nullable=False)
    tags = Column(Text, nullable=True)  # カンマ区切りタグ
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # リレーションシップ
    category = relationship("TemplateCategory", back_populates="templates")
    creator = relationship("User", foreign_keys=[created_by])

    def __init__(self, **kwargs):
        # 機密情報の暗号化
        if 'template_content' in kwargs and kwargs['template_content']:
            kwargs['template_content'] = encrypt_sensitive_data(kwargs['template_content'])
        
        if 'system_message' in kwargs and kwargs['system_message']:
            kwargs['system_message'] = encrypt_sensitive_data(kwargs['system_message'])
        
        super().__init__(**kwargs)

    @property
    def decrypted_template_content(self) -> Optional[str]:
        """テンプレート内容の復号化"""
        if self.template_content:
            try:
                return decrypt_sensitive_data(self.template_content)
            except:
                return None
        return None

    @property
    def decrypted_system_message(self) -> Optional[str]:
        """システムメッセージの復号化"""
        if self.system_message:
            try:
                return decrypt_sensitive_data(self.system_message)
            except:
                return None
        return None

    @property
    def parameter_list(self) -> List[Dict]:
        """パラメータリストの取得"""
        if self.parameters:
            try:
                return json.loads(self.parameters) if isinstance(self.parameters, str) else self.parameters
            except:
                return []
        return []

    @property
    def tag_list(self) -> List[str]:
        """タグリストの取得"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    @property
    def allowed_department_list(self) -> List[str]:
        """許可部署リストの取得"""
        if self.allowed_departments:
            return [dept.strip() for dept in self.allowed_departments.split(',') if dept.strip()]
        return []

    @property
    def allowed_role_list(self) -> List[str]:
        """許可役職リストの取得"""
        if self.allowed_roles:
            return [role.strip() for role in self.allowed_roles.split(',') if role.strip()]
        return []

    @property
    def is_active(self) -> bool:
        """アクティブ状態チェック"""
        return self.status == TemplateStatus.ACTIVE

    @property
    def is_public(self) -> bool:
        """パブリックアクセスかどうか"""
        return self.access_level == TemplateAccessLevel.PUBLIC

    def can_access(self, user) -> bool:
        """ユーザーのアクセス権限チェック"""
        # 作成者は常にアクセス可能
        if self.created_by == user.id:
            return True
        
        # 管理者は全てアクセス可能
        if user.is_admin:
            return True
        
        # 非アクティブなテンプレートはアクセス不可
        if not self.is_active:
            return False
        
        # アクセスレベルによるチェック
        if self.access_level == TemplateAccessLevel.PUBLIC:
            return True
        
        if self.access_level == TemplateAccessLevel.DEPARTMENT:
            return user.department in self.allowed_department_list
        
        if self.access_level == TemplateAccessLevel.ROLE:
            return user.role.value in self.allowed_role_list
        
        if self.access_level == TemplateAccessLevel.PRIVATE:
            return False
        
        return False

    def render_template(self, parameters: Dict[str, str]) -> str:
        """テンプレートのレンダリング"""
        template_content = self.decrypted_template_content
        if not template_content:
            return ""
        
        # シンプルな置換（より高度なテンプレートエンジンも使用可能）
        rendered = template_content
        for key, value in parameters.items():
            placeholder = f"{{{key}}}"
            rendered = rendered.replace(placeholder, str(value))
        
        return rendered

    def increment_usage(self):
        """使用回数をインクリメント"""
        self.usage_count += 1
        self.last_used_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def activate(self):
        """テンプレートをアクティブ化"""
        self.status = TemplateStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self):
        """テンプレートを非アクティブ化"""
        self.status = TemplateStatus.INACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def archive(self):
        """テンプレートをアーカイブ"""
        self.status = TemplateStatus.ARCHIVED
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, name='{self.name}', status='{self.status.value}')>"