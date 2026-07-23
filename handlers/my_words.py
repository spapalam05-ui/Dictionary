from database import get_all_words, delete_word
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


router = Router()


# 📋 Мои слова
@router.message(F.text == "📋 Мои слова")
async def my_words(message: Message):

    words = await get_all_words(message.from_user.id)

    if not words:
        await message.answer("📚 У тебя пока нет слов.")
        return

    keyboard = []

    for word_id, english, russian in words:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"🇬🇧 {english}",
                    callback_data=f"word_{word_id}"
                )
            ]
        )

    await message.answer(
        "📚 <b>Выбери слово:</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML"
    )


# Открыть слово
@router.callback_query(F.data.startswith("word_"))
async def open_word(callback: CallbackQuery):

    word_id = int(callback.data.split("_")[1])

    words = await get_all_words(callback.from_user.id)

    for wid, english, russian in words:

        if wid == word_id:

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✏️ Редактировать",
                            callback_data=f"edit_{word_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад",
                            callback_data="my_words"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🗑️ Удалить",
                            callback_data=f"delete_{word_id}"
                        )
                    ]
                ]
            )


            await callback.message.edit_text(
                f"🇬🇧 <b>{english}</b>\n"
                f"🇷🇺 {russian}",
                reply_markup=keyboard,
                parse_mode="HTML"
            )

            break

    await callback.answer()


# Подтверждение удаления
@router.callback_query(
    F.data.startswith("delete_") &
    ~F.data.startswith("delete_yes_")
)
async def delete_confirm(callback: CallbackQuery):

    word_id = int(callback.data.split("_")[1])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да",
                    callback_data=f"delete_yes_{word_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Нет",
                    callback_data="my_words"
                )
            ]
        ]
    )


    await callback.message.edit_text(
        "🗑️ <b>Удалить это слово?</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


# Удаление слова
@router.callback_query(F.data.startswith("delete_yes_"))
async def delete_yes(callback: CallbackQuery):

    word_id = int(callback.data.split("_")[2])

    await delete_word(word_id)
    from handlers.word import study_sessions

    study_sessions.pop(callback.from_user.id, None)

    await callback.answer("✅ Слово удалено")

    await back_to_words(callback)


# Возврат к списку слов
@router.callback_query(F.data == "my_words")
async def back_to_words(callback: CallbackQuery):

    words = await get_all_words(callback.from_user.id)


    if not words:
        await callback.message.edit_text(
            "📚 У тебя пока нет слов."
        )

        await callback.answer()
        return


    keyboard = []

    for word_id, english, russian in words:

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"🇬🇧 {english}",
                    callback_data=f"word_{word_id}"
                )
            ]
        )


    await callback.message.edit_text(
        "📚 <b>Выбери слово:</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML"
    )

    await callback.answer()