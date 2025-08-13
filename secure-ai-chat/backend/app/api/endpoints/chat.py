"""
チャット機能APIエンドポイント（修正版）
AI対話、履歴管理、リアルタイム通信
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from pydantic import BaseModel
from datetime import datetime
import logging

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.models.chat import Chat, ChatMessage, MessageType, ChatStatus
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic モデル
class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[int] = None
    template_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    message_id: int
    chat_id: int
    response: str
    timestamp: str
    processing_time: float
    tokens_used: Optional[int] = None

class ChatInfo(BaseModel):
    id: int
    title: str
    status: str
    created_at: str
    updated_at: str
    message_count: int
    last_message_at: Optional[str] = None

class ChatMessageInfo(BaseModel):
    id: int
    message_type: str
    content: str
    timestamp: str
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[int] = None

class ChatCreate(BaseModel):
    title: Optional[str] = None
    system_prompt: Optional[str] = None
    ai_model: Optional[str] = "gpt-4"
    temperature: Optional[float] = 0.7

class ChatUpdate(BaseModel):
    title: Optional[str] = None
    system_prompt: Optional[str] = None

# チャットエンドポイント
@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """チャットメッセージ送信"""
    
    start_time = datetime.utcnow()
    
    try:
        # チャット取得または作成
        if chat_request.chat_id:
            result = await db.execute(
                select(Chat).where(
                    and_(
                        Chat.id == chat_request.chat_id,
                        Chat.user_id == current_user.id
                    )
                )
            )
            chat = result.scalar_one_or_none()
            
            if not chat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="チャットが見つかりません"
                )
        else:
            # 新しいチャット作成
            chat_title = chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message
            chat = Chat(
                title=chat_title,
                user_id=current_user.id,
                ai_model="gpt-4",
                status=ChatStatus.ACTIVE
            )
            db.add(chat)
            await db.commit()
            await db.refresh(chat)
        
        # ユーザーメッセージ保存
        user_message = ChatMessage(
            chat_id=chat.id,
            message_type=MessageType.USER,
            content=chat_request.message
        )
        db.add(user_message)
        await db.commit()
        await db.refresh(user_message)
        
        # AI応答生成
        try:
            # チャット履歴取得
            history_result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.chat_id == chat.id)
                .order_by(ChatMessage.created_at)
                .limit(20)  # 直近20メッセージ
            )
            history_messages = history_result.scalars().all()
            
            # メッセージを OpenAI API形式に変換
            messages = []
            
            # システムプロンプトがあれば追加
            if chat.decrypted_system_prompt:
                messages.append({
                    "role": "system",
                    "content": chat.decrypted_system_prompt
                })
            
            # 履歴メッセージを追加（現在のメッセージは除く）
            for msg in history_messages[:-1]:  # 最後のメッセージ（現在のユーザーメッセージ）は除く
                role = "user" if msg.message_type == MessageType.USER else "assistant"
                content = msg.decrypted_content
                if content:
                    messages.append({"role": role, "content": content})
            
            # 現在のメッセージを追加
            messages.append({"role": "user", "content": chat_request.message})
            
            # テナント情報の確認
            if not current_user.tenant:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="テナント情報が見つかりません"
                )
            
            # レート制限チェック
            can_proceed, limit_message = await ai_service.check_rate_limit(
                current_user, current_user.tenant, db
            )
            if not can_proceed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=limit_message
                )
            
            # AI応答生成（テナント別API設定を使用）
            ai_response = await ai_service.generate_completion(
                messages=messages,
                tenant=current_user.tenant,  # テナント情報を追加
                model=chat.ai_model,
                temperature=float(chat.temperature) if chat.temperature else 0.7,
                max_tokens=chat.max_tokens,
                user_id=current_user.id,
                chat_id=chat.id,
                db=db
            )
            
            # AI応答保存
            ai_message = ChatMessage(
                chat_id=chat.id,
                message_type=MessageType.ASSISTANT,
                content=ai_response.get("content", "応答を生成できませんでした"),
                tokens_used=ai_response.get("tokens_used"),
                processing_time_ms=ai_response.get("processing_time_ms")
            )
            db.add(ai_message)
            
            # チャット更新時刻を更新
            chat.update_last_message_time()
            
            await db.commit()
            await db.refresh(ai_message)
            
            return ChatResponse(
                message_id=ai_message.id,
                chat_id=chat.id,
                response=ai_response.get("content", ""),
                timestamp=ai_message.created_at.isoformat(),
                processing_time=float(ai_response.get("processing_time_ms", 0)) / 1000,
                tokens_used=ai_response.get("tokens_used")
            )
            
        except Exception as e:
            logger.error(f"AI応答生成エラー: {str(e)}")
            
            # エラー応答保存
            processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            error_message = ChatMessage(
                chat_id=chat.id,
                message_type=MessageType.ASSISTANT,
                content=f"申し訳ございません。応答の生成中にエラーが発生しました。",
                processing_time_ms=processing_time_ms
            )
            db.add(error_message)
            await db.commit()
            await db.refresh(error_message)
            
            return ChatResponse(
                message_id=error_message.id,
                chat_id=chat.id,
                response=error_message.decrypted_content or "エラーが発生しました",
                timestamp=error_message.created_at.isoformat(),
                processing_time=float(processing_time_ms) / 1000
            )
    
    except Exception as e:
        logger.error(f"チャットメッセージ処理エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="メッセージの処理中にエラーが発生しました"
        )

@router.get("/chats", response_model=List[ChatInfo])
async def get_chats(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """チャット一覧取得"""
    
    # ユーザーのチャット取得
    result = await db.execute(
        select(Chat)
        .where(Chat.user_id == current_user.id)
        .order_by(desc(Chat.updated_at))
        .limit(limit)
        .offset(offset)
    )
    chats = result.scalars().all()
    
    # 各チャットの情報を取得
    chat_info_list = []
    for chat in chats:
        # メッセージ数取得
        message_count_result = await db.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.chat_id == chat.id)
        )
        message_count = message_count_result.scalar() or 0
        
        chat_info_list.append(ChatInfo(
            id=chat.id,
            title=chat.title,
            status=chat.status.value,
            created_at=chat.created_at.isoformat(),
            updated_at=chat.updated_at.isoformat(),
            message_count=message_count,
            last_message_at=chat.last_message_at.isoformat() if chat.last_message_at else None
        ))
    
    return chat_info_list

@router.get("/chats/{chat_id}/messages", response_model=List[ChatMessageInfo])
async def get_chat_messages(
    chat_id: int,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """チャットメッセージ履歴取得"""
    
    # チャット存在確認
    chat_result = await db.execute(
        select(Chat).where(
            and_(
                Chat.id == chat_id,
                Chat.user_id == current_user.id
            )
        )
    )
    chat = chat_result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="チャットが見つかりません"
        )
    
    # メッセージ履歴取得
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat.id)
        .order_by(ChatMessage.created_at)
        .limit(limit)
        .offset(offset)
    )
    messages = result.scalars().all()
    
    return [
        ChatMessageInfo(
            id=msg.id,
            message_type=msg.message_type.value,
            content=msg.decrypted_content or "",
            timestamp=msg.created_at.isoformat(),
            tokens_used=msg.tokens_used,
            processing_time_ms=msg.processing_time_ms
        )
        for msg in messages
    ]

@router.post("/chats", response_model=ChatInfo)
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """新しいチャット作成"""
    
    # 新しいチャット作成
    chat = Chat(
        title=chat_data.title or "新しいチャット",
        user_id=current_user.id,
        ai_model=chat_data.ai_model or "gpt-4",
        system_prompt=chat_data.system_prompt,
        temperature=str(chat_data.temperature) if chat_data.temperature else "0.7",
        status=ChatStatus.ACTIVE
    )
    
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    
    return ChatInfo(
        id=chat.id,
        title=chat.title,
        status=chat.status.value,
        created_at=chat.created_at.isoformat(),
        updated_at=chat.updated_at.isoformat(),
        message_count=0,
        last_message_at=None
    )

@router.put("/chats/{chat_id}", response_model=ChatInfo)
async def update_chat(
    chat_id: int,
    chat_update: ChatUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """チャット更新"""
    
    # チャット取得
    result = await db.execute(
        select(Chat).where(
            and_(
                Chat.id == chat_id,
                Chat.user_id == current_user.id
            )
        )
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="チャットが見つかりません"
        )
    
    # 更新
    if chat_update.title:
        chat.title = chat_update.title
    
    if chat_update.system_prompt is not None:
        chat.system_prompt = chat_update.system_prompt
    
    chat.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(chat)
    
    return ChatInfo(
        id=chat.id,
        title=chat.title,
        status=chat.status.value,
        created_at=chat.created_at.isoformat(),
        updated_at=chat.updated_at.isoformat(),
        message_count=0,  # 簡略化
        last_message_at=chat.last_message_at.isoformat() if chat.last_message_at else None
    )

@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """チャット削除"""
    
    # チャット取得
    result = await db.execute(
        select(Chat).where(
            and_(
                Chat.id == chat_id,
                Chat.user_id == current_user.id
            )
        )
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="チャットが見つかりません"
        )
    
    # アーカイブに変更（完全削除ではなく）
    chat.status = ChatStatus.DELETED
    chat.updated_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"チャット削除: {chat_id} by {current_user.username}")

@router.put("/chats/{chat_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """チャットアーカイブ"""
    
    # チャット取得
    result = await db.execute(
        select(Chat).where(
            and_(
                Chat.id == chat_id,
                Chat.user_id == current_user.id
            )
        )
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="チャットが見つかりません"
        )
    
    # アーカイブ
    chat.archive()
    
    await db.commit()
    
    logger.info(f"チャットアーカイブ: {chat_id} by {current_user.username}")