from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import get_users_count

router = Router()


@router.message(Command("id"))
async def my_id(message: Message):
    await message.answer(f"Твой ID: {message.from_user.id}")


ADMIN_ID = 123456789


@router.message(Command("users"))
async def users(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    count = await get_users_count()

    await message.answer(f"👥 Пользователей: {count}")