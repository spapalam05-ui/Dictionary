from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database import (
    add_forgotten_word,
    add_learned_word,
    get_favorite_words,
    get_words,
    init_user_stats,
    is_favorite,
    is_premium,
    toggle_favorite,
)

router = Router()


# Последняя показанная карточка пользователя
last_words: dict[int, tuple[int, str, str]] = {}

# Активные уроки пользователей
study_sessions: dict[int, dict] = {}


# =========================================================
# КЛАВИАТУРЫ
# =========================================================

def show_translation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👁 Показать перевод",
                    callback_data="show_translation",
                )
            ]
        ]
    )


def premium_answer_keyboard(
    word_id: int,
    favorite: bool,
) -> InlineKeyboardMarkup:

    if favorite:
        favorite_text = "💛 Убрать из избранного"
    else:
        favorite_text = "⭐ В избранное"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Знаю",
                    callback_data="know_word",
                ),
                InlineKeyboardButton(
                    text="❌ Не знаю",
                    callback_data="dont_know_word",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=favorite_text,
                    callback_data=f"favorite_{word_id}",
                )
            ],
        ]
    )


def free_answer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➡️ Следующее",
                    callback_data="next_word",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐ Открыть Premium",
                    callback_data="premium",
                )
            ],
        ]
    )


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


# =========================================================
# ПОКАЗ СЛЕДУЮЩЕГО СЛОВА
# =========================================================

async def show_next_word(
    message: Message,
    user_id: int,
) -> None:

    session = study_sessions.get(user_id)


    if session is None:
        
        await message.answer(
            "📚 У тебя пока нет активного урока.\n\n"
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
                    f"❌ Слов для повторения: "
                    f"<b>{len(forgotten_words)}</b>\n\n"
                    "Нажми кнопку ниже, чтобы повторить их.",
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
                    "Ты прошёл все карточки!"
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
                "🔁 <b>Повторяем ещё раз слова, которые "
                "ты пока не запомнил.</b>",
                parse_mode="HTML",
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
    # ПОКАЗЫВАЕМ КАРТОЧКУ
    # =====================================================

    word_id, english, russian = words[index]

    last_words[user_id] = (
        word_id,
        english,
        russian,
    )

    if repeat_mode:
        title = "🔁 Повторение"
    elif session.get("favorite_mode"):
        title = "⭐ Избранное"
    elif category_name:
        title = f"📁 {category_name}"
    else:
        title = "📖 Карточка"

    await message.answer(
        f"{title}\n\n"
        f"<b>{index + 1}/{len(words)}</b>\n\n"
        f"🇬🇧 <b>{english}</b>\n\n"
        "🤔 Попробуй вспомнить перевод.",
        reply_markup=show_translation_keyboard(),
        parse_mode="HTML",
    )


# =========================================================
# ОБЫЧНЫЕ КАРТОЧКИ — ВСЕ СЛОВА
# =========================================================

@router.message(Command("word"))
async def word(message: Message) -> None:

    user_id = message.from_user.id

    current_session = study_sessions.get(user_id)

    # Создаём новый урок, если урока нет
    # или пользователь до этого учил слова из папки
    if (
        current_session is None
        or current_session.get("category_id") is not None
    ):
        words = await get_words(user_id)

        if not words:
            await message.answer(
                "📚 У тебя пока нет слов.\n\n"
                "Добавь слова через кнопку «➕ Добавить»."
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

    await word(message)


# =========================================================
# ПОКАЗ ПЕРЕВОДА
# =========================================================

@router.callback_query(F.data == "show_translation")
async def show_translation_callback(
    callback: CallbackQuery,
) -> None:

    user_id = callback.from_user.id
    session = study_sessions.get(user_id)
    current_word = last_words.get(user_id)

    if session is None or current_word is None:
        await callback.answer(
            "Урок уже завершён.",
            show_alert=True,
        )
        return

    word_id, english, russian = current_word

    premium = await is_premium(user_id)

    if premium:
        favorite = await is_favorite(
            user_id,
            word_id,
        )

        keyboard = premium_answer_keyboard(
            word_id,
            bool(favorite),
        )

        additional_text = (
            "Оцени, запомнил ли ты это слово:"
        )

    else:
        keyboard = free_answer_keyboard()

        additional_text = (
            "➡️ Нажми «Следующее».\n\n"
            "⭐ В Premium доступны кнопки "
            "«Знаю» и «Не знаю» с повторением слов."
        )

    await callback.message.edit_text(
        f"🇬🇧 <b>{english}</b>\n\n"
        f"🇷🇺 <b>{russian}</b>\n\n"
        f"{additional_text}",
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# ДОБАВИТЬ ИЛИ УБРАТЬ ИЗ ИЗБРАННОГО
# =========================================================

@router.callback_query(F.data.startswith("favorite_"))
async def favorite_callback(
    callback: CallbackQuery,
) -> None:

    user_id = callback.from_user.id

    if not await is_premium(user_id):
        await callback.answer(
            "⭐ Избранное доступно только в Premium.",
            show_alert=True,
        )
        return

    try:
        word_id = int(
            callback.data.split("_", 1)[1]
        )
    except (ValueError, IndexError):
        await callback.answer(
            "❌ Ошибка слова.",
            show_alert=True,
        )
        return

    current_word = last_words.get(user_id)

    if current_word is None or current_word[0] != word_id:
        await callback.answer(
            "Карточка уже устарела.",
            show_alert=True,
        )
        return

    await toggle_favorite(
        user_id,
        word_id,
    )

    favorite = await is_favorite(
        user_id,
        word_id,
    )

    await callback.message.edit_reply_markup(
        reply_markup=premium_answer_keyboard(
            word_id,
            bool(favorite),
        )
    )

    if favorite:
        await callback.answer(
            "⭐ Слово добавлено в избранное."
        )
    else:
        await callback.answer(
            "Слово удалено из избранного."
        )


# =========================================================
# БЕСПЛАТНО — СЛЕДУЮЩЕЕ СЛОВО
# =========================================================

@router.callback_query(F.data == "next_word")
async def next_word_callback(
    callback: CallbackQuery,
) -> None:

    user_id = callback.from_user.id
    session = study_sessions.get(user_id)

    if session is None:
        await callback.answer(
            "Урок уже завершён.",
            show_alert=True,
        )
        return

    session["index"] = session.get("index", 0) + 1

    await init_user_stats(user_id)
    await add_learned_word(user_id)

    last_words.pop(user_id, None)

    await callback.answer()
    await callback.message.delete()

    await show_next_word(
        callback.message,
        user_id,
    )


# =========================================================
# PREMIUM — ЗНАЮ
# =========================================================

@router.callback_query(F.data == "know_word")
async def know_word_callback(
    callback: CallbackQuery,
) -> None:

    user_id = callback.from_user.id

    if not await is_premium(user_id):
        await callback.answer(
            "Функция доступна только в Premium.",
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

    session["index"] = session.get("index", 0) + 1

    await init_user_stats(user_id)
    await add_learned_word(user_id)

    last_words.pop(user_id, None)

    await callback.answer("✅ Отлично!")
    await callback.message.delete()

    await show_next_word(
        callback.message,
        user_id,
    )


# =========================================================
# PREMIUM — НЕ ЗНАЮ
# =========================================================

@router.callback_query(F.data == "dont_know_word")
async def dont_know_word_callback(
    callback: CallbackQuery,
) -> None:

    user_id = callback.from_user.id

    if not await is_premium(user_id):
        await callback.answer(
            "Функция доступна только в Premium.",
            show_alert=True,
        )
        return

    session = study_sessions.get(user_id)
    current_word = last_words.get(user_id)

    if session is None or current_word is None:
        await callback.answer(
            "Урок уже завершён.",
            show_alert=True,
        )
        return

    forgotten_words = session.setdefault(
        "repeat",
        [],
    )

    # Не добавляем одно и то же слово дважды
    current_word_id = current_word[0]

    already_added = any(
        word[0] == current_word_id
        for word in forgotten_words
    )

    if not already_added:
        forgotten_words.append(current_word)

    session["index"] = session.get("index", 0) + 1

    await init_user_stats(user_id)
    await add_forgotten_word(user_id)

    last_words.pop(user_id, None)

    await callback.answer(
        "🔁 Слово добавлено на повторение."
    )

    await callback.message.delete()

    await show_next_word(
        callback.message,
        user_id,
    )


# =========================================================
# НАЧАТЬ ПОВТОРЕНИЕ
# =========================================================

@router.callback_query(F.data == "start_repeat")
async def start_repeat_callback(
    callback: CallbackQuery,
) -> None:

    user_id = callback.from_user.id

    if not await is_premium(user_id):
        await callback.answer(
            "Повторение забытых слов доступно "
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

    forgotten_words = session.get("repeat", [])

    if not forgotten_words:
        await callback.answer(
            "Нет слов для повторения.",
            show_alert=True,
        )
        return

    session["words"] = forgotten_words.copy()
    session["repeat"] = []
    session["index"] = 0
    session["repeat_mode"] = True

    await callback.answer()
    await callback.message.delete()

    await callback.message.answer(
        "🔁 <b>Начинаем повторение забытых слов!</b>",
        parse_mode="HTML",
    )

    await show_next_word(
        callback.message,
        user_id,
    )


# =========================================================
# ОБНОВЛЕНИЕ КАРТОЧЕК
# =========================================================

@router.message(F.text == "🔄 Обновить карточки")
async def reset_words(
    message: Message,
) -> None:

    user_id = message.from_user.id

    study_sessions.pop(user_id, None)
    last_words.pop(user_id, None)

    await message.answer(
        "✅ Карточки обновлены.\n\n"
        "Нажми «📖 Карточка», чтобы начать заново."
    )

# =========================================================
# КАРТОЧКИ ИЗ ИЗБРАННОГО
# =========================================================

@router.message(Command("favorites"))
@router.message(F.text == "⭐ Избранное")
async def favorite_words_lesson(
    message: Message,
    state: FSMContext,
) -> None:

    await state.clear()

    user_id = message.from_user.id

    if not await is_premium(user_id):
        await message.answer(
            "⭐ Избранное доступно только в Premium."
        )
        return

    favorite_words = await get_favorite_words(user_id)

    words = [
        (
            row["id"],
            row["english"],
            row["russian"],
        )
        for row in favorite_words
    ]

    if not words:
        await message.answer(
            "⭐ У тебя пока нет избранных слов.\n\n"
            "Открой карточку, покажи перевод и нажми "
            "«⭐ В избранное»."
        )
        return

    study_sessions[user_id] = {
        "words": words,
        "repeat": [],
        "index": 0,
        "repeat_mode": False,
        "favorite_mode": True,
        "category_id": None,
        "category_name": None,
    }

    last_words.pop(user_id, None)

    await message.answer(
        f"⭐ <b>Избранные слова</b>\n\n"
        f"Всего слов: <b>{len(words)}</b>",
        parse_mode="HTML",
    )

    await show_next_word(
        message,
        user_id,
    )