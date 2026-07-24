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
    session["repeat"].append(last_words[user_id])

    # Следующая карточка
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

    # Просто идём дальше
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

@router.callback_query(F.data == "next_word")
async def next_word(callback: CallbackQuery):

    user_id = callback.from_user.id
    session = study_sessions[user_id]

    # Если обычные слова закончились
    if session["index"] >= len(session["words"]):

        # Есть забытые слова
        if session["repeat"]:

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔁 Повторить забытые слова",
                            callback_data="start_repeat"
                        )
                    ]
                ]
            )

            await callback.message.edit_text(
                "📚 Основной урок закончен!\n\n"
                "Теперь повторим слова, которые ты не знал.",
                reply_markup=keyboard
            )

            await callback.answer()
            return

        # Всё выучено
        await callback.message.edit_text(
            "🎉 Поздравляю!\n\n"
            "Ты выучил все слова!"
        )

        study_sessions.pop(user_id, None)

        await callback.answer()
        return

    await callback.message.delete()

    await show_next_word(
        callback.message,
        user_id
    )

    await callback.answer()
