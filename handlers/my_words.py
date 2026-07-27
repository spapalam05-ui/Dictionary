from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database import (
    get_all_words,
    delete_word,
    delete_all_words,
    update_word,
)
router = Router()

editing_words = {}
editing_data = {}


# =========================================================
# МОИ СЛОВА
# =========================================================

@router.message(F.text == "📋 Мои слова")
async def my_words(message: Message):

    words = await get_all_words(message.from_user.id)

    if not words:
        await message.answer(
            "📚 У тебя пока нет слов."
        )
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

    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔀 Перемешать слова",
                callback_data="shuffle_words"
            )
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                text="🗑 Удалить все слова",
                callback_data="delete_all_words"
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


# =========================================================
# ОТКРЫТЬ СЛОВО
# =========================================================

@router.callback_query(F.data.startswith("word_"))
async def open_word(callback: CallbackQuery):

    word_id = int(callback.data.split("_")[1])

    words = await get_all_words(callback.from_user.id)

    for wid, english, russian in words:

        if wid != word_id:
            continue

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

        try:
            await callback.message.edit_text(
                f"🇬🇧 <b>{english}</b>\n"
                f"🇷🇺 {russian}",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise

        break

    await callback.answer()


# =========================================================
# ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ
# =========================================================

@router.callback_query(
    F.data.startswith("delete_")
    & ~F.data.startswith("delete_yes_")
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

    try:
        await callback.message.edit_text(
            "🗑️ <b>Удалить это слово?</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise

    await callback.answer()


# =========================================================
# УДАЛЕНИЕ СЛОВА
# =========================================================

@router.callback_query(F.data.startswith("delete_yes_"))
async def delete_yes(callback: CallbackQuery):

    word_id = int(callback.data.split("_")[2])

    await delete_word(word_id)

    from handlers.word import study_sessions

    study_sessions.pop(callback.from_user.id, None)

    await callback.answer("✅ Слово удалено")

    await back_to_words(callback)

# =========================================================
# ВОЗВРАТ К СПИСКУ СЛОВ
# =========================================================

@router.callback_query(F.data == "my_words")
async def back_to_words(callback: CallbackQuery):

    words = await get_all_words(callback.from_user.id)

    if not words:
        try:
            await callback.message.edit_text(
                "📚 У тебя пока нет слов."
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise

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

    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔀 Перемешать слова",
                callback_data="shuffle_words"
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="🗑 Удалить все слова",
                callback_data="delete_all_words"
            )
        ]
    )

    try:
        await callback.message.edit_text(
            "📚 <b>Выбери слово:</b>",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard
            ),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise

    await callback.answer()


# =========================================================
# РЕДАКТИРОВАНИЕ
# =========================================================

@router.callback_query(F.data.startswith("edit_"))
async def edit_word(callback: CallbackQuery):

    word_id = int(callback.data.split("_")[1])

    editing_words[callback.from_user.id] = word_id

    try:
        await callback.message.edit_text(
            "✏️ Отправь новое слово в формате:\n\n"
            "apple - яблоко"
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise

    await callback.answer()


# =========================================================
# ПОЛУЧЕНИЕ НОВОГО ТЕКСТА
# =========================================================

def user_is_editing_word(message: Message) -> bool:
    return (
        message.from_user is not None
        and message.from_user.id in editing_words
    )


@router.message(user_is_editing_word)
async def process_edit(message: Message):

    user_id = message.from_user.id

    if not message.text:
        await message.answer(
            "❌ Отправь новое слово текстом."
        )
        return

    if "-" not in message.text:
        await message.answer(
            "❌ Неправильный формат.\n\n"
            "Напиши так:\n"
            "apple - яблоко"
        )
        return

    english, russian = map(
        str.strip,
        message.text.split("-", 1)
    )

    if not english or not russian:
        await message.answer(
            "❌ Оба слова должны быть заполнены.\n\n"
            "Например:\n"
            "apple - яблоко"
        )
        return

    editing_data[user_id] = (
        english,
        russian,
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💾 Сохранить",
                    callback_data="save_words"
                )
            ]
        ]
    )

    await message.answer(
        f"🇬🇧 {english}\n"
        f"🇷🇺 {russian}\n\n"
        "Нажми «💾 Сохранить».",
        reply_markup=keyboard
    )

    if "-" not in message.text:
        await message.answer(
            "❌ Формат:\n\napple - яблоко"
        )
        return

    english, russian = map(
        str.strip,
        message.text.split("-", 1)
    )

    editing_data[user_id] = (
        english,
        russian,
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💾 Сохранить",
                    callback_data="save_words"
                )
            ]
        ]
    )

    await message.answer(
        f"🇬🇧 {english}\n"
        f"🇷🇺 {russian}\n\n"
        "Нажми «Сохранить».",
        reply_markup=keyboard
    )

# =========================================================
# СОХРАНЕНИЕ ИЗМЕНЕНИЙ
# =========================================================

@router.callback_query(F.data == "save_words")
async def save_words(callback: CallbackQuery):

    user_id = callback.from_user.id

    if (
        user_id not in editing_words
        or user_id not in editing_data
    ):
        await callback.answer(
            "❌ Нет данных для сохранения",
            show_alert=True,
        )
        return

    word_id = editing_words[user_id]
    english, russian = editing_data[user_id]

    await update_word(
        word_id,
        english,
        russian,
    )

    from handlers.word import study_sessions

    # Сбрасываем текущую сессию,
    # чтобы карточки обновились.
    study_sessions.pop(user_id, None)

    del editing_words[user_id]
    del editing_data[user_id]

    await callback.answer(
        "✅ Изменения сохранены!"
    )

    await back_to_words(callback)


@router.callback_query(F.data == "delete_all_words")
async def delete_all_words_confirm(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Да, удалить",
                    callback_data="delete_all_words_yes",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="my_words",
                ),
            ]
        ]
    )

    await callback.message.edit_text(
        "⚠️ <b>Удалить все слова?</b>\n\n"
        "Это действие нельзя отменить.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    await callback.answer()


@router.callback_query(F.data == "delete_all_words_yes")
async def delete_all_words_yes(callback: CallbackQuery):

    user_id = callback.from_user.id

    await delete_all_words(user_id)

    from handlers.word import study_sessions, last_words

    study_sessions.pop(user_id, None)
    last_words.pop(user_id, None)

    await callback.message.edit_text(
        "✅ <b>Все слова успешно удалены.</b>",
        parse_mode="HTML",
    )

    await callback.answer()