"""
セキュアAIチャット - WebSocketエンドポイント
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import json
import logging

from app.websocket.manager import manager
from app.core.auth import get_current_user_ws
from app.models.user import User
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/chat/{chat_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    chat_id: int,
    token: str = Query(...),
):
    """チャット用WebSocketエンドポイント"""
    
    user = None
    try:
        # JWTトークンから認証情報を取得
        user = await get_current_user_ws(token)
        
        # WebSocket接続確立
        await manager.connect(websocket, user.id, chat_id)
        
        logger.info(f"WebSocketチャット接続確立: user={user.username}, chat_id={chat_id}")
        
        while True:
            # クライアントからのメッセージ受信
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            await handle_websocket_message(websocket, user, chat_id, message_data)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocketチャット切断: user={user.username if user else 'Unknown'}, chat_id={chat_id}")
        
    except Exception as e:
        logger.error(f"WebSocketチャットエラー: {e}")
        if websocket.client_state.name != 'DISCONNECTED':
            await websocket.close(code=1000, reason=f"Error: {str(e)}")
        
    finally:
        # 接続クリーンアップ
        manager.disconnect(websocket)

async def handle_websocket_message(
    websocket: WebSocket, 
    user: User, 
    chat_id: int, 
    message_data: dict
):
    """WebSocketメッセージハンドラー"""
    
    try:
        message_type = message_data.get("type")
        
        if message_type == "typing":
            # タイピングインジケーター
            is_typing = message_data.get("is_typing", False)
            await manager.broadcast_typing_indicator(chat_id, user.id, is_typing)
            
        elif message_type == "message":
            # 新しいメッセージ送信
            content = message_data.get("content", "")
            if content.strip():
                # メッセージをデータベースに保存（実際の実装では必要）
                # ここでは簡単なブロードキャスト
                await manager.broadcast_new_message(chat_id, {
                    "id": None,  # 実際のメッセージIDを設定
                    "content": content,
                    "user_id": user.id,
                    "username": user.username,
                    "type": "user"
                })
                
        elif message_type == "ai_request":
            # AI応答リクエスト
            await handle_ai_request(chat_id, user, message_data)
            
        elif message_type == "ping":
            # 生存確認
            await manager.send_personal_message({
                "type": "pong",
                "timestamp": message_data.get("timestamp")
            }, websocket)
            
    except Exception as e:
        logger.error(f"メッセージ処理エラー: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"メッセージ処理エラー: {str(e)}"
        }, websocket)

async def handle_ai_request(chat_id: int, user: User, message_data: dict):
    """AI応答リクエスト処理"""
    
    try:
        messages = message_data.get("messages", [])
        model = message_data.get("model", "gpt-4")
        stream = message_data.get("stream", False)
        
        if not messages:
            await manager.send_message_to_user(user.id, {
                "type": "error",
                "message": "メッセージが空です"
            })
            return
        
        # ストリーミングレスポンス
        if stream:
            await handle_streaming_ai_response(chat_id, user, messages, model)
        else:
            # 単発レスポンス
            response = await ai_service.generate_completion(
                messages=messages,
                model=model,
                user_id=user.id,
                chat_id=chat_id
            )
            
            await manager.broadcast_ai_stream(chat_id, {
                "type": "completed",
                "content": response["content"],
                "model": response["model"],
                "tokens_used": response["tokens_used"],
                "processing_time_ms": response["processing_time_ms"]
            })
            
    except Exception as e:
        logger.error(f"AI応答処理エラー: {e}")
        await manager.broadcast_ai_stream(chat_id, {
            "type": "error",
            "message": f"AI応答エラー: {str(e)}"
        })

async def handle_streaming_ai_response(
    chat_id: int, 
    user: User, 
    messages: list, 
    model: str
):
    """ストリーミングAI応答処理"""
    
    try:
        # ストリーミング開始通知
        await manager.broadcast_ai_stream(chat_id, {
            "type": "streaming_start",
            "model": model
        })
        
        # AI応答のストリーミング生成
        async for chunk in ai_service.generate_completion(
            messages=messages,
            model=model,
            stream=True,
            user_id=user.id,
            chat_id=chat_id
        ):
            await manager.broadcast_ai_stream(chat_id, chunk)
            
    except Exception as e:
        logger.error(f"ストリーミングAI応答エラー: {e}")
        await manager.broadcast_ai_stream(chat_id, {
            "type": "error",
            "message": f"ストリーミングエラー: {str(e)}"
        })

@router.websocket("/status")
async def websocket_status_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """ステータス監視用WebSocketエンドポイント"""
    
    try:
        # 認証
        user = await get_current_user_ws(token)
        
        # 管理者権限チェック
        if not user.is_admin:
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        await manager.connect(websocket, user.id)
        
        while True:
            # ステータス情報送信
            status_data = {
                "type": "system_status",
                "active_connections": manager.get_connection_count(),
                "active_users": len(manager.get_active_users()),
                "timestamp": "2024-01-01T00:00:00Z"  # 実際のタイムスタンプ
            }
            
            await manager.send_personal_message(status_data, websocket)
            
            # 30秒間隔で更新
            import asyncio
            await asyncio.sleep(30)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocketステータス接続切断: user={user.username}")
        
    except Exception as e:
        logger.error(f"WebSocketステータスエラー: {e}")
        
    finally:
        manager.disconnect(websocket)