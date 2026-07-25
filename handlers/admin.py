from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message()
async def admin_commands(message: Message):
    print("TEXT =", repr(message.text))
    await message.answer("Получил: " + str(message.text))