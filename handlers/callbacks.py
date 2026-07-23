from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from handlers.word import last_words, word, user_decks

router = Router()


@router.callback_query(F.data == "show_translation")
async def show_translation(callback: CallbackQuery):
    word_data = last_words.get(callback.from_user.id)

    if not word_data:
        await callback.answer("Сначала используй /word")
        return

    word_id, english, russian = word_data

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
                ),
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

    word_data = last_words.get(user_id)

    if not word_data:
        await callback.answer()
        return

    # Добавляем слово в повторение
    user_decks[user_id]["repeat"].append(word_data)

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
        "❌ Это слово попадёт в повторение.",
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(F.data == "know")
async def know(callback: CallbackQuery):

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
        "✅ Отлично!",
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(F.data == "next_word")
async def next_word(callback: CallbackQuery):
    await callback.message.delete()
    await word(callback.message)
    await callback.answer()