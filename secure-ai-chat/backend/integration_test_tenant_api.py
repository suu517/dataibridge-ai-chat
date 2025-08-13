#!/usr/bin/env python3
"""
テナント別API設定の統合テスト
"""
import asyncio
import json
import httpx
from datetime import datetime

class TenantAPIIntegrationTest:
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.test_results = []
    
    async def test_tenant_registration(self):
        """テナント登録テスト"""
        print("🧪 テナント登録テスト開始...")
        
        async with httpx.AsyncClient() as client:
            # テナント登録
            tenant_data = {
                "name": "テストカンパニー",
                "domain": "test-company.example.com",
                "subdomain": "testcompany",
                "admin_email": "admin@test-company.com",
                "admin_name": "テスト管理者",
                "admin_password": "SecurePass123!",
                "plan_type": "starter"
            }
            
            try:
                response = await client.post(f"{self.base_url}/tenants/register", json=tenant_data)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ テナント登録成功: {data.get('message')}")
                    return data
                else:
                    print(f"❌ テナント登録失敗: {response.status_code} - {response.text}")
                    return None
                    
            except Exception as e:
                print(f"❌ テナント登録エラー: {str(e)}")
                return None
    
    async def test_authentication(self, admin_email: str, password: str):
        """認証テスト"""
        print("🧪 認証テスト開始...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/auth/login", json={
                    "username": admin_email,
                    "password": password
                })
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    print("✅ 認証成功")
                    return token
                else:
                    print(f"❌ 認証失敗: {response.status_code} - {response.text}")
                    return None
                    
            except Exception as e:
                print(f"❌ 認証エラー: {str(e)}")
                return None
    
    async def test_api_settings_endpoints(self, token: str):
        """API設定エンドポイントテスト"""
        print("🧪 API設定エンドポイントテスト開始...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                # 現在の設定取得
                response = await client.get(f"{self.base_url}/tenants/ai-settings", headers=headers)
                
                if response.status_code == 200:
                    settings = response.json()
                    print("✅ API設定取得成功")
                    print(f"   プロバイダー: {settings.get('ai_provider')}")
                    print(f"   システムデフォルト: {settings.get('use_system_default')}")
                else:
                    print(f"❌ API設定取得失敗: {response.status_code}")
                    return False
                
                # 使用量統計取得
                response = await client.get(f"{self.base_url}/tenants/usage-stats", headers=headers)
                
                if response.status_code == 200:
                    stats = response.json()
                    print("✅ 使用量統計取得成功")
                    print(f"   今日の使用量: {stats.get('daily_tokens')} トークン")
                    print(f"   月間制限: {stats.get('monthly_limit')} トークン")
                else:
                    print(f"❌ 使用量統計取得失敗: {response.status_code}")
                    return False
                
                return True
                
            except Exception as e:
                print(f"❌ API設定エンドポイントエラー: {str(e)}")
                return False
    
    async def test_ai_settings_update(self, token: str):
        """AI設定更新テスト"""
        print("🧪 AI設定更新テスト開始...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                # システムデフォルトに設定
                update_data = {
                    "provider": "system_default"
                }
                
                response = await client.post(
                    f"{self.base_url}/tenants/ai-settings", 
                    json=update_data, 
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ AI設定更新成功")
                    print(f"   メッセージ: {result.get('message')}")
                    return True
                else:
                    print(f"❌ AI設定更新失敗: {response.status_code} - {response.text}")
                    return False
                
            except Exception as e:
                print(f"❌ AI設定更新エラー: {str(e)}")
                return False
    
    async def test_invalid_api_settings(self, token: str):
        """不正なAPI設定のバリデーションテスト"""
        print("🧪 不正なAPI設定バリデーションテスト開始...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                # 不正なOpenAI設定
                invalid_data = {
                    "provider": "openai",
                    "openai_settings": {
                        "api_key": "invalid_key",  # sk-で始まらない
                        "model": "gpt-4"
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/tenants/ai-settings", 
                    json=invalid_data, 
                    headers=headers
                )
                
                if response.status_code == 400:
                    error = response.json()
                    print("✅ 不正なAPI設定が正しく拒否されました")
                    print(f"   エラー: {error.get('detail')}")
                    return True
                else:
                    print(f"❌ 不正なAPI設定が受け入れられました: {response.status_code}")
                    return False
                
            except Exception as e:
                print(f"❌ バリデーションテストエラー: {str(e)}")
                return False
    
    async def test_database_migration(self):
        """データベースマイグレーション確認テスト"""
        print("🧪 データベースマイグレーション確認テスト開始...")
        
        import subprocess
        import os
        
        try:
            # 現在のディレクトリを取得
            current_dir = os.getcwd()
            backend_dir = "/Users/sugayayoshiyuki/Desktop/secure-ai-chat/backend"
            
            # バックエンドディレクトリに移動してマイグレーション状況確認
            result = subprocess.run(
                ["source", "venv/bin/activate", "&&", "alembic", "current"],
                shell=True,
                cwd=backend_dir,
                capture_output=True,
                text=True
            )
            
            if "add_ai_settings_to_tenant" in result.stdout:
                print("✅ データベースマイグレーション確認成功")
                print(f"   現在のマイグレーション: add_ai_settings_to_tenant")
                return True
            else:
                print(f"❌ マイグレーション確認失敗: {result.stdout}")
                return False
                
        except Exception as e:
            print(f"❌ マイグレーション確認エラー: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """全テストを実行"""
        print("🚀 テナント別API設定統合テスト開始")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # データベースマイグレーション確認
        migration_ok = await self.test_database_migration()
        self.test_results.append(("データベースマイグレーション", migration_ok))
        
        print("\n" + "-" * 60)
        
        # テナント登録（既存の場合はスキップ）
        tenant_data = await self.test_tenant_registration()
        tenant_ok = tenant_data is not None
        self.test_results.append(("テナント登録", tenant_ok))
        
        if not tenant_ok:
            print("❌ テナント登録に失敗したため、以降のテストをスキップします")
            return self.print_summary(start_time)
        
        print("\n" + "-" * 60)
        
        # 認証テスト
        token = await self.test_authentication("admin@test-company.com", "SecurePass123!")
        auth_ok = token is not None
        self.test_results.append(("認証", auth_ok))
        
        if not auth_ok:
            print("❌ 認証に失敗したため、以降のテストをスキップします")
            return self.print_summary(start_time)
        
        print("\n" + "-" * 60)
        
        # API設定エンドポイントテスト
        endpoints_ok = await self.test_api_settings_endpoints(token)
        self.test_results.append(("API設定エンドポイント", endpoints_ok))
        
        print("\n" + "-" * 60)
        
        # AI設定更新テスト
        update_ok = await self.test_ai_settings_update(token)
        self.test_results.append(("AI設定更新", update_ok))
        
        print("\n" + "-" * 60)
        
        # バリデーションテスト
        validation_ok = await self.test_invalid_api_settings(token)
        self.test_results.append(("バリデーション", validation_ok))
        
        print("\n" + "=" * 60)
        self.print_summary(start_time)
    
    def print_summary(self, start_time):
        """テスト結果サマリー表示"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("📊 テスト結果サマリー")
        print(f"実行時間: {duration:.2f}秒")
        print()
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print()
        print(f"結果: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 全テストに成功しました！")
        else:
            print("⚠️  一部のテストが失敗しました")
        
        return failed == 0

async def main():
    """メイン実行関数"""
    test = TenantAPIIntegrationTest()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())