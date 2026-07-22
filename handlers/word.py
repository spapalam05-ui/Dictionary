from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database import get_random_word
from keyboards.word_keyboard import show_translation_keyboard

router = Router()

# Последнее показанное слово
last_words = {}


@router.message(Command("word"))
async def word(message: Message):

    last = last_words.get(message.from_user.id)

    last_id = None
    if last:
        last_id = last[0]

    result = await get_random_word(
        message.from_user.id,
        last_id
    )

    if result is None:
        await message.answer(
            "📚 У тебя пока нет слов.\nДобавь их через /add"
        )
        return

    word_id, english, russian, weight = result

    last_words[message.from_user.id] = (
        word_id,
        english,
        russian,
        weight
    )

    await message.answer(
        f"📖 <b>Карточка</b>\n\n"
        f"🇬🇧 <b>{english}</b>\n\n"
        f"🤔 Попробуй вспомнить перевод.",
        reply_markup=show_translation_keyboard,
        parse_mode="HTML"
    )


@router.message(F.text == "📖 Карточка")
async def word_button(message: Message):
    await word(message)