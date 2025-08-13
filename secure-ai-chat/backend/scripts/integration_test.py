#!/usr/bin/env python3
"""
セキュアAIチャット - 統合テストスクリプト
"""

import asyncio
import sys
import os
from pathlib import Path
import json
import time
from typing import Dict, Any, Optional
import logging

# パスを追加
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_password_hash, verify_token
from app.models.user import User, UserRole, UserStatus

logger = logging.getLogger(__name__)

class IntegrationTester:
    """統合テスト実行クラス"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.auth_token = None
        self.test_results = {}
        self.client = None
    
    async def setup(self):
        """テスト環境セットアップ"""
        print("🔄 テスト環境をセットアップ中...")
        
        # HTTPクライアントセットアップ
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0
        )
        
        # データベース接続テスト
        try:
            async_engine = create_async_engine(settings.database_url_async)
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await async_engine.dispose()
            print("✅ データベース接続テスト成功")
        except Exception as e:
            print(f"❌ データベース接続テスト失敗: {e}")
            return False
        
        return True
    
    async def cleanup(self):
        """テスト環境クリーンアップ"""
        if self.client:
            await self.client.aclose()
    
    async def test_health_check(self) -> bool:
        """ヘルスチェックテスト"""
        print("🔄 ヘルスチェックテスト中...")
        
        try:
            response = await self.client.get("/health")
            
            if response.status_code == 200:
                data = response.json()
                expected_keys = ["status", "service", "version", "environment"]
                
                if all(key in data for key in expected_keys):
                    print("✅ ヘルスチェックテスト成功")
                    return True
                else:
                    print(f"❌ ヘルスチェックレスポンス不正: {data}")
                    return False
            else:
                print(f"❌ ヘルスチェック失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ ヘルスチェックエラー: {e}")
            return False
    
    async def test_authentication(self) -> bool:
        """認証機能テスト"""
        print("🔄 認証機能テスト中...")
        
        try:
            # ログインテスト
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = await self.client.post("/api/v1/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if "access_token" in data and "user" in data:
                    self.auth_token = data["access_token"]
                    print("✅ ログインテスト成功")
                    
                    # 認証が必要なエンドポイントテスト
                    headers = {"Authorization": f"Bearer {self.auth_token}"}
                    me_response = await self.client.get("/api/v1/auth/me", headers=headers)
                    
                    if me_response.status_code == 200:
                        print("✅ 認証トークン検証テスト成功")
                        return True
                    else:
                        print(f"❌ 認証トークン検証失敗: {me_response.status_code}")
                        return False
                else:
                    print(f"❌ ログインレスポンス不正: {data}")
                    return False
            else:
                print(f"❌ ログイン失敗: {response.status_code}")
                if response.status_code == 404:
                    print("  ℹ️ 管理者ユーザーが作成されていない可能性があります")
                return False
                
        except Exception as e:
            print(f"❌ 認証テストエラー: {e}")
            return False
    
    async def test_user_management(self) -> bool:
        """ユーザー管理機能テスト"""
        print("🔄 ユーザー管理機能テスト中...")
        
        if not self.auth_token:
            print("❌ 認証トークンがありません")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # プロフィール取得テスト
            response = await self.client.get("/api/v1/users/profile", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                expected_keys = ["id", "username", "email", "role"]
                
                if all(key in data for key in expected_keys):
                    print("✅ ユーザープロフィール取得テスト成功")
                    
                    # プロフィール更新テスト
                    update_data = {
                        "full_name": "Test Admin Updated",
                        "department": "IT Operations"
                    }
                    
                    update_response = await self.client.put(
                        "/api/v1/users/profile",
                        headers=headers,
                        json=update_data
                    )
                    
                    if update_response.status_code == 200:
                        print("✅ ユーザープロフィール更新テスト成功")
                        return True
                    else:
                        print(f"❌ プロフィール更新失敗: {update_response.status_code}")
                        return False
                else:
                    print(f"❌ プロフィールレスポンス不正: {data}")
                    return False
            else:
                print(f"❌ プロフィール取得失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ ユーザー管理テストエラー: {e}")
            return False
    
    async def test_template_management(self) -> bool:
        """テンプレート管理機能テスト"""
        print("🔄 テンプレート管理機能テスト中...")
        
        if not self.auth_token:
            print("❌ 認証トークンがありません")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # カテゴリ一覧取得テスト
            categories_response = await self.client.get("/api/v1/templates/categories", headers=headers)
            
            if categories_response.status_code == 200:
                categories = categories_response.json()
                print(f"✅ テンプレートカテゴリ取得テスト成功 ({len(categories)}個のカテゴリ)")
                
                # テンプレート一覧取得テスト
                templates_response = await self.client.get("/api/v1/templates/", headers=headers)
                
                if templates_response.status_code == 200:
                    templates_data = templates_response.json()
                    print("✅ テンプレート一覧取得テスト成功")
                    
                    # テンプレート作成テスト
                    if categories:
                        create_data = {
                            "name": "テストテンプレート",
                            "description": "統合テスト用テンプレート",
                            "content": "あなたは{{role}}として{{task}}を実行してください。",
                            "category_id": categories[0]["id"],
                            "parameters": [
                                {"name": "role", "description": "役割", "type": "string"},
                                {"name": "task", "description": "タスク", "type": "string"}
                            ],
                            "tags": ["テスト", "自動生成"],
                            "access_level": "private"
                        }
                        
                        create_response = await self.client.post(
                            "/api/v1/templates/",
                            headers=headers,
                            json=create_data
                        )
                        
                        if create_response.status_code == 200:
                            print("✅ テンプレート作成テスト成功")
                            return True
                        else:
                            print(f"❌ テンプレート作成失敗: {create_response.status_code}")
                            print(f"   エラー: {create_response.text}")
                            return False
                    else:
                        print("⚠️ カテゴリが存在しないためテンプレート作成テストをスキップ")
                        return True
                else:
                    print(f"❌ テンプレート一覧取得失敗: {templates_response.status_code}")
                    return False
            else:
                print(f"❌ カテゴリ取得失敗: {categories_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ テンプレート管理テストエラー: {e}")
            return False
    
    async def test_ai_integration(self) -> bool:
        """AI統合機能テスト"""
        print("🔄 AI統合機能テスト中...")
        
        if not self.auth_token:
            print("❌ 認証トークンがありません")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # AIヘルスチェック
            health_response = await self.client.get("/api/v1/ai/health", headers=headers)
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✅ AIヘルスチェックテスト成功: {health_data.get('status', 'unknown')}")
                
                # モデル一覧取得
                models_response = await self.client.get("/api/v1/ai/models", headers=headers)
                
                if models_response.status_code == 200:
                    print("✅ AIモデル一覧取得テスト成功")
                    
                    # トークン使用量取得
                    usage_response = await self.client.get("/api/v1/ai/usage", headers=headers)
                    
                    if usage_response.status_code == 200:
                        usage_data = usage_response.json()
                        print(f"✅ トークン使用量取得テスト成功: {usage_data.get('tokens_used_today', 0)}トークン使用済み")
                        
                        # コンテンツ検証テスト
                        validate_data = {"text": "こんにちは、テストです。"}
                        validate_response = await self.client.post(
                            "/api/v1/ai/validate-content",
                            headers=headers,
                            json=validate_data
                        )
                        
                        if validate_response.status_code == 200:
                            print("✅ コンテンツ検証テスト成功")
                            return True
                        else:
                            print(f"❌ コンテンツ検証失敗: {validate_response.status_code}")
                            return False
                    else:
                        print(f"❌ 使用量取得失敗: {usage_response.status_code}")
                        return False
                else:
                    print(f"❌ モデル一覧取得失敗: {models_response.status_code}")
                    return False
            else:
                print(f"❌ AIヘルスチェック失敗: {health_response.status_code}")
                print("  ⚠️ AI APIキーが設定されていない可能性があります")
                return False
                
        except Exception as e:
            print(f"❌ AI統合テストエラー: {e}")
            return False
    
    async def test_chat_functionality(self) -> bool:
        """チャット機能テスト"""
        print("🔄 チャット機能テスト中...")
        
        if not self.auth_token:
            print("❌ 認証トークンがありません")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # チャット一覧取得
            chats_response = await self.client.get("/api/v1/chats/", headers=headers)
            
            if chats_response.status_code == 200:
                chats_data = chats_response.json()
                print("✅ チャット一覧取得テスト成功")
                
                # チャット作成テスト
                create_data = {
                    "title": "統合テスト用チャット",
                    "system_prompt": "あなたは親切なAIアシスタントです。"
                }
                
                create_response = await self.client.post(
                    "/api/v1/chats/",
                    headers=headers,
                    json=create_data
                )
                
                if create_response.status_code == 200:
                    chat_data = create_response.json()
                    chat_id = chat_data["id"]
                    print(f"✅ チャット作成テスト成功 (ID: {chat_id})")
                    
                    # チャット詳細取得
                    detail_response = await self.client.get(f"/api/v1/chats/{chat_id}", headers=headers)
                    
                    if detail_response.status_code == 200:
                        print("✅ チャット詳細取得テスト成功")
                        return True
                    else:
                        print(f"❌ チャット詳細取得失敗: {detail_response.status_code}")
                        return False
                else:
                    print(f"❌ チャット作成失敗: {create_response.status_code}")
                    print(f"   エラー: {create_response.text}")
                    return False
            else:
                print(f"❌ チャット一覧取得失敗: {chats_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ チャット機能テストエラー: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """全テスト実行"""
        print("🚀 統合テストを開始します...\n")
        
        setup_success = await self.setup()
        if not setup_success:
            return {"setup": False}
        
        tests = [
            ("ヘルスチェック", self.test_health_check),
            ("認証機能", self.test_authentication),
            ("ユーザー管理", self.test_user_management),
            ("テンプレート管理", self.test_template_management),
            ("AI統合", self.test_ai_integration),
            ("チャット機能", self.test_chat_functionality),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
                print(f"{'✅' if result else '❌'} {test_name}テスト: {'成功' if result else '失敗'}\n")
            except Exception as e:
                results[test_name] = False
                print(f"❌ {test_name}テスト: エラー - {e}\n")
        
        await self.cleanup()
        return results

async def main():
    """メイン処理"""
    tester = IntegrationTester()
    results = await tester.run_all_tests()
    
    print("=" * 50)
    print("📊 テスト結果サマリー")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    for test_name, result in results.items():
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
    
    print(f"\n総テスト数: {total_tests}")
    print(f"成功: {passed_tests}")
    print(f"失敗: {failed_tests}")
    print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests > 0:
        print("\n⚠️  失敗したテストがあります。詳細を確認してください。")
        print("   - データベースが初期化されているか確認してください")
        print("   - アプリケーションサーバーが起動しているか確認してください") 
        print("   - AI APIキーが正しく設定されているか確認してください")
        sys.exit(1)
    else:
        print("\n🎉 全テストが成功しました！")
        print("   secure-ai-chatアプリケーションは正常に動作しています。")

if __name__ == "__main__":
    asyncio.run(main())