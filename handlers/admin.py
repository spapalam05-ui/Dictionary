from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from database import get_users_count

router = Router()

print("ADMIN ROUTER LOADED")

ADMIN_ID = 1203468356

@router.message()
async def test(message: Message):
    print("Любое сообщение:", message.text)

@router.message(F.text == "/id")
async def my_id(message: Message):
    print("ID COMMAND WORKED")
    await message.answer(f"Твой ID: {message.from_user.id}")


@router.message(Command("users"))
async def users(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    count = await get_users_count()
    await message.answer(f"👥 Пользователей: {count}")