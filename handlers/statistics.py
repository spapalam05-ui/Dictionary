from aiogram import Router, F
from aiogram.types import Message

from database import (
    get_categories_count,
    get_user_stats,
    get_words_count,
    get_favorite_words,
    is_premium,
)

router = Router()


@router.message(F.text == "📊 Статистика")
async def statistics(message: Message):

    user_id = message.from_user.id

    words = await get_words_count(user_id)
    categories = await get_categories_count(user_id)
    favorites = await get_favorite_words(user_id)
    premium = await is_premium(user_id)

    stats = await get_user_stats(user_id)

    if stats["registered_at"]:
        register_date = stats["registered_at"].strftime("%d.%m.%Y")
    else:
        register_date = "Неизвестно"

    premium_text = "✅ Активен" if premium else "❌ Не активен"

    await message.answer(
        "📊 <b>Моя статистика</b>\n\n"

        f"📚 Всего слов: <b>{words}</b>\n"
        f"⭐ Избранных: <b>{len(favorites)}</b>\n"
        f"📂 Категорий: <b>{categories}</b>\n\n"

        "━━━━━━━━━━━━━━\n\n"

        f"✅ Выучено: <b>{stats['learned']}</b>\n"
        f"❌ Не знаю: <b>{stats['forgotten']}</b>\n"
        f"🔥 Сегодня изучено: <b>{stats['today_learned']}</b>\n"
        f"🎯 Серия дней: <b>{stats['streak']}</b>\n\n"

        "━━━━━━━━━━━━━━\n\n"

        f"👑 Premium: {premium_text}\n"
        f"📅 Регистрация: <b>{register_date}</b>",
        parse_mode="HTML",
    )