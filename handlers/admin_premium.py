from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import ADMIN_ID
from database import activate_premium

router = Router()

PREMIUM_DAYS = 90


class AdminPremiumState(StatesGroup):
    waiting_for_user_id = State()


def admin_premium_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Выдать Premium",
                    callback_data="admin_give_premium",
                )
            ]
        ]
    )


@router.message(F.text == "/admin")
async def admin_panel(
    message: Message,
) -> None:

    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет доступа.")
        return

    await message.answer(
        "🛠 <b>Админ-панель</b>\n\n"
        "Выбери действие:",
        reply_markup=admin_premium_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_give_premium")
async def ask_user_id(
    callback,
    state: FSMContext,
) -> None:

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "⛔ У тебя нет доступа.",
            show_alert=True,
        )
        return

    await state.set_state(
        AdminPremiumState.waiting_for_user_id
    )

    await callback.message.answer(
        "👤 Отправь Telegram ID пользователя,\n"
        "которому нужно выдать Premium на 3 месяца.\n\n"
        "Например:\n"
        "<code>8974219370</code>",
        parse_mode="HTML",
    )

    await callback.answer()


@router.message(
    AdminPremiumState.waiting_for_user_id
)
async def give_premium_by_id(
    message: Message,
    state: FSMContext,
) -> None:

    if message.from_user.id != ADMIN_ID:
        await state.clear()
        await message.answer("⛔ У тебя нет доступа.")
        return

    try:
        user_id = int(message.text.strip())

    except (ValueError, AttributeError):
        await message.answer(
            "❌ ID должен состоять только из цифр.\n\n"
            "Попробуй ещё раз."
        )
        return

    premium_until = (
        datetime.now(timezone.utc)
        + timedelta(days=PREMIUM_DAYS)
    )

    await activate_premium(
        user_id=user_id,
        premium_until=premium_until,
        telegram_payment_charge_id=(
            f"admin_gift_{user_id}_"
            f"{int(datetime.now(timezone.utc).timestamp())}"
        ),
    )

    premium_until_text = premium_until.strftime(
        "%d.%m.%Y"
    )

    try:
        await message.bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 <b>Тебе выдан Premium!</b>\n\n"
                "👑 Срок: <b>3 месяца</b>\n"
                f"📅 Premium активен до: "
                f"<b>{premium_until_text}</b>\n\n"
                "Приятного изучения! 🚀"
            ),
            parse_mode="HTML",
        )

        user_notification = (
            "✅ Пользователь получил уведомление."
        )

    except Exception:
        user_notification = (
            "⚠️ Premium выдан, но сообщение пользователю "
            "не отправилось.\n"
            "Возможно, он ещё не запускал бота."
        )

    await state.clear()

    await message.answer(
        "✅ <b>Premium успешно выдан!</b>\n\n"
        f"👤 ID: <code>{user_id}</code>\n"
        "⏳ Срок: <b>3 месяца</b>\n"
        f"📅 До: <b>{premium_until_text}</b>\n\n"
        f"{user_notification}",
        parse_mode="HTML",
    )