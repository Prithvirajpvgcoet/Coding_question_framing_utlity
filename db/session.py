import os
from contextlib import asynccontextmanager, contextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine, text

DATABASE_URL      = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/assessment_db")
DATABASE_SYNC_URL = os.getenv("DATABASE_SYNC_URL", "postgresql://postgres:postgres@localhost:5432/assessment_db")

async_engine      = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

sync_engine = create_engine(DATABASE_SYNC_URL, pool_size=5)


@asynccontextmanager
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


@contextmanager
def get_session_sync():
    from sqlalchemy.orm import Session
    with Session(sync_engine) as session:
        yield session


async def set_rls_client(session: AsyncSession, client_id: str):
    """Set the RLS context variable for multi-tenant isolation."""
    await session.execute(
        text("SET LOCAL app.current_client_id = :cid"),
        {"cid": client_id}
    )