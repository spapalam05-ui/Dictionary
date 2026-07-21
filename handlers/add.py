from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram import Router, F
from aiogram.types import Message

from database import add_word

router = Router()

@router.message(F.text == "➕ Добавить")
async def add_button(message: Message):
    await message.answer(
        "✍️ Напиши слово в формате:\n\n"
        "/add apple - яблоко"
    )

@router.message(Command("add"))
async def add(message: Message, command: CommandObject):
    print("TEXT =", message.text)
    print("ARGS =", command.args)

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