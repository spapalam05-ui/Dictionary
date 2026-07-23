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

        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders(
                user_id INTEGER PRIMARY KEY,
                remind_time TEXT
            )
        """)

        await db.commit()


async def add_word(user_id: int, english: str, russian: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
             """
            INSERT INTO words(user_id, english, russian)
             VALUES (?, ?, ?)
            """,
            (user_id, english, russian)
)
        await db.commit()


async def get_words(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT id, english, russian
            FROM words
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,)
        )

        return await cursor.fetchall()



async def set_reminder(user_id: int, remind_time: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO reminders(user_id, remind_time)
            VALUES (?, ?)
            """,
            (user_id, remind_time)
        )
        await db.commit()


async def get_reminders():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT user_id, remind_time
            FROM reminders
            """
        )

        return await cursor.fetchall()