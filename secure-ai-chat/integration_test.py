#!/usr/bin/env python3
"""
セキュアAIチャット - フロントエンド・バックエンド統合テスト
"""

import asyncio
import aiohttp
import json
import time
import websockets
from datetime import datetime
from typing import Dict, Any, Optional

# テスト設定
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
WS_URL = "ws://localhost:8000"

class IntegrationTester:
    """統合テストクラス"""
    
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_user_id = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_backend_health(self) -> bool:
        """バックエンドヘルスチェック"""
        print("=== バックエンドヘルスチェック ===")
        
        try:
            async with self.session.get(f"{BACKEND_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ バックエンド正常動作: {data['service']} v{data['version']}")
                    return True
                else:
                    print(f"❌ バックエンドエラー: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ バックエンド接続エラー: {e}")
            return False
    
    async def test_frontend_health(self) -> bool:
        """フロントエンドヘルスチェック"""
        print("\n=== フロントエンドヘルスチェック ===")
        
        try:
            async with self.session.get(FRONTEND_URL) as response:
                if response.status == 200:
                    print("✅ フロントエンド正常動作")
                    return True
                else:
                    print(f"❌ フロントエンドエラー: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ フロントエンド接続エラー: {e}")
            return False
    
    async def test_authentication(self) -> bool:
        """認証機能テスト"""
        print("\n=== 認証機能テスト ===")
        
        try:
            # テストユーザー登録
            register_data = {
                "username": f"test_user_{int(time.time())}",
                "email": f"test_{int(time.time())}@example.com",
                "password": "TestPassword123!",
                "full_name": "テストユーザー"
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/api/v1/auth/register",
                json=register_data
            ) as response:
                if response.status in [200, 201]:
                    print("✅ ユーザー登録成功")
                elif response.status == 400:
                    # すでに存在する場合はログインを試行
                    print("ℹ️ ユーザーが既に存在 - ログインを試行")
                else:
                    print(f"❌ ユーザー登録失敗: HTTP {response.status}")
                    return False
            
            # ログイン
            login_data = {
                "username": register_data["username"],
                "password": register_data["password"]
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/api/v1/auth/login",
                data=login_data  # Form data for OAuth2
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    if self.auth_token:
                        print("✅ ログイン成功")
                        return True
                    else:
                        print("❌ トークン取得失敗")
                        return False
                else:
                    print(f"❌ ログイン失敗: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ 認証テストエラー: {e}")
            return False
    
    async def test_api_endpoints(self) -> bool:
        """APIエンドポイントテスト"""
        print("\n=== APIエンドポイントテスト ===")
        
        if not self.auth_token:
            print("❌ 認証トークンが必要です")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # ユーザー情報取得
            async with self.session.get(
                f"{BACKEND_URL}/api/v1/users/me",
                headers=headers
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    self.test_user_id = user_data.get("id")
                    print(f"✅ ユーザー情報取得成功: {user_data.get('username')}")
                else:
                    print(f"❌ ユーザー情報取得失敗: HTTP {response.status}")
                    return False
            
            # テンプレート一覧取得
            async with self.session.get(
                f"{BACKEND_URL}/api/v1/templates",
                headers=headers
            ) as response:
                if response.status == 200:
                    templates_data = await response.json()
                    template_count = len(templates_data.get("templates", []))
                    print(f"✅ テンプレート一覧取得成功: {template_count}件")
                else:
                    print(f"❌ テンプレート一覧取得失敗: HTTP {response.status}")
                    return False
            
            # AI利用可能モデル一覧
            async with self.session.get(
                f"{BACKEND_URL}/api/v1/ai/models",
                headers=headers
            ) as response:
                if response.status == 200:
                    models_data = await response.json()
                    model_count = len(models_data.get("models", []))
                    print(f"✅ AIモデル一覧取得成功: {model_count}モデル")
                else:
                    print(f"❌ AIモデル一覧取得失敗: HTTP {response.status}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ APIテストエラー: {e}")
            return False
    
    async def test_ai_integration(self) -> bool:
        """AI統合機能テスト"""
        print("\n=== AI統合機能テスト ===")
        
        if not self.auth_token:
            print("❌ 認証トークンが必要です")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # 簡単なAIリクエスト
            ai_request = {
                "messages": [
                    {
                        "role": "system",
                        "content": "あなたは親切なAIアシスタントです。"
                    },
                    {
                        "role": "user",
                        "content": "こんにちは！簡単な挨拶をお願いします。"
                    }
                ],
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 100
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/api/v1/ai/chat",
                json=ai_request,
                headers=headers
            ) as response:
                if response.status == 200:
                    ai_data = await response.json()
                    content = ai_data.get("content", "")[:50]
                    tokens = ai_data.get("tokens_used", 0)
                    processing_time = ai_data.get("processing_time_ms", 0)
                    print(f"✅ AI応答成功: '{content}...' ({tokens}トークン, {processing_time}ms)")
                    return True
                else:
                    text_response = await response.text()
                    print(f"❌ AI応答失敗: HTTP {response.status}")
                    print(f"   エラー詳細: {text_response[:200]}")
                    return False
                    
        except Exception as e:
            print(f"❌ AI統合テストエラー: {e}")
            return False
    
    async def test_websocket_connection(self) -> bool:
        """WebSocket接続テスト"""
        print("\n=== WebSocket接続テスト ===")
        
        if not self.auth_token:
            print("❌ 認証トークンが必要です")
            return False
        
        try:
            # WebSocket接続テスト
            ws_url = f"{WS_URL}/ws/chat/1?token={self.auth_token}"
            
            async with websockets.connect(ws_url) as websocket:
                print("✅ WebSocket接続成功")
                
                # 接続確認メッセージ待機
                try:
                    welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    welcome_data = json.loads(welcome_msg)
                    if welcome_data.get("type") == "connection_established":
                        print("✅ WebSocket接続確立確認")
                        return True
                    else:
                        print(f"❌ 予期しないメッセージ: {welcome_data}")
                        return False
                        
                except asyncio.TimeoutError:
                    print("❌ WebSocket接続確認タイムアウト")
                    return False
                    
        except Exception as e:
            print(f"❌ WebSocketテストエラー: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """全テスト実行"""
        print("🚀 セキュアAIチャット - 統合テスト開始\n")
        
        results = {}
        
        # 各テスト実行
        results["backend_health"] = await self.test_backend_health()
        results["frontend_health"] = await self.test_frontend_health()
        results["authentication"] = await self.test_authentication()
        results["api_endpoints"] = await self.test_api_endpoints()
        results["ai_integration"] = await self.test_ai_integration()
        results["websocket"] = await self.test_websocket_connection()
        
        # 結果サマリー
        print("\n" + "="*50)
        print("📊 テスト結果サマリー")
        print("="*50)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\n合格率: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 すべてのテストが成功しました！")
        else:
            print("⚠️  一部のテストが失敗しました。設定を確認してください。")
        
        return results

async def main():
    """メイン処理"""
    print("セキュアAIチャット - 統合テストスイート")
    print("="*50)
    
    async with IntegrationTester() as tester:
        results = await tester.run_all_tests()
        
        # 設定ガイド
        if not all(results.values()):
            print("\n📝 トラブルシューティング:")
            
            if not results.get("backend_health"):
                print("・バックエンド: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
                
            if not results.get("frontend_health"):
                print("・フロントエンド: cd frontend && npm run dev")
                
            if not results.get("ai_integration"):
                print("・AI API: .envファイルにOPENAI_API_KEYまたはAzure OpenAI設定を追加")
                print("  export OPENAI_API_KEY='your-openai-api-key-here'")

if __name__ == "__main__":
    asyncio.run(main())