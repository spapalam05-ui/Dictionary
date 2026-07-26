from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database import (
    MAX_CATEGORIES,
    add_words_batch,
    create_category,
    delete_category,
    get_categories,
    get_categories_count,
    get_category,
    get_words,
    is_premium,
)
from handlers.word import show_next_word, study_sessions


router = Router()


class CategoryStates(StatesGroup):
    waiting_for_category_name = State()
    waiting_for_category_words = State()


# =========================================================
# КЛАВИАТУРЫ
# =========================================================

def categories_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Создать папку",
                    callback_data="create_category",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📂 Мои папки",
                    callback_data="my_categories",
                )
            ],
        ]
    )


def cancel_category_creation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="cancel_category_action",
                )
            ]
        ]
    )


def category_words_input_keyboard(
    category_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💾 Сохранить",
                    callback_data=f"save_category_words:{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=f"cancel_category_words:{category_id}",
                )
            ],
        ]
    )


def category_keyboard(
    category_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 Проходить карточки",
                    callback_data=f"study_category:{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ Добавить слова",
                    callback_data=f"add_category_words:{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Посмотреть слова",
                    callback_data=f"view_category_words:{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить папку",
                    callback_data=f"confirm_delete_category:{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="my_categories",
                )
            ],
        ]
    )


def back_to_category_keyboard(
    category_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Вернуться в папку",
                    callback_data=f"open_category:{category_id}",
                )
            ]
        ]
    )


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

async def safe_edit_text(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    try:
        await message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error).lower():
            raise


def parse_words(text: str) -> tuple[list[tuple[str, str]], list[str]]:
    """
    Разбирает текст вида:

    apple - яблоко
    banana - банан

    Возвращает:
    - правильные пары слов;
    - строки с ошибочным форматом.
    """
    words: list[tuple[str, str]] = []
    invalid_lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if "-" not in line:
            invalid_lines.append(line)
            continue

        english, russian = map(
            str.strip,
            line.split("-", 1),
        )

        if not english or not russian:
            invalid_lines.append(line)
            continue

        words.append((english, russian))

    return words, invalid_lines


async def show_categories(
    message: Message,
    user_id: int,
    edit: bool = False,
) -> None:
    categories = await get_categories(user_id)
    categories_count = len(categories)

    buttons: list[list[InlineKeyboardButton]] = []

    for category_id, name, words_count in categories:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"📁 {name} ({words_count})",
                    callback_data=f"open_category:{category_id}",
                )
            ]
        )

    if categories_count < MAX_CATEGORIES:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="➕ Создать папку",
                    callback_data="create_category",
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons,
    )

    if categories:
        text = (
            "📂 <b>Мои папки</b>\n\n"
            f"Создано: <b>{categories_count}/{MAX_CATEGORIES}</b>\n\n"
            "Выбери папку:"
        )
    else:
        text = (
            "📂 <b>У тебя пока нет папок</b>\n\n"
            "Создай папку, например:\n"
            "• Еда\n"
            "• Работа\n"
            "• Глаголы\n\n"
            f"Можно создать до <b>{MAX_CATEGORIES}</b> папок."
        )

    if edit:
        await safe_edit_text(
            message,
            text,
            keyboard,
        )
    else:
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


async def show_category(
    message: Message,
    user_id: int,
    category_id: int,
    edit: bool = True,
) -> bool:
    category = await get_category(
        user_id,
        category_id,
    )

    if category is None:
        if edit:
            await safe_edit_text(
                message,
                "❌ Папка не найдена.",
            )
        else:
            await message.answer("❌ Папка не найдена.")
        return False

    _, category_name = category

    words = await get_words(
        user_id,
        category_id,
    )

    text = (
        f"📁 <b>{category_name}</b>\n\n"
        f"📚 Слов: <b>{len(words)}</b>\n\n"
        "Выбери действие:"
    )

    keyboard = category_keyboard(category_id)

    if edit:
        await safe_edit_text(
            message,
            text,
            keyboard,
        )
    else:
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    return True


# =========================================================
# СПИСОК КАТЕГОРИЙ
# =========================================================

@router.callback_query(F.data == "my_categories")
async def my_categories_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await is_premium(callback.from_user.id):
        await callback.answer(
            "Категории доступны только в Premium.",
            show_alert=True,
        )
        return

    await state.clear()
    await callback.answer()

    await show_categories(
        callback.message,
        callback.from_user.id,
        edit=True,
    )


# =========================================================
# СОЗДАНИЕ КАТЕГОРИИ
# =========================================================

@router.callback_query(F.data == "create_category")
async def create_category_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    user_id = callback.from_user.id

    if not await is_premium(user_id):
        await callback.answer(
            "Категории доступны только в Premium.",
            show_alert=True,
        )
        return

    categories_count = await get_categories_count(user_id)

    if categories_count >= MAX_CATEGORIES:
        await callback.answer(
            f"Можно создать максимум {MAX_CATEGORIES} папок.",
            show_alert=True,
        )
        return

    await state.clear()
    await state.set_state(
        CategoryStates.waiting_for_category_name,
    )

    await safe_edit_text(
        callback.message,
        "➕ <b>Создание папки</b>\n\n"
        "Напиши название папки.\n\n"
        "Например:\n"
        "<code>Еда</code>",
        cancel_category_creation_keyboard(),
    )

    await callback.answer()


@router.message(
    CategoryStates.waiting_for_category_name,
)
async def receive_category_name(
    message: Message,
    state: FSMContext,
) -> None:
    if not message.text:
        await message.answer(
            "❌ Отправь название папки текстом.",
        )
        return

    name = message.text.strip()

    if len(name) < 2:
        await message.answer(
            "❌ Название слишком короткое.",
        )
        return

    if len(name) > 40:
        await message.answer(
            "❌ Название должно быть не длиннее 40 символов.",
        )
        return

    categories_count = await get_categories_count(
        message.from_user.id,
    )

    if categories_count >= MAX_CATEGORIES:
        await state.clear()
        await message.answer(
            f"❌ Можно создать максимум {MAX_CATEGORIES} папок.",
        )
        return

    category_id = await create_category(
        message.from_user.id,
        name,
    )

    if category_id is None:
        await message.answer(
            "❌ Папка с таким названием уже существует "
            "или достигнут лимит папок.",
        )
        return

    await state.set_state(
        CategoryStates.waiting_for_category_words,
    )
    await state.update_data(
        category_id=category_id,
        category_name=name,
        pending_words=[],
        creating_new_category=True,
    )

    await message.answer(
        f"✅ Папка <b>{name}</b> создана!\n\n"
        "Теперь отправь слова в формате:\n\n"
        "<code>apple - яблоко\n"
        "banana - банан\n"
        "house - дом</code>\n\n"
        "Можно отправлять слова несколькими сообщениями.\n"
        "Когда закончишь, нажми <b>💾 Сохранить</b>.",
        reply_markup=category_words_input_keyboard(
            category_id,
        ),
        parse_mode="HTML",
    )


# =========================================================
# ДОБАВЛЕНИЕ НЕСКОЛЬКИХ СЛОВ
# =========================================================

@router.callback_query(
    F.data.startswith("add_category_words:"),
)
async def add_category_words_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    category_id = int(
        callback.data.split(":", 1)[1],
    )

    category = await get_category(
        callback.from_user.id,
        category_id,
    )

    if category is None:
        await callback.answer(
            "Папка не найдена.",
            show_alert=True,
        )
        return

    await state.clear()
    await state.set_state(
        CategoryStates.waiting_for_category_words,
    )
    await state.update_data(
        category_id=category_id,
        category_name=category[1],
        pending_words=[],
        creating_new_category=False,
    )

    await safe_edit_text(
        callback.message,
        f"➕ <b>Добавление слов</b>\n\n"
        f"Папка: <b>{category[1]}</b>\n\n"
        "Отправь слова в формате:\n\n"
        "<code>apple - яблоко\n"
        "banana - банан\n"
        "house - дом</code>\n\n"
        "Можно отправлять несколько сообщений.\n"
        "Когда закончишь, нажми <b>💾 Сохранить</b>.",
        category_words_input_keyboard(category_id),
    )

    await callback.answer()


@router.message(
    CategoryStates.waiting_for_category_words,
)
async def receive_category_words(
    message: Message,
    state: FSMContext,
) -> None:
    if not message.text:
        await message.answer(
            "❌ Отправь слова текстом.",
        )
        return

    words, invalid_lines = parse_words(
        message.text,
    )

    if not words:
        await message.answer(
            "❌ Не удалось найти слова.\n\n"
            "Правильный формат:\n"
            "<code>apple - яблоко</code>",
            parse_mode="HTML",
        )
        return

    data = await state.get_data()
    pending_words = data.get("pending_words", [])
    pending_words.extend(words)

    await state.update_data(
        pending_words=pending_words,
    )

    category_id = data.get("category_id")

    text = (
        f"✅ Добавлено в ожидание: <b>{len(words)}</b>\n"
        f"📚 Всего перед сохранением: "
        f"<b>{len(pending_words)}</b>"
    )

    if invalid_lines:
        preview = "\n".join(
            f"• {line}"
            for line in invalid_lines[:5]
        )

        text += (
            "\n\n⚠️ Эти строки пропущены:\n"
            f"<code>{preview}</code>"
        )

    text += (
        "\n\nМожешь отправить ещё слова "
        "или нажать <b>💾 Сохранить</b>."
    )

    await message.answer(
        text,
        reply_markup=category_words_input_keyboard(
            category_id,
        ),
        parse_mode="HTML",
    )


@router.callback_query(
    F.data.startswith("save_category_words:"),
)
async def save_category_words_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    category_id = int(
        callback.data.split(":", 1)[1],
    )

    data = await state.get_data()

    saved_category_id = data.get("category_id")
    pending_words = data.get("pending_words", [])

    if saved_category_id != category_id:
        await callback.answer(
            "Сессия добавления слов устарела.",
            show_alert=True,
        )
        await state.clear()
        return

    category = await get_category(
        callback.from_user.id,
        category_id,
    )

    if category is None:
        await state.clear()
        await callback.answer(
            "Папка больше не существует.",
            show_alert=True,
        )
        return

    if not pending_words:
        await callback.answer(
            "Сначала отправь хотя бы одно слово.",
            show_alert=True,
        )
        return

    added_count = await add_words_batch(
        callback.from_user.id,
        pending_words,
        category_id,
    )

    if added_count <= 0:
        await callback.answer(
            "Не удалось сохранить слова.",
            show_alert=True,
        )
        return

    await state.clear()
    await callback.answer(
        f"✅ Сохранено слов: {added_count}",
    )

    await safe_edit_text(
        callback.message,
        f"✅ В папку <b>{category[1]}</b> "
        f"сохранено слов: <b>{added_count}</b>.",
        category_keyboard(category_id),
    )


@router.callback_query(
    F.data.startswith("cancel_category_words:"),
)
async def cancel_category_words_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    category_id = int(
        callback.data.split(":", 1)[1],
    )

    data = await state.get_data()
    creating_new_category = data.get(
        "creating_new_category",
        False,
    )
    saved_category_id = data.get("category_id")

    await state.clear()

    if (
        creating_new_category
        and saved_category_id == category_id
    ):
        words = await get_words(
            callback.from_user.id,
            category_id,
        )

        if not words:
            await delete_category(
                callback.from_user.id,
                category_id,
            )
            await callback.answer(
                "Создание папки отменено.",
            )
            await show_categories(
                callback.message,
                callback.from_user.id,
                edit=True,
            )
            return

    await callback.answer("Добавление слов отменено.")

    await show_category(
        callback.message,
        callback.from_user.id,
        category_id,
        edit=True,
    )


@router.callback_query(
    F.data == "cancel_category_action",
)
async def cancel_category_action(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.clear()
    await callback.answer("Отменено.")

    await show_categories(
        callback.message,
        callback.from_user.id,
        edit=True,
    )


# =========================================================
# ОТКРЫТИЕ И ПРОСМОТР ПАПКИ
# =========================================================

@router.callback_query(
    F.data.startswith("open_category:"),
)
async def open_category_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    category_id = int(
        callback.data.split(":", 1)[1],
    )

    await state.clear()

    opened = await show_category(
        callback.message,
        callback.from_user.id,
        category_id,
        edit=True,
    )

    if opened:
        await callback.answer()
    else:
        await callback.answer(
            "Папка не найдена.",
            show_alert=True,
        )


@router.callback_query(
    F.data.startswith("view_category_words:"),
)
async def view_category_words_callback(
    callback: CallbackQuery,
) -> None:
    category_id = int(
        callback.data.split(":", 1)[1],
    )

    category = await get_category(
        callback.from_user.id,
        category_id,
    )

    if category is None:
        await callback.answer(
            "Папка не найдена.",
            show_alert=True,
        )
        return

    words = await get_words(
        callback.from_user.id,
        category_id,
    )

    if not words:
        text = (
            f"📋 <b>{category[1]}</b>\n\n"
            "В этой папке пока нет слов."
        )
    else:
        lines = [
            f"{index}. 🇬🇧 {english} — 🇷🇺 {russian}"
            for index, (_, english, russian)
            in enumerate(words, start=1)
        ]

        text = (
            f"📋 <b>{category[1]}</b>\n\n"
            + "\n".join(lines)
        )

        # Telegram ограничивает длину сообщения.
        if len(text) > 3900:
            text = (
                f"📋 <b>{category[1]}</b>\n\n"
                + "\n".join(lines[:100])
                + "\n\n…показаны первые 100 слов."
            )

    await safe_edit_text(
        callback.message,
        text,
        back_to_category_keyboard(category_id),
    )

    await callback.answer()


# =========================================================
# КАРТОЧКИ ПО КАТЕГОРИИ
# =========================================================

@router.callback_query(
    F.data.startswith("study_category:"),
)
async def study_category_callback(
    callback: CallbackQuery,
) -> None:
    category_id = int(
        callback.data.split(":", 1)[1],
    )

    category = await get_category(
        callback.from_user.id,
        category_id,
    )

    if category is None:
        await callback.answer(
            "Папка не найдена.",
            show_alert=True,
        )
        return

    words = await get_words(
        callback.from_user.id,
        category_id,
    )

    if not words:
        await callback.answer(
            "В этой папке пока нет слов.",
            show_alert=True,
        )
        return

    user_id = callback.from_user.id

    study_sessions[user_id] = {
        "words": words,
        "index": 0,
        "repeat": [],
        "repeat_mode": False,
        "category_id": category_id,
        "category_name": category[1],
    }

    await callback.answer()
    await callback.message.delete()

    await show_next_word(
        callback.message,
        user_id,
    )


# =========================================================
# УДАЛЕНИЕ КАТЕГОРИИ
# =========================================================

@router.callback_query(
    F.data.startswith("confirm_delete_category:"),
)
async def confirm_delete_category_callback(
    callback: CallbackQuery,
) -> None:
    category_id = int(
        callback.data.split(":", 1)[1],
    )

    category = await get_category(
        callback.from_user.id,
        category_id,
    )

    if category is None:
        await callback.answer(
            "Папка не найдена.",
            show_alert=True,
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data=f"delete_category:{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=f"open_category:{category_id}",
                )
            ],
        ]
    )

    await safe_edit_text(
        callback.message,
        f"🗑 <b>Удалить папку «{category[1]}»?</b>\n\n"
        "Слова не удалятся и останутся в общем списке.",
        keyboard,
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("delete_category:"),
)
async def delete_category_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    category_id = int(
        callback.data.split(":", 1)[1],
    )

    deleted = await delete_category(
        callback.from_user.id,
        category_id,
    )

    if not deleted:
        await callback.answer(
            "Папка не найдена.",
            show_alert=True,
        )
        return

    await state.clear()
    await callback.answer("✅ Папка удалена.")

    await show_categories(
        callback.message,
        callback.from_user.id,
        edit=True,
    )