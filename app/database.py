from sqlalchemy import text
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.settings import settings

async_engine = create_async_engine(
    url=settings.database_url,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_timeout=10,
    pool_recycle=3600,
    connect_args={
        "server_settings": {
            "application_name": "image_",
            "tcp_keepalives_idle": "30",
            "tcp_keepalives_interval": "10",
            "tcp_keepalives_count": "5",
        },
    },
    echo=False,
)


session_gen = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def initialize_db():
    async with async_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def shutdown():
    await async_engine.dispose()


async def get_async_db_session():
    async with session_gen() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
