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


def progress_bar(percent: int) -> str:
    filled = round(percent / 10)
    return "█" * filled + "░" * (10 - filled)


@router.message(F.text == "📊 Статистика")
async def statistics(message: Message):

    user_id = message.from_user.id

    words = await get_words_count(user_id)
    categories = await get_categories_count(user_id)
    favorites = await get_favorite_words(user_id)
    premium = await is_premium(user_id)

    stats = await get_user_stats(user_id)

    learned = stats["learned"]
    forgotten = stats["forgotten"]

    total_answers = learned + forgotten

    if total_answers == 0:
        percent = 0
    else:
        percent = round((learned / total_answers) * 100)

    bar = progress_bar(percent)

    if percent >= 90:
        status = "🏆 Мастер слов!"
    elif percent >= 75:
        status = "🚀 Отличный результат!"
    elif percent >= 50:
        status = "📚 Хороший прогресс!"
    elif percent >= 25:
        status = "🌱 Продолжай учиться!"
    else:
        status = "💪 Всё только начинается!"

    if stats["registered_at"]:
        register_date = stats["registered_at"].strftime("%d.%m.%Y")
    else:
        register_date = "Неизвестно"

    premium_text = "✅ Активен" if premium else "❌ Не активен"

    await message.answer(
        "📊 <b>Моя статистика</b>\n\n"

        "📚 <b>Слова</b>\n"
        f"├ 📖 Всего: <b>{words}</b>\n"
        f"├ ⭐ Избранных: <b>{len(favorites)}</b>\n"
        f"└ 📁 Папок: <b>{categories}</b>\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "🎓 <b>Обучение</b>\n"
        f"├ ✅ Выучено: <b>{learned}</b>\n"
        f"├ ❌ Не знаю: <b>{forgotten}</b>\n"
        f"├ 📅 Сегодня: <b>{stats['today_learned']}</b>\n"
        f"└ 🔥 Серия: <b>{stats['streak']}</b>\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "📈 <b>Прогресс</b>\n\n"
        f"<code>{bar}</code> <b>{percent}%</b>\n\n"
        f"{status}\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "👤 <b>Аккаунт</b>\n"
        f"├ 👑 Premium: {premium_text}\n"
        f"└ 📅 Регистрация: <b>{register_date}</b>",

        parse_mode="HTML",
    )