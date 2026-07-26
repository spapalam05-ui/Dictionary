from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from keyboards.premium_keyboard import premium_keyboard

router = Router()


@router.message(F.text == "⭐ Premium")
async def premium_menu(message: Message):

    await message.answer(
        "⭐ <b>Premium</b>\n\n"
        "Что дает Premium?\n\n"
        "✅ Безлимит слов\n"
        "✅ Все будущие функции\n"
        "✅ Поддержка проекта\n\n"
        "Стоимость: <b>100 ⭐ Telegram Stars</b>",
        parse_mode="HTML",
        reply_markup=premium_keyboard
    )


@router.callback_query(F.data == "buy_premium")
async def buy(callback: CallbackQuery):

    await callback.answer()

    await callback.message.answer(
        "💳 Скоро здесь появится оплата через Telegram Stars."
    )