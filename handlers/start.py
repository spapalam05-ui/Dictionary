from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards.menu import menu
from database import add_user

router = Router()

@router.message()
async def test(message: Message):
    print(message.from_user.id)