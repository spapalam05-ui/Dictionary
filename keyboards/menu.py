from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📖 Карточка"),
            KeyboardButton(text="➕ Добавить"),
        ],
        [
            KeyboardButton(text="⭐ Избранное"),
            KeyboardButton(text="📋 Мои слова"),
        ],
        [
            KeyboardButton(text="❓ Помощь"),
            KeyboardButton(text="📁 Папки"),
        ],
        [
            KeyboardButton(text="⏰ Напоминание"),
            KeyboardButton(text="⭐ Premium"),
        ],
    ],
    resize_keyboard=True
)