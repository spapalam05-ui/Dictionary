import os
import random
import asyncpg


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("Переменная DATABASE_URL не найдена")


async def get_connection():
    return await asyncpg.connect(DATABASE_URL)


async def init_db():
    conn = await get_connection()

    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS words(
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                english TEXT NOT NULL,
                russian TEXT NOT NULL,
                position INTEGER NOT NULL DEFAULT 0
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders(
                user_id BIGINT PRIMARY KEY,
                remind_datetime TEXT NOT NULL
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id BIGINT PRIMARY KEY
                is_premium BOOLEAN DEFAULT FALSE
            )
        """)
        await conn.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS is_premium BOOLEAN DEFAULT FALSE
        """)

        print("✅ Таблицы PostgreSQL созданы/проверены")

    finally:
        await conn.close()


async def add_word(user_id: int, english: str, russian: str):
    conn = await get_connection()

    try:
        max_position = await conn.fetchval("""
            SELECT COALESCE(MAX(position), 0)
            FROM words
            WHERE user_id = $1
        """, user_id)

        await conn.execute("""
            INSERT INTO words(user_id, english, russian, position)
            VALUES ($1, $2, $3, $4)
        """, user_id, english, russian, max_position + 1)

    finally:
        await conn.close()


async def get_words(user_id: int):
    conn = await get_connection()

    try:
        rows = await conn.fetch("""
            SELECT id, english, russian
            FROM words
            WHERE user_id = $1
            ORDER BY position, id
        """, user_id)

        return [
            (row["id"], row["english"], row["russian"])
            for row in rows
        ]

    finally:
        await conn.close()


async def get_all_words(user_id: int):
    return await get_words(user_id)


async def set_reminder(user_id: int, remind_datetime: str):
    conn = await get_connection()

    try:
        await conn.execute("""
            INSERT INTO reminders(user_id, remind_datetime)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET remind_datetime = EXCLUDED.remind_datetime
        """, user_id, remind_datetime)

    finally:
        await conn.close()


async def get_reminders():
    conn = await get_connection()

    try:
        rows = await conn.fetch("""
            SELECT user_id, remind_datetime
            FROM reminders
        """)

        return [
            (row["user_id"], row["remind_datetime"])
            for row in rows
        ]

    finally:
        await conn.close()


async def delete_reminder(user_id: int):
    conn = await get_connection()

    try:
        await conn.execute(
            "DELETE FROM reminders WHERE user_id = $1",
            user_id
        )

    finally:
        await conn.close()


async def add_user(user_id: int):
    conn = await get_connection()

    try:
        await conn.execute("""
            INSERT INTO users(user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id)

    finally:
        await conn.close()


async def get_users_count():
    conn = await get_connection()

    try:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM users"
        )

    finally:
        await conn.close()


async def get_words_count(user_id: int):
    conn = await get_connection()

    try:
        return await conn.fetchval("""
            SELECT COUNT(*)
            FROM words
            WHERE user_id = $1
        """, user_id)

    finally:
        await conn.close()


async def delete_word(word_id: int):
    conn = await get_connection()

    try:
        await conn.execute(
            "DELETE FROM words WHERE id = $1",
            word_id
        )

    finally:
        await conn.close()


async def update_word(
    word_id: int,
    english: str,
    russian: str
):
    conn = await get_connection()

    try:
        await conn.execute("""
            UPDATE words
            SET english = $1,
                russian = $2
            WHERE id = $3
        """, english, russian, word_id)

    finally:
        await conn.close()


async def shuffle_words(user_id: int):
    conn = await get_connection()

    try:
        rows = await conn.fetch("""
            SELECT id
            FROM words
            WHERE user_id = $1
            ORDER BY position, id
        """, user_id)

        if len(rows) < 2:
            return

        ids = [row["id"] for row in rows]
        random.shuffle(ids)

        async with conn.transaction():
            for position, word_id in enumerate(ids, start=1):
                await conn.execute("""
                    UPDATE words
                    SET position = $1
                    WHERE id = $2
                """, position, word_id)

    finally:
        await conn.close()

async def is_premium(user_id: int):
    conn = await get_connection()

    try:
        result = await conn.fetchval(
            "SELECT is_premium FROM users WHERE user_id = $1",
            user_id
        )

        return bool(result)

    finally:
        await conn.close()


async def give_premium(user_id: int):
    conn = await get_connection()

    try:
        await conn.execute("""
            UPDATE users
            SET is_premium = TRUE
            WHERE user_id = $1
        """, user_id)

    finally:
        await conn.close()


async def remove_premium(user_id: int):
    conn = await get_connection()

    try:
        await conn.execute("""
            UPDATE users
            SET is_premium = FALSE
            WHERE user_id = $1
        """, user_id)

    finally:
        await conn.close()