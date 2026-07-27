import os
import random
from typing import Iterable

import asyncpg


DATABASE_URL = os.getenv("DATABASE_URL")
MAX_CATEGORIES = 5

if not DATABASE_URL:
    raise RuntimeError("Переменная DATABASE_URL не найдена")


async def get_connection():
    return await asyncpg.connect(DATABASE_URL)


async def init_db():
    conn = await get_connection()

    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id BIGINT PRIMARY KEY,
                is_premium BOOLEAN DEFAULT FALSE
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_stats(
                user_id BIGINT PRIMARY KEY,
                learned INTEGER NOT NULL DEFAULT 0,
                forgotten INTEGER NOT NULL DEFAULT 0,
                today_learned INTEGER NOT NULL DEFAULT 0,
                streak INTEGER NOT NULL DEFAULT 0,
                registered_at TIMESTAMP NOT NULL DEFAULT NOW(),
                last_activity DATE
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS categories(
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                name TEXT NOT NULL,
                UNIQUE(user_id, name)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS words(
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                english TEXT NOT NULL,
                russian TEXT NOT NULL,
                position INTEGER NOT NULL DEFAULT 0,
                category_id BIGINT
            )
        """)

        await conn.execute("""
            ALTER TABLE words
            ADD COLUMN IF NOT EXISTS category_id BIGINT
        """)

        await conn.execute("""
            ALTER TABLE words
            ADD COLUMN IF NOT EXISTS favorite BOOLEAN DEFAULT FALSE
        """)

        await conn.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = 'words_category_id_fkey'
                ) THEN
                    ALTER TABLE words
                    ADD CONSTRAINT words_category_id_fkey
                    FOREIGN KEY (category_id)
                    REFERENCES categories(id)
                    ON DELETE SET NULL;
                END IF;
            END
            $$;
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders(
                user_id BIGINT PRIMARY KEY,
                remind_datetime TEXT NOT NULL
            )
        """)

        await conn.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS is_premium BOOLEAN DEFAULT FALSE
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_words_user_id
            ON words(user_id)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_words_category_id
            ON words(category_id)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_categories_user_id
            ON categories(user_id)
        """)

        print("✅ Таблицы PostgreSQL созданы/проверены")

    finally:
        await conn.close()


# =========================================================
# СЛОВА
# =========================================================

async def add_word(
    user_id: int,
    english: str,
    russian: str,
    category_id: int | None = None,
):
    english = english.strip()
    russian = russian.strip()

    if not english or not russian:
        return False

    conn = await get_connection()

    try:
        if category_id is not None:
            category_exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1
                    FROM categories
                    WHERE id = $1
                      AND user_id = $2
                )
            """, category_id, user_id)

            if not category_exists:
                return False

        max_position = await conn.fetchval("""
            SELECT COALESCE(MAX(position), 0)
            FROM words
            WHERE user_id = $1
        """, user_id)

        await conn.execute("""
            INSERT INTO words(
                user_id,
                english,
                russian,
                position,
                category_id
            )
            VALUES ($1, $2, $3, $4, $5)
        """,
            user_id,
            english,
            russian,
            max_position + 1,
            category_id,
        )

        return True

    finally:
        await conn.close()


async def add_words_batch(
    user_id: int,
    words: Iterable[tuple[str, str]],
    category_id: int | None = None,
):
    prepared_words = []

    for english, russian in words:
        english = english.strip()
        russian = russian.strip()

        if english and russian:
            prepared_words.append((english, russian))

    if not prepared_words:
        return 0

    conn = await get_connection()

    try:
        async with conn.transaction():
            if category_id is not None:
                category_exists = await conn.fetchval("""
                    SELECT EXISTS(
                        SELECT 1
                        FROM categories
                        WHERE id = $1
                          AND user_id = $2
                    )
                """, category_id, user_id)

                if not category_exists:
                    return 0

            max_position = await conn.fetchval("""
                SELECT COALESCE(MAX(position), 0)
                FROM words
                WHERE user_id = $1
            """, user_id)

            rows = [
                (
                    user_id,
                    english,
                    russian,
                    max_position + index,
                    category_id,
                )
                for index, (english, russian)
                in enumerate(prepared_words, start=1)
            ]

            await conn.executemany("""
                INSERT INTO words(
                    user_id,
                    english,
                    russian,
                    position,
                    category_id
                )
                VALUES ($1, $2, $3, $4, $5)
            """, rows)

        return len(rows)

    finally:
        await conn.close()


async def get_words(
    user_id: int,
    category_id: int | None = None,
):
    conn = await get_connection()

    try:
        if category_id is None:
            rows = await conn.fetch("""
                SELECT id, english, russian
                FROM words
                WHERE user_id = $1
                ORDER BY position, id
            """, user_id)

        else:
            rows = await conn.fetch("""
                SELECT id, english, russian
                FROM words
                WHERE user_id = $1
                  AND category_id = $2
                ORDER BY position, id
            """, user_id, category_id)

        return [
            (
                row["id"],
                row["english"],
                row["russian"],
            )
            for row in rows
        ]

    finally:
        await conn.close()


async def get_word(
    user_id: int,
    word_id: int,
):
    conn = await get_connection()

    try:
        row = await conn.fetchrow("""
            SELECT
                id,
                english,
                russian,
                category_id
            FROM words
            WHERE id = $1
              AND user_id = $2
        """, word_id, user_id)

        if row is None:
            return None

        return (
            row["id"],
            row["english"],
            row["russian"],
            row["category_id"],
        )

    finally:
        await conn.close()


async def get_all_words(user_id: int):
    return await get_words(user_id)


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


async def get_category_words_count(
    user_id: int,
    category_id: int,
):
    conn = await get_connection()

    try:
        return await conn.fetchval("""
            SELECT COUNT(*)
            FROM words
            WHERE user_id = $1
              AND category_id = $2
        """, user_id, category_id)

    finally:
        await conn.close()


async def move_word_to_category(
    user_id: int,
    word_id: int,
    category_id: int,
):
    conn = await get_connection()

    try:
        category_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1
                FROM categories
                WHERE id = $1
                  AND user_id = $2
            )
        """, category_id, user_id)

        if not category_exists:
            return False

        result = await conn.execute("""
            UPDATE words
            SET category_id = $1
            WHERE id = $2
              AND user_id = $3
        """,
            category_id,
            word_id,
            user_id,
        )

        return result == "UPDATE 1"

    finally:
        await conn.close()


async def delete_word(word_id: int):
    conn = await get_connection()

    try:
        await conn.execute(
            "DELETE FROM words WHERE id = $1",
            word_id,
        )

    finally:
        await conn.close()


async def update_word(
    word_id: int,
    english: str,
    russian: str,
):
    conn = await get_connection()

    try:
        await conn.execute("""
            UPDATE words
            SET english = $1,
                russian = $2
            WHERE id = $3
        """,
            english.strip(),
            russian.strip(),
            word_id,
        )

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


# =========================================================
# КАТЕГОРИИ
# =========================================================

async def get_categories_count(user_id: int):
    conn = await get_connection()

    try:
        return await conn.fetchval("""
            SELECT COUNT(*)
            FROM categories
            WHERE user_id = $1
        """, user_id)

    finally:
        await conn.close()


async def create_category(
    user_id: int,
    name: str,
):
    name = name.strip()

    if not name:
        return None

    conn = await get_connection()

    try:
        async with conn.transaction():
            categories_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM categories
                WHERE user_id = $1
            """, user_id)

            if categories_count >= MAX_CATEGORIES:
                return None

            category_id = await conn.fetchval("""
                INSERT INTO categories(user_id, name)
                VALUES ($1, $2)
                ON CONFLICT (user_id, name)
                DO NOTHING
                RETURNING id
            """, user_id, name)

            return category_id

    finally:
        await conn.close()


async def get_categories(user_id: int):
    conn = await get_connection()

    try:
        rows = await conn.fetch("""
            SELECT
                c.id,
                c.name,
                COUNT(w.id) AS words_count
            FROM categories c
            LEFT JOIN words w
                ON w.category_id = c.id
                AND w.user_id = c.user_id
            WHERE c.user_id = $1
            GROUP BY c.id, c.name
            ORDER BY c.id
        """, user_id)

        return [
            (
                row["id"],
                row["name"],
                row["words_count"],
            )
            for row in rows
        ]

    finally:
        await conn.close()


async def get_category(
    user_id: int,
    category_id: int,
):
    conn = await get_connection()

    try:
        row = await conn.fetchrow("""
            SELECT id, name
            FROM categories
            WHERE id = $1
              AND user_id = $2
        """, category_id, user_id)

        if row is None:
            return None

        return row["id"], row["name"]

    finally:
        await conn.close()


async def delete_category(
    user_id: int,
    category_id: int,
):
    conn = await get_connection()

    try:
        result = await conn.execute("""
            DELETE FROM categories
            WHERE id = $1
              AND user_id = $2
        """, category_id, user_id)

        return result == "DELETE 1"

    finally:
        await conn.close()


# =========================================================
# НАПОМИНАНИЯ
# =========================================================

async def set_reminder(
    user_id: int,
    remind_datetime: str,
):
    conn = await get_connection()

    try:
        await conn.execute("""
            INSERT INTO reminders(user_id, remind_datetime)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET
                remind_datetime = EXCLUDED.remind_datetime
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
            (
                row["user_id"],
                row["remind_datetime"],
            )
            for row in rows
        ]

    finally:
        await conn.close()


async def delete_reminder(user_id: int):
    conn = await get_connection()

    try:
        await conn.execute(
            "DELETE FROM reminders WHERE user_id = $1",
            user_id,
        )

    finally:
        await conn.close()


# =========================================================
# ПОЛЬЗОВАТЕЛИ И PREMIUM
# =========================================================

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


async def is_premium(user_id: int):
    conn = await get_connection()

    try:
        result = await conn.fetchval("""
            SELECT is_premium
            FROM users
            WHERE user_id = $1
        """, user_id)

        return bool(result)

    finally:
        await conn.close()


async def give_premium(user_id: int):
    conn = await get_connection()

    try:
        await conn.execute("""
            INSERT INTO users(user_id, is_premium)
            VALUES ($1, TRUE)
            ON CONFLICT (user_id)
            DO UPDATE SET is_premium = TRUE
        """, user_id)

    finally:
        await conn.close()


async def remove_premium(user_id: int):
    conn = await get_connection()

    try:
        await conn.execute("""
            INSERT INTO users(user_id, is_premium)
            VALUES ($1, FALSE)
            ON CONFLICT (user_id)
            DO UPDATE SET is_premium = FALSE
        """, user_id)

    finally:
        await conn.close()

async def toggle_favorite(user_id: int, word_id: int):
    conn = await get_connection()

    await conn.execute("""
        UPDATE words
        SET favorite = NOT favorite
        WHERE id=$1 AND user_id=$2
    """, word_id, user_id)

    await conn.close()

async def is_favorite(user_id: int, word_id: int):

    conn = await get_connection()

    result = await conn.fetchval("""
        SELECT favorite
        FROM words
        WHERE id=$1
        AND user_id=$2
    """, word_id, user_id)

    await conn.close()

    return result

async def get_favorite_words(user_id: int):

    conn = await get_connection()

    words = await conn.fetch("""
        SELECT id, english, russian
        FROM words
        WHERE user_id=$1
        AND favorite=TRUE
        ORDER BY english
    """, user_id)

    await conn.close()

    return words

async def init_user_stats(user_id: int):
    conn = await get_connection()

    try:
        await conn.execute("""
            INSERT INTO user_stats(
                user_id,
                last_activity
            )
            VALUES(
                $1,
                CURRENT_DATE
            )
            ON CONFLICT (user_id)
            DO NOTHING
        """, user_id)

    finally:
        await conn.close()

async def add_learned_word(user_id: int):
    conn = await get_connection()

    try:
        await conn.execute("""
            INSERT INTO user_stats(
                user_id,
                learned,
                today_learned,
                last_activity
            )
            VALUES(
                $1,
                1,
                1,
                CURRENT_DATE
            )

            ON CONFLICT (user_id)
            DO UPDATE SET
                learned = user_stats.learned + 1,
                today_learned = user_stats.today_learned + 1,
                last_activity = CURRENT_DATE
        """, user_id)

    finally:
        await conn.close()

async def add_forgotten_word(user_id: int):
    conn = await get_connection()

    try:
        await conn.execute("""
            INSERT INTO user_stats(
                user_id,
                forgotten,
                last_activity
            )
            VALUES(
                $1,
                1,
                CURRENT_DATE
            )

            ON CONFLICT (user_id)
            DO UPDATE SET
                forgotten = user_stats.forgotten + 1,
                last_activity = CURRENT_DATE
        """, user_id)

    finally:
        await conn.close()

async def get_user_stats(user_id: int):
    conn = await get_connection()

    try:
        row = await conn.fetchrow("""
            SELECT
                learned,
                forgotten,
                today_learned,
                streak,
                registered_at
            FROM user_stats
            WHERE user_id = $1
        """, user_id)

        if row is None:
            return {
                "learned": 0,
                "forgotten": 0,
                "today_learned": 0,
                "streak": 0,
                "registered_at": None,
            }

        return {
            "learned": row["learned"],
            "forgotten": row["forgotten"],
            "today_learned": row["today_learned"],
            "streak": row["streak"],
            "registered_at": row["registered_at"],
        }

    finally:
        await conn.close()