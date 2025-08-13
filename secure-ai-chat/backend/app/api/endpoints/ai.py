"""
セキュアAIチャット - AI API エンドポイント（修正版）
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator
import json
import asyncio
import time

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models.user import User
from app.models.audit import AuditAction, AuditLevel
from app.services.ai_service import ai_service, AIServiceException
from app.services.logging_service import log_security_event

router = APIRouter()

# Pydantic モデル
class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str = Field(..., min_length=1, max_length=10000)

class CompletionRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_items=1, max_items=50)
    model: Optional[str] = Field(None, max_length=100)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)
    stream: bool = Field(False)
    
    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError('メッセージが必要です')
        
        # システムメッセージは最初のメッセージのみ許可
        system_count = sum(1 for msg in v if msg.role == 'system')
        if system_count > 1:
            raise ValueError('システムメッセージは1つまで設定できます')
        
        if system_count == 1 and v[0].role != 'system':
            raise ValueError('システムメッセージは最初に配置してください')
        
        return v

class CompletionResponse(BaseModel):
    content: str
    model: str
    tokens_used: int
    processing_time_ms: int
    finish_reason: str
    metadata: Dict[str, Any]

class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    max_tokens: int
    cost_per_1k_tokens: float

class TokenUsageResponse(BaseModel):
    user_id: int
    tokens_used_today: int
    daily_limit: int
    remaining_tokens: int
    limit_reached: bool

@router.get("/models", response_model=List[ModelInfo])
async def get_available_models(
    current_user: User = Depends(get_current_active_user)
):
    """利用可能なAIモデル一覧を取得"""
    try:
        models = ai_service.get_available_models(current_user)
        return models
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"モデル一覧取得エラー: {str(e)}"
        )

@router.get("/usage", response_model=TokenUsageResponse)
async def get_token_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """現在のトークン使用状況を取得"""
    try:
        tokens_used_today = await ai_service.count_user_tokens_today(db, current_user.id)
        daily_limit = 50000  # 設定可能にする
        
        return TokenUsageResponse(
            user_id=current_user.id,
            tokens_used_today=tokens_used_today,
            daily_limit=daily_limit,
            remaining_tokens=max(0, daily_limit - tokens_used_today),
            limit_reached=tokens_used_today >= daily_limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"使用状況取得エラー: {str(e)}"
        )

@router.post("/chat", response_model=CompletionResponse)
async def create_completion(
    request_data: CompletionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """AI補完を生成（非ストリーミング）"""
    
    # レート制限チェック
    rate_limit_ok, rate_limit_msg = await ai_service.check_rate_limit(current_user, db)
    if not rate_limit_ok:
        # 制限超過を監査ログに記録
        await log_security_event(
            db=db,
            event_type="rate_limit_exceeded",
            user_id=current_user.id,
            ip_address=request.headers.get("X-Forwarded-For") or (request.client.host if request.client else None),
            details={"message": rate_limit_msg},
            success=False
        )
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=rate_limit_msg
        )
    
    # モデルアクセス権限チェック
    model = request_data.model or "gpt-3.5-turbo"
    if not await ai_service.validate_model_access(current_user, model):
        await log_security_event(
            db=db,
            event_type="unauthorized_access",
            user_id=current_user.id,
            ip_address=request.headers.get("X-Forwarded-For") or (request.client.host if request.client else None),
            details={"attempted_model": model},
            success=False
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"モデル '{model}' へのアクセス権限がありません"
        )
    
    try:
        # メッセージを辞書形式に変換
        messages = [msg.dict() for msg in request_data.messages]
        
        # AI API呼び出し
        result = await ai_service.generate_completion(
            messages=messages,
            model=model,
            temperature=request_data.temperature,
            max_tokens=request_data.max_tokens,
            stream=False,
            user_id=current_user.id,
            db=db
        )
        
        return CompletionResponse(**result)
        
    except AIServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI補完生成エラー: {str(e)}"
        )

@router.post("/chat/stream")
async def create_streaming_completion(
    request_data: CompletionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """AI補完を生成（ストリーミング）"""
    
    # レート制限チェック
    rate_limit_ok, rate_limit_msg = await ai_service.check_rate_limit(current_user, db)
    if not rate_limit_ok:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=rate_limit_msg
        )
    
    # モデルアクセス権限チェック
    model = request_data.model or "gpt-3.5-turbo"
    if not await ai_service.validate_model_access(current_user, model):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"モデル '{model}' へのアクセス権限がありません"
        )
    
    async def generate_stream():
        """ストリーミングレスポンス生成器"""
        try:
            # メッセージを辞書形式に変換
            messages = [msg.dict() for msg in request_data.messages]
            
            # ストリーミング AI API呼び出し
            stream_generator = ai_service.generate_completion(
                messages=messages,
                model=model,
                temperature=request_data.temperature,
                max_tokens=request_data.max_tokens,
                stream=True,
                user_id=current_user.id,
                db=db
            )
            
            async for chunk in stream_generator:
                # Server-Sent Events (SSE) 形式でレスポンス
                chunk_data = json.dumps(chunk, ensure_ascii=False)
                yield f"data: {chunk_data}\n\n"
                
                # 完了チェック
                if chunk.get("type") == "completed" or chunk.get("type") == "error":
                    break
            
            # ストリーム終了
            yield "data: [DONE]\n\n"
            
        except AIServiceException as e:
            error_chunk = {
                "type": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_chunk = {
                "type": "error", 
                "error": f"内部サーバーエラー: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

@router.post("/validate-content")
async def validate_content(
    content: Dict[str, str],
    current_user: User = Depends(get_current_active_user)
):
    """コンテンツの安全性を検証"""
    
    # 基本的なコンテンツフィルタリング
    text = content.get("text", "")
    
    # 禁止されたキーワードチェック（実装例）
    forbidden_keywords = [
        # セキュリティリスクのあるキーワード
        "sql injection", "xss", "script", "password", "secret",
        # 不適切なコンテンツキーワード
        # 実際の運用では、より詳細なフィルターが必要
    ]
    
    violations = []
    text_lower = text.lower()
    
    for keyword in forbidden_keywords:
        if keyword in text_lower:
            violations.append(keyword)
    
    # 文字数チェック
    if len(text) > 10000:
        violations.append("文字数上限超過")
    
    is_safe = len(violations) == 0
    
    return {
        "is_safe": is_safe,
        "violations": violations,
        "message": "安全です" if is_safe else f"以下の問題があります: {', '.join(violations)}"
    }

@router.get("/health")
async def ai_health_check():
    """AI サービスヘルスチェック"""
    
    try:
        # 簡単なテストリクエストでAI APIの状態確認
        test_messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        # タイムアウト付きでテスト
        test_result = await asyncio.wait_for(
            ai_service.generate_completion(
                messages=test_messages,
                model="gpt-3.5-turbo",
                temperature=0.1,
                max_tokens=10
            ),
            timeout=30.0
        )
        
        return {
            "status": "healthy",
            "ai_service": "available",
            "model_tested": "gpt-3.5-turbo",
            "response_time_ms": test_result.get("processing_time_ms", 0)
        }
        
    except asyncio.TimeoutError:
        return {
            "status": "degraded",
            "ai_service": "timeout",
            "error": "AI APIの応答がタイムアウトしました"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "ai_service": "unavailable", 
            "error": str(e)
        }