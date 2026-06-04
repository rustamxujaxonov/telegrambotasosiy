import asyncpg
import logging
from datetime import datetime, timedelta
from config import DATABASE_URL

logger = logging.getLogger(__name__)
pool = None

async def init_db():
    global pool
    try:
        pool = await asyncpg.create_pool(DATABASE_URL)
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    full_name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    gender TEXT NOT NULL,
                    region TEXT NOT NULL,
                    is_premium BOOLEAN DEFAULT FALSE,
                    premium_until TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS chats (
                    id SERIAL PRIMARY KEY,
                    user1_id BIGINT NOT NULL,
                    user2_id BIGINT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                );
                CREATE TABLE IF NOT EXISTS premium_requests (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    plan_key TEXT NOT NULL,
                    photo_file_id TEXT,
                    status TEXT DEFAULT 'pending',
                    admin_msg_id BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS search_queue (
                    user_id BIGINT PRIMARY KEY,
                    gender_want TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        logger.info("✅ PostgreSQL bazasi tayyor")
    except Exception as e:
        logger.error(f"❌ Baza xatosi: {e}")

# ─── FOYDALANUVCHI ──────────────────────────────────────────────────────────────

async def get_user(user_id: int):
    return await pool.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)

async def create_user(user_id: int, username: str, full_name: str, age: int, gender: str, region: str):
    await pool.execute("""
        INSERT INTO users (user_id, username, full_name, age, gender, region)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (user_id) DO UPDATE SET 
        username=$2, full_name=$3, age=$4, gender=$5, region=$6
    """, user_id, username, full_name, age, gender, region)

async def update_user(user_id: int, **kwargs):
    for k, v in kwargs.items():
        await pool.execute(f"UPDATE users SET {k} = $1 WHERE user_id = $2", v, user_id)

async def is_premium(user_id: int) -> bool:
    row = await pool.fetchrow("SELECT is_premium, premium_until FROM users WHERE user_id = $1", user_id)
    if not row or not row['is_premium']:
        return False
    if row['premium_until'] and row['premium_until'] < datetime.now():
        await pool.execute("UPDATE users SET is_premium=FALSE, premium_until=NULL WHERE user_id=$1", user_id)
        return False
    return True

async def grant_premium(user_id: int, days: int):
    row = await pool.fetchrow("SELECT premium_until FROM users WHERE user_id = $1", user_id)
    base = row['premium_until'] if (row and row['premium_until'] and row['premium_until'] > datetime.now()) else datetime.now()
    new_until = base + timedelta(days=days)
    await pool.execute("UPDATE users SET is_premium=TRUE, premium_until=$1 WHERE user_id=$2", new_until, user_id)

# ─── NAVBAT VA CHAT (Qolgan funksiyalar ham shu tartibda) ────────────────────────

async def add_to_queue(user_id: int, gender_want: str):
    await pool.execute("INSERT INTO search_queue (user_id, gender_want) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET gender_want=$2", user_id, gender_want)

async def remove_from_queue(user_id: int):
    await pool.execute("DELETE FROM search_queue WHERE user_id = $1", user_id)

async def find_match(user_id: int, gender_want: str) -> int | None:
    user = await get_user(user_id)
    row = await pool.fetchrow("""
        SELECT sq.user_id FROM search_queue sq
        JOIN users u ON sq.user_id = u.user_id
        WHERE sq.user_id != $1
          AND (sq.gender_want = $2 OR sq.gender_want = 'any')
          AND ($3 = 'any' OR u.gender = $3)
        ORDER BY sq.added_at ASC LIMIT 1
    """, user_id, user['gender'], gender_want)
    return row['user_id'] if row else None

async def create_chat(user1_id: int, user2_id: int) -> int:
    return await pool.fetchval("INSERT INTO chats (user1_id, user2_id) VALUES ($1, $2) RETURNING id", user1_id, user2_id)

async def get_active_chat(user_id: int):
    return await pool.fetchrow("SELECT * FROM chats WHERE is_active = TRUE AND (user1_id = $1 OR user2_id = $1)", user_id)

async def end_chat(user_id: int):
    await pool.execute("UPDATE chats SET is_active=FALSE, ended_at=CURRENT_TIMESTAMP WHERE is_active=TRUE AND (user1_id=$1 OR user2_id=$1)", user_id)

async def get_partner_id(user_id: int) -> int | None:
    chat = await get_active_chat(user_id)
    return chat['user2_id'] if chat['user1_id'] == user_id else chat['user1_id'] if chat else None
