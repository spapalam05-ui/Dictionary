from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import update_weight
from handlers.word import last_words

router = Router()


@router.callback_query(F.data == "show_translation")
async def show_translation(callback: CallbackQuery):
    word = last_words.get(callback.from_user.id)

    if not word:
        await callback.answer("Сначала используй /word")
        return

    word_id, english, russian, weight = word

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
    word = last_words.get(callback.from_user.id)

    if not word:
        await callback.answer()
        return

    word_id, english, russian, weight = word

    await update_weight(word_id, 70)

    await callback.message.edit_text(
        "😔 <b>Ничего страшного!</b>\n\n"
        "Это слово будет попадаться чаще, чтобы ты быстрее его запомнил.",
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "maybe")
async def maybe(callback: CallbackQuery):
    word = last_words.get(callback.from_user.id)

    if not word:
        await callback.answer()
        return

    word_id, english, russian, weight = word

    await update_weight(word_id, 25)

    await callback.message.edit_text(
        "🙂 <b>Почти получилось!</b>\n\n"
        "Будем иногда повторять это слово, чтобы закрепить его.",
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "know")
async def know(callback: CallbackQuery):
    word = last_words.get(callback.from_user.id)

    if not word:
        await callback.answer()
        return

    word_id, english, russian, weight = word

    await update_weight(word_id, 5)

    await callback.message.edit_text(
        "🎉 <b>Отлично!</b>\n\n"
        "Теперь это слово будет показываться гораздо реже.",
        parse_mode="HTML"
    )

    await callback.answer()