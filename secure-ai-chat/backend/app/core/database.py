"""
セキュアAIチャット - データベース設定
"""

from typing import AsyncGenerator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 同期エンジン（マイグレーション用）
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)

# 非同期エンジン（アプリケーション用）
async_engine = create_async_engine(
    settings.database_url_async,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True
)

# セッション設定
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# async_session エイリアス（WebSocket認証で使用）
async_session = AsyncSessionLocal

# ベースモデル
Base = declarative_base()

# メタデータ設定
metadata = MetaData()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """データベースセッション取得"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# エイリアス（互換性のため）
get_database_session = get_db
get_async_db = get_db

async def create_tables():
    """テーブル作成"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_tables():
    """テーブル削除"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)