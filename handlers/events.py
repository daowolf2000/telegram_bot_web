import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from collections import defaultdict

EVENTS_FILE = "data/events.json"


def load_events() -> dict:
    """
    Загружает данные мероприятий из JSON-файла.

    Returns:
        dict: Словарь с мероприятиями по датам.
              Пустой словарь, если файл не найден.
    """
    if not os.path.exists(EVENTS_FILE):
        return {}
    with open(EVENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def group_events_by_date(events_data: dict) -> dict:
    """
    Группирует мероприятия по дате.

    Args:
        events_data (dict): Словарь с мероприятиями по датам.

    Returns:
        dict: Отсортированный словарь с датами и списками мероприятий.
    """
    grouped = defaultdict(list)
    for date, events in events_data.items():
        grouped[date].extend(events)
    return dict(sorted(grouped.items()))


def build_dates_keyboard(dates: list) -> InlineKeyboardMarkup:
    """
    Формирует клавиатуру с кнопками выбора даты мероприятий.

    Args:
        dates (list): Список дат.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками дат.
    """
    keyboard = [
        [InlineKeyboardButton(f"📅 {date}", callback_data=f"event_date|{date}")]
        for date in dates
    ]
    return InlineKeyboardMarkup(keyboard)


def format_events_text(events: list, date: str) -> str:
    """
    Форматирует текст с описанием мероприятий на выбранную дату.

    Args:
        events (list): Список мероприятий.
        date (str): Дата мероприятий.

    Returns:
        str: Отформатированный текст с мероприятиями.
    """
    lines = [f"📅 *{date}*\n"]
    for event in events:
        time_str = event.get("time", "")
        if "end_time" in event:
            time_str += f" - {event['end_time']}"
        title = event.get("title", "Без названия")
        desc = event.get("description", "")
        lines.append(f"🕒 {time_str} *{title}*")
        if desc:
            lines.append(f"_{desc}_")
        lines.append("")  # пустая строка между мероприятиями
    return "\n".join(lines)


async def show_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /events — показывает список дат с мероприятиями.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    events_data = load_events()
    if not events_data:
        await update.message.reply_text("Мероприятия пока не запланированы.")
        return

    grouped_events = group_events_by_date(events_data)
    dates = list(grouped_events.keys())

    context.user_data["events_grouped"] = grouped_events
    context.user_data["events_dates"] = dates

    keyboard = build_dates_keyboard(dates)
    await update.message.reply_text("Выберите дату мероприятия:", reply_markup=keyboard)


async def event_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик callback_query для выбора даты и навигации по мероприятиям.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    query = update.callback_query
    data = query.data

    grouped_events = context.user_data.get("events_grouped")
    dates = context.user_data.get("events_dates")

    if not grouped_events or not dates:
        await query.answer("Пожалуйста, заново вызовите команду /events")
        return

    if data.startswith("event_date|"):
        date = data.split("|", 1)[1]
        events = grouped_events.get(date, [])

        if not events:
            await query.answer("Мероприятий на эту дату нет.")
            return

        text = format_events_text(events, date)
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("⬅️ Назад к датам", callback_data="event_back")]]
        )

        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=keyboard)
        await query.answer()

    elif data == "event_back":
        keyboard = build_dates_keyboard(dates)
        await query.edit_message_text("Выберите дату мероприятия:", reply_markup=keyboard)
        await query.answer()

    else:
        await query.answer()
