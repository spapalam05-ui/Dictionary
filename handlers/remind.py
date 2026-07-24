import asyncio
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import get_reminders
from keyboards.remind_keyboard import remind_keyboard

router = Router()


@router.message(Command("remind"))
async def remind(message: Message):
    await message.answer(
        "⏰ Через сколько напомнить повторить слова?",
        reply_markup=remind_keyboard
    )


async def reminder_loop(bot):
    while True:

        now = datetime.now()

        reminders = await get_reminders()

        for user_id, remind_datetime in reminders:

            remind_datetime = datetime.fromisoformat(remind_datetime)

            if now >= remind_datetime:
                try:
                    await bot.send_message(
                        user_id,
                        "📚 Время повторить слова!\n\nНажми /word 🇬🇧"
                    )

                    from database import delete_reminder
                    await delete_reminder(user_id)

                except Exception as e:
                    print(e)

        await asyncio.sleep(30)