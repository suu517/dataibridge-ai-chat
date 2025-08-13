#!/usr/bin/env python3
"""
セキュアAIチャット - データベース管理スクリプト
"""

import asyncio
import sys
import os
from pathlib import Path
import logging

# パスを追加してアプリケーションモジュールをインポート可能に
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.exc import ProgrammingError
import asyncpg
from alembic.config import Config
from alembic import command as alembic_command

from app.core.config import settings
from app.core.database import get_db, Base
from app.models.user import User, UserRole, UserStatus
from app.models.template import TemplateCategory
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self):
        self.sync_db_url = settings.DATABASE_URL
        self.async_db_url = settings.database_url_async
        self.alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    
    async def create_database(self):
        """データベースを作成（存在しない場合）"""
        print("🔄 データベースの作成チェック中...")
        
        # PostgreSQLの場合、管理者データベースに接続してDBを作成
        if self.sync_db_url.startswith('postgresql'):
            # データベース名を抽出
            db_name = self.sync_db_url.split('/')[-1]
            admin_url = self.sync_db_url.rsplit('/', 1)[0] + '/postgres'
            
            try:
                # 管理者データベースに接続
                admin_engine = create_engine(admin_url)
                
                with admin_engine.connect() as conn:
                    # データベース存在確認
                    result = conn.execute(
                        text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
                    )
                    
                    if not result.fetchone():
                        # 自動コミットモードで実行
                        conn.execute(text("COMMIT"))
                        conn.execute(text(f"CREATE DATABASE {db_name}"))
                        print(f"✅ データベース '{db_name}' を作成しました")
                    else:
                        print(f"ℹ️ データベース '{db_name}' は既に存在します")
                
                admin_engine.dispose()
                
            except Exception as e:
                print(f"❌ データベース作成エラー: {e}")
                return False
        
        return True
    
    async def run_migrations(self):
        """マイグレーション実行"""
        print("🔄 マイグレーションを実行中...")
        
        try:
            # Alembicでマイグレーション実行
            alembic_command.upgrade(self.alembic_cfg, "head")
            print("✅ マイグレーション完了")
            return True
        except Exception as e:
            print(f"❌ マイグレーションエラー: {e}")
            return False
    
    async def create_initial_data(self):
        """初期データ作成"""
        print("🔄 初期データを作成中...")
        
        async_engine = create_async_engine(self.async_db_url)
        
        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # セッション作成
            async_session = AsyncSession(async_engine)
            
            try:
                # 管理者ユーザーを作成
                admin_user = User(
                    username="admin",
                    email="admin@company.com",
                    password_hash=get_password_hash("admin123"),
                    full_name="System Administrator",
                    department="IT",
                    position="Administrator",
                    role=UserRole.ADMIN,
                    status=UserStatus.ACTIVE,
                    is_active=True,
                    email_verified=True,
                    login_attempts=0,
                    two_fa_enabled=False
                )
                
                # 既存チェック
                existing_admin = await async_session.execute(
                    text("SELECT id FROM users WHERE username = 'admin' OR email = 'admin@company.com'")
                )
                
                if not existing_admin.fetchone():
                    async_session.add(admin_user)
                    await async_session.commit()
                    print("✅ 管理者ユーザー作成完了 (username: admin, password: admin123)")
                else:
                    print("ℹ️ 管理者ユーザーは既に存在します")
                
                # デフォルトテンプレートカテゴリ作成
                default_categories = [
                    {
                        "name": "ビジネス",
                        "description": "ビジネス関連のプロンプトテンプレート",
                        "icon": "briefcase",
                        "color": "#3b82f6",
                        "sort_order": 1
                    },
                    {
                        "name": "技術",
                        "description": "技術関連のプロンプトテンプレート", 
                        "icon": "code",
                        "color": "#10b981",
                        "sort_order": 2
                    },
                    {
                        "name": "教育",
                        "description": "教育・学習関連のプロンプトテンプレート",
                        "icon": "academic-cap",
                        "color": "#f59e0b",
                        "sort_order": 3
                    },
                    {
                        "name": "クリエイティブ",
                        "description": "創作活動関連のプロンプトテンプレート",
                        "icon": "sparkles",
                        "color": "#8b5cf6",
                        "sort_order": 4
                    }
                ]
                
                for category_data in default_categories:
                    existing_category = await async_session.execute(
                        text(f"SELECT id FROM template_categories WHERE name = '{category_data['name']}'")
                    )
                    
                    if not existing_category.fetchone():
                        category = TemplateCategory(**category_data, is_active=True)
                        async_session.add(category)
                
                await async_session.commit()
                print("✅ デフォルトカテゴリ作成完了")
                
            except Exception as e:
                await async_session.rollback()
                print(f"❌ 初期データ作成エラー: {e}")
                return False
            finally:
                await async_session.close()
        
        except Exception as e:
            print(f"❌ データベース接続エラー: {e}")
            return False
        finally:
            await async_engine.dispose()
        
        return True
    
    async def reset_database(self):
        """データベースをリセット"""
        print("🔄 データベースをリセット中...")
        
        async_engine = create_async_engine(self.async_db_url)
        
        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                print("✅ 全テーブル削除完了")
                
                await conn.run_sync(Base.metadata.create_all)
                print("✅ テーブル再作成完了")
        
        except Exception as e:
            print(f"❌ データベースリセットエラー: {e}")
            return False
        finally:
            await async_engine.dispose()
        
        return True
    
    async def check_connection(self):
        """データベース接続テスト"""
        print("🔄 データベース接続をテスト中...")
        
        try:
            async_engine = create_async_engine(self.async_db_url)
            
            async with async_engine.connect() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ データベース接続成功: {version}")
            
            await async_engine.dispose()
            return True
            
        except Exception as e:
            print(f"❌ データベース接続エラー: {e}")
            return False
    
    def generate_migration(self, message: str):
        """新しいマイグレーションを生成"""
        print(f"🔄 マイグレーションを生成中: {message}")
        
        try:
            alembic_command.revision(
                self.alembic_cfg, 
                message=message, 
                autogenerate=True
            )
            print("✅ マイグレーション生成完了")
            return True
        except Exception as e:
            print(f"❌ マイグレーション生成エラー: {e}")
            return False

async def main():
    """メイン処理"""
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python db_manage.py init        # データベース初期化")
        print("  python db_manage.py migrate     # マイグレーション実行")
        print("  python db_manage.py reset       # データベースリセット")
        print("  python db_manage.py check       # 接続テスト")
        print("  python db_manage.py generate <message>  # マイグレーション生成")
        return
    
    command = sys.argv[1]
    db_manager = DatabaseManager()
    
    if command == "init":
        print("🚀 データベース初期化を開始...")
        
        success = True
        success &= await db_manager.create_database()
        success &= await db_manager.run_migrations()
        success &= await db_manager.create_initial_data()
        
        if success:
            print("🎉 データベース初期化完了!")
            print("\n管理者ログイン情報:")
            print("  ユーザー名: admin")
            print("  パスワード: admin123")
            print("  ⚠️ 本番環境では必ずパスワードを変更してください")
        else:
            print("❌ データベース初期化に失敗しました")
            sys.exit(1)
    
    elif command == "migrate":
        success = await db_manager.run_migrations()
        if not success:
            sys.exit(1)
    
    elif command == "reset":
        confirm = input("⚠️ 全データが削除されます。続行しますか? (y/N): ")
        if confirm.lower() == 'y':
            success = await db_manager.reset_database()
            if success:
                print("✅ データベースリセット完了")
            else:
                sys.exit(1)
        else:
            print("キャンセルされました")
    
    elif command == "check":
        success = await db_manager.check_connection()
        if not success:
            sys.exit(1)
    
    elif command == "generate":
        if len(sys.argv) < 3:
            print("❌ マイグレーションメッセージが必要です")
            print("使用例: python db_manage.py generate 'Add user table'")
            sys.exit(1)
        
        message = sys.argv[2]
        success = db_manager.generate_migration(message)
        if not success:
            sys.exit(1)
    
    else:
        print(f"❌ 未知のコマンド: {command}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())