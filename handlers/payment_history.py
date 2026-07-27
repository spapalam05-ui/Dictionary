from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_ID
from database import (
    get_payments_statistics,
    get_premium_payments,
)

router = Router()


@router.message(Command("payments"))
async def show_payments(
    message: Message,
) -> None:

    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет доступа.")
        return

    statistics = await get_payments_statistics()
    payments = await get_premium_payments(limit=20)

    header = (
        "💳 <b>История оплат</b>\n\n"
        f"📦 Всего покупок: "
        f"<b>{statistics['payments_count']}</b>\n"
        f"⭐ Получено без возвратов: "
        f"<b>{statistics['received_stars']}</b>\n"
        f"↩️ Возвратов: "
        f"<b>{statistics['refunds_count']}</b>\n"
        f"⭐ Возвращено: "
        f"<b>{statistics['refunded_stars']}</b>\n\n"
    )

    if not payments:
        await message.answer(
            header + "Оплат пока не было.",
            parse_mode="HTML",
        )
        return

    payment_blocks = []

    for payment in payments:
        username = payment["username"]

        if username:
            username_text = f"@{escape(username)}"
        else:
            username_text = "Не указан"

        full_name = escape(
            payment["full_name"] or "Без имени"
        )

        paid_at = payment["paid_at"].strftime(
            "%d.%m.%Y %H:%M"
        )

        if payment["premium_until"]:
            premium_until = payment[
                "premium_until"
            ].strftime("%d.%m.%Y")
        else:
            premium_until = "Не указан"

        if payment["is_refunded"]:
            status = "↩️ Возвращён"
        else:
            status = "✅ Оплачен"

        payment_blocks.append(
            f"{status}\n"
            f"👤 {full_name}\n"
            f"🔗 {username_text}\n"
            f"🆔 <code>{payment['user_id']}</code>\n"
            f"⭐ {payment['amount']} "
            f"{payment['currency']}\n"
            f"📅 Оплата: {paid_at}\n"
            f"👑 Premium до: {premium_until}"
        )

    result = header + "\n\n".join(payment_blocks)

    await message.answer(
        result,
        parse_mode="HTML",
    )