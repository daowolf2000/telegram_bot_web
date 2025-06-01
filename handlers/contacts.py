import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

CONTACTS_FILE = "data/contacts.json"


def load_contacts() -> dict:
    """
    Загружает данные контактов из JSON-файла.

    Returns:
        dict: Словарь с категориями контактов.
              Пустой словарь, если файл не найден.
    """
    if not os.path.exists(CONTACTS_FILE):
        return {}
    with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


async def contacts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает команду показа контактов.

    Отправляет пользователю список категорий контактов с кнопками.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    contacts_data = load_contacts()
    if not contacts_data:
        if update.callback_query:
            await update.callback_query.message.edit_text("Контакты временно недоступны.")
        else:
            await update.message.reply_text("Контакты временно недоступны.")
        return

    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"contacts_cat|{cat}")]
        for cat in contacts_data.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.edit_text(
            "Выберите категорию контактов:", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Выберите категорию контактов:", reply_markup=reply_markup
        )


async def contacts_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор категории контактов.

    Отправляет список контактов в выбранной категории с кликабельными номерами.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    contacts_data = load_contacts()
    query = update.callback_query
    await query.answer()

    _, category = query.data.split("|", 1)
    contacts = contacts_data.get(category, [])

    if not contacts:
        await query.edit_message_text(
            f"В категории *{category}* контакты не найдены.", parse_mode="Markdown"
        )
        return

    lines = [f"📂 *{category}*:\n"]
    for c in contacts:
        name = c.get("name", "Без имени")
        phone = c.get("phone", "")
        info = c.get("info", "")

        phone_formatted = phone.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
        if not phone_formatted.startswith("+"):
            phone_formatted = "+" + phone_formatted

        phone_link = f"[📱 {phone}]({phone_formatted})"

        lines.append(f"👤 *{name}*")
        lines.append(phone_link)
        if info:
            lines.append(f"ℹ️ _{info}_")
        lines.append("")

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Назад", callback_data="contacts_back")]]
    )

    text = "\n".join(lines)
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)


async def contacts_back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатие кнопки "Назад" в меню контактов.

    Возвращает пользователя к списку категорий контактов.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    query = update.callback_query
    await query.answer()
    await contacts_handler(update, context)
