import os
import sys
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import selectors

import os
import sys

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))



# All the models are imported into database.base, then imported into here for Alembic to see
from app.models.base import Base
target_metadata = Base.metadata

# Setting up logging of alembic migrations to the terminal
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the database URL from the DATABASE_URL env var (set in docker-compose.yml)
db_url = os.environ.get("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# Function to handle migrations
def do_run_migrations(connection):
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations() -> None:
    # Run migrations in 'online' mode using an Async Engine.
    # Build configuration with our DATABASE_URL
    configuration = config.get_section(config.config_ini_section, {})
    
    # Creating asynchronous connection engine, remember alembic is synchronous on it's own
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Opening the asynchronous connection
    async with connectable.connect() as connection:
        # Feeding in the synchronous migration function 
        await connection.run_sync(do_run_migrations)

    # Closing the connection engine
    await connectable.dispose()

# Creating an asyncio event loop and runnging the loop until completion
loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(run_migrations())
finally:
    loop.close()
