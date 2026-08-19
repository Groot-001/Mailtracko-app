import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection

from src.core.config.settings import config as app_config
from src.shared.infrastructure.db import Base

# Import all models so Alembic can detect them
from src.modules.auth.infrastructure.models.user_model import UserModel  # noqa: F401
from src.modules.auth.infrastructure.models.user_account_model import UserAccountModel  # noqa: F401
from src.modules.auth.infrastructure.models.user_token_model import UserTokenModel  # noqa: F401

from src.modules.auth.infrastructure.models.user_session_model import UserSessionModel  # noqa: F401
from src.modules.campaign.infrastructure.models.campaign_models import *  # noqa: F401,F403
from src.modules.platform.infrastructure.models.platform_models import *  # noqa: F401,F403


config = context.config
config.set_main_option(
    "sqlalchemy.url",
    app_config.DATABASE_URL.replace("%", "%%"),
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    from sqlalchemy.ext.asyncio import create_async_engine
    connectable = create_async_engine(app_config.DATABASE_URL, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online():
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
