import asyncio
import os

from aiohttp import web
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db

from handlers.start import router as start_router
from handlers.help import router as help_router
from handlers.add import router as add_router
from handlers.word import router as word_router
from handlers.callbacks import router as callbacks_router
from handlers.remind import router as remind_router
from handlers.my_words import router as my_words_router
from handlers.admin import router as admin_router
from handlers.remind import reminder_loop
from handlers.premium import router as premium_router
from handlers.payments import router as payments_router
from handlers.categories import router as categories_router
from handlers.menu_buttons import router as menu_buttons_router
from handlers.statistics import router as statistics_router
from handlers.refund import router as refund_router
from handlers.payment_history import (
    router as payment_history_router,
)


bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# =========================================================
# ПОДКЛЮЧЕНИЕ РОУТЕРОВ
# =========================================================

# Главное меню
dp.include_router(menu_buttons_router)

# Основные команды
dp.include_router(admin_router)
dp.include_router(start_router)

# Premium и оплата Telegram Stars
dp.include_router(premium_router)
dp.include_router(payments_router)
dp.include_router(refund_router)
dp.include_router(payment_history_router)

# Другие разделы
dp.include_router(help_router)
dp.include_router(remind_router)
dp.include_router(my_words_router)
dp.include_router(statistics_router)

# Обычные кнопки главного меню
dp.include_router(word_router)
dp.include_router(add_router)

# Категории
dp.include_router(categories_router)

# Общие callback-обработчики подключаем последними
dp.include_router(callbacks_router)


# =========================================================
# HTTP-СЕРВЕР ДЛЯ RAILWAY
# =========================================================

async def home(request: web.Request) -> web.Response:
    return web.Response(
        text="DictionaryBot работает ✅"
    )


async def start_web_server() -> web.AppRunner:
    app = web.Application()

    app.router.add_get("/", home)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", "8080"))

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=port,
    )

    await site.start()

    print(f"🌐 HTTP-сервер запущен на порту {port}")

    return runner


# =========================================================
# ЗАПУСК БОТА
# =========================================================

async def main() -> None:
    runner = None
    reminder_task = None

    try:
        await init_db()

        runner = await start_web_server()

        reminder_task = asyncio.create_task(
            reminder_loop(bot)
        )

        print("📚 DictionaryBot запущен!")

        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )

    except Exception:
        import traceback
        traceback.print_exc()

    finally:
        if reminder_task:
            reminder_task.cancel()

            try:
                await reminder_task
            except asyncio.CancelledError:
                pass

        if runner:
            await runner.cleanup()

        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())