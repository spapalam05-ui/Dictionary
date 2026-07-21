from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from database import set_reminder

router = Router()


@router.message(Command("remind"))
async def remind(message: Message, command: CommandObject):

    if command.args is None:
        await message.answer(
            "Используй:\n/remind 20:00"
        )
        return

    remind_time = command.args.strip()

    if len(remind_time) != 5 or ":" not in remind_time:
        await message.answer(
            "❌ Неверный формат.\nПример: /remind 20:00"
        )
        return

    await set_reminder(
        message.from_user.id,
        remind_time
    )

    await message.answer(
        f"✅ Напоминание установлено на {remind_time}"
    )