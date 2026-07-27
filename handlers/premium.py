from aiogram import Router, F
from aiogram.types import (
    Message,
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


@router.message(F.text == "⭐ Premium")
async def premium_menu(message: Message):

    premium = await is_premium(message.from_user.id)

    if premium:
        status = "🟢 <b>Активен</b>"
    else:
        status = "🔴 <b>Не активирован</b>"

    keyboard = [
        [
            InlineKeyboardButton(
                text="⭐ Избранное",
                callback_data="open_favorites"
            )
        ],
        [
            InlineKeyboardButton(
                text="📂 Категории",
                callback_data="my_categories"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏰ Напоминания",
                callback_data="premium_reminders"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="premium_stats"
            )
        ]
    ]

    if not premium:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="💳 Купить Premium",
                    callback_data="buy_premium"
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
            inline_keyboard=keyboard
        )
    )


@router.callback_query(F.data == "premium_stats")
async def premium_stats(callback):

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
        parse_mode="HTML"
    )

    await callback.answer()