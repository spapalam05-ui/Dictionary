from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database import is_premium

router = Router()


@router.message(F.text == "⭐ Premium")
async def premium_menu(message: Message):

    premium = await is_premium(message.from_user.id)

    if premium:
        text = (
            "⭐ <b>Premium</b>\n\n"
            "Добро пожаловать в Premium!"
        )
    else:
        text = (
            "⭐ <b>Premium</b>\n\n"
            "У тебя пока нет Premium."
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📂 Категории",
                    callback_data="my_categories"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Купить Premium",
                    callback_data="buy_premium"
                )
            ]
        ]
    )

    await message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )