from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database import get_stats

router = Router()


@router.message(Command("stats"))
async def stats(message: Message):

    total, dontknow, maybe, know = await get_stats(message.from_user.id)

    await message.answer(
        f"📊 <b>Твоя статистика</b>\n\n"

        f"📚 Всего слов: <b>{total}</b>\n\n"

        f"❌ Не знаю: <b>{dontknow}</b>\n"
        f"🤔 Сомневаюсь: <b>{maybe}</b>\n"
        f"✅ Знаю: <b>{know}</b>",
        parse_mode="HTML"
    )


# Кнопка "📊 Статистика"
@router.message(F.text == "📊 Статистика")
async def stats_button(message: Message):
    await stats(message)