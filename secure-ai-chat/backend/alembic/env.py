"""
Alembic環境設定

セキュアAIチャット用データベースマイグレーション設定
"""

import asyncio
import os
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# アプリケーションのモデルをインポート
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings
from app.models.base import Base
from app.models.user import User
from app.models.template import PromptTemplate, TemplateCategory
from app.models.chat import Chat, ChatMessage
from app.models.audit import AuditLog

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_url():
    """データベースURLを取得"""
    return os.getenv("DATABASE_URL", "postgresql://sugayayoshiyuki@localhost:5432/secure_ai_chat")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """マイグレーション実行"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    """非同期でマイグレーションを実行"""
    connectable = create_async_engine(
        get_url().replace("postgresql://", "postgresql+asyncpg://"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # 非同期の場合
    if get_url().startswith("postgresql://"):
        asyncio.run(run_async_migrations())
    else:
        # 同期の場合（fallback）
        connectable = create_engine(get_url())
        
        with connectable.connect() as connection:
            do_run_migrations(connection)

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()