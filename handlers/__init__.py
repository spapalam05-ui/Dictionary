import aiosqlite
import random

DB_NAME = "dictionary.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS words(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                english TEXT,
                russian TEXT,
                weight INTEGER DEFAULT 70
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders(
                user_id INTEGER PRIMARY KEY,
                remind_time TEXT
            )
        """)

        print("✅ Таблица reminders проверена/создана")

        await db.commit()