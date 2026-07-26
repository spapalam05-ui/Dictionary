from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text == "⭐ Premium")
async def premium_menu(message: Message):
    print("✅ КНОПКА PREMIUM НАЖАТА")

    await message.answer(
        "⭐ Premium работает!"
    )