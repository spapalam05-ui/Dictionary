from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database import get_words
from keyboards.word_keyboard import show_translation_keyboard
from aiogram.fsm.context import FSMContext

router = Router()

# Последняя показанная карточка пользователя
last_words: dict[int, tuple[int, str, str]] = {}

# Активные уроки пользователей
study_sessions: dict[int, dict] = {}


def lesson_finished_keyboard(
    category_id: int | None = None,
    show_repeat: bool = False,
) -> InlineKeyboardMarkup | None:
    buttons: list[list[InlineKeyboardButton]] = []

    if show_repeat:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🔁 Повторить забытые слова",
                    callback_data="start_repeat",
                )
            ]
        )

    if category_id is not None:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="📁 Вернуться в папку",
                    callback_data=f"open_category:{category_id}",
                )
            ]
        )

    if not buttons:
        return None

    return InlineKeyboardMarkup(
        inline_keyboard=buttons,
    )


async def show_next_word(
    message: Message,
    user_id: int,
) -> None:
    session = study_sessions.get(user_id)

    if session is None:
        await message.answer(
            "📚 У тебя пока нет активного урока.\n"
            "Нажми «📖 Карточка» или выбери папку."
        )
        return

    words = session.get("words", [])

    if not words:
        study_sessions.pop(user_id, None)
        last_words.pop(user_id, None)

        await message.answer(
            "📚 Нет доступных слов."
        )
        return

    index = session.get("index", 0)
    repeat_mode = session.get("repeat_mode", False)
    category_id = session.get("category_id")
    category_name = session.get("category_name")

    # =====================================================
    # УРОК ЗАКОНЧИЛСЯ
    # =====================================================
    if index >= len(words):

        # Закончили основной урок
        if not repeat_mode:
            forgotten_words = session.get("repeat", [])

            if forgotten_words:
                keyboard = lesson_finished_keyboard(
                    category_id=category_id,
                    show_repeat=True,
                )

                await message.answer(
                    "🎉 <b>Основной урок завершён!</b>\n\n"
                    f"Ты пока не запомнил слов: "
                    f"<b>{len(forgotten_words)}</b>",
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
                return

            study_sessions.pop(user_id, None)
            last_words.pop(user_id, None)

            keyboard = lesson_finished_keyboard(
                category_id=category_id,
            )

            if category_name:
                text = (
                    "🏆 <b>Поздравляем!</b>\n\n"
                    f"Ты прошёл все карточки из папки "
                    f"<b>{category_name}</b>!"
                )
            else:
                text = (
                    "🏆 <b>Поздравляем!</b>\n\n"
                    "Ты выучил все слова!"
                )

            await message.answer(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            return

        # Закончили повторение
        forgotten_words = session.get("repeat", [])

        if forgotten_words:
            session["words"] = forgotten_words.copy()
            session["repeat"] = []
            session["index"] = 0
            session["repeat_mode"] = True

            await message.answer(
                "🔁 Повторяем слова, которые ты "
                "ещё не запомнил."
            )

            await show_next_word(
                message,
                user_id,
            )
            return

        study_sessions.pop(user_id, None)
        last_words.pop(user_id, None)

        keyboard = lesson_finished_keyboard(
            category_id=category_id,
        )

        if category_name:
            text = (
                "🏆 <b>Поздравляем!</b>\n\n"
                f"Ты выучил все слова из папки "
                f"<b>{category_name}</b>!"
            )
        else:
            text = (
                "🏆 <b>Поздравляем!</b>\n\n"
                "Ты выучил все слова!"
            )

        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return

    # =====================================================
    # ПОКАЗЫВАЕМ СЛЕДУЮЩУЮ КАРТОЧКУ
    # =====================================================
    word_id, english, russian = words[index]

    last_words[user_id] = (
        word_id,
        english,
        russian,
    )

    if repeat_mode:
        title = "🔁 Повторение"
    elif category_name:
        title = f"📁 {category_name}"
    else:
        title = "📖 Карточка"

    await message.answer(
        f"{title}\n\n"
        f"<b>{index + 1}/{len(words)}</b>\n\n"
        f"🇬🇧 <b>{english}</b>\n\n"
        "🤔 Попробуй вспомнить перевод.",
        reply_markup=show_translation_keyboard,
        parse_mode="HTML",
    )


# =========================================================
# ОБЫЧНЫЕ КАРТОЧКИ — ВСЕ СЛОВА
# =========================================================

@router.message(Command("word"))
async def word(message: Message) -> None:
    user_id = message.from_user.id

    # Команда /word начинает обычный урок заново,
    # если сейчас активен урок из папки.
    current_session = study_sessions.get(user_id)

    if (
        current_session is None
        or current_session.get("category_id") is not None
    ):
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
            "repeat_mode": False,
            "category_id": None,
            "category_name": None,
        }

    await show_next_word(
        message,
        user_id,
    )


@router.message(F.text == "📖 Карточка")
async def word_button(
    message: Message,
    state: FSMContext,
) -> None:
    await state.clear()

    print("✅ НАЖАТА КНОПКА КАРТОЧКА")

    await word(message)


# =========================================================
# ОБНОВЛЕНИЕ КАРТОЧЕК
# =========================================================

@router.message(F.text == "🔄 Обновить карточки")
async def reset_words(message: Message) -> None:
    user_id = message.from_user.id

    study_sessions.pop(user_id, None)
    last_words.pop(user_id, None)

    await message.answer(
        "✅ Карточки обновлены.\n\n"
        "Нажми «📖 Карточка», чтобы начать заново."
    )