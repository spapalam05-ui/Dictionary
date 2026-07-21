from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📖 Карточка"),
            KeyboardButton(text="➕ Добавить"),
        ],
        [
            KeyboardButton(text="📊 Статистика"),
            KeyboardButton(text="❓ Помощь"),
        ],
    ],
    resize_keyboard=True
)