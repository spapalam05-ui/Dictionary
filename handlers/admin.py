from aiogram import Router
from aiogram.types import Message

from database import get_users_count

router = Router()

ADMIN_ID = 1203468356


@router.message()
async def admin_commands(message: Message):
    print("Получено:", repr(message.text))

    if message.text == "/id":
        await message.answer(f"Твой ID: {message.from_user.id}")
        return

    if message.text == "/users":
        if message.from_user.id != ADMIN_ID:
            await message.answer("Нет доступа")
            return

        count = await get_users_count()
        await message.answer(f"👥 Пользователей: {count}")