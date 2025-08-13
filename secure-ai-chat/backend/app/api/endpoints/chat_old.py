"""
チャット機能APIエンドポイント
AI対話、履歴管理、リアルタイム通信
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import logging

from app.core.database import get_db
from app.api.endpoints.auth import get_current_active_user, get_current_user
from app.models.user import User
from app.models.chat import Chat, ChatMessage
from app.services.ai_service import ai_service
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()

# WebSocket接続管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(json.dumps(message))

manager = ConnectionManager()

# Pydantic モデル
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    template_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    message_id: int
    session_id: str
    response: str
    timestamp: str
    processing_time: float
    token_usage: Optional[Dict[str, int]] = None

class ChatSessionInfo(BaseModel):
    id: int
    session_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    last_message: Optional[str]

class ChatMessageInfo(BaseModel):
    id: int
    message_type: str  # 'user' | 'assistant'
    content: str
    timestamp: str
    token_usage: Optional[Dict[str, int]]
    processing_time: Optional[float]

class SessionCreate(BaseModel):
    title: Optional[str] = None
    template_id: Optional[int] = None

class SessionUpdate(BaseModel):
    title: str

# チャットエンドポイント
@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """チャットメッセージ送信"""
    
    start_time = datetime.utcnow()
    
    try:
        # チャット取得または作成
        if chat_request.session_id:
            try:
                chat_id = int(chat_request.session_id)
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
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="無効なセッションIDです"
                )
        else:
            # 新しいチャット作成
            chat = Chat(
                title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message,
                user_id=current_user.id,
                ai_model="gpt-4"
            )
            db.add(chat)
            await db.commit()
            await db.refresh(chat)
        
        # ユーザーメッセージ保存
        from app.models.chat import MessageType
        user_message = ChatMessage(
            chat_id=chat.id,
            message_type=MessageType.USER,
            content=chat_request.message
        )
        db.add(user_message)
        
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
            
            # 履歴メッセージを追加
            for msg in history_messages:
                role = "user" if msg.message_type == MessageType.USER else "assistant"
                content = msg.decrypted_content
                if content:
                    messages.append({"role": role, "content": content})
            
            # 現在のメッセージを追加
            messages.append({"role": "user", "content": chat_request.message})
            
            # AI応答生成
            ai_response = await ai_service.generate_completion(
                messages=messages,
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
            
            # WebSocket通信（リアルタイム通知）
            await manager.send_personal_message({
                "type": "chat_response",
                "session_id": str(chat.id),
                "message": ai_response.get("content"),
                "timestamp": ai_message.created_at.isoformat()
            }, current_user.id)
            
            return ChatResponse(
                message_id=ai_message.id,
                session_id=str(chat.id),
                response=ai_response.get("content"),
                timestamp=ai_message.created_at.isoformat(),
                processing_time=float(ai_message.processing_time_ms) / 1000 if ai_message.processing_time_ms else 0.0,
                token_usage={"total_tokens": ai_message.tokens_used} if ai_message.tokens_used else None
            )
            
        except Exception as e:
            logger.error(f"AI応答生成エラー: {str(e)}")
            
            # エラー応答保存
            processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            error_message = ChatMessage(
                chat_id=chat.id,
                message_type=MessageType.ASSISTANT,
                content=f"申し訳ございません。応答の生成中にエラーが発生しました: {str(e)}",
                processing_time_ms=processing_time_ms
            )
            db.add(error_message)
            await db.commit()
            await db.refresh(error_message)
            
            return ChatResponse(
                message_id=error_message.id,
                session_id=str(chat.id),
                response=error_message.decrypted_content,
                timestamp=error_message.created_at.isoformat(),
                processing_time=float(processing_time_ms) / 1000
            )
    
    except Exception as e:
        logger.error(f"チャットメッセージ処理エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="メッセージの処理中にエラーが発生しました"
        )

@router.get("/sessions", response_model=List[ChatSessionInfo])
async def get_chat_sessions(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """チャットセッション一覧取得"""
    
    # ユーザーのセッション取得
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(desc(ChatSession.updated_at))
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().all()
    
    # 各セッションの情報を取得
    session_info_list = []
    for session in sessions:
        # メッセージ数取得
        message_count_result = await db.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session.id)
        )
        message_count = message_count_result.scalar() or 0
        
        # 最後のメッセージ取得
        last_message_result = await db.execute(
            select(ChatMessage.content)
            .where(ChatMessage.session_id == session.id)
            .order_by(desc(ChatMessage.timestamp))
            .limit(1)
        )
        last_message = last_message_result.scalar_one_or_none()
        
        session_info_list.append(ChatSessionInfo(
            id=session.id,
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            message_count=message_count,
            last_message=last_message[:100] + "..." if last_message and len(last_message) > 100 else last_message
        ))
    
    return session_info_list

@router.get("/sessions/{session_id}", response_model=List[ChatMessageInfo])
async def get_chat_history(
    session_id: str,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """チャット履歴取得"""
    
    # セッション存在確認
    session_result = await db.execute(
        select(ChatSession).where(
            and_(
                ChatSession.session_id == session_id,
                ChatSession.user_id == current_user.id
            )
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="チャットセッションが見つかりません"
        )
    
    # メッセージ履歴取得
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.timestamp)
        .limit(limit)
        .offset(offset)
    )
    messages = result.scalars().all()
    
    return [
        ChatMessageInfo(
            id=msg.id,
            message_type=msg.message_type,
            content=msg.content,
            timestamp=msg.timestamp.isoformat(),
            token_usage=msg.token_usage,
            processing_time=msg.processing_time
        )
        for msg in messages
    ]

@router.post("/sessions", response_model=ChatSessionInfo)
async def create_chat_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """新しいチャットセッション作成"""
    
    # 新しいセッション作成
    session = ChatSession(
        session_id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=session_data.title or "新しいチャット",
        template_id=session_data.template_id
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return ChatSessionInfo(
        id=session.id,
        session_id=session.session_id,
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        message_count=0,
        last_message=None
    )

@router.put("/sessions/{session_id}", response_model=ChatSessionInfo)
async def update_chat_session(
    session_id: str,
    session_update: SessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """チャットセッション更新"""
    
    # セッション取得
    result = await db.execute(
        select(ChatSession).where(
            and_(
                ChatSession.session_id == session_id,
                ChatSession.user_id == current_user.id
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="チャットセッションが見つかりません"
        )
    
    # タイトル更新
    session.title = session_update.title
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(session)
    
    return ChatSessionInfo(
        id=session.id,
        session_id=session.session_id,
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        message_count=0,  # 簡略化
        last_message=None  # 簡略化
    )

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """チャットセッション削除"""
    
    # セッション取得
    result = await db.execute(
        select(ChatSession).where(
            and_(
                ChatSession.session_id == session_id,
                ChatSession.user_id == current_user.id
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="チャットセッションが見つかりません"
        )
    
    # 関連メッセージ削除（カスケード削除）
    await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id)
    )
    
    # セッション削除
    await db.delete(session)
    await db.commit()
    
    logger.info(f"チャットセッション削除: {session_id} by {current_user.email}")

# WebSocket エンドポイント
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket接続エンドポイント"""
    
    try:
        # ユーザー認証（簡易版 - 実際にはトークン認証を実装）
        # TODO: WebSocketでのJWT認証実装
        
        await manager.connect(websocket, user_id)
        logger.info(f"WebSocket接続: user_id={user_id}")
        
        try:
            while True:
                # クライアントからのメッセージ受信
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # メッセージタイプに応じた処理
                if message_data.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message_data.get("type") == "chat_typing":
                    # タイピング状態通知（将来実装）
                    pass
                
        except WebSocketDisconnect:
            manager.disconnect(user_id)
            logger.info(f"WebSocket切断: user_id={user_id}")
            
    except Exception as e:
        logger.error(f"WebSocketエラー: {str(e)}")
        await websocket.close()