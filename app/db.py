from pathlib import Path

import asyncpg

from . import config

pool: asyncpg.Pool | None = None


async def init() -> None:
    global pool
    pool = await asyncpg.create_pool(config.DATABASE_URL, min_size=1, max_size=10)
    for sql in sorted(Path(__file__).parent.parent.joinpath("migrations").glob("*.sql")):
        await pool.execute(sql.read_text())


async def close() -> None:
    if pool:
        await pool.close()
