from datetime import datetime, timedelta, timezone
from html import escape

from aiogram import Bot, F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from config import ADMIN_ID
from database import (
    activate_premium,
    is_premium,
    save_premium_payment,
)

router = Router()


# =========================================================
# НАСТРОЙКИ PREMIUM
# =========================================================

PREMIUM_PRICE = 100
PREMIUM_DAYS = 90
PREMIUM_PAYLOAD = "dictionary_premium_90_days"


# =========================================================
# КЛАВИАТУРА ПОКУПКИ
# =========================================================

def premium_payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"⭐ Купить за {PREMIUM_PRICE} Stars",
                    callback_data="buy_premium_stars",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="premium",
                )
            ],
        ]
    )


# =========================================================
# ПОКАЗ ПРЕДЛОЖЕНИЯ PREMIUM
# =========================================================

@router.callback_query(F.data == "buy_premium")
async def buy_premium_menu(
    callback: CallbackQuery,
) -> None:

    user_id = callback.from_user.id

    if await is_premium(user_id):
        await callback.answer(
            "👑 У тебя уже активен Premium.",
            show_alert=True,
        )
        return

    await callback.message.answer(
        "👑 <b>DictionaryBot Premium</b>\n\n"
        "Открой дополнительные возможности:\n\n"
        "📂 категории и папки;\n"
        "🔄 выбор направления карточек;\n"
        "⭐ избранные слова;\n"
        "✅ кнопки «Знаю» и «Не знаю»;\n"
        "🔁 повторение забытых слов;\n"
        "⚡ массовое добавление слов;\n"
        "📊 расширенная статистика.\n\n"
        "━━━━━━━━━━━━━━\n"
        "⏳ Срок Premium: <b>3 месяца</b>\n"
        f"💰 Стоимость: <b>{PREMIUM_PRICE} ⭐</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "Оплата проходит безопасно внутри Telegram.",
        reply_markup=premium_payment_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# СОЗДАНИЕ СЧЁТА TELEGRAM STARS
# =========================================================

@router.callback_query(F.data == "buy_premium_stars")
async def send_premium_invoice(
    callback: CallbackQuery,
) -> None:

    user_id = callback.from_user.id

    if await is_premium(user_id):
        await callback.answer(
            "👑 У тебя уже активен Premium.",
            show_alert=True,
        )
        return

    prices = [
        LabeledPrice(
            label="Premium на 3 месяца",
            amount=PREMIUM_PRICE,
        )
    ]

    await callback.message.answer_invoice(
        title="DictionaryBot Premium",
        description=(
            "Premium-доступ ко всем функциям "
            "DictionaryBot на 3 месяца."
        ),
        payload=PREMIUM_PAYLOAD,
        currency="XTR",
        prices=prices,
        provider_token="",
    )

    await callback.answer()


# =========================================================
# ПРОВЕРКА ПЕРЕД ОПЛАТОЙ
# =========================================================

@router.pre_checkout_query()
async def process_pre_checkout_query(
    pre_checkout_query: PreCheckoutQuery,
) -> None:

    if pre_checkout_query.invoice_payload != PREMIUM_PAYLOAD:
        await pre_checkout_query.answer(
            ok=False,
            error_message=(
                "Не удалось проверить покупку. "
                "Попробуй создать счёт заново."
            ),
        )
        return

    if pre_checkout_query.currency != "XTR":
        await pre_checkout_query.answer(
            ok=False,
            error_message="Неверная валюта платежа.",
        )
        return

    if pre_checkout_query.total_amount != PREMIUM_PRICE:
        await pre_checkout_query.answer(
            ok=False,
            error_message="Неверная сумма платежа.",
        )
        return

    await pre_checkout_query.answer(ok=True)


# =========================================================
# УСПЕШНАЯ ОПЛАТА
# =========================================================

@router.message(F.successful_payment)
async def successful_premium_payment(
    message: Message,
    bot: Bot,
) -> None:

    payment = message.successful_payment

    if payment is None:
        return

    if payment.invoice_payload != PREMIUM_PAYLOAD:
        await message.answer(
            "❌ Платёж получен, но покупка не распознана.\n\n"
            "Напиши разработчику: @Num1233215"
        )
        return

    if payment.currency != "XTR":
        await message.answer(
            "❌ Получена неизвестная валюта платежа."
        )
        return

    if payment.total_amount != PREMIUM_PRICE:
        await message.answer(
            "❌ Сумма платежа не совпадает."
        )
        return

    user_id = message.from_user.id

    premium_until = (
        datetime.now(timezone.utc)
        + timedelta(days=PREMIUM_DAYS)
    )

    await activate_premium(
        user_id=user_id,
        premium_until=premium_until,
        telegram_payment_charge_id=(
            payment.telegram_payment_charge_id
        ),
    )

    await save_premium_payment(
        user_id=user_id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        amount=payment.total_amount,
        currency=payment.currency,
        telegram_payment_charge_id=(
            payment.telegram_payment_charge_id
        ),
        premium_until=premium_until,
    )

    premium_until_text = premium_until.strftime(
        "%d.%m.%Y"
    )

    await message.answer(
        "🎉 <b>Оплата прошла успешно!</b>\n\n"
        "👑 Premium активирован.\n"
        "⏳ Срок действия: <b>3 месяца</b>\n"
        f"📅 Premium активен до: <b>{premium_until_text}</b>\n\n"
        "Теперь тебе доступны все Premium-возможности.\n\n"
        "Спасибо за поддержку DictionaryBot! ⭐",
        parse_mode="HTML",
    )

    # =====================================================
    # УВЕДОМЛЕНИЕ АДМИНИСТРАТОРУ
    # =====================================================

    username_text = (
        f"@{escape(message.from_user.username)}"
        if message.from_user.username
        else "Не указан"
    )

    full_name = escape(
        message.from_user.full_name or "Без имени"
    )

    if ADMIN_ID:
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "💰 <b>Новая покупка Premium!</b>\n\n"
                    f"👤 Имя: <b>{full_name}</b>\n"
                    f"🔗 Username: {username_text}\n"
                    f"🆔 ID: <code>{user_id}</code>\n"
                    f"⭐ Оплачено: "
                    f"<b>{payment.total_amount} Stars</b>\n"
                    f"📅 Premium до: "
                    f"<b>{premium_until_text}</b>"
                ),
                parse_mode="HTML",
            )

        except Exception as error:
            print(
                "❌ Не удалось отправить уведомление "
                f"администратору: {error}"
            )