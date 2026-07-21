import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db

from handlers.start import router as start_router
from handlers.help import router as help_router
from handlers.add import router as add_router
from handlers.word import router as word_router
from handlers.callbacks import router as callbacks_router 
from handlers.stats import router as stats_router
from handlers.remind import router as remind_router

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(help_router)
dp.include_router(add_router)
dp.include_router(word_router)
dp.include_router(callbacks_router)
dp.include_router(stats_router)
dp.include_router(remind_router)


from handlers.remind import reminder_loop

async def main():
    await init_db()

    # запускаем напоминания
    asyncio.create_task(reminder_loop(bot))

    print("📚 DictionaryBot запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())