#!/usr/bin/env python3
"""
セキュアAIチャット - AI API接続テスト
"""

import asyncio
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import settings

async def test_openai_connection():
    """OpenAI API接続テスト"""
    print("=== AI API接続テスト ===\n")
    
    # 設定確認
    print("1. 設定確認:")
    print(f"   - 環境: {settings.ENVIRONMENT}")
    print(f"   - Azure OpenAI使用: {settings.use_azure_openai}")
    
    if settings.use_azure_openai:
        print(f"   - Azure エンドポイント: {settings.AZURE_OPENAI_ENDPOINT}")
        print(f"   - APIキー設定: {'有' if settings.AZURE_OPENAI_API_KEY else '無'}")
        print(f"   - デプロイメント名: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
    else:
        print(f"   - OpenAI APIキー設定: {'有' if settings.OPENAI_API_KEY else '無'}")
        print(f"   - モデル: {settings.OPENAI_MODEL}")
    
    print()
    
    # APIキーが設定されているかチェック
    if not settings.use_azure_openai and not settings.OPENAI_API_KEY:
        print("❌ AI APIキーが設定されていません")
        print("\n設定方法:")
        print("1. .envファイルを編集して以下を追加:")
        print("   OPENAI_API_KEY=your-openai-api-key-here")
        print("   または")
        print("   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
        print("   AZURE_OPENAI_API_KEY=your-azure-openai-api-key")
        return False
    
    # AI サービステスト
    try:
        print("2. AI サービス初期化テスト:")
        from app.services.ai_service import ai_service
        print("   ✅ AI サービス初期化成功")
    except Exception as e:
        print(f"   ❌ AI サービス初期化エラー: {e}")
        return False
    
    # 簡単なテストメッセージ
    test_messages = [
        {
            "role": "system",
            "content": "あなたは親切なAIアシスタントです。"
        },
        {
            "role": "user",
            "content": "こんにちは！簡単な挨拶をお願いします。"
        }
    ]
    
    try:
        print("\n3. AI API呼び出しテスト:")
        print("   テストメッセージを送信中...")
        
        response = await ai_service.generate_completion(
            messages=test_messages,
            temperature=0.7,
            max_tokens=100
        )
        
        print("   ✅ AI API呼び出し成功!")
        print(f"   - レスポンス: {response['content'][:100]}...")
        print(f"   - モデル: {response['model']}")
        print(f"   - トークン使用量: {response['tokens_used']}")
        print(f"   - 処理時間: {response['processing_time_ms']}ms")
        
        return True
        
    except Exception as e:
        print(f"   ❌ AI API呼び出しエラー: {e}")
        return False

async def test_available_models():
    """利用可能モデル一覧テスト"""
    print("\n4. 利用可能モデル一覧:")
    
    try:
        from app.services.ai_service import ai_service
        from app.models.user import User
        
        # テスト用ユーザー（管理者権限）
        test_user = User(
            username="test_admin",
            email="admin@test.com",
            is_admin=True
        )
        
        models = ai_service.get_available_models(test_user)
        
        for model in models:
            print(f"   - {model['name']} ({model['id']})")
            print(f"     説明: {model['description']}")
            print(f"     最大トークン: {model['max_tokens']:,}")
            print(f"     1Kトークン単価: ${model['cost_per_1k_tokens']}")
            print()
            
    except Exception as e:
        print(f"   ❌ モデル一覧取得エラー: {e}")

def main():
    """メイン処理"""
    print("セキュアAIチャット - AI API接続テスト\n")
    
    # 環境変数の設定を促すメッセージ
    if not os.getenv('OPENAI_API_KEY') and not os.getenv('AZURE_OPENAI_API_KEY'):
        print("🔑 AI APIキーを設定してください:")
        print("   export OPENAI_API_KEY='your-openai-api-key-here'")
        print("   または")
        print("   export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        print("   export AZURE_OPENAI_API_KEY='your-azure-openai-api-key'\n")
    
    # 非同期テスト実行
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(test_openai_connection())
        
        if success:
            loop.run_until_complete(test_available_models())
            print("🎉 すべてのテストが正常に完了しました!")
        else:
            print("\n❌ テストに失敗しました。設定を確認してください。")
            
    except KeyboardInterrupt:
        print("\n⏹️  テストが中断されました。")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    main()