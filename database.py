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
        await db.commit()

        


async def add_word(user_id: int, english: str, russian: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO words(user_id, english, russian, weight)
            VALUES (?, ?, ?, 70)
            """,
            (user_id, english, russian)
        )
        await db.commit()


async def get_random_word(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT id, english, russian, weight
            FROM words
            WHERE user_id = ?
            """,
            (user_id,)
        )

        words = await cursor.fetchall()

    if not words:
        return None

    weights = [word[3] for word in words]

    return random.choices(words, weights=weights, k=1)[0]
async def update_weight(word_id: int, weight: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE words
            SET weight = ?
            WHERE id = ?
            """,
            (weight, word_id)
        )
        await db.commit()

async def get_stats(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            "SELECT COUNT(*) FROM words WHERE user_id = ?",
            (user_id,)
        )
        total = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM words WHERE user_id = ? AND weight = 70",
            (user_id,)
        )
        dontknow = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM words WHERE user_id = ? AND weight = 25",
            (user_id,)
        )
        maybe = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM words WHERE user_id = ? AND weight = 5",
            (user_id,)
        )
        know = (await cursor.fetchone())[0]

    return total, dontknow, maybe, know
        