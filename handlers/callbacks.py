from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from handlers.word import (
    last_words,
    study_sessions,
    show_next_word,
)

router = Router()


@router.callback_query(F.data == "show_translation")
async def show_translation(callback: CallbackQuery):

    user_id = callback.from_user.id

    if user_id not in last_words:
        await callback.answer()
        return

    word_id, english, russian = last_words[user_id]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Не знаю",
                    callback_data="dontknow"
                ),
                InlineKeyboardButton(
                    text="✅ Знаю",
                    callback_data="know"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        f"📖 <b>Карточка</b>\n\n"
        f"🇬🇧 <b>{english}</b>\n"
        f"🇷🇺 <b>{russian}</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "dontknow")
async def dontknow(callback: CallbackQuery):

    user_id = callback.from_user.id

    session = study_sessions[user_id]

    # Добавляем слово в повторение
    word = session["words"][session["index"]]

    if word not in session["repeat"]:
        session["repeat"].append(word)

    session["index"] += 1


    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➡️ Следующее слово",
                    callback_data="next_word"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "❌ <b>Не страшно!</b>\n\n"
        "Это слово попадёт в повторение.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "know")
async def know(callback: CallbackQuery):

    user_id = callback.from_user.id
    session = study_sessions[user_id]

    # Если сейчас режим повторения
    if session["repeat_mode"]:

        word = session["words"][session["index"]]

        if word in session["repeat"]:
            session["repeat"].remove(word)

    session["index"] += 1

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➡️ Следующее слово",
                    callback_data="next_word"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "✅ <b>Отлично!</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(F.data == "next_word")
async def next_word(callback: CallbackQuery):

    await callback.message.delete()

    await show_next_word(
        callback.message,
        callback.from_user.id
    )

    await callback.answer()

@router.callback_query(F.data == "start_repeat")
async def start_repeat(callback: CallbackQuery):

    user_id = callback.from_user.id
    session = study_sessions[user_id]

    session["words"] = session["repeat"]
    session["repeat"] = []
    session["index"] = 0
    session["repeat_mode"] = True

    await callback.message.delete()

    await show_next_word(
        callback.message,
        user_id
    )

    await callback.answer()
