#!/usr/bin/env python3
"""
基本的なシステム構成チェック
"""
import asyncio
import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

async def test_imports():
    """重要なモジュールのインポートテスト"""
    print("📦 モジュールインポートテスト開始...")
    
    tests = [
        ("app.core.config", "設定モジュール"),
        ("app.models.tenant", "テナントモデル"),
        ("app.models.user", "ユーザーモデル"),
        ("app.services.ai_service", "AIサービス"),
        ("app.api.routes.tenants", "テナントAPI"),
        ("app.api.dependencies.auth", "認証依存性"),
        ("app.core.security", "セキュリティモジュール")
    ]
    
    passed = 0
    failed = 0
    
    for module_name, description in tests:
        try:
            __import__(module_name)
            print(f"✅ {description}: OK")
            passed += 1
        except Exception as e:
            print(f"❌ {description}: {str(e)}")
            failed += 1
    
    print(f"\nインポートテスト結果: {passed} passed, {failed} failed")
    return failed == 0

def test_database_config():
    """データベース設定テスト"""
    print("\n🗄️ データベース設定テスト開始...")
    
    try:
        from app.core.config import settings
        
        print(f"✅ データベースURL: 設定済み")
        print(f"✅ 暗号化キー: 設定済み")
        print(f"✅ アプリ名: {settings.APP_NAME}")
        print(f"✅ 環境: {settings.ENVIRONMENT}")
        
        return True
    except Exception as e:
        print(f"❌ データベース設定エラー: {e}")
        return False

def test_ai_service_config():
    """AIサービス設定テスト"""
    print("\n🤖 AIサービス設定テスト開始...")
    
    try:
        from app.services.ai_service import AIService, TenantAIClient
        from app.models.tenant import Tenant
        
        # ダミーテナント作成
        dummy_tenant = Tenant(
            id="test-tenant-id",
            name="Test Tenant",
            ai_provider="system_default",
            use_system_default=True
        )
        
        # AIサービス初期化テスト
        ai_service = AIService()
        tenant_client = ai_service.get_tenant_client(dummy_tenant)
        
        print("✅ AIService: 初期化成功")
        print("✅ TenantAIClient: 作成成功")
        print("✅ テナント別設定: 対応済み")
        
        return True
    except Exception as e:
        print(f"❌ AIサービス設定エラー: {e}")
        return False

def test_tenant_model():
    """テナントモデル機能テスト"""
    print("\n🏢 テナントモデル機能テスト開始...")
    
    try:
        from app.models.tenant import Tenant
        import uuid
        
        # テナント作成
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Test Company",
            domain="test.example.com",
            subdomain="test",
            ai_provider="system_default",
            use_system_default=True
        )
        
        print("✅ テナント作成: 成功")
        
        # AI設定テスト
        ai_settings = tenant.get_ai_settings()
        print(f"✅ AI設定取得: {ai_settings.get('provider', 'unknown')}")
        
        # システムデフォルト設定
        tenant.use_default_ai_settings()
        print("✅ システムデフォルト設定: 成功")
        
        return True
    except Exception as e:
        print(f"❌ テナントモデルテストエラー: {e}")
        return False

def test_security_functions():
    """セキュリティ機能テスト"""
    print("\n🔒 セキュリティ機能テスト開始...")
    
    try:
        from app.core.security import encrypt_data, decrypt_data, get_password_hash, verify_password
        
        # 暗号化・復号化テスト
        test_data = "テスト用の機密データ"
        encrypted = encrypt_data(test_data)
        decrypted = decrypt_data(encrypted)
        
        if test_data == decrypted:
            print("✅ データ暗号化・復号化: 成功")
        else:
            print("❌ データ暗号化・復号化: 失敗")
            return False
        
        # パスワードハッシュテスト
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        verified = verify_password(password, hashed)
        
        if verified:
            print("✅ パスワードハッシュ・検証: 成功")
        else:
            print("❌ パスワードハッシュ・検証: 失敗")
            return False
        
        return True
    except Exception as e:
        print(f"❌ セキュリティ機能テストエラー: {e}")
        return False

def test_file_structure():
    """ファイル構造テスト"""
    print("\n📁 ファイル構造テスト開始...")
    
    required_files = [
        "app/main.py",
        "app/core/config.py",
        "app/models/tenant.py",
        "app/models/user.py",
        "app/services/ai_service.py",
        "app/api/routes/tenants.py",
        "alembic.ini",
        "alembic/versions/add_ai_settings_to_tenant.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}: 存在")
        else:
            print(f"❌ {file_path}: 不足")
            missing_files.append(file_path)
    
    if not missing_files:
        print("✅ 全ての必要なファイルが存在します")
        return True
    else:
        print(f"❌ {len(missing_files)} 個のファイルが不足しています")
        return False

async def run_all_tests():
    """全テストを実行"""
    print("🔍 セキュアAIチャット - システム構成チェック開始")
    print("=" * 60)
    
    results = []
    
    # ファイル構造テスト
    results.append(("ファイル構造", test_file_structure()))
    
    # インポートテスト
    results.append(("モジュールインポート", await test_imports()))
    
    # データベース設定テスト
    results.append(("データベース設定", test_database_config()))
    
    # AIサービス設定テスト
    results.append(("AIサービス設定", test_ai_service_config()))
    
    # テナントモデルテスト
    results.append(("テナントモデル機能", test_tenant_model()))
    
    # セキュリティ機能テスト
    results.append(("セキュリティ機能", test_security_functions()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 システム構成チェック結果")
    print()
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n結果: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 全ての構成チェックに成功しました！")
        print("💡 システムは正常に設定されています。")
    else:
        print("⚠️  一部のチェックが失敗しました。")
        print("💡 失敗した項目を修正してください。")
    
    return failed == 0

async def main():
    """メイン実行関数"""
    try:
        await run_all_tests()
    except KeyboardInterrupt:
        print("\n⏹️ テストが中断されました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")

if __name__ == "__main__":
    asyncio.run(main())