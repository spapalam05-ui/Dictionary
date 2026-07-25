from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "/id")
async def my_id(message: Message):
    print("ID COMMAND")
    await message.answer(f"Твой ID: {message.from_user.id}")