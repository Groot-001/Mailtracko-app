import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config.settings import config


async def main():
    engine = create_async_engine(config.DATABASE_URL)

    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                """
                SELECT
                    id,
                    email,
                    metadata,
                    subscribed,
                    contact_list_id,
                    organization_id
                FROM contact_contacts
                ORDER BY id DESC
                LIMIT 20
                """
            )
        )

        rows = result.mappings().all()

        for row in rows:
            print(dict(row))

    await engine.dispose()


asyncio.run(main())