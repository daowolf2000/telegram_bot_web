import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

GUIDE_FILE = "data/guide.json"


def load_guide() -> dict:
    """
    Загружает данные путеводителя из JSON-файла.

    Returns:
        dict: Словарь с категориями и списками мест.
              Пустой словарь, если файл не найден.
    """
    if not os.path.exists(GUIDE_FILE):
        return {}
    with open(GUIDE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def format_phone_number(phone: str) -> str:
    """
    Приводит номер телефона к международному формату для кликабельности.

    Args:
        phone (str): Исходный номер телефона.

    Returns:
        str: Отформатированный номер телефона.
    """
    phone = phone.strip()
    digits = "".join(filter(str.isdigit, phone))
    if digits.startswith("8") and len(digits) == 11:
        digits = "+7" + digits[1:]
    elif not phone.startswith("+"):
        digits = "+" + digits
    else:
        digits = phone
    return digits


async def guide_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает команду /guide или вызов меню путеводителя.

    Отправляет пользователю список категорий путеводителя с кнопками.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    guide_data = load_guide()
    if not guide_data:
        if update.callback_query:
            await update.callback_query.message.edit_text("Путеводитель временно недоступен.")
        else:
            await update.message.reply_text("Путеводитель временно недоступен.")
        return

    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"guide_cat|{cat}")]
        for cat in guide_data.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.edit_text(
            "Выберите категорию путеводителя:",
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(
            "Выберите категорию путеводителя:",
            reply_markup=reply_markup,
        )


async def guide_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор категории путеводителя.

    Отправляет список мест в категории с контактами и ссылками.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    guide_data = load_guide()
    query = update.callback_query
    await query.answer()

    _, category = query.data.split("|", 1)
    places = guide_data.get(category, [])

    if not places:
        await query.edit_message_text(
            f"В категории *{category}* ничего не найдено.", parse_mode="Markdown"
        )
        return

    lines = [f"📂 *{category}*:\n"]
    for place in places:
        name = place.get("name", "Без названия")
        phone = place.get("phone", "")
        address = place.get("address", "")
        description = place.get("description", "")
        links = place.get("links", [])  # список словарей с keys: url, text

        phone_formatted = ""
        if phone:
            phone_number = format_phone_number(phone)
            phone_formatted = f"[📱 {phone}]({phone_number})"

        lines.append(f"📌 *{name}*")
        if phone_formatted:
            lines.append(phone_formatted)
        if address:
            lines.append(f"📍 {address}")

        link_texts = []
        for link in links:
            url = link.get("url")
            text = link.get("text", "Ссылка")
            if url:
                link_texts.append(f"[{text}]({url})")
        if link_texts:
            lines.append("🔗 " + ", ".join(link_texts))

        if description:
            lines.append(f"ℹ️ _{description}_")
        lines.append("")

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Назад", callback_data="guide_back")]]
    )

    text = "\n".join(lines)
    await query.edit_message_text(
        text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=keyboard
    )


async def guide_back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатие кнопки "Назад" в меню путеводителя.

    Возвращает пользователя к списку категорий.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    query = update.callback_query
    await query.answer()
    await guide_handler(update, context)
