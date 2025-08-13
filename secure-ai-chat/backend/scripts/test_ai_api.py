#!/usr/bin/env python3
"""
OpenAI API テストスクリプト
"""

import asyncio
import sys
import os
from pathlib import Path

# パスを追加してアプリケーションモジュールをインポート可能に
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.core.config import settings
import openai
from openai import AsyncOpenAI

async def test_openai_api():
    """OpenAI APIテスト"""
    
    print("🔄 OpenAI API接続テスト開始...")
    print(f"使用するAPIキー: {settings.OPENAI_API_KEY[:10]}...{settings.OPENAI_API_KEY[-10:]}")
    
    try:
        # OpenAI クライアント作成
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # テスト用のシンプルなリクエスト
        test_messages = [
            {
                "role": "user",
                "content": "こんにちは！テストメッセージです。短く挨拶を返してください。"
            }
        ]
        
        print("📤 テストリクエストを送信中...")
        
        # ChatCompletion API呼び出し
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=test_messages,
            max_tokens=50,
            temperature=0.7
        )
        
        # レスポンス処理
        if response.choices and len(response.choices) > 0:
            ai_response = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            print("✅ OpenAI API テスト成功!")
            print(f"📝 AI応答: {ai_response}")
            print(f"🔢 使用トークン数: {tokens_used}")
            print(f"🤖 使用モデル: {response.model}")
            
            return True
        else:
            print("❌ レスポンスが空です")
            return False
            
    except openai.AuthenticationError as e:
        print(f"❌ 認証エラー: APIキーが無効です")
        print(f"   エラー詳細: {str(e)}")
        return False
        
    except openai.RateLimitError as e:
        print(f"❌ レート制限エラー: リクエスト頻度が高すぎます")
        print(f"   エラー詳細: {str(e)}")
        return False
        
    except openai.APIError as e:
        print(f"❌ API エラー: {str(e)}")
        return False
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {str(e)}")
        return False

async def test_streaming_api():
    """ストリーミングAPIテスト"""
    
    print("\n🔄 OpenAI ストリーミングAPI テスト開始...")
    
    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        test_messages = [
            {
                "role": "user", 
                "content": "「AI技術」について1-2文で簡潔に説明してください。"
            }
        ]
        
        print("📤 ストリーミングリクエストを送信中...")
        
        # ストリーミング API呼び出し
        stream = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=test_messages,
            max_tokens=100,
            temperature=0.5,
            stream=True
        )
        
        print("📺 ストリーミングレスポンス:")
        full_response = ""
        
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    content = delta.content
                    print(content, end='', flush=True)
                    full_response += content
        
        print(f"\n\n✅ ストリーミングAPI テスト成功!")
        print(f"📝 完全な応答: {full_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ ストリーミングAPIエラー: {str(e)}")
        return False

async def test_model_availability():
    """利用可能なモデルをテスト"""
    
    print("\n🔄 利用可能モデル確認中...")
    
    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # モデル一覧取得
        models = await client.models.list()
        
        # ChatGPTモデルのみフィルタ
        chat_models = []
        for model in models.data:
            if any(keyword in model.id for keyword in ['gpt-3.5', 'gpt-4']):
                chat_models.append(model.id)
        
        print("✅ 利用可能なチャットモデル:")
        for model in sorted(chat_models):
            print(f"   • {model}")
        
        return True
        
    except Exception as e:
        print(f"❌ モデル一覧取得エラー: {str(e)}")
        return False

async def main():
    """メイン処理"""
    
    print("🤖 OpenAI API 総合テスト")
    print("=" * 50)
    
    # 設定確認
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "demo-key-not-functional":
        print("❌ OpenAI APIキーが設定されていません")
        print("   .env ファイルで OPENAI_API_KEY を設定してください")
        sys.exit(1)
    
    # テスト実行
    tests = [
        ("基本APIテスト", test_openai_api),
        ("ストリーミングAPIテスト", test_streaming_api),
        ("モデル可用性テスト", test_model_availability),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except KeyboardInterrupt:
            print("\n\n⚠️ テストが中断されました")
            sys.exit(1)
        except Exception as e:
            print(f"❌ {test_name}で予期しないエラー: {str(e)}")
            results[test_name] = False
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 テスト結果サマリー")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
    
    print(f"\n総テスト数: {total_tests}")
    print(f"成功: {passed_tests}")
    print(f"失敗: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 全てのテストが成功しました!")
        print("   OpenAI API統合は正常に動作しています。")
    else:
        print(f"\n⚠️ {total_tests - passed_tests}個のテストが失敗しました。")
        print("   APIキーや設定を確認してください。")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())