from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from database import add_word, get_words_count

router = Router()


@router.message(F.text == "➕ Добавить")
async def add_button(message: Message):
    await message.answer(
        "✍️ Напиши слово в формате:\n\n"
        "/add apple - яблоко"
    )


@router.message(Command("add"))
async def add(message: Message, command: CommandObject):

    count = await get_words_count(message.from_user.id)

    if count >= 50:
        await message.answer(
            "❌ Ты достиг лимита в 50 слов.\n\n"
            "Удалите ненужные слова, чтобы добавить новые."
        )
        return

    if command.args is None:
        await message.answer(
            "Используй:\n"
            "/add apple - яблоко"
        )
        return

    if "-" not in command.args:
        await message.answer(
            "Используй:\n"
            "/add apple - яблоко"
        )
        return

    english, russian = map(str.strip, command.args.split("-", 1))

    await add_word(
        message.from_user.id,
        english,
        russian
    )

    await message.answer(
        f"✅ Слово добавлено!\n\n"
        f"🇬🇧 {english}\n"
        f"🇷🇺 {russian}"
    )