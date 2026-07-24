import os
import aiosqlite
import random

DB_NAME = "dictionary.db"

print("База данных:", os.path.abspath(DB_NAME))

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
                remind_datetime TEXT
            )
        """)

        await db.commit()


async def add_word(user_id: int, english: str, russian: str):
    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            """
            SELECT COALESCE(MAX(position), 0)
            FROM words
            WHERE user_id = ?
            """,
            (user_id,)
        )

        max_position = (await cursor.fetchone())[0]

        await db.execute(
            """
            INSERT INTO words(user_id, english, russian, position)
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                english,
                russian,
                max_position + 1
            )
        )

        await db.commit()


async def get_words(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT id, english, russian
            FROM words
            WHERE user_id = ?
            ORDER BY position
            """,
            (user_id,)
        )

        return await cursor.fetchall()



async def set_reminder(user_id: int, remind_datetime: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO reminders(user_id, remind_datetime)
            VALUES (?, ?)
            """,
            (user_id, remind_datetime)
        )
        await db.commit()


async def get_reminders():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT user_id, remind_datetime
            FROM reminders
            """
        )

        return await cursor.fetchall()
    
async def get_all_words(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT id, english, russian
            FROM words
            WHERE user_id = ?
            ORDER BY position
            """,
            (user_id,)
        )

        return await cursor.fetchall()


        
async def delete_word(word_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM words WHERE id = ?",
            (word_id,)
        )
        await db.commit()

async def update_word(word_id: int, english: str, russian: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE words
            SET english = ?, russian = ?
            WHERE id = ?
            """,
            (english, russian, word_id)
        )
        await db.commit()

async def delete_reminder(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM reminders WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

async def shuffle_words(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            """
            SELECT id
            FROM words
            WHERE user_id = ?
            ORDER BY position
            """,
            (user_id,)
        )

        words = await cursor.fetchall()

        if len(words) < 2:
            return

        ids = [word[0] for word in words]

        random.shuffle(ids)

        for position, word_id in enumerate(ids, start=1):
            await db.execute(
                """
                UPDATE words
                SET position = ?
                WHERE id = ?
                """,
                (position, word_id)
            )

        await db.commit()