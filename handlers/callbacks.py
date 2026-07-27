from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from database import (
    delete_reminder,
    is_premium,
    set_reminder,
    shuffle_words,
)
from handlers.my_words import back_to_words
from handlers.word import (
    last_words,
    show_next_word,
    study_sessions,
)


router = Router()


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ КЛАВИАТУРЫ
# =========================================================

def answer_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки ответа для Premium-пользователей.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Не знаю",
                    callback_data="dontknow",
                ),
                InlineKeyboardButton(
                    text="✅ Знаю",
                    callback_data="know",
                ),
            ]
        ]
    )


def next_word_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопка перехода к следующему слову.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➡️ Следующее слово",
                    callback_data="next_word",
                )
            ]
        ]
    )


def get_card_title(user_id: int) -> str:
    """
    Возвращает заголовок текущего урока.
    """
    session = study_sessions.get(user_id)

    if session is None:
        return "📖 Карточка"

    if session.get("repeat_mode"):
        return "🔁 Повторение"

    category_name = session.get("category_name")

    if category_name:
        return f"📁 {category_name}"

    return "📖 Карточка"


async def safe_edit_text(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> bool:
    """
    Безопасно изменяет сообщение.

    Если Telegram сообщает, что сообщение не изменилось,
    ошибка игнорируется.
    """
    try:
        await callback.message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
        return True

    except TelegramBadRequest as error:
        if "message is not modified" in str(error):
            return False

        raise


async def safe_delete_message(
    callback: CallbackQuery,
) -> None:
    """
    Безопасно удаляет сообщение.
    """
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass


# =========================================================
# ПОКАЗ ПЕРЕВОДА
# =========================================================

@router.callback_query(F.data == "show_translation")
async def show_translation(
    callback: CallbackQuery,
) -> None:
    user_id = callback.from_user.id

    word = last_words.get(user_id)
    session = study_sessions.get(user_id)

    if word is None or session is None:
        await callback.answer(
            "Карточка уже устарела.",
            show_alert=True,
        )
        return

    _, english, russian = word

    index = session.get("index", 0)
    words = session.get("words", [])
    title = get_card_title(user_id)

    premium = await is_premium(user_id)

    if premium:
        keyboard = answer_keyboard()

        additional_text = (
            "\n\nВыбери, запомнил ли ты это слово:"
        )
    else:
        keyboard = next_word_keyboard()

        additional_text = (
            "\n\n➡️ Нажми «Следующее слово».\n\n"
            "⭐ В Premium доступны кнопки "
            "«Знаю» и «Не знаю», а также повторение "
            "забытых слов."
        )

    await safe_edit_text(
        callback=callback,
        text=(
            f"{title}\n\n"
            f"<b>{index + 1}/{len(words)}</b>\n\n"
            f"🇬🇧 <b>{english}</b>\n"
            f"🇷🇺 <b>{russian}</b>"
            f"{additional_text}"
        ),
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# ОТВЕТ «НЕ ЗНАЮ» — PREMIUM
# =========================================================

@router.callback_query(F.data == "dontknow")
async def dontknow(
    callback: CallbackQuery,
) -> None:
    user_id = callback.from_user.id

    if not await is_premium(user_id):
        await callback.answer(
            "⭐ Эта функция доступна только в Premium.",
            show_alert=True,
        )
        return

    session = study_sessions.get(user_id)

    if session is None:
        await callback.answer(
            "Урок уже завершён.",
            show_alert=True,
        )
        return

    words = session.get("words", [])
    index = session.get("index", 0)

    if index >= len(words):
        await callback.answer(
            "Эта карточка уже обработана.",
            show_alert=True,
        )
        return

    word = words[index]
    repeat_words = session.setdefault("repeat", [])

    # Не добавляем одно слово в повторение несколько раз.
    if word not in repeat_words:
        repeat_words.append(word)

    session["index"] = index + 1

    last_words.pop(user_id, None)

    await safe_edit_text(
        callback=callback,
        text=(
            "❌ <b>Не страшно!</b>\n\n"
            "Это слово попадёт в повторение."
        ),
        reply_markup=next_word_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer(
        "🔁 Слово добавлено на повторение."
    )


# =========================================================
# ОТВЕТ «ЗНАЮ» — PREMIUM
# =========================================================

@router.callback_query(F.data == "know")
async def know(
    callback: CallbackQuery,
) -> None:
    user_id = callback.from_user.id

    if not await is_premium(user_id):
        await callback.answer(
            "⭐ Эта функция доступна только в Premium.",
            show_alert=True,
        )
        return

    session = study_sessions.get(user_id)

    if session is None:
        await callback.answer(
            "Урок уже завершён.",
            show_alert=True,
        )
        return

    words = session.get("words", [])
    index = session.get("index", 0)

    if index >= len(words):
        await callback.answer(
            "Эта карточка уже обработана.",
            show_alert=True,
        )
        return

    word = words[index]

    # Во время повторения правильный ответ
    # удаляет слово из списка забытых.
    if session.get("repeat_mode"):
        repeat_words = session.setdefault(
            "repeat",
            [],
        )

        if word in repeat_words:
            repeat_words.remove(word)

    session["index"] = index + 1

    last_words.pop(user_id, None)

    await safe_edit_text(
        callback=callback,
        text="✅ <b>Отлично!</b>",
        reply_markup=next_word_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer("✅ Правильно!")


# =========================================================
# СЛЕДУЮЩАЯ КАРТОЧКА
# =========================================================

@router.callback_query(F.data == "next_word")
async def next_word(
    callback: CallbackQuery,
) -> None:
    user_id = callback.from_user.id

    if user_id not in study_sessions:
        await callback.answer(
            "Урок уже завершён.",
            show_alert=True,
        )
        return

    await callback.answer()

    await safe_delete_message(callback)

    await show_next_word(
        callback.message,
        user_id,
    )


# =========================================================
# ПОВТОР ЗАБЫТЫХ СЛОВ — PREMIUM
# =========================================================

@router.callback_query(F.data == "start_repeat")
async def start_repeat(
    callback: CallbackQuery,
) -> None:
    user_id = callback.from_user.id

    if not await is_premium(user_id):
        await callback.answer(
            "⭐ Повторение забытых слов доступно "
            "только в Premium.",
            show_alert=True,
        )
        return

    session = study_sessions.get(user_id)

    if session is None:
        await callback.answer(
            "Урок уже завершён.",
            show_alert=True,
        )
        return

    repeat_words = session.get("repeat", [])

    if not repeat_words:
        await callback.answer(
            "Нет слов для повторения.",
            show_alert=True,
        )
        return

    session["words"] = repeat_words.copy()
    session["index"] = 0
    session["repeat_mode"] = True

    await callback.answer()

    await safe_delete_message(callback)

    await callback.message.answer(
        "🔁 <b>Начинаем повторение забытых слов!</b>",
        parse_mode="HTML",
    )

    await show_next_word(
        callback.message,
        user_id,
    )


# =========================================================
# НАПОМИНАНИЯ — PREMIUM
# =========================================================

@router.callback_query(F.data.startswith("remind_"))
async def reminder_buttons(
    callback: CallbackQuery,
) -> None:
    user_id = callback.from_user.id

    if not await is_premium(user_id):
        await callback.answer(
            "⭐ Напоминания доступны только в Premium.",
            show_alert=True,
        )
        return

    if callback.data == "remind_off":
        await delete_reminder(user_id)

        await safe_edit_text(
            callback=callback,
            text="❌ Напоминание отключено.",
        )

        await callback.answer(
            "Напоминание отключено."
        )
        return

    reminder_options = {
        "remind_30m": (
            timedelta(minutes=30),
            "30 минут",
        ),
        "remind_1h": (
            timedelta(hours=1),
            "1 час",
        ),
        "remind_3h": (
            timedelta(hours=3),
            "3 часа",
        ),
        "remind_6h": (
            timedelta(hours=6),
            "6 часов",
        ),
        "remind_1d": (
            timedelta(days=1),
            "1 день",
        ),
    }

    option = reminder_options.get(callback.data)

    if option is None:
        await callback.answer(
            "Неизвестный вариант напоминания.",
            show_alert=True,
        )
        return

    delta, readable_time = option

    remind_datetime = datetime.now() + delta

    await set_reminder(
        user_id,
        remind_datetime.isoformat(),
    )

    await safe_edit_text(
        callback=callback,
        text=(
            "✅ Напоминание установлено.\n\n"
            f"Я напомню тебе через {readable_time}."
        ),
    )

    await callback.answer(
        "✅ Напоминание установлено!"
    )


# =========================================================
# ПЕРЕМЕШИВАНИЕ ОБЩЕГО СПИСКА СЛОВ
# =========================================================

@router.callback_query(F.data == "shuffle_words")
async def shuffle_words_callback(
    callback: CallbackQuery,
) -> None:
    user_id = callback.from_user.id

    await shuffle_words(user_id)

    # Сбрасываем текущий урок, чтобы карточки
    # загрузились в новом порядке.
    study_sessions.pop(user_id, None)
    last_words.pop(user_id, None)

    await callback.answer(
        "✅ Слова перемешаны!"
    )

    try:
        await back_to_words(callback)

    except TelegramBadRequest as error:
        # Если случайное перемешивание дало такой же порядок,
        # Telegram сообщает, что сообщение не изменилось.
        if "message is not modified" not in str(error):
            raise