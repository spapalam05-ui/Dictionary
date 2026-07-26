from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

premium_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⭐ Купить Premium",
                callback_data="buy_premium"
            )
        ]
    ]
)
