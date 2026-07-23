from aiogram import Router, F
from aiogram.types import Message

from database import get_all_words

router = Router()


@router.message(F.text == "📋 Мои слова")
async def my_words(message: Message):

    words = await get_all_words(message.from_user.id)

    if not words:
        await message.answer("📚 У тебя пока нет слов.")
        return

    text = "📚 <b>Твои слова:</b>\n\n"

    for i, (_, english, russian) in enumerate(words, start=1):
        text += f"{i}. 🇬🇧 <b>{english}</b> — 🇷🇺 {russian}\n"

    await message.answer(
        text,
        parse_mode="HTML"
    )