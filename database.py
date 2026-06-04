import asyncpg
import os
from config import DATABASE_URL # Railway'dan olingan URL

async def get_db_pool():
    return await asyncpg.create_pool(DATABASE_URL)

async def init_db():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                age INT,
                gender TEXT,
                region TEXT,
                is_premium BOOLEAN DEFAULT FALSE
            )
        ''')
    await pool.close()
