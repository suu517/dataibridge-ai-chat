#!/usr/bin/env python3
"""
簡易APIサーバー - OpenAI APIテスト用
"""

import os
import asyncio
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import openai
from openai import AsyncOpenAI
import json
import uuid
from datetime import datetime

# 認証システムのインポート
from app.api.auth import router as auth_router
from app.core.middleware import TenantMiddleware, require_auth, get_current_user
from app.models.auth import User

# 環境変数から設定を読み込み
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not found in environment variables")

# FastAPIアプリ作成
app = FastAPI(title="Secure AI Chat API", version="1.0.0")

# ミドルウェア設定
app.add_middleware(TenantMiddleware)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発用：本番では制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 認証ルーター追加
app.include_router(auth_router)

# リクエスト・レスポンスモデル
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 500

class ChatResponse(BaseModel):
    content: str
    model: str
    tokens_used: int
    processing_time_ms: int
    finish_reason: str
    metadata: dict

# プロンプトテンプレート関連のモデル
class PromptTemplate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    category: str
    system_prompt: str
    variables: List[Dict[str, Any]] = []
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    created_at: str
    updated_at: str
    is_active: bool = True

class CreateTemplateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    system_prompt: str
    variables: List[Dict[str, Any]] = []
    example_input: Optional[str] = None
    example_output: Optional[str] = None

class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    system_prompt: Optional[str] = None
    variables: Optional[List[Dict[str, Any]]] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    is_active: Optional[bool] = None

class UseTemplateRequest(BaseModel):
    variables: Dict[str, str] = {}
    user_message: str
    model: str = "gpt-3.5-turbo"

# インメモリーテンプレートストレージ（デモ用）
templates_storage: Dict[str, PromptTemplate] = {}

# デモテンプレート作成
def create_demo_templates():
    demo_templates = [
        PromptTemplate(
            id="business_email",
            name="📧 ビジネスメール作成",
            description="情報を入力するだけで、プロフェッショナルなビジネスメールを自動生成",
            category="ビジネス",
            system_prompt="""あなたは30年の経験を持つ一流のビジネスコミュニケーション専門家です。
以下の指針に従って、最高品質のビジネスメールを作成してください：

【メール構成の基本原則】
1. 件名: 内容が一目で分かる具体的で簡潔なもの
2. 宛名: 敬語を適切に使用し、相手の立場を考慮
3. 挨拶: 関係性に応じた適切な挨拶文
4. 本文: 目的を明確に伝え、具体的で行動しやすい内容
5. 締め: 感謝の気持ちと今後の関係継続への配慮
6. 署名: 必要に応じて連絡先情報を含む

【トーン別の調整】
- フォーマル: 敬語を徹底し、格式高い表現を使用
- カジュアル: 親しみやすさを保ちながら礼儀は維持
- 友好的: 温かみのある表現で関係性を重視

【必須要素】
- 相手（{recipient}）への配慮を最優先
- 目的（{purpose}）を明確かつ具体的に伝達
- 選択されたトーン（{tone}）に完全に合致
- 日本のビジネス文化に適合
- 読み手が行動しやすい具体的な提案

ユーザーの要求を分析し、上記の専門知識を活用して完璧なビジネスメールを作成してください。""",
            variables=[
                {"name": "recipient", "type": "string", "description": "メールの送信先（例: 田中部長、山田様）", "required": True},
                {"name": "purpose", "type": "string", "description": "メールの目的（例: 会議の日程調整、資料の送付）", "required": True},
                {"name": "tone", "type": "select", "options": ["フォーマル", "カジュアル", "友好的"], "default": "フォーマル", "description": "メールのトーン"}
            ],
            example_input="来週の企画会議の時間を変更したいのでお知らせします",
            example_output="件名: 企画会議の日程変更のお知らせ\n\n田中部長\n\nいつもお世話になっております...",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_active=True
        ),
        PromptTemplate(
            id="code_review",
            name="🔍 AIコードレビュー",
            description="コードを入力するだけで、プロの開発者レベルの詳細なレビューを実行",
            category="開発",
            system_prompt="""あなたは20年以上の経験を持つシニアソフトウェアエンジニア兼セキュリティスペシャリストです。
以下の専門的な観点から、提供されたコードを包括的に分析してください：

【分析観点】
🔒 **セキュリティ**: 脆弱性、インジェクション攻撃、認証・認可の問題
⚡ **パフォーマンス**: 計算量、メモリ使用、データベースクエリ最適化
📖 **可読性**: コード構造、命名規則、コメント、保守性
🏗️ **アーキテクチャ**: 設計パターン、SOLID原則、分離度
🧪 **テスタビリティ**: 単体テスト容易性、依存関係注入

【レビュー形式】
1. **概要評価** (1-10点)
2. **良い点** (具体的な箇所を引用)
3. **改善点** (優先度付き、具体的な修正案)
4. **セキュリティ警告** (該当する場合)
5. **リファクタリング提案** (改良版コード例)

【重点分析項目】
- {language}言語のベストプラクティス準拠
- {focus}の観点を特に重視
- 業界標準規格への適合性
- 将来のメンテナンス性

プロの開発チームで行われる実際のコードレビューと同等の品質で、建設的で実用的なフィードバックを提供してください。""",
            variables=[
                {"name": "language", "type": "string", "description": "プログラミング言語（例: Python, JavaScript, Java）", "required": True},
                {"name": "focus", "type": "select", "options": ["セキュリティ", "パフォーマンス", "可読性", "全般"], "default": "全般", "description": "重点的にチェックしたい項目"}
            ],
            example_input="このPython関数をレビューしてください",
            example_output="## 🔍 コードレビュー結果\n\n**総合評価: 7/10**\n\n### ✅ 良い点\n- 関数名が処理内容を適切に表現...",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_active=True
        ),
        PromptTemplate(
            id="creative_writing",
            name="✍️ ストーリー創作支援",
            description="あらすじを入力するだけで、魅力的な物語の詳細プロットを自動生成",
            category="クリエイティブ",
            system_prompt="""あなたは数々のベストセラー作品を手掛けた経験豊富な小説家兼編集者です。
{genre}ジャンルの専門知識を活用し、以下の要素を含む魅力的な物語を構築してください：

【創作指針】
📖 **物語構造**: 起承転結を明確に設定し、読者を引き込む展開
👥 **キャラクター**: 立体的で共感できる登場人物の設定
🌍 **世界観**: {genre}ジャンルにふさわしい詳細な設定
⚡ **コンフリクト**: 主人公が直面する内的・外的な葛藤
💫 **テーマ**: {theme}を物語に自然に織り込む

【{genre}ジャンルの特徴を活用】
- ジャンル固有の魅力的な要素を盛り込む
- 読者の期待に応えつつ、意外性も提供
- ジャンルの定番を理解した上での独創性

【{length}に適した構成】
- 適切な情報密度と展開速度
- 読者が最後まで読み通せるペース配分
- クライマックスへの効果的な盛り上げ

【アウトプット形式】
1. **あらすじ** (魅力的な要約)
2. **主要キャラクター** (3-5人、詳細設定)
3. **プロット** (章構成と主要事件)
4. **世界観・設定** (舞台背景)
5. **テーマとメッセージ**
6. **読者へのアピールポイント**

読者が「この物語を読みたい！」と思える、出版レベルの企画書を作成してください。""",
            variables=[
                {"name": "genre", "type": "select", "options": ["ファンタジー", "SF", "ミステリー", "恋愛", "ホラー", "歴史小説", "冒険"], "required": True, "description": "物語のジャンル"},
                {"name": "length", "type": "select", "options": ["短編", "中編", "長編"], "default": "短編", "description": "作品の長さ"},
                {"name": "theme", "type": "string", "description": "物語に込めたいテーマ（例: 友情、成長、運命）", "required": True}
            ],
            example_input="近未来の宇宙ステーションで起こる謎の事件について",
            example_output="# 📚 物語企画書\n\n## あらすじ\n西暦2087年、火星軌道上の宇宙ステーション「アルテミス7」で...",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_active=True
        ),
        PromptTemplate(
            id="meeting_minutes",
            name="📝 議事録作成",
            description="会議内容を入力するだけで、整理された見やすい議事録を自動作成",
            category="ビジネス",
            system_prompt="""あなたは企業秘書や会議運営の専門家として、効果的な議事録を作成します。
以下の構造化された形式で、プロフェッショナルな議事録を作成してください：

【議事録の基本構成】
📅 **会議情報**: 日時、参加者、会議名
📋 **アジェンダ**: 議題の整理と分類
💬 **討議内容**: 主要な意見や提案の要約
✅ **決定事項**: 合意に至った内容を明確化
📝 **アクションアイテム**: 担当者と期限付きのタスク
📌 **次回予定**: フォローアップ事項

【品質基準】
- 参加していない人が読んでも内容が理解できる
- 決定事項と検討事項を明確に区別
- アクションアイテムは具体的で実行可能
- {meeting_type}会議にふさわしい詳細度
- 重要度に応じた情報の構造化

【フォーマット調整】
- {format}形式での出力
- 読みやすいレイアウトと見出し
- 必要に応じて図表や箇条書きを活用

会議参加者全員が合意できる、正確で有用な議事録を作成してください。""",
            variables=[
                {"name": "meeting_type", "type": "select", "options": ["定例会議", "プロジェクト会議", "役員会議", "企画会議", "進捗会議"], "default": "定例会議", "description": "会議の種類"},
                {"name": "format", "type": "select", "options": ["標準", "詳細", "簡潔"], "default": "標準", "description": "議事録の詳細度"}
            ],
            example_input="今日の営業部の週次会議について整理してください",
            example_output="# 📝 営業部週次会議 議事録\n\n**日時**: 2024年...\n**参加者**: ...\n\n## 📋 討議内容\n...",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_active=True
        )
    ]
    
    for template in demo_templates:
        templates_storage[template.id] = template

# 初期化時にデモテンプレートを作成
create_demo_templates()

# ヘルスチェック
@app.get("/")
async def root():
    return {
        "message": "🔐 Secure AI Chat API",
        "version": "1.0.0",
        "status": "ready",
        "features": ["AI Chat", "Prompt Templates"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Secure AI Chat",
        "version": "1.0.0"
    }

# AI チャットエンドポイント
@app.post("/api/v1/ai/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest, 
    current_user: Optional[User] = Depends(get_current_user)
):
    """AI チャット補完"""
    
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured"
        )
    
    try:
        # OpenAI クライアント作成
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # メッセージ変換
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        import time
        start_time = time.time()
        
        # API呼び出し
        response = await client.chat.completions.create(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # レスポンス作成
        return ChatResponse(
            content=response.choices[0].message.content,
            model=response.model,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            processing_time_ms=processing_time,
            finish_reason=response.choices[0].finish_reason,
            metadata={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }
        )
        
    except openai.AuthenticationError:
        raise HTTPException(
            status_code=401,
            detail="Invalid OpenAI API key"
        )
    except openai.RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="OpenAI API rate limit exceeded. Please check your billing and quota settings."
        )
    except openai.APIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"OpenAI API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# モデル一覧取得
@app.get("/api/v1/ai/models")
async def get_models():
    """利用可能なモデル一覧を取得"""
    
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured"
        )
    
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        models = await client.models.list()
        
        # GPTモデルのみフィルタ
        gpt_models = []
        for model in models.data:
            if any(keyword in model.id for keyword in ['gpt-3.5', 'gpt-4']):
                gpt_models.append({
                    "id": model.id,
                    "name": model.id,
                    "description": f"OpenAI {model.id}",
                    "max_tokens": 4096 if "gpt-3.5" in model.id else 8192,
                    "cost_per_1k_tokens": 0.002 if "gpt-3.5" in model.id else 0.03
                })
        
        return gpt_models
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch models: {str(e)}"
        )

# プロンプトテンプレート管理API

@app.get("/api/v1/templates", response_model=List[PromptTemplate])
async def get_templates(category: Optional[str] = None):
    """テンプレート一覧を取得"""
    templates = list(templates_storage.values())
    
    if category:
        templates = [t for t in templates if t.category.lower() == category.lower()]
    
    # アクティブなテンプレートのみ返す
    active_templates = [t for t in templates if t.is_active]
    return sorted(active_templates, key=lambda x: x.updated_at, reverse=True)

@app.get("/api/v1/templates/categories")
async def get_categories():
    """利用可能なテンプレートカテゴリ一覧を取得"""
    categories = list(set(t.category for t in templates_storage.values() if t.is_active))
    return sorted(categories)

@app.get("/api/v1/templates/{template_id}", response_model=PromptTemplate)
async def get_template(template_id: str):
    """指定されたテンプレートを取得"""
    if template_id not in templates_storage:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = templates_storage[template_id]
    if not template.is_active:
        raise HTTPException(status_code=404, detail="Template not active")
    
    return template

@app.post("/api/v1/templates", response_model=PromptTemplate)
async def create_template(template_data: CreateTemplateRequest):
    """新しいテンプレートを作成"""
    template_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    template = PromptTemplate(
        id=template_id,
        name=template_data.name,
        description=template_data.description,
        category=template_data.category,
        system_prompt=template_data.system_prompt,
        variables=template_data.variables,
        example_input=template_data.example_input,
        example_output=template_data.example_output,
        created_at=now,
        updated_at=now,
        is_active=True
    )
    
    templates_storage[template_id] = template
    return template

@app.put("/api/v1/templates/{template_id}", response_model=PromptTemplate)
async def update_template(template_id: str, template_data: UpdateTemplateRequest):
    """テンプレートを更新"""
    if template_id not in templates_storage:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = templates_storage[template_id]
    
    # フィールドを更新
    if template_data.name is not None:
        template.name = template_data.name
    if template_data.description is not None:
        template.description = template_data.description
    if template_data.category is not None:
        template.category = template_data.category
    if template_data.system_prompt is not None:
        template.system_prompt = template_data.system_prompt
    if template_data.variables is not None:
        template.variables = template_data.variables
    if template_data.example_input is not None:
        template.example_input = template_data.example_input
    if template_data.example_output is not None:
        template.example_output = template_data.example_output
    if template_data.is_active is not None:
        template.is_active = template_data.is_active
    
    template.updated_at = datetime.now().isoformat()
    templates_storage[template_id] = template
    return template

@app.delete("/api/v1/templates/{template_id}")
async def delete_template(template_id: str):
    """テンプレートを削除（非活性化）"""
    if template_id not in templates_storage:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 完全削除ではなく非活性化
    template = templates_storage[template_id]
    template.is_active = False
    template.updated_at = datetime.now().isoformat()
    
    return {"message": "Template deactivated successfully"}

@app.post("/api/v1/templates/{template_id}/use", response_model=ChatResponse)
async def use_template(template_id: str, request: UseTemplateRequest):
    """テンプレートを使用してAIチャット"""
    if template_id not in templates_storage:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = templates_storage[template_id]
    if not template.is_active:
        raise HTTPException(status_code=404, detail="Template not active")
    
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # システムプロンプトを変数で置換
        system_prompt = template.system_prompt
        for var_name, var_value in request.variables.items():
            placeholder = f"{{{var_name}}}"
            system_prompt = system_prompt.replace(placeholder, var_value)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.user_message}
        ]
        
        import time
        start_time = time.time()
        
        response = await client.chat.completions.create(
            model=request.model,
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            content=response.choices[0].message.content,
            model=response.model,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            processing_time_ms=processing_time,
            finish_reason=response.choices[0].finish_reason,
            metadata={
                "template_id": template_id,
                "template_name": template.name,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }
        )
        
    except openai.AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid OpenAI API key")
    except openai.RateLimitError:
        raise HTTPException(status_code=429, detail="OpenAI API rate limit exceeded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)