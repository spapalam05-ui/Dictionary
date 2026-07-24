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
                russian TEXT
            )
        """)

        # Проверяем, есть ли колонка position
        cursor = await db.execute("PRAGMA table_info(words)")
        columns = await cursor.fetchall()

        column_names = [column[1] for column in columns]

        if "position" not in column_names:
            await db.execute(
                "ALTER TABLE words ADD COLUMN position INTEGER"
            )

        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders(
                user_id INTEGER PRIMARY KEY,
                remind_time TEXT
            )
        """)

        print("✅ Таблица reminders проверена/создана")

        await db.commit()