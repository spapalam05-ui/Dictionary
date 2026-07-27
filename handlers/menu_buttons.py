from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message


router = Router()


@router.message(F.text == "➕ Добавить")
async def add_button(
    message: Message,
    state: FSMContext,
) -> None:

    await state.clear()

    await message.answer(
        "✍️ Напиши слово в формате:\n\n"
        "<code>/add apple - яблоко</code>\n\n"
        "Для добавления в определённую категорию "
        "открой раздел «📂 Категории».",
        parse_mode="HTML",
    )