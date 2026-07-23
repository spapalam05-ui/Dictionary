from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database import get_words
from keyboards.word_keyboard import show_translation_keyboard

router = Router()

# Активные уроки
study_sessions = {}

# Последняя карточка
last_words = {}


@router.message(Command("word"))
async def word(message: Message):

    user_id = message.from_user.id

    # Создаём урок только один раз
    if user_id not in study_sessions:

        words = await get_words(user_id)

        if not words:
            await message.answer(
                "📚 У тебя пока нет слов.\nДобавь их через /add"
            )
            return

        study_sessions[user_id] = {
            "main": words,
            "repeat": [],
            "index": 0,
            "repeat_mode": False
        }

    session = study_sessions[user_id]

    # Основная колода закончилась
    if session["index"] >= len(session["main"]):

        # Есть слова на повторение
        if not session["repeat_mode"] and session["repeat"]:

            session["main"] = session["repeat"]
            session["repeat"] = []
            session["index"] = 0
            session["repeat_mode"] = True

        else:

            del study_sessions[user_id]

            await message.answer(
                "🎉 Поздравляю!\n\nТы прошёл все карточки."
            )
            return

    word_id, english, russian = session["main"][session["index"]]

    last_words[user_id] = (
        word_id,
        english,
        russian
    )

    await message.answer(
        f"📖 <b>{session['index'] + 1}/{len(session['main'])}</b>\n\n"
        f"🇬🇧 <b>{english}</b>\n\n"
        f"🤔 Попробуй вспомнить перевод.",
        reply_markup=show_translation_keyboard,
        parse_mode="HTML"
    )


@router.message(F.text == "📖 Карточка")
async def word_button(message: Message):
    await word(message)