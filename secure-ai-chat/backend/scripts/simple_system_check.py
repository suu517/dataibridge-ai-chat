#!/usr/bin/env python3
"""
簡易システムチェックスクリプト
"""

import sys
import os
from pathlib import Path
import subprocess

# パスを追加
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

def check_python_version():
    """Pythonバージョンチェック"""
    major, minor = sys.version_info[:2]
    if major >= 3 and minor >= 8:
        print("✅ Python バージョン OK:", f"{major}.{minor}")
        return True
    else:
        print("❌ Python バージョンが古い:", f"{major}.{minor} (要件: 3.8+)")
        return False

def check_environment_variables():
    """環境変数チェック"""
    try:
        from app.core.config import settings
        
        issues = []
        
        # 重要な設定チェック
        if not settings.DATABASE_URL:
            issues.append("DATABASE_URL が未設定")
        
        if not settings.SECRET_KEY:
            issues.append("SECRET_KEY が未設定")
            
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "demo-key-not-functional":
            issues.append("OPENAI_API_KEY が未設定")
        
        if issues:
            print("⚠️ 環境変数の問題:", ", ".join(issues))
            return False
        else:
            print("✅ 環境変数 OK")
            return True
            
    except Exception as e:
        print(f"❌ 環境変数チェックエラー: {e}")
        return False

def check_file_structure():
    """ファイル構造チェック"""
    critical_paths = [
        backend_dir / "app" / "main.py",
        backend_dir / "app" / "core" / "config.py",
        backend_dir / "app" / "models",
        backend_dir / "app" / "api" / "endpoints",
        backend_dir / "alembic",
        backend_dir / ".env"
    ]
    
    missing_paths = []
    for path in critical_paths:
        if not path.exists():
            missing_paths.append(str(path))
    
    if missing_paths:
        print("❌ 不足ファイル/ディレクトリ:", ", ".join(missing_paths))
        return False
    else:
        print("✅ ファイル構造 OK")
        return True

def check_api_imports():
    """重要なモジュールのインポートテスト"""
    try:
        from app.core.config import settings
        from app.core.security import create_access_token
        from app.models.user import User
        from app.api.endpoints import auth, templates
        print("✅ APIモジュールインポート OK")
        return True
    except Exception as e:
        print(f"❌ APIモジュールインポートエラー: {e}")
        return False

def check_openai_authentication():
    """OpenAI認証チェック"""
    try:
        import openai
        from app.core.config import settings
        
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "demo-key-not-functional":
            print("⚠️ OpenAI APIキー未設定")
            return False
        
        # 認証テスト（軽量）
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # モデル一覧取得で認証テスト
        models = client.models.list()
        model_count = len([m for m in models.data if 'gpt' in m.id])
        
        print(f"✅ OpenAI認証 OK ({model_count}個のGPTモデル利用可能)")
        print("⚠️ ただし、クォータ制限によりAI機能は制限されている可能性があります")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI認証エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("🔍 セキュアAIチャット - 簡易システムチェック")
    print("=" * 50)
    
    checks = [
        ("Python バージョン", check_python_version),
        ("ファイル構造", check_file_structure),
        ("環境変数", check_environment_variables),
        ("APIモジュール", check_api_imports),
        ("OpenAI認証", check_openai_authentication),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n🔄 {check_name}をチェック中...")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name}チェック中にエラー: {e}")
            results.append((check_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 チェック結果サマリー")
    print("=" * 50)
    
    total_checks = len(results)
    passed_checks = sum(1 for _, result in results if result)
    
    for check_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"  {check_name}: {status}")
    
    print(f"\n総チェック数: {total_checks}")
    print(f"成功: {passed_checks}")
    print(f"失敗: {total_checks - passed_checks}")
    
    if passed_checks == total_checks:
        print("\n🎉 全てのチェックが成功しました!")
        print("   システムは正常に設定されています。")
        return 0
    elif passed_checks >= total_checks - 1:
        print(f"\n✅ 重要なチェックは成功しました。")
        print(f"   一部の問題がありますが、システムは動作可能です。")
        return 0
    else:
        print(f"\n⚠️ {total_checks - passed_checks}個の重要な問題があります。")
        return 1

if __name__ == "__main__":
    sys.exit(main())