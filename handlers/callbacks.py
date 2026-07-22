from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import update_weight
from handlers.word import last_words, word

router = Router()


@router.callback_query(F.data == "show_translation")
async def show_translation(callback: CallbackQuery):
    word_data = last_words.get(callback.from_user.id)

    if not word_data:
        await callback.answer("Сначала используй /word")
        return

    word_id, english, russian, weight = word_data

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Не знаю", callback_data="dontknow"),
                InlineKeyboardButton(text="🤔 Сомневаюсь", callback_data="maybe"),
                InlineKeyboardButton(text="✅ Знаю", callback_data="know"),
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
    word_data = last_words.get(callback.from_user.id)

    if not word_data:
        await callback.answer()
        return

    word_id, english, russian, weight = word_data

    await update_weight(word_id, 100)

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
        "😔 <b>Ничего страшного!</b>\n\n"
        "Это слово будет попадаться чаще, чтобы ты быстрее его запомнил.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "maybe")
async def maybe(callback: CallbackQuery):
    word_data = last_words.get(callback.from_user.id)

    if not word_data:
        await callback.answer()
        return

    word_id, english, russian, weight = word_data

    await update_weight(word_id, 30)

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
        "🙂 <b>Почти получилось!</b>\n\n"
        "Будем иногда повторять это слово, чтобы закрепить его.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "know")
async def know(callback: CallbackQuery):
    word_data = last_words.get(callback.from_user.id)

    if not word_data:
        await callback.answer()
        return

    word_id, english, russian, weight = word_data

    new_weight = max(1, weight // 2)
    await update_weight(word_id, new_weight)
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
        "🎉 <b>Отлично!</b>\n\n"
        "Теперь это слово будет показываться гораздо реже.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "next_word")
async def next_word(callback: CallbackQuery):
    await callback.message.delete()
    await word(callback.message)
    await callback.answer()