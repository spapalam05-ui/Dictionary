import asyncio
from datetime import datetime

from database import get_reminders


async def reminder_loop(bot):
    while True:
        now = datetime.now().strftime("%H:%M")

        reminders = await get_reminders()

        for user_id, remind_time in reminders:
            if remind_time == now:
                try:
                    await bot.send_message(
                        user_id,
                        "📚 Время повторить английские слова!\n\nИспользуй /word 🇬🇧"
                    )
                except Exception as e:
                    print(e)

        await asyncio.sleep(60)