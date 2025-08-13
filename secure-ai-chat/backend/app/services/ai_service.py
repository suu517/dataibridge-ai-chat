"""
セキュアAIチャット - AI API統合サービス
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from datetime import datetime, timezone
import httpx
from openai import AsyncOpenAI, AsyncAzureOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.models.tenant import Tenant
from app.models.chat import Chat, ChatMessage, MessageType
from app.models.audit import AuditLog, AuditAction, AuditLevel
from app.core.security import hash_data

class TenantAIClient:
    """テナント専用AIクライアント"""
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self._client: Optional[AsyncOpenAI | AsyncAzureOpenAI] = None
        self._client_initialized = False
    
    def _init_client(self) -> AsyncOpenAI | AsyncAzureOpenAI:
        """テナント設定に基づいてAIクライアントを初期化"""
        if self._client_initialized:
            return self._client
        
        ai_settings = self.tenant.get_ai_settings()
        
        try:
            if ai_settings.get("use_azure", False):
                # Azure OpenAI クライアント
                self._client = AsyncAzureOpenAI(
                    api_key=ai_settings["azure_api_key"],
                    api_version=ai_settings["azure_api_version"],
                    azure_endpoint=ai_settings["azure_endpoint"]
                )
            else:
                # OpenAI クライアント
                self._client = AsyncOpenAI(
                    api_key=ai_settings["openai_api_key"]
                )
            
            self._client_initialized = True
            return self._client
            
        except Exception as e:
            raise ValueError(f"テナント {self.tenant.name} のAI クライアント初期化エラー: {e}")
    
    @property
    def client(self) -> AsyncOpenAI | AsyncAzureOpenAI:
        """AIクライアントを取得"""
        if not self._client_initialized:
            return self._init_client()
        
        if self._client is None:
            raise ValueError(f"テナント {self.tenant.name} の利用可能なAI クライアントがありません")
        
        return self._client
    
    def get_model_name(self) -> str:
        """使用するモデル名を取得"""
        ai_settings = self.tenant.get_ai_settings()
        
        if ai_settings.get("use_azure", False):
            return ai_settings.get("azure_deployment", "gpt-4")
        else:
            return ai_settings.get("openai_model", "gpt-4")


class AIService:
    """AI API統合サービス（マルチテナント対応）"""
    
    def __init__(self):
        self._tenant_clients: Dict[str, TenantAIClient] = {}
    
    def get_tenant_client(self, tenant: Tenant) -> TenantAIClient:
        """テナント用AIクライアントを取得"""
        tenant_key = str(tenant.id)
        
        if tenant_key not in self._tenant_clients:
            self._tenant_clients[tenant_key] = TenantAIClient(tenant)
        
        return self._tenant_clients[tenant_key]
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        tenant: Tenant,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """AIレスポンスを生成（テナント別API設定対応）"""
        
        start_time = time.time()
        
        # テナント用AIクライアント取得
        tenant_client = self.get_tenant_client(tenant)
        
        # デフォルトモデル設定（テナント設定に基づく）
        if not model:
            model = tenant_client.get_model_name()
        
        # リクエストデータの準備
        request_data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            request_data["max_tokens"] = max_tokens
        
        # セキュリティ: リクエスト内容のハッシュ化（監査用）
        request_hash = hash_data(json.dumps(messages, sort_keys=True))
        
        try:
            # AI API呼び出し
            if stream:
                return await self._generate_stream_completion(
                    tenant_client, request_data, start_time, user_id, chat_id, request_hash, db
                )
            else:
                return await self._generate_single_completion(
                    tenant_client, request_data, start_time, user_id, chat_id, request_hash, db
                )
                
        except Exception as e:
            # エラー監査ログ
            if db and user_id:
                await self._log_ai_error(
                    db, user_id, str(e), request_hash, 
                    time.time() - start_time, str(tenant.id)
                )
            
            raise AIServiceException(f"AI API呼び出しエラー: {str(e)}")
    
    async def _generate_single_completion(
        self,
        tenant_client: TenantAIClient,
        request_data: Dict[str, Any],
        start_time: float,
        user_id: Optional[int],
        chat_id: Optional[int],
        request_hash: str,
        db: Optional[AsyncSession]
    ) -> Dict[str, Any]:
        """単発のAIレスポンス生成（テナント別対応）"""
        
        try:
            response: ChatCompletion = await tenant_client.client.chat.completions.create(**request_data)
            
            processing_time = time.time() - start_time
            
            # レスポンス解析
            choice = response.choices[0] if response.choices else None
            if not choice:
                raise AIServiceException("AI APIからの応答が不正です")
            
            result = {
                "content": choice.message.content or "",
                "model": response.model,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "processing_time_ms": int(processing_time * 1000),
                "finish_reason": choice.finish_reason,
                "metadata": {
                    "request_id": response.id if hasattr(response, 'id') else None,
                    "created": response.created if hasattr(response, 'created') else None,
                    "usage": response.usage.model_dump() if response.usage else None
                }
            }
            
            # 監査ログ記録
            if db and user_id:
                await self._log_ai_request(
                    db, user_id, chat_id, request_hash, result, processing_time, str(tenant_client.tenant.id)
                )
            
            return result
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "rate_limit" in error_msg or "too many requests" in error_msg:
                raise AIServiceException("AI APIのレート制限に達しました。しばらく時間をおいてから再試行してください。")
            elif "quota" in error_msg or "insufficient_quota" in error_msg:
                raise AIServiceException("AI APIの利用制限に達しました。テナント管理者にお問い合わせください。")
            elif "content_policy" in error_msg or "policy_violation" in error_msg:
                raise AIServiceException("リクエスト内容がAIのコンテンツポリシーに違反しています。")
            elif "invalid_api_key" in error_msg or "authentication" in error_msg:
                raise AIServiceException("AI APIキーが無効です。テナントのAPI設定を確認してください。")
            elif "model_not_found" in error_msg or "model does not exist" in error_msg:
                raise AIServiceException("指定されたAIモデルが見つかりません。API設定を確認してください。")
            elif "timeout" in error_msg or "timed out" in error_msg:
                raise AIServiceException("AI APIの応答がタイムアウトしました。再試行してください。")
            elif "connection" in error_msg or "network" in error_msg:
                raise AIServiceException("AI APIへの接続に失敗しました。ネットワーク接続を確認してください。")
            else:
                # より詳細なエラー情報を含める
                raise AIServiceException(f"AI API呼び出しエラー: {str(e)[:200]}")
    
    async def _generate_stream_completion(
        self,
        tenant_client: TenantAIClient,
        request_data: Dict[str, Any],
        start_time: float,
        user_id: Optional[int],
        chat_id: Optional[int],
        request_hash: str,
        db: Optional[AsyncSession]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """ストリーミングAIレスポンス生成（テナント別対応）"""
        
        full_content = ""
        total_tokens = 0
        
        try:
            stream = await tenant_client.client.chat.completions.create(**request_data)
            
            async for chunk in stream:
                chunk: ChatCompletionChunk
                
                if chunk.choices and chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    full_content += content_chunk
                    
                    yield {
                        "type": "content",
                        "content": content_chunk,
                        "full_content": full_content,
                        "model": chunk.model,
                        "timestamp": int(time.time() * 1000)
                    }
                
                # 最終チャンク
                if chunk.choices and chunk.choices[0].finish_reason:
                    processing_time = time.time() - start_time
                    
                    # 使用トークン数の取得（可能であれば）
                    if hasattr(chunk, 'usage') and chunk.usage:
                        total_tokens = chunk.usage.total_tokens
                    
                    final_result = {
                        "type": "completed",
                        "content": full_content,
                        "model": chunk.model,
                        "tokens_used": total_tokens,
                        "processing_time_ms": int(processing_time * 1000),
                        "finish_reason": chunk.choices[0].finish_reason
                    }
                    
                    # 監査ログ記録
                    if db and user_id:
                        await self._log_ai_request(
                            db, user_id, chat_id, request_hash, final_result, processing_time, str(tenant_client.tenant.id)
                        )
                    
                    yield final_result
                    
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }
    
    async def _log_ai_request(
        self,
        db: AsyncSession,
        user_id: int,
        chat_id: Optional[int],
        request_hash: str,
        result: Dict[str, Any],
        processing_time: float,
        tenant_id: Optional[str] = None
    ):
        """AI APIリクエストを監査ログに記録"""
        
        details = {
            "request_hash": request_hash,
            "model": result.get("model"),
            "tokens_used": result.get("tokens_used", 0),
            "processing_time_ms": result.get("processing_time_ms", 0),
            "finish_reason": result.get("finish_reason")
        }
        
        # テナント情報を追加
        if tenant_id:
            details["tenant_id"] = tenant_id
        
        audit_log = AuditLog.create_log(
            action=AuditAction.AI_REQUEST,
            description=f"AI API呼び出し (モデル: {result.get('model', 'unknown')})",
            user_id=user_id,
            level=AuditLevel.LOW,
            resource_type="ai_request",
            resource_id=str(chat_id) if chat_id else None,
            success=True,
            details=details
        )
        
        db.add(audit_log)
        await db.commit()
    
    async def _log_ai_error(
        self,
        db: AsyncSession,
        user_id: int,
        error_message: str,
        request_hash: str,
        processing_time: float,
        tenant_id: Optional[str] = None
    ):
        """AI APIエラーを監査ログに記録"""
        
        details = {
            "request_hash": request_hash,
            "processing_time_ms": int(processing_time * 1000)
        }
        
        # テナント情報を追加
        if tenant_id:
            details["tenant_id"] = tenant_id
        
        audit_log = AuditLog.create_log(
            action=AuditAction.AI_ERROR,
            description=f"AI API呼び出しエラー: {error_message}",
            user_id=user_id,
            level=AuditLevel.HIGH,
            resource_type="ai_request",
            success=False,
            error_message=error_message,
            details=details
        )
        
        db.add(audit_log)
        await db.commit()
    
    async def validate_model_access(
        self, 
        user: User, 
        model: str
    ) -> bool:
        """モデルアクセス権限を検証"""
        
        # 管理者は全モデルアクセス可能
        if user.is_admin:
            return True
        
        # 基本モデルは全ユーザーアクセス可能
        basic_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        if model in basic_models:
            return True
        
        # 部署・役職別の制限（将来実装予定）
        # 現在は基本モデルのみ許可
        return False
    
    async def count_user_tokens_today(
        self, 
        db: AsyncSession, 
        user_id: int,
        tenant_id: Optional[str] = None
    ) -> int:
        """ユーザーの今日のトークン使用量を取得（テナント別対応）"""
        
        today = datetime.now(timezone.utc).date()
        
        # 監査ログからトークン使用量を集計
        from sqlalchemy import select, func, and_
        
        conditions = [
            AuditLog.user_id == user_id,
            AuditLog.action == AuditAction.AI_REQUEST,
            func.date(AuditLog.timestamp) == today,
            AuditLog.success == "true"
        ]
        
        # テナント別フィルタリング
        if tenant_id:
            conditions.append(
                func.json_extract(AuditLog.details, '$.tenant_id') == tenant_id
            )
        
        query = select(func.sum(
            func.cast(
                func.json_extract(AuditLog.details, '$.tokens_used'), 
                'INTEGER'
            )
        )).where(and_(*conditions))
        
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def check_rate_limit(
        self, 
        user: User, 
        tenant: Tenant,
        db: AsyncSession
    ) -> Tuple[bool, str]:
        """ユーザーとテナントのレート制限をチェック"""
        
        # 管理者は制限なし
        if user.is_admin:
            return True, "OK"
        
        # 今日のトークン使用量チェック（ユーザー個別）
        tokens_used_today = await self.count_user_tokens_today(db, user.id, str(tenant.id))
        
        # ユーザー個別制限値
        daily_user_token_limit = 10000  # 1日10,000トークン
        
        if tokens_used_today >= daily_user_token_limit:
            return False, f"個人の1日のトークン制限({daily_user_token_limit:,})に達しました"
        
        # テナント全体の使用量チェック
        tenant_tokens_today = await self.count_tenant_tokens_today(db, tenant.id)
        tenant_limit = tenant.max_tokens_per_month // 30  # 月間制限を日割り
        
        if tenant_tokens_today >= tenant_limit:
            return False, f"組織の1日のトークン制限({tenant_limit:,})に達しました"
        
        return True, "OK"
    
    async def count_tenant_tokens_today(
        self,
        db: AsyncSession,
        tenant_id: str
    ) -> int:
        """テナント全体の今日のトークン使用量を取得"""
        
        today = datetime.now(timezone.utc).date()
        
        from sqlalchemy import select, func, and_
        
        query = select(func.sum(
            func.cast(
                func.json_extract(AuditLog.details, '$.tokens_used'), 
                'INTEGER'
            )
        )).where(
            and_(
                func.json_extract(AuditLog.details, '$.tenant_id') == tenant_id,
                AuditLog.action == AuditAction.AI_REQUEST,
                func.date(AuditLog.timestamp) == today,
                AuditLog.success == True
            )
        )
        
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def count_tenant_tokens_monthly(
        self,
        db: AsyncSession,
        tenant_id: str
    ) -> int:
        """テナント全体の過去30日間のトークン使用量を取得"""
        
        from datetime import timedelta
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        from sqlalchemy import select, func, and_
        
        query = select(func.sum(
            func.cast(
                func.json_extract(AuditLog.details, '$.tokens_used'), 
                'INTEGER'
            )
        )).where(
            and_(
                func.json_extract(AuditLog.details, '$.tenant_id') == tenant_id,
                AuditLog.action == AuditAction.AI_REQUEST,
                AuditLog.timestamp >= thirty_days_ago,
                AuditLog.success == True
            )
        )
        
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def get_tenant_usage_breakdown(
        self,
        db: AsyncSession,
        tenant_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """テナントの使用量を日別に取得（グラフ用）"""
        
        from datetime import timedelta
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        from sqlalchemy import select, func, and_
        
        query = select(
            func.date(AuditLog.timestamp).label('date'),
            func.sum(
                func.cast(
                    func.json_extract(AuditLog.details, '$.tokens_used'), 
                    'INTEGER'
                )
            ).label('tokens_used')
        ).where(
            and_(
                func.json_extract(AuditLog.details, '$.tenant_id') == tenant_id,
                AuditLog.action == AuditAction.AI_REQUEST,
                AuditLog.timestamp >= start_date,
                AuditLog.success == True
            )
        ).group_by(
            func.date(AuditLog.timestamp)
        ).order_by(
            func.date(AuditLog.timestamp)
        )
        
        result = await db.execute(query)
        
        breakdown = []
        for row in result:
            breakdown.append({
                'date': row.date.isoformat(),
                'tokens_used': row.tokens_used or 0
            })
        
        return breakdown
    
    def get_available_models(self, user: User, tenant: Tenant) -> List[Dict[str, Any]]:
        """ユーザーとテナントが利用可能なモデル一覧を取得"""
        
        models = []
        ai_settings = tenant.get_ai_settings()
        
        # テナント設定に基づくモデル一覧
        if ai_settings.get("use_azure", False):
            # Azure OpenAI モデル
            azure_models = [
                {
                    "id": ai_settings.get("azure_deployment", "gpt-4"),
                    "name": f"Azure {ai_settings.get('azure_deployment', 'gpt-4')}",
                    "description": "テナント専用Azure OpenAIモデル",
                    "provider": "azure_openai",
                    "max_tokens": 8192,
                    "cost_per_1k_tokens": 0.03
                }
            ]
            models.extend(azure_models)
        else:
            # OpenAI モデル
            openai_model = ai_settings.get("openai_model", "gpt-4")
            openai_models = [
                {
                    "id": openai_model,
                    "name": f"OpenAI {openai_model}",
                    "description": "テナント専用OpenAIモデル",
                    "provider": "openai",
                    "max_tokens": 8192 if "gpt-4" in openai_model else 4096,
                    "cost_per_1k_tokens": 0.03 if "gpt-4" in openai_model else 0.0015
                }
            ]
            models.extend(openai_models)
        
        # システムデフォルトモデル（フォールバック用）
        if ai_settings.get("provider") == "system_default" or user.is_admin:
            system_models = [
                {
                    "id": "system-default",
                    "name": "システムデフォルト",
                    "description": "システム管理者設定のモデル",
                    "provider": "system",
                    "max_tokens": 8192,
                    "cost_per_1k_tokens": 0.03
                }
            ]
            models.extend(system_models)
        
        return models

class AIServiceException(Exception):
    """AI サービス例外"""
    pass

# グローバル AI サービスインスタンス
ai_service = AIService()