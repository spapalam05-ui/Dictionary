from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database import get_random_word
from keyboards.word_keyboard import show_translation_keyboard

router = Router()

# Последнее показанное слово
last_words = {}

# Последние 5 слов
recent_words = {}


@router.message(Command("word"))
async def word(message: Message):

    while True:
        result = await get_random_word(message.from_user.id)

        if result is None:
            await message.answer(
                "📚 У тебя пока нет слов.\nДобавь их через /add"
            )
            return

        word_id, english, russian, weight = result

        history = recent_words.get(message.from_user.id, [])

        # Не показываем последние 5 слов
        if word_id not in history:
            break

    # Сохраняем последнее слово
    last_words[message.from_user.id] = (
        word_id,
        english,
        russian,
        weight
    )

    # Добавляем слово в историю
    history.append(word_id)

    if len(history) > 5:
        history.pop(0)

    recent_words[message.from_user.id] = history

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