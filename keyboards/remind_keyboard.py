from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

remind_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⏰ Через 30 минут",
                callback_data="remind_30m"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏰ Через 1 час",
                callback_data="remind_1h"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏰ Через 3 часа",
                callback_data="remind_3h"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏰ Через 6 часов",
                callback_data="remind_6h"
            )
        ],
        [
            InlineKeyboardButton(
                text="🌙 Завтра",
                callback_data="remind_1d"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отключить напоминание",
                callback_data="remind_off"
            )
        ]
    ]
)