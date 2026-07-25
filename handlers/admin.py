from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

print("ADMIN LOADED")

router = Router()

@router.message(Command("id"))
async def my_id(message: Message):
    print("ID COMMAND")
    await message.answer(f"Твой ID: {message.from_user.id}")