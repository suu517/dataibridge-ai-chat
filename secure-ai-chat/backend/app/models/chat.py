"""
セキュアAIチャット - チャットモデル
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data

class ChatStatus(str, enum.Enum):
    """チャット状態"""
    ACTIVE = "active"      # アクティブ
    ARCHIVED = "archived"  # アーカイブ済み
    DELETED = "deleted"    # 削除済み

class MessageType(str, enum.Enum):
    """メッセージタイプ"""
    USER = "user"          # ユーザーメッセージ
    ASSISTANT = "assistant" # AIアシスタントメッセージ
    SYSTEM = "system"      # システムメッセージ
    TEMPLATE = "template"  # テンプレート使用メッセージ

class Chat(Base):
    """チャットセッションモデル"""
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    
    # 基本情報
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ChatStatus), default=ChatStatus.ACTIVE, nullable=False)
    
    # ユーザー関連
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 設定情報
    ai_model = Column(String(50), nullable=False, default="gpt-4")
    system_prompt = Column(Text, nullable=True)  # 暗号化される
    temperature = Column(String(10), nullable=False, default="0.7")
    max_tokens = Column(Integer, nullable=True)
    
    # メタデータ
    extra_metadata = Column(JSON, nullable=True)  # 追加情報をJSON形式で保存
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    
    # リレーションシップ
    user = relationship("User", back_populates="chats")
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    def __init__(self, **kwargs):
        # システムプロンプトの暗号化
        if 'system_prompt' in kwargs and kwargs['system_prompt']:
            kwargs['system_prompt'] = encrypt_sensitive_data(kwargs['system_prompt'])
        
        super().__init__(**kwargs)

    @property
    def decrypted_system_prompt(self) -> Optional[str]:
        """システムプロンプトの復号化"""
        if self.system_prompt:
            try:
                return decrypt_sensitive_data(self.system_prompt)
            except:
                return None
        return None

    @property
    def message_count(self) -> int:
        """メッセージ数"""
        return len(self.messages)

    @property
    def is_active(self) -> bool:
        """アクティブ状態チェック"""
        return self.status == ChatStatus.ACTIVE

    def archive(self):
        """チャットをアーカイブ"""
        self.status = ChatStatus.ARCHIVED
        self.updated_at = datetime.now(timezone.utc)

    def activate(self):
        """チャットをアクティブ化"""
        self.status = ChatStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def update_last_message_time(self):
        """最終メッセージ時刻を更新"""
        self.last_message_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f"<Chat(id={self.id}, title='{self.title}', user_id={self.user_id})>"

class ChatMessage(Base):
    """チャットメッセージモデル"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    
    # チャット関連
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    
    # メッセージ情報
    message_type = Column(Enum(MessageType), nullable=False)
    content = Column(Text, nullable=False)  # 暗号化される
    
    # AI関連情報
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=True)
    ai_model = Column(String(50), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # メタデータ
    extra_metadata = Column(JSON, nullable=True)  # 追加情報（API応答詳細など）
    
    # システム情報
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # リレーションシップ
    chat = relationship("Chat", back_populates="messages")
    template = relationship("PromptTemplate", foreign_keys=[prompt_template_id])

    def __init__(self, **kwargs):
        # メッセージ内容の暗号化
        if 'content' in kwargs and kwargs['content']:
            kwargs['content'] = encrypt_sensitive_data(kwargs['content'])
        
        super().__init__(**kwargs)

    @property
    def decrypted_content(self) -> Optional[str]:
        """メッセージ内容の復号化"""
        if self.content:
            try:
                return decrypt_sensitive_data(self.content)
            except:
                return None
        return None

    @property
    def is_user_message(self) -> bool:
        """ユーザーメッセージかどうか"""
        return self.message_type == MessageType.USER

    @property
    def is_assistant_message(self) -> bool:
        """AIアシスタントメッセージかどうか"""
        return self.message_type == MessageType.ASSISTANT

    @property
    def is_template_based(self) -> bool:
        """テンプレートベースメッセージかどうか"""
        return self.prompt_template_id is not None

    def soft_delete(self):
        """論理削除"""
        self.is_deleted = True
        self.updated_at = datetime.now(timezone.utc)

    def restore(self):
        """削除復元"""
        self.is_deleted = False
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, chat_id={self.chat_id}, type='{self.message_type.value}')>"