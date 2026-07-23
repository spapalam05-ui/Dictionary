from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database import get_words
from keyboards.word_keyboard import show_translation_keyboard

router = Router()

# Последняя показанная карточка
last_words = {}

# Активные уроки
study_sessions = {}


async def show_next_word(message: Message, user_id: int):

    session = study_sessions.get(user_id)

    if session is None:
        await message.answer(
            "📚 У тебя пока нет слов.\nДобавь их через /add"
        )
        return

    if not session["words"]:
        await message.answer("📚 Нет доступных слов.")
        return

    if session["index"] >= len(session["words"]):
        await message.answer(
            "🎉 Все слова закончены!\n\n"
            "Можно начать заново через 📖 Карточка"
        )

        del study_sessions[user_id]
        return


    word_id, english, russian = session["words"][session["index"]]

    last_words[user_id] = (
        word_id,
        english,
        russian
    )


    title = "📖 Карточка"

    if session["repeat_mode"]:
        title = "🔁 Повторение"


    await message.answer(
        f"{title}\n\n"
        f"<b>{session['index'] + 1}/{len(session['words'])}</b>\n\n"
        f"🇬🇧 <b>{english}</b>\n\n"
        f"🤔 Попробуй вспомнить перевод.",
        reply_markup=show_translation_keyboard,
        parse_mode="HTML"
    )


@router.message(Command("word"))
async def word(message: Message):

    user_id = message.from_user.id

    # Если урок ещё не начат
    if user_id not in study_sessions:

        words = await get_words(user_id)

        if not words:
            await message.answer(
                "📚 У тебя пока нет слов.\n"
                "Добавь их через /add"
            )
            return

        study_sessions[user_id] = {
            "words": words,
            "repeat": [],
            "index": 0,
            "repeat_mode": False
        }

    await show_next_word(message, user_id)


@router.message(F.text == "📖 Карточка")
async def word_button(message: Message):
    await word(message)

@router.message(F.text == "🔄 Обновить карточки")
async def reset_words(message: Message):

    user_id = message.from_user.id

    if user_id in study_sessions:
        del study_sessions[user_id]

    await message.answer(
        "✅ Карточки обновлены"
    )