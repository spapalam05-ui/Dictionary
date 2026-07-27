from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from database import (
    add_word,
    get_words_count,
    is_premium,
)


router = Router()


FREE_WORDS_LIMIT = 50


class AddWordStates(StatesGroup):
    waiting_for_words = State()


def parse_words(
    text: str,
) -> tuple[list[tuple[str, str]], list[str]]:
    """
    Разбирает текст:

    apple - яблоко
    banana - банан

    Возвращает:
    1. Правильные пары слов.
    2. Строки с неправильным форматом.
    """

    words: list[tuple[str, str]] = []
    invalid_lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if "-" not in line:
            invalid_lines.append(line)
            continue

        english, russian = map(
            str.strip,
            line.split("-", 1),
        )

        if not english or not russian:
            invalid_lines.append(line)
            continue

        words.append((english, russian))

    return words, invalid_lines


@router.message(F.text == "➕ Добавить")
async def add_button(
    message: Message,
    state: FSMContext,
) -> None:
    await state.clear()
    await state.set_state(
        AddWordStates.waiting_for_words,
    )

    premium = await is_premium(
        message.from_user.id,
    )

    if premium:
        text = (
            "⚡ <b>Массовое добавление слов</b>\n\n"
            "Отправь одно или несколько слов.\n"
            "Каждое слово пиши с новой строки:\n\n"
            "<code>"
            "add - добавить\n"
            "apple - яблоко\n"
            "banana - банан\n"
            "house - дом"
            "</code>\n\n"
            "Все слова будут добавлены за один раз."
        )
    else:
        text = (
            "✍️ <b>Добавление слова</b>\n\n"
            "Отправь одно слово в формате:\n\n"
            "<code>apple - яблоко</code>\n\n"
            "⚡ Массовое добавление нескольких слов "
            "доступно в Premium."
        )

    await message.answer(
        text,
        parse_mode="HTML",
    )


@router.message(
    AddWordStates.waiting_for_words,
)
async def receive_words(
    message: Message,
    state: FSMContext,
) -> None:
    if not message.text:
        await message.answer(
            "❌ Отправь слова обычным текстом."
        )
        return

    user_id = message.from_user.id

    premium = await is_premium(user_id)
    current_count = await get_words_count(user_id)

    words, invalid_lines = parse_words(
        message.text,
    )

    if not words:
        await message.answer(
            "❌ Не удалось найти слова.\n\n"
            "Используй формат:\n"
            "<code>apple - яблоко</code>",
            parse_mode="HTML",
        )
        return

    # Бесплатный пользователь может добавить
    # только одно слово за одно сообщение.
    if not premium and len(words) > 1:
        await message.answer(
            "🔒 Массовое добавление доступно "
            "только в Premium.\n\n"
            "Бесплатно можно отправить только "
            "одно слово:\n"
            "<code>apple - яблоко</code>",
            parse_mode="HTML",
        )
        return

    if not premium and current_count >= FREE_WORDS_LIMIT:
        await state.clear()

        await message.answer(
            "❌ Ты достиг бесплатного лимита "
            f"в {FREE_WORDS_LIMIT} слов.\n\n"
            "⭐ Premium — 1990 ₸\n"
            "• Безлимитное количество слов\n"
            "• Массовое добавление\n"
            "• Папки для слов\n"
            "• Расширенная статистика"
        )
        return

    # Защищаем бесплатный лимит,
    # даже если позже разрешим несколько слов.
    if not premium:
        available_slots = (
            FREE_WORDS_LIMIT - current_count
        )
        words = words[:available_slots]

    added_count = 0

    for english, russian in words:
        await add_word(
            user_id,
            english,
            russian,
        )
        added_count += 1

    await state.clear()

    response = (
        f"✅ <b>Добавлено слов: {added_count}</b>"
    )

    if added_count == 1:
        english, russian = words[0]

        response += (
            f"\n\n🇬🇧 {english}"
            f"\n🇷🇺 {russian}"
        )

    if invalid_lines:
        invalid_preview = "\n".join(
            f"• {line}"
            for line in invalid_lines[:5]
        )

        response += (
            f"\n\n⚠️ Пропущено строк: "
            f"<b>{len(invalid_lines)}</b>\n"
            f"<code>{invalid_preview}</code>"
        )

    await message.answer(
        response,
        parse_mode="HTML",
    )


@router.message(Command("add"))
async def add_command(
    message: Message,
    command: CommandObject,
) -> None:
    user_id = message.from_user.id

    premium = await is_premium(user_id)
    current_count = await get_words_count(user_id)

    if command.args is None:
        await message.answer(
            "Используй:\n"
            "<code>/add apple - яблоко</code>",
            parse_mode="HTML",
        )
        return

    words, invalid_lines = parse_words(
        command.args,
    )

    if not words:
        await message.answer(
            "❌ Неправильный формат.\n\n"
            "Используй:\n"
            "<code>/add apple - яблоко</code>",
            parse_mode="HTML",
        )
        return

    if not premium and len(words) > 1:
        await message.answer(
            "🔒 Массовое добавление доступно "
            "только в Premium."
        )
        return

    if not premium and current_count >= FREE_WORDS_LIMIT:
        await message.answer(
            "❌ Ты достиг бесплатного лимита "
            f"в {FREE_WORDS_LIMIT} слов.\n\n"
            "⭐ Оформи Premium для снятия лимита."
        )
        return

    if not premium:
        words = words[:1]

    added_count = 0

    for english, russian in words:
        await add_word(
            user_id,
            english,
            russian,
        )
        added_count += 1

    response = (
        f"✅ Добавлено слов: <b>{added_count}</b>"
    )

    if added_count == 1:
        english, russian = words[0]

        response += (
            f"\n\n🇬🇧 {english}"
            f"\n🇷🇺 {russian}"
        )

    if invalid_lines:
        response += (
            f"\n\n⚠️ Пропущено строк: "
            f"<b>{len(invalid_lines)}</b>"
        )

    await message.answer(
        response,
        parse_mode="HTML",
    )