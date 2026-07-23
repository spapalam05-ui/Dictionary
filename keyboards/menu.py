from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📖 Карточка"),
            KeyboardButton(text="➕ Добавить"),
        ],
        [   
            KeyboardButton(text="❓ Помощь"),
            KeyboardButton(text="📋 Мои слова")
        ],
    ],
    resize_keyboard=True
)