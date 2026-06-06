import aiosqlite
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                ref_by      INTEGER DEFAULT NULL,
                balance     INTEGER DEFAULT 0,
                total_refs  INTEGER DEFAULT 0,
                total_withdrawn INTEGER DEFAULT 0,
                joined_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                amount      INTEGER,
                card_number TEXT,
                status      TEXT DEFAULT 'pending',
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


# ── Foydalanuvchi ──────────────────────────────────────────────────────────────

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return await cur.fetchone()


async def register_user(user_id: int, username: str, full_name: str, ref_by: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name, ref_by) VALUES (?,?,?,?)",
            (user_id, username, full_name, ref_by)
        )
        await db.commit()


async def add_stars(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id=?",
            (amount, user_id)
        )
        await db.commit()


async def inc_referral(referrer_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET total_refs = total_refs + 1 WHERE user_id=?",
            (referrer_id,)
        )
        await db.commit()


async def deduct_stars(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance - ?, total_withdrawn = total_withdrawn + ? WHERE user_id=?",
            (amount, amount, user_id)
        )
        await db.commit()


# ── Statistika ─────────────────────────────────────────────────────────────────

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT COUNT(*) as total, SUM(balance) as stars FROM users")
        row = await cur.fetchone()
        cur2 = await db.execute("SELECT COUNT(*) as cnt FROM withdrawals WHERE status='pending'")
        pending = await cur2.fetchone()
        return row, pending


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users ORDER BY total_refs DESC")
        return await cur.fetchall()


# ── Withdraw ───────────────────────────────────────────────────────────────────

async def create_withdrawal(user_id: int, amount: int, card: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO withdrawals (user_id, amount, card_number) VALUES (?,?,?)",
            (user_id, amount, card)
        )
        await db.commit()
        return cur.lastrowid


async def get_pending_withdrawals():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM withdrawals WHERE status='pending' ORDER BY created_at"
        )
        return await cur.fetchall()


async def update_withdrawal_status(wid: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE withdrawals SET status=? WHERE id=?",
            (status, wid)
        )
        await db.commit()


async def get_user_withdrawals(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM withdrawals WHERE user_id=? ORDER BY created_at DESC LIMIT 10",
            (user_id,)
        )
        return await cur.fetchall()
