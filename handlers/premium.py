from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database import is_premium


router = Router()


def get_premium_keyboard(premium_active: bool):
    if premium_active:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📂 Категории слов",
                        callback_data="my_categories"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 Статистика",
                        callback_data="premium_statistics"
                    ),
                    InlineKeyboardButton(
                        text="🔥 Серия",
                        callback_data="premium_streak"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Premium активен",
                        callback_data="premium_active"
                    )
                ]
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔒 Категории слов",
                    callback_data="locked_categories"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔒 Статистика",
                    callback_data="locked_statistics"
                ),
                InlineKeyboardButton(
                    text="🔒 Серия",
                    callback_data="locked_streak"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Купить Premium — 1990 ₸",
                    callback_data="buy_premium"
                )
            ]
        ]
    )


@router.message(F.text == "⭐ Premium")
async def premium_menu(message: Message):
    premium_active = await is_premium(
        message.from_user.id
    )

    if premium_active:
        text = (
            "⭐ <b>Premium</b>\n\n"
            "✅ Premium активен\n\n"
            "Тебе доступны:\n"
            "♾️ Безлимит слов\n"
            "📂 Категории слов\n"
            "📊 Статистика обучения\n"
            "🔥 Серия дней"
        )
    else:
        text = (
            "⭐ <b>Premium</b>\n\n"
            "Что даёт Premium?\n\n"
            "♾️ Безлимит слов\n"
            "📂 Категории слов\n"
            "📊 Статистика обучения\n"
            "🔥 Серия дней\n\n"
            "Стоимость: <b>1990 ₸</b>"
        )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_premium_keyboard(
            premium_active
        )
    )


@router.callback_query(F.data == "premium_active")
async def premium_active_callback(
    callback: CallbackQuery
):
    await callback.answer(
        "✅ Premium уже активен",
        show_alert=True
    )


@router.callback_query(
    F.data.in_({
        "locked_categories",
        "locked_statistics",
        "locked_streak",
    })
)
async def locked_feature(
    callback: CallbackQuery
):
    await callback.answer(
        "🔒 Эта функция доступна только в Premium.",
        show_alert=True
    )


@router.callback_query(F.data == "premium_statistics")
async def premium_statistics(
    callback: CallbackQuery
):
    premium_active = await is_premium(
        callback.from_user.id
    )

    if not premium_active:
        await callback.answer(
            "🔒 Доступно только в Premium.",
            show_alert=True
        )
        return

    await callback.answer()

    await callback.message.answer(
        "📊 <b>Статистика</b>\n\n"
        "Функция скоро будет добавлена.",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "premium_streak")
async def premium_streak(
    callback: CallbackQuery
):
    premium_active = await is_premium(
        callback.from_user.id
    )

    if not premium_active:
        await callback.answer(
            "🔒 Доступно только в Premium.",
            show_alert=True
        )
        return

    await callback.answer()

    await callback.message.answer(
        "🔥 <b>Серия обучения</b>\n\n"
        "Функция скоро будет добавлена.",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "buy_premium")
async def buy(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        "💳 <b>Покупка Premium</b>\n\n"
        "Стоимость: <b>1990 ₸</b>\n\n"
        "Скоро здесь появится кнопка оплаты.",
        parse_mode="HTML"
    )