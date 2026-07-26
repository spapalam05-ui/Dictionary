from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import get_words
from handlers.word import study_sessions, last_words, show_next_word


router = Router()


@router.message(F.text == "📖 Карточка")
async def cards_button(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    user_id = message.from_user.id
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

    last_words.pop(user_id, None)

    await show_next_word(message, user_id)


@router.message(F.text == "➕ Добавить")
async def add_button(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    await message.answer(
        "✍️ Напиши слово в формате:\n\n"
        "<code>/add apple - яблоко</code>\n\n"
        "Для добавления в определённую категорию "
        "открой раздел «📂 Категории».",
        parse_mode="HTML",
    )