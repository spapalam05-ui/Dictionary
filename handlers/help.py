from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

from aiogram import F

@router.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    await help_command(message)

@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "📚 Команды:\n\n"
        "/add apple - яблоко\n"
        "/word - случайное слово\n"
    )


@router.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    await help_command(message)