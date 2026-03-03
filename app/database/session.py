import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Use the exact URL we verified in your alembic.ini
# Fallback to the Docker service name if the environment variable isn't set
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@db:5432/tennis_analytics"
)

# 1. Create the Async Engine
# echo=True is helpful for debugging SQL, set to False for production
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=20,       # Professional pool size for high-concurrency
    max_overflow=10
)

# 2. Create the Async Session Factory
# expire_on_commit=False prevents 'detached instance' errors in Asyncio
async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

# 3. FastAPI Dependency
# This allows you to use 'db: AsyncSession = Depends(get_db)' in your routes
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
