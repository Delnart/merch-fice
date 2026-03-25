from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        # Ensure recipient_name column exists on orders (migration)
        await conn.execute(text(
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS recipient_name VARCHAR(255)"
        ))
