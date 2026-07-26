from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import get_users_count

router = Router()

ADMIN_ID = 1203468356


@router.message(Command("users"))
async def users_count(message: Message):
    print("/users от", message.from_user.id)

    if message.from_user.id != ADMIN_ID:
        return

    count = await get_users_count()

    await message.answer(
        f"👥 Всего пользователей: {count}"
    )