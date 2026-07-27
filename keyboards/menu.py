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
            KeyboardButton(text="📊 Статистика"),
            KeyboardButton(text="📁 Папки"),
        ],
        [
            KeyboardButton(text="⏰ Напоминание"),
            KeyboardButton(text="⭐ Premium"),
        ],
        [
            KeyboardButton(text="❓ Помощь"),
        ],
    ],
    resize_keyboard=True
)