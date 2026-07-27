from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from database import (
    get_payment_charge_id,
    mark_payment_refunded,
    remove_premium,
)

router = Router()


from config import ADMIN_ID


@router.message(Command("refund"))
async def refund_star_payment(
    message: Message,
    bot: Bot,
) -> None:

    # Команда доступна только тебе
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет доступа.")
        return

    # Использование:
    # /refund 987654321
    command_parts = message.text.split()

    if len(command_parts) != 2:
        await message.answer(
            "❌ Неверный формат.\n\n"
            "Используй:\n"
            "<code>/refund ID_покупателя</code>",
            parse_mode="HTML",
        )
        return

    try:
        buyer_user_id = int(command_parts[1])
    except ValueError:
        await message.answer(
            "❌ Telegram ID должен состоять только из цифр."
        )
        return

    payment_charge_id = await get_payment_charge_id(
        buyer_user_id
    )

    if not payment_charge_id:
        await message.answer(
            "❌ У этого пользователя не найден платёж.\n\n"
            "Проверь его Telegram ID."
        )
        return

    try:
        refunded = await bot.refund_star_payment(
            user_id=buyer_user_id,
            telegram_payment_charge_id=payment_charge_id,
        )

        if not refunded:
            await message.answer(
                "❌ Telegram не подтвердил возврат."
            )
            return

        await remove_premium(buyer_user_id)

        await mark_payment_refunded(payment_charge_id)
        await remove_premium(buyer_user_id)

        await message.answer(
            "✅ <b>Возврат выполнен!</b>\n\n"
            f"👤 Пользователь: <code>{buyer_user_id}</code>\n"
            "⭐ Stars возвращены покупателю.\n"
            "👑 Premium отключён.",
            parse_mode="HTML",
        )

    except Exception as error:
        await message.answer(
            "❌ <b>Ошибка возврата:</b>\n\n"
            f"<code>{error}</code>",
            parse_mode="HTML",
        )