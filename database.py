import aiosqlite
import os
import logging
from datetime import datetime

from config import DB_PATH

logger = logging.getLogger(__name__)


async def init_db():
    """Ma'lumotlar bazasini ishga tushirish"""
    os.makedirs("data", exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Foydalanuvchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT NOT NULL,
                age         INTEGER NOT NULL,
                gender      TEXT NOT NULL,
                region      TEXT NOT NULL,
                is_premium  INTEGER DEFAULT 0,
                premium_until TEXT,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                is_blocked  INTEGER DEFAULT 0
            )
        """)
        
        # Muloqotlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id    INTEGER NOT NULL,
                user2_id    INTEGER NOT NULL,
                started_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                ended_at    TEXT,
                is_active   INTEGER DEFAULT 1
            )
        """)
        
        # Premium so'rovlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS premium_requests (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                plan_key    TEXT NOT NULL,
                photo_file_id TEXT,
                status      TEXT DEFAULT 'pending',
                admin_msg_id INTEGER,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Qidiruvdagi foydalanuvchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS search_queue (
                user_id     INTEGER PRIMARY KEY,
                gender_want TEXT,
                added_at    TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()
    
    logger.info("✅ Ma'lumotlar bazasi tayyor")


# ─── FOYDALANUVCHI ──────────────────────────────────────────────────────────────

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            return await cur.fetchone()


async def create_user(user_id: int, username: str, full_name: str,
                      age: int, gender: str, region: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users
            (user_id, username, full_name, age, gender, region)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, full_name, age, gender, region))
        await db.commit()


async def update_user(user_id: int, **kwargs):
    if not kwargs:
        return
    cols = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [user_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {cols} WHERE user_id = ?", vals)
        await db.commit()


async def is_premium(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT is_premium, premium_until FROM users WHERE user_id = ?",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
            if not row or not row[0]:
                return False
            if row[1]:
                until = datetime.fromisoformat(row[1])
                if until < datetime.now():
                    # Premium muddati tugagan
                    async with aiosqlite.connect(DB_PATH) as db2:
                        await db2.execute(
                            "UPDATE users SET is_premium=0, premium_until=NULL WHERE user_id=?",
                            (user_id,)
                        )
                        await db2.commit()
                    return False
            return True


async def grant_premium(user_id: int, days: int):
    from datetime import timedelta
    now = datetime.now()
    
    # Hozirgi premium muddatini tekshirish
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT premium_until FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
    
    if row and row[0]:
        try:
            current_until = datetime.fromisoformat(row[0])
            if current_until > now:
                base = current_until
            else:
                base = now
        except Exception:
            base = now
    else:
        base = now
    
    new_until = base + timedelta(days=days)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET is_premium=1, premium_until=?
            WHERE user_id=?
        """, (new_until.isoformat(), user_id))
        await db.commit()


# ─── QIDIRUV NAVBATI ────────────────────────────────────────────────────────────

async def add_to_queue(user_id: int, gender_want: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO search_queue (user_id, gender_want, added_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (user_id, gender_want))
        await db.commit()


async def remove_from_queue(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM search_queue WHERE user_id = ?", (user_id,))
        await db.commit()


async def find_match(user_id: int, gender_want: str) -> int | None:
    """Mos muloqotchi qidirish"""
    user = await get_user(user_id)
    if not user:
        return None
    
    user_gender = user["gender"]
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Navbatdagi birovni topish:
        # 1) O'zimiz qidirgan jinsga mos
        # 2) U ham bizni qidirmoqda yoki random qidirmoqda
        # 3) O'zimiz emas
        async with db.execute("""
            SELECT sq.user_id FROM search_queue sq
            JOIN users u ON sq.user_id = u.user_id
            WHERE sq.user_id != ?
              AND (sq.gender_want = ? OR sq.gender_want = 'any')
              AND (? = 'any' OR u.gender = ?)
            ORDER BY sq.added_at ASC
            LIMIT 1
        """, (user_id, user_gender, gender_want, gender_want)) as cur:
            row = await cur.fetchone()
            return row["user_id"] if row else None


# ─── MULOQOT ────────────────────────────────────────────────────────────────────

async def create_chat(user1_id: int, user2_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO chats (user1_id, user2_id)
            VALUES (?, ?)
        """, (user1_id, user2_id))
        await db.commit()
        return cur.lastrowid


async def get_active_chat(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM chats
            WHERE is_active = 1
              AND (user1_id = ? OR user2_id = ?)
        """, (user_id, user_id)) as cur:
            return await cur.fetchone()


async def end_chat(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE chats SET is_active=0, ended_at=CURRENT_TIMESTAMP
            WHERE is_active=1 AND (user1_id=? OR user2_id=?)
        """, (user_id, user_id))
        await db.commit()


async def get_partner_id(user_id: int) -> int | None:
    chat = await get_active_chat(user_id)
    if not chat:
        return None
    if chat["user1_id"] == user_id:
        return chat["user2_id"]
    return chat["user1_id"]


# ─── PREMIUM SO'ROV ─────────────────────────────────────────────────────────────

async def create_premium_request(user_id: int, plan_key: str, photo_file_id: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO premium_requests (user_id, plan_key, photo_file_id)
            VALUES (?, ?, ?)
        """, (user_id, plan_key, photo_file_id))
        await db.commit()
        return cur.lastrowid


async def get_premium_request(request_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM premium_requests WHERE id = ?", (request_id,)
        ) as cur:
            return await cur.fetchone()


async def update_premium_request(request_id: int, **kwargs):
    if not kwargs:
        return
    cols = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [request_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE premium_requests SET {cols} WHERE id = ?", vals)
        await db.commit()
