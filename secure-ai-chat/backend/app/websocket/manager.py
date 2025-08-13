"""
セキュアAIチャット - WebSocket接続マネージャー
"""

import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket接続管理クラス"""
    
    def __init__(self):
        # アクティブな接続: user_id -> Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # チャットルーム接続: chat_id -> Set[user_id]
        self.chat_rooms: Dict[int, Set[int]] = {}
        # 接続メタデータ
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, chat_id: int = None):
        """WebSocket接続を確立"""
        try:
            await websocket.accept()
            
            # ユーザー接続を記録
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            
            # チャットルーム参加
            if chat_id:
                if chat_id not in self.chat_rooms:
                    self.chat_rooms[chat_id] = set()
                self.chat_rooms[chat_id].add(user_id)
            
            # 接続メタデータ保存
            self.connection_metadata[websocket] = {
                "user_id": user_id,
                "chat_id": chat_id,
                "connected_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }
            
            logger.info(f"WebSocket接続確立: user_id={user_id}, chat_id={chat_id}")
            
            # 接続完了メッセージ送信
            await self.send_personal_message({
                "type": "connection_established",
                "user_id": user_id,
                "chat_id": chat_id,
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
            
        except Exception as e:
            logger.error(f"WebSocket接続エラー: {e}")
            raise
    
    def disconnect(self, websocket: WebSocket):
        """WebSocket接続を切断"""
        try:
            metadata = self.connection_metadata.get(websocket, {})
            user_id = metadata.get("user_id")
            chat_id = metadata.get("chat_id")
            
            # ユーザー接続から削除
            if user_id and user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # チャットルームから退出
            if chat_id and chat_id in self.chat_rooms:
                self.chat_rooms[chat_id].discard(user_id)
                if not self.chat_rooms[chat_id]:
                    del self.chat_rooms[chat_id]
            
            # メタデータ削除
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket接続切断: user_id={user_id}, chat_id={chat_id}")
            
        except Exception as e:
            logger.error(f"WebSocket切断処理エラー: {e}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """特定の接続にメッセージ送信"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
            
            # アクティビティ更新
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["last_activity"] = datetime.utcnow()
                
        except WebSocketDisconnect:
            # 接続が既に切れている場合
            self.disconnect(websocket)
        except Exception as e:
            logger.error(f"メッセージ送信エラー: {e}")
    
    async def send_message_to_user(self, user_id: int, message: dict):
        """特定ユーザーのすべての接続にメッセージ送信"""
        if user_id in self.active_connections:
            disconnected_connections = []
            
            for connection in self.active_connections[user_id].copy():
                try:
                    await self.send_personal_message(message, connection)
                except:
                    disconnected_connections.append(connection)
            
            # 切断された接続を削除
            for connection in disconnected_connections:
                self.disconnect(connection)
    
    async def broadcast_to_chat(self, chat_id: int, message: dict, exclude_user_id: int = None):
        """チャットルーム内の全ユーザーにブロードキャスト"""
        if chat_id not in self.chat_rooms:
            return
        
        for user_id in self.chat_rooms[chat_id]:
            if exclude_user_id and user_id == exclude_user_id:
                continue
            
            await self.send_message_to_user(user_id, message)
    
    async def broadcast_typing_indicator(self, chat_id: int, user_id: int, is_typing: bool):
        """タイピングインジケーターをブロードキャスト"""
        message = {
            "type": "typing_indicator",
            "chat_id": chat_id,
            "user_id": user_id,
            "is_typing": is_typing,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_chat(chat_id, message, exclude_user_id=user_id)
    
    async def broadcast_new_message(self, chat_id: int, message_data: dict):
        """新しいメッセージをチャットルームにブロードキャスト"""
        message = {
            "type": "new_message",
            "chat_id": chat_id,
            "message": message_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_chat(chat_id, message)
    
    async def broadcast_ai_stream(self, chat_id: int, stream_data: dict):
        """AIストリーミングレスポンスをブロードキャスト"""
        message = {
            "type": "ai_stream",
            "chat_id": chat_id,
            "stream_data": stream_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_chat(chat_id, message)
    
    def get_active_users(self, chat_id: int = None) -> List[int]:
        """アクティブユーザー一覧を取得"""
        if chat_id:
            return list(self.chat_rooms.get(chat_id, set()))
        else:
            return list(self.active_connections.keys())
    
    def get_connection_count(self) -> int:
        """総接続数を取得"""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_user_connection_count(self, user_id: int) -> int:
        """特定ユーザーの接続数を取得"""
        return len(self.active_connections.get(user_id, set()))
    
    async def cleanup_inactive_connections(self, timeout_minutes: int = 30):
        """非アクティブな接続をクリーンアップ"""
        current_time = datetime.utcnow()
        inactive_connections = []
        
        for websocket, metadata in self.connection_metadata.items():
            last_activity = metadata.get("last_activity", current_time)
            if (current_time - last_activity).total_seconds() > (timeout_minutes * 60):
                inactive_connections.append(websocket)
        
        for websocket in inactive_connections:
            try:
                await websocket.close(code=1000, reason="Timeout")
            except:
                pass
            self.disconnect(websocket)
        
        if inactive_connections:
            logger.info(f"非アクティブ接続をクリーンアップ: {len(inactive_connections)}個")

# グローバル接続マネージャー
manager = ConnectionManager()

# 定期的なクリーンアップタスク
async def periodic_cleanup():
    """定期クリーンアップタスク"""
    while True:
        try:
            await asyncio.sleep(300)  # 5分間隔
            await manager.cleanup_inactive_connections()
        except Exception as e:
            logger.error(f"定期クリーンアップエラー: {e}")

# バックグラウンドタスクとして実行
asyncio.create_task(periodic_cleanup())