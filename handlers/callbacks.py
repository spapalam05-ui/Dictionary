from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from database import shuffle_words

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

    session = study_sessions.get(user_id)

    if session is None:
        await callback.answer()
        return

    if not session["repeat"]:
        await callback.answer("Нет слов для повторения.")
        return

    session["words"] = session["repeat"].copy()
    session["index"] = 0
    session["repeat_mode"] = True

    await callback.message.delete()

    await show_next_word(
        callback.message,
        user_id
    )

    await callback.answer()

from datetime import datetime, timedelta
from database import set_reminder, delete_reminder


@router.callback_query(F.data.startswith("remind_"))
async def reminder_buttons(callback: CallbackQuery):

    user_id = callback.from_user.id

    if callback.data == "remind_off":
        await delete_reminder(user_id)

        await callback.message.edit_text(
            "❌ Напоминание отключено."
        )

        await callback.answer()
        return

    delta = None

    if callback.data == "remind_30m":
        delta = timedelta(minutes=30)

    elif callback.data == "remind_1h":
        delta = timedelta(hours=1)

    elif callback.data == "remind_3h":
        delta = timedelta(hours=3)

    elif callback.data == "remind_6h":
        delta = timedelta(hours=6)

    elif callback.data == "remind_1d":
        delta = timedelta(days=1)

    remind_datetime = datetime.now() + delta

    await set_reminder(
        user_id,
        remind_datetime.isoformat()
    )

    await callback.message.edit_text(
        f"✅ Напоминание установлено.\n\n"
        f"Я напомню тебе через {callback.data.replace('remind_', '')}."
    )

    await callback.answer()

@router.callback_query(F.data == "shuffle_words")
async def shuffle_words_callback(callback: CallbackQuery):

    await shuffle_words(callback.from_user.id)

    from handlers.word import study_sessions
    study_sessions.pop(callback.from_user.id, None)

    await callback.answer("✅ Слова перемешаны!")

    callback.data = "my_words"
    await back_to_words(callback)