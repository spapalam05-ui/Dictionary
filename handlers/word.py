from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database import get_words
from keyboards.word_keyboard import show_translation_keyboard

router = Router()

# Последняя карточка
last_words = {}

# Колода пользователя
user_decks = {}


@router.message(Command("word"))
async def word(message: Message):
    user_id = message.from_user.id

    # Если колоды нет — создаем
    if user_id not in user_decks:

        words = await get_words(user_id)

        if not words:
            await message.answer(
                "📚 У тебя пока нет слов.\nДобавь их через /add"
            )
            return

        user_decks[user_id] = {
            "words": words,
            "index": 0,
            "repeat": []
        }

    deck = user_decks[user_id]

    # Закончились все слова
    if deck["index"] >= len(deck["words"]):

        # Есть слова на повторение
        if deck["repeat"]:

            deck["words"] = deck["repeat"]
            deck["repeat"] = []
            deck["index"] = 0

            await message.answer(
                "🔁 Начинаем повторение слов, которые ты не знал!"
            )

        else:
            await message.answer(
                "🎉 Отлично!\n\nТы прошёл все слова!"
            )

            del user_decks[user_id]
            return

    word_data = deck["words"][deck["index"]]

    deck["index"] += 1

    last_words[user_id] = word_data

    word_id, english, russian = word_data

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