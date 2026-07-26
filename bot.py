import asyncio
import hashlib
import os

from aiohttp import web
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db, give_premium

from handlers.start import router as start_router
from handlers.help import router as help_router
from handlers.add import router as add_router
from handlers.word import router as word_router
from handlers.callbacks import router as callbacks_router
from handlers.remind import router as remind_router
from handlers.my_words import router as my_words_router
from handlers.admin import router as admin_router
from handlers.premium import router as premium_router
from handlers.remind import reminder_loop


ROBOKASSA_PASSWORD_2 = os.getenv("ROBOKASSA_PASSWORD_2")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

dp.include_router(admin_router)
dp.include_router(start_router)
dp.include_router(help_router)
dp.include_router(add_router)
dp.include_router(word_router)
dp.include_router(callbacks_router)
dp.include_router(remind_router)
dp.include_router(my_words_router)
dp.include_router(premium_router)


async def home(request: web.Request):
    return web.Response(text="DictionaryBot работает ✅")


async def payment_result(request: web.Request):
    if request.method == "POST":
        data = await request.post()
    else:
        data = request.query

    out_sum = data.get("OutSum")
    inv_id = data.get("InvId")
    signature_value = data.get("SignatureValue")

    # В InvId мы будем передавать Telegram ID пользователя
    user_id = inv_id

    if not out_sum or not inv_id or not signature_value:
        return web.Response(
            text="Не хватает параметров",
            status=400
        )

    if not ROBOKASSA_PASSWORD_2:
        print("❌ ROBOKASSA_PASSWORD_2 не найден")
        return web.Response(
            text="Ошибка настройки сервера",
            status=500
        )

    signature_string = (
        f"{out_sum}:{inv_id}:{ROBOKASSA_PASSWORD_2}"
    )

    calculated_signature = hashlib.sha256(
        signature_string.encode("utf-8")
    ).hexdigest()

    if calculated_signature.lower() != signature_value.lower():
        print("❌ Неверная подпись Robokassa")
        return web.Response(
            text="Неверная подпись",
            status=403
        )

    try:
        telegram_user_id = int(user_id)

        await give_premium(telegram_user_id)

        await bot.send_message(
            telegram_user_id,
            "🎉 <b>Оплата прошла успешно!</b>\n\n"
            "⭐ Premium активирован.",
            parse_mode="HTML"
        )

        print(
            f"✅ Premium выдан пользователю "
            f"{telegram_user_id}"
        )

    except ValueError:
        return web.Response(
            text="Неверный InvId",
            status=400
        )

    except Exception as error:
        print("❌ Ошибка обработки оплаты:", error)
        return web.Response(
            text="Ошибка обработки оплаты",
            status=500
        )

    # Robokassa требует ответ OK + номер счёта
    return web.Response(text=f"OK{inv_id}")


async def start_web_server():
    app = web.Application()

    app.router.add_get("/", home)
    app.router.add_get("/payment/result", payment_result)
    app.router.add_post("/payment/result", payment_result)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", "8080"))

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=port
    )

    await site.start()

    print(f"🌐 HTTP-сервер запущен на порту {port}")

    return runner


async def main():
    runner = None

    try:
        await init_db()

        runner = await start_web_server()

        asyncio.create_task(reminder_loop(bot))

        print("📚 DictionaryBot запущен!")

        await dp.start_polling(bot)

    except Exception:
        import traceback
        traceback.print_exc()

    finally:
        if runner:
            await runner.cleanup()

        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())