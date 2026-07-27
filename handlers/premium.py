from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database import (
    is_premium,
    get_words_count,
    get_categories_count,
    get_favorite_words,
)

router = Router()


# Выбранное направление карточек
# en_ru — английский → русский
# ru_en — русский → английский
# random — случайное направление
user_card_directions: dict[int, str] = {}


def get_user_card_direction(user_id: int) -> str:
    """
    Возвращает выбранное направление карточек.
    По умолчанию: английский → русский.
    """
    return user_card_directions.get(user_id, "en_ru")


@router.message(F.text == "⭐ Premium")
async def premium_menu(message: Message):

    user_id = message.from_user.id
    premium = await is_premium(user_id)

    if premium:
        status = "🟢 <b>Активен</b>"
    else:
        status = "🔴 <b>Не активирован</b>"

    keyboard = [
        [
            InlineKeyboardButton(
                text="📂 Категории",
                callback_data="my_categories",
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Направление карточек",
                callback_data="card_direction",
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="premium_stats",
            )
        ],
    ]

    if not premium:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="💳 Купить Premium",
                    callback_data="buy_premium",
                )
            ]
        )

    await message.answer(
        f"""
⭐ <b>Premium</b>

Статус: {status}

Выберите нужный раздел:
""",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard,
        ),
    )


# =========================================================
# НАПРАВЛЕНИЕ КАРТОЧЕК
# =========================================================

@router.callback_query(F.data == "card_direction")
async def card_direction_menu(callback: CallbackQuery):

    user_id = callback.from_user.id
    premium = await is_premium(user_id)

    if not premium:
        await callback.answer(
            "⭐ Изменение направления доступно только с Premium.",
            show_alert=True,
        )
        return

    current_direction = get_user_card_direction(user_id)

    direction_names = {
        "en_ru": "🇬🇧 Английский → Русский",
        "ru_en": "🇷🇺 Русский → Английский",
        "random": "🔀 Случайное направление",
    }

    current_name = direction_names.get(
        current_direction,
        "🇬🇧 Английский → Русский",
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇬🇧 Английский → Русский",
                    callback_data="direction_en_ru",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🇷🇺 Русский → Английский",
                    callback_data="direction_ru_en",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔀 Случайное направление",
                    callback_data="direction_random",
                )
            ],
        ]
    )

    await callback.message.answer(
        f"""
🔄 <b>Направление карточек</b>

Сейчас выбрано:
<b>{current_name}</b>

Выберите направление:
""",
        parse_mode="HTML",
        reply_markup=keyboard,
    )

    await callback.answer()


@router.callback_query(F.data == "direction_en_ru")
async def direction_en_ru(callback: CallbackQuery):

    user_id = callback.from_user.id
    premium = await is_premium(user_id)

    if not premium:
        await callback.answer(
            "⭐ Эта функция доступна только с Premium.",
            show_alert=True,
        )
        return

    user_card_directions[user_id] = "en_ru"

    await callback.answer(
        "🇬🇧 Выбрано: Английский → Русский",
        show_alert=True,
    )


@router.callback_query(F.data == "direction_ru_en")
async def direction_ru_en(callback: CallbackQuery):

    user_id = callback.from_user.id
    premium = await is_premium(user_id)

    if not premium:
        await callback.answer(
            "⭐ Эта функция доступна только с Premium.",
            show_alert=True,
        )
        return

    user_card_directions[user_id] = "ru_en"

    await callback.answer(
        "🇷🇺 Выбрано: Русский → Английский",
        show_alert=True,
    )


@router.callback_query(F.data == "direction_random")
async def direction_random(callback: CallbackQuery):

    user_id = callback.from_user.id
    premium = await is_premium(user_id)

    if not premium:
        await callback.answer(
            "⭐ Эта функция доступна только с Premium.",
            show_alert=True,
        )
        return

    user_card_directions[user_id] = "random"

    await callback.answer(
        "🔀 Выбрано случайное направление",
        show_alert=True,
    )


# =========================================================
# СТАТИСТИКА PREMIUM
# =========================================================

@router.callback_query(F.data == "premium_stats")
async def premium_stats(callback: CallbackQuery):

    user_id = callback.from_user.id

    words = await get_words_count(user_id)
    categories = await get_categories_count(user_id)
    favorites = await get_favorite_words(user_id)
    premium = await is_premium(user_id)

    await callback.message.answer(
        f"""
📊 <b>Статистика</b>

📚 Всего слов: <b>{words}</b>

⭐ Избранных: <b>{len(favorites)}</b>

📂 Категорий: <b>{categories}</b>

👑 Premium:
{"✅ Активен" if premium else "❌ Нет"}

Продолжай учить английский! 🚀
""",
        parse_mode="HTML",
    )

    await callback.answer()