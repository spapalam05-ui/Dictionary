from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database import (
    is_premium,
    create_category,
    get_categories,
    get_category,
    delete_category,
    add_word,
    get_words,
)

from handlers.word import (
    study_sessions,
    show_next_word,
)


router = Router()


class CategoryStates(StatesGroup):
    waiting_for_category_name = State()
    waiting_for_category_word = State()


def categories_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Создать категорию",
                    callback_data="create_category"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📂 Мои категории",
                    callback_data="my_categories"
                )
            ]
        ]
    )


async def show_categories(
    message: Message,
    user_id: int,
    edit: bool = False
):
    categories = await get_categories(user_id)

    if not categories:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Создать категорию",
                        callback_data="create_category"
                    )
                ]
            ]
        )

        text = (
            "📂 <b>У тебя пока нет категорий.</b>\n\n"
            "Создай первую категорию, например:\n"
            "• Путешествия\n"
            "• Работа\n"
            "• Фильмы"
        )

    else:
        buttons = []

        for category_id, name, words_count in categories:
            buttons.append([
                InlineKeyboardButton(
                    text=f"📂 {name} — {words_count} слов",
                    callback_data=f"open_category:{category_id}"
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                text="➕ Создать категорию",
                callback_data="create_category"
            )
        ])

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=buttons
        )

        text = "📂 <b>Мои категории</b>"

    if edit:
        await message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


@router.message(F.text == "📂 Категории")
async def categories_button(message: Message):
    premium = await is_premium(message.from_user.id)

    if not premium:
        await message.answer(
            "🔒 <b>Категории доступны только в Premium.</b>\n\n"
            "⭐ Premium — 1990 ₸\n"
            "• Безлимит слов\n"
            "• Категории\n"
            "• Статистика\n"
            "• Серия обучения",
            parse_mode="HTML"
        )
        return

    await message.answer(
        "📂 <b>Категории слов</b>\n\n"
        "Разделяй слова по темам и учи только нужную категорию.",
        reply_markup=categories_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "my_categories")
async def my_categories_callback(callback: CallbackQuery):
    premium = await is_premium(callback.from_user.id)

    if not premium:
        await callback.answer(
            "Категории доступны только в Premium.",
            show_alert=True
        )
        return

    await show_categories(
        callback.message,
        callback.from_user.id,
        edit=True
    )

    await callback.answer()


@router.callback_query(F.data == "create_category")
async def create_category_callback(
    callback: CallbackQuery,
    state: FSMContext
):
    premium = await is_premium(callback.from_user.id)

    if not premium:
        await callback.answer(
            "Категории доступны только в Premium.",
            show_alert=True
        )
        return

    await state.set_state(
        CategoryStates.waiting_for_category_name
    )

    await callback.message.edit_text(
        "➕ <b>Создание категории</b>\n\n"
        "Напиши название категории.\n\n"
        "Например: <code>Путешествия</code>",
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(
    CategoryStates.waiting_for_category_name
)
async def receive_category_name(
    message: Message,
    state: FSMContext
):
    name = message.text.strip()

    if len(name) < 2:
        await message.answer(
            "❌ Название слишком короткое."
        )
        return

    if len(name) > 40:
        await message.answer(
            "❌ Название должно быть короче 40 символов."
        )
        return

    category_id = await create_category(
        message.from_user.id,
        name
    )

    if category_id is None:
        await message.answer(
            "❌ Категория с таким названием уже существует."
        )
        return

    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📂 Открыть категорию",
                    callback_data=f"open_category:{category_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📂 Все категории",
                    callback_data="my_categories"
                )
            ]
        ]
    )

    await message.answer(
        f"✅ Категория <b>{name}</b> создана!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(
    F.data.startswith("open_category:")
)
async def open_category(callback: CallbackQuery):
    category_id = int(
        callback.data.split(":")[1]
    )

    category = await get_category(
        callback.from_user.id,
        category_id
    )

    if category is None:
        await callback.answer(
            "Категория не найдена.",
            show_alert=True
        )
        return

    _, category_name = category

    words = await get_words(
        callback.from_user.id,
        category_id
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить слово",
                    callback_data=f"add_category_word:{category_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📖 Учить категорию",
                    callback_data=f"study_category:{category_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑️ Удалить категорию",
                    callback_data=f"confirm_delete_category:{category_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="my_categories"
                )
            ]
        ]
    )

    if words:
        words_preview = "\n".join(
            f"• 🇬🇧 {english} — 🇷🇺 {russian}"
            for _, english, russian in words[:10]
        )

        if len(words) > 10:
            words_preview += (
                f"\n\n…и ещё {len(words) - 10}"
            )
    else:
        words_preview = "В категории пока нет слов."

    await callback.message.edit_text(
        f"📂 <b>{category_name}</b>\n\n"
        f"📚 Слов: <b>{len(words)}</b>\n\n"
        f"{words_preview}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("add_category_word:")
)
async def add_category_word_callback(
    callback: CallbackQuery,
    state: FSMContext
):
    category_id = int(
        callback.data.split(":")[1]
    )

    category = await get_category(
        callback.from_user.id,
        category_id
    )

    if category is None:
        await callback.answer(
            "Категория не найдена.",
            show_alert=True
        )
        return

    await state.update_data(
        category_id=category_id
    )

    await state.set_state(
        CategoryStates.waiting_for_category_word
    )

    await callback.message.edit_text(
        f"➕ <b>Добавление слова</b>\n\n"
        f"Категория: <b>{category[1]}</b>\n\n"
        "Напиши слово в формате:\n"
        "<code>apple - яблоко</code>",
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(
    CategoryStates.waiting_for_category_word
)
async def receive_category_word(
    message: Message,
    state: FSMContext
):
    text = message.text.strip()

    if "-" not in text:
        await message.answer(
            "❌ Неправильный формат.\n\n"
            "Напиши так:\n"
            "<code>apple - яблоко</code>",
            parse_mode="HTML"
        )
        return

    english, russian = map(
        str.strip,
        text.split("-", 1)
    )

    if not english or not russian:
        await message.answer(
            "❌ Слово и перевод не должны быть пустыми."
        )
        return

    data = await state.get_data()
    category_id = data["category_id"]

    category = await get_category(
        message.from_user.id,
        category_id
    )

    if category is None:
        await state.clear()
        await message.answer(
            "❌ Категория больше не существует."
        )
        return

    added = await add_word(
        message.from_user.id,
        english,
        russian,
        category_id
    )

    if not added:
        await state.clear()
        await message.answer(
            "❌ Не удалось добавить слово."
        )
        return

    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить ещё",
                    callback_data=f"add_category_word:{category_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📂 Открыть категорию",
                    callback_data=f"open_category:{category_id}"
                )
            ]
        ]
    )

    await message.answer(
        f"✅ Слово добавлено в категорию "
        f"<b>{category[1]}</b>!\n\n"
        f"🇬🇧 {english}\n"
        f"🇷🇺 {russian}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(
    F.data.startswith("study_category:")
)
async def study_category(callback: CallbackQuery):
    category_id = int(
        callback.data.split(":")[1]
    )

    category = await get_category(
        callback.from_user.id,
        category_id
    )

    if category is None:
        await callback.answer(
            "Категория не найдена.",
            show_alert=True
        )
        return

    words = await get_words(
        callback.from_user.id,
        category_id
    )

    if not words:
        await callback.answer(
            "В этой категории пока нет слов.",
            show_alert=True
        )
        return

    user_id = callback.from_user.id

    study_sessions[user_id] = {
        "words": words,
        "index": 0,
        "repeat": [],
        "repeat_mode": False,
        "category_id": category_id
    }

    await callback.message.delete()

    await show_next_word(
        callback.message,
        user_id
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("confirm_delete_category:")
)
async def confirm_delete_category(
    callback: CallbackQuery
):
    category_id = int(
        callback.data.split(":")[1]
    )

    category = await get_category(
        callback.from_user.id,
        category_id
    )

    if category is None:
        await callback.answer(
            "Категория не найдена.",
            show_alert=True
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data=f"delete_category:{category_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=f"open_category:{category_id}"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        f"🗑️ Удалить категорию "
        f"<b>{category[1]}</b>?\n\n"
        "Слова не удалятся. Они останутся в общем списке.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("delete_category:")
)
async def delete_category_callback(
    callback: CallbackQuery
):
    category_id = int(
        callback.data.split(":")[1]
    )

    deleted = await delete_category(
        callback.from_user.id,
        category_id
    )

    if not deleted:
        await callback.answer(
            "Категория не найдена.",
            show_alert=True
        )
        return

    await callback.answer(
        "✅ Категория удалена"
    )

    await show_categories(
        callback.message,
        callback.from_user.id,
        edit=True
    )