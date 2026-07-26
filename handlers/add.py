from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import (
    add_word,
    get_words_count,
    is_premium,
)


router = Router()


@router.message(F.text == "➕ Добавить")
async def add_button(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    print("✅ НАЖАТА КНОПКА ДОБАВИТЬ")

    await message.answer(
        "✍️ Напиши слово в формате:\n\n"
        "<code>/add apple - яблоко</code>\n\n"
        "Для добавления в определённую категорию "
        "открой раздел «📂 Категории».",
        parse_mode="HTML",
    )


@router.message(Command("add"))
async def add(
    message: Message,
    command: CommandObject
):
    user_id = message.from_user.id

    count = await get_words_count(user_id)
    premium = await is_premium(user_id)

    if not premium and count >= 50:
        await message.answer(
            "❌ Ты достиг бесплатного лимита в 50 слов.\n\n"
            "⭐ Premium — 1990 ₸\n"
            "• Безлимит слов\n"
            "• Категории слов\n"
            "• Статистика\n"
            "• Серия обучения"
        )
        return

    if command.args is None or "-" not in command.args:
        await message.answer(
            "Используй:\n"
            "<code>/add apple - яблоко</code>",
            parse_mode="HTML"
        )
        return

    english, russian = map(
        str.strip,
        command.args.split("-", 1)
    )

    if not english or not russian:
        await message.answer(
            "❌ Слово и перевод не должны быть пустыми."
        )
        return

    await add_word(
        user_id,
        english,
        russian
    )

    await message.answer(
        f"✅ Слово добавлено!\n\n"
        f"🇬🇧 {english}\n"
        f"🇷🇺 {russian}"
    )