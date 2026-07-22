from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


show_translation_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👀 Показать перевод",
                callback_data="show_translation"
            )
        ]
    ]
)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➡️ Следующее слово",
                callback_data="next_word"
            )
        ]
    ]
)