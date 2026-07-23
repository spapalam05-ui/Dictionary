from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database import get_words
from keyboards.word_keyboard import show_translation_keyboard

router = Router()

# Активные уроки пользователей
study_sessions = {}

# Текущее слово
last_words = {}


@router.message(Command("word"))
async def word(message: Message):
    user_id = message.from_user.id

    # Если урока нет — создаём
    if user_id not in study_sessions:

        words = await get_words(user_id)

        if not words:
            await message.answer(
                "📚 У тебя пока нет слов.\nДобавь их через /add"
            )
            return

        study_sessions[user_id] = {
            "words": words,
            "index": 0,
            "repeat": [],
            "repeat_mode": False
        }

    session = study_sessions[user_id]

    # ---------- Первый круг ----------
    if not session["repeat_mode"]:

        if session["index"] >= len(session["words"]):

            if session["repeat"]:
                session["words"] = session["repeat"]
                session["repeat"] = []
                session["index"] = 0
                session["repeat_mode"] = True

                await message.answer(
                    "🔁 Повторяем слова, которые ты не знал."
                )
            else:
                del study_sessions[user_id]

                await message.answer(
                    "🎉 Поздравляем!\n\nВсе слова выучены!"
                )
                return

    # ---------- Второй круг ----------
    else:

        if session["index"] >= len(session["words"]):

            del study_sessions[user_id]

            await message.answer(
                "🎉 Отлично!\n\nТеперь ты знаешь все слова!"
            )
            return

    word_data = session["words"][session["index"]]

    last_words[user_id] = word_data

    word_id, english, russian = word_data

    total = len(session["words"])
    current = session["index"] + 1

    await message.answer(
        f"📖 <b>{current}/{total}</b>\n\n"
        f"🇬🇧 <b>{english}</b>\n\n"
        f"🤔 Попробуй вспомнить перевод.",
        reply_markup=show_translation_keyboard,
        parse_mode="HTML"
    )


@router.message(F.text == "📖 Карточка")
async def word_button(message: Message):
    await word(message)