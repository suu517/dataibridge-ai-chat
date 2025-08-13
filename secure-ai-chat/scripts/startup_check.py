#!/usr/bin/env python3
"""
セキュアAIチャット - 起動前システムチェック
"""

import asyncio
import sys
import os
from pathlib import Path
import logging
import subprocess
from typing import Dict, List, Tuple, Any
import psutil
import socket

# パスを追加
project_root = Path(__file__).parent.parent
backend_dir = project_root / "backend"
frontend_dir = project_root / "frontend"

sys.path.append(str(backend_dir))

try:
    from backend.app.core.config import settings
except ImportError:
    print("❌ バックエンドモジュールのインポートに失敗しました")
    sys.exit(1)

class SystemChecker:
    """システムチェッククラス"""
    
    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []
    
    def add_check(self, name: str, status: bool, message: str, severity: str = "info"):
        """チェック結果を追加"""
        self.checks.append({
            "name": name,
            "status": status,
            "message": message,
            "severity": severity
        })
        
        if severity == "error" and not status:
            self.errors.append(f"{name}: {message}")
        elif severity == "warning" and not status:
            self.warnings.append(f"{name}: {message}")
    
    def check_python_version(self) -> bool:
        """Pythonバージョンチェック"""
        major, minor = sys.version_info[:2]
        required_major, required_minor = 3, 8
        
        if major >= required_major and minor >= required_minor:
            self.add_check(
                "Python バージョン",
                True,
                f"Python {major}.{minor} (要件: Python {required_major}.{required_minor}+)"
            )
            return True
        else:
            self.add_check(
                "Python バージョン",
                False,
                f"Python {major}.{minor} は古すぎます (要件: Python {required_major}.{required_minor}+)",
                "error"
            )
            return False
    
    def check_required_packages(self) -> bool:
        """必須パッケージチェック"""
        required_packages = [
            "fastapi", "sqlalchemy", "asyncpg", "uvicorn",
            "alembic", "httpx", "pydantic", "python-jose",
            "passlib", "cryptography", "redis", "psutil"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if not missing_packages:
            self.add_check(
                "必須パッケージ",
                True,
                f"全ての必須パッケージが利用可能 ({len(required_packages)}個)"
            )
            return True
        else:
            self.add_check(
                "必須パッケージ",
                False,
                f"不足パッケージ: {', '.join(missing_packages)}",
                "error"
            )
            return False
    
    def check_environment_variables(self) -> bool:
        """環境変数チェック"""
        critical_vars = ["DATABASE_URL"]
        recommended_vars = [
            "SECRET_KEY", "JWT_SECRET_KEY", "ENCRYPTION_KEY",
            "AZURE_OPENAI_API_KEY", "OPENAI_API_KEY"
        ]
        
        missing_critical = []
        missing_recommended = []
        
        for var in critical_vars:
            value = os.getenv(var) or getattr(settings, var, None)
            if not value:
                missing_critical.append(var)
        
        for var in recommended_vars:
            value = os.getenv(var) or getattr(settings, var, None)
            if not value:
                missing_recommended.append(var)
        
        if not missing_critical:
            self.add_check(
                "必須環境変数",
                True,
                "全ての必須環境変数が設定済み"
            )
            
            if missing_recommended:
                self.add_check(
                    "推奨環境変数",
                    False,
                    f"未設定の推奨変数: {', '.join(missing_recommended)}",
                    "warning"
                )
            else:
                self.add_check(
                    "推奨環境変数",
                    True,
                    "全ての推奨環境変数が設定済み"
                )
            
            return True
        else:
            self.add_check(
                "必須環境変数",
                False,
                f"未設定の必須変数: {', '.join(missing_critical)}",
                "error"
            )
            return False
    
    def check_database_connection(self) -> bool:
        """データベース接続チェック"""
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.ext.asyncio import create_async_engine
            
            # 同期エンジンでのテスト
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            engine.dispose()
            
            self.add_check(
                "データベース接続",
                True,
                "データベースへの接続が正常"
            )
            return True
            
        except Exception as e:
            self.add_check(
                "データベース接続",
                False,
                f"データベース接続エラー: {str(e)}",
                "error"
            )
            return False
    
    def check_redis_connection(self) -> bool:
        """Redis接続チェック"""
        try:
            import redis
            
            # Redis URLを解析
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)
            r.ping()
            r.close()
            
            self.add_check(
                "Redis接続",
                True,
                "Redisへの接続が正常"
            )
            return True
            
        except Exception as e:
            self.add_check(
                "Redis接続",
                False,
                f"Redis接続エラー: {str(e)}",
                "warning"
            )
            return False
    
    def check_file_permissions(self) -> bool:
        """ファイル権限チェック"""
        critical_paths = [
            backend_dir,
            backend_dir / "app",
            backend_dir / "alembic",
            frontend_dir if frontend_dir.exists() else None
        ]
        
        issues = []
        
        for path in critical_paths:
            if path and path.exists():
                try:
                    # 読み取り権限チェック
                    if not os.access(path, os.R_OK):
                        issues.append(f"{path}: 読み取り権限なし")
                    
                    # 書き込み権限チェック (ログディレクトリなど)
                    if path == backend_dir and not os.access(path, os.W_OK):
                        issues.append(f"{path}: 書き込み権限なし")
                
                except Exception as e:
                    issues.append(f"{path}: 権限チェックエラー - {e}")
        
        if not issues:
            self.add_check(
                "ファイル権限",
                True,
                "必要なファイル・ディレクトリへのアクセス権限が正常"
            )
            return True
        else:
            self.add_check(
                "ファイル権限",
                False,
                f"権限の問題: {'; '.join(issues)}",
                "error"
            )
            return False
    
    def check_port_availability(self) -> bool:
        """ポート使用可能性チェック"""
        ports_to_check = [
            (8000, "バックエンドAPI"),
            (3000, "フロントエンド"),
        ]
        
        unavailable_ports = []
        
        for port, description in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    unavailable_ports.append(f"ポート{port} ({description})")
            except Exception:
                pass
            finally:
                sock.close()
        
        if not unavailable_ports:
            self.add_check(
                "ポート使用可能性",
                True,
                "必要なポートが全て使用可能"
            )
            return True
        else:
            self.add_check(
                "ポート使用可能性",
                False,
                f"使用中のポート: {', '.join(unavailable_ports)}",
                "warning"
            )
            return False
    
    def check_system_resources(self) -> bool:
        """システムリソースチェック"""
        # メモリチェック
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        if available_gb < 1.0:
            self.add_check(
                "メモリ使用可能量",
                False,
                f"使用可能メモリが少ない: {available_gb:.1f}GB (推奨: 1GB以上)",
                "warning"
            )
        else:
            self.add_check(
                "メモリ使用可能量",
                True,
                f"使用可能メモリ: {available_gb:.1f}GB"
            )
        
        # ディスク容量チェック
        disk = psutil.disk_usage(str(project_root))
        free_gb = disk.free / (1024**3)
        
        if free_gb < 1.0:
            self.add_check(
                "ディスク容量",
                False,
                f"ディスク容量が少ない: {free_gb:.1f}GB (推奨: 1GB以上)",
                "warning"
            )
        else:
            self.add_check(
                "ディスク容量",
                True,
                f"使用可能ディスク容量: {free_gb:.1f}GB"
            )
        
        return True
    
    def check_security_configuration(self) -> bool:
        """セキュリティ設定チェック"""
        issues = []
        
        # プロダクション環境での設定チェック
        if settings.is_production:
            if not settings.SSL_CERT_PATH or not settings.SSL_KEY_PATH:
                issues.append("SSL証明書が設定されていません")
            
            if settings.DEBUG:
                issues.append("本番環境でDEBUGモードが有効です")
            
            if not settings.SECRET_KEY or settings.SECRET_KEY == "your-super-secret-key-change-this-in-production":
                issues.append("デフォルトのSECRET_KEYが使用されています")
        
        # AI API設定チェック
        if not settings.use_azure_openai and not getattr(settings, 'OPENAI_API_KEY', None):
            issues.append("AI APIキーが設定されていません")
        
        if not issues:
            self.add_check(
                "セキュリティ設定",
                True,
                "セキュリティ設定が適切です"
            )
            return True
        else:
            severity = "error" if settings.is_production else "warning"
            self.add_check(
                "セキュリティ設定",
                False,
                f"セキュリティ問題: {'; '.join(issues)}",
                severity
            )
            return False
    
    def run_all_checks(self) -> Dict[str, Any]:
        """全チェック実行"""
        print("🔍 システムチェックを実行中...\n")
        
        checks_to_run = [
            self.check_python_version,
            self.check_required_packages,
            self.check_environment_variables,
            self.check_database_connection,
            self.check_redis_connection,
            self.check_file_permissions,
            self.check_port_availability,
            self.check_system_resources,
            self.check_security_configuration,
        ]
        
        results = []
        
        for check_func in checks_to_run:
            try:
                check_func()
            except Exception as e:
                self.add_check(
                    check_func.__name__.replace('check_', '').replace('_', ' ').title(),
                    False,
                    f"チェック中にエラーが発生: {str(e)}",
                    "error"
                )
        
        return {
            "checks": self.checks,
            "warnings": self.warnings,
            "errors": self.errors
        }
    
    def print_results(self):
        """結果を出力"""
        print("=" * 60)
        print("📊 システムチェック結果")
        print("=" * 60)
        
        for check in self.checks:
            status_icon = "✅" if check["status"] else "❌"
            
            if check["severity"] == "warning":
                status_icon = "⚠️"
            
            print(f"{status_icon} {check['name']}: {check['message']}")
        
        print(f"\n総チェック数: {len(self.checks)}")
        print(f"成功: {sum(1 for c in self.checks if c['status'])}")
        print(f"警告: {len(self.warnings)}")
        print(f"エラー: {len(self.errors)}")
        
        if self.errors:
            print(f"\n❌ 以下のエラーを修正してください:")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"\n⚠️  以下の警告を確認してください:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if not self.errors and not self.warnings:
            print(f"\n🎉 全てのチェックが成功しました！")
            print(f"   システムは起動準備完了です。")
        elif not self.errors:
            print(f"\n✅ 重要なエラーはありませんが、警告を確認してください。")
        else:
            print(f"\n❌ エラーが検出されました。修正後に再度チェックを実行してください。")

def main():
    """メイン処理"""
    print("🚀 セキュアAIチャット - システム起動チェック")
    print(f"プロジェクトルート: {project_root}")
    print(f"環境: {getattr(settings, 'ENVIRONMENT', 'unknown')}")
    print()
    
    checker = SystemChecker()
    results = checker.run_all_checks()
    checker.print_results()
    
    # 終了コード設定
    if checker.errors:
        sys.exit(1)
    elif checker.warnings:
        sys.exit(2)  # 警告あり
    else:
        sys.exit(0)  # 全て正常

if __name__ == "__main__":
    main()