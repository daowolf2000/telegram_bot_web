# handlers/tours.py

import os
import re
import aiohttp
from collections import defaultdict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.tours import load_tours
from services.registrations import get_user_registrations, save_user_registrations


def group_tours_by_date(tours):
    """
    Группирует список туров по дате.

    Args:
        tours (list): Список туров (словарей).

    Returns:
        dict: Отсортированный словарь с ключами — датами и значениями — списками туров.
    """
    grouped = defaultdict(list)
    for tour in tours:
        grouped[tour["date"]].append(tour)
    return dict(sorted(grouped.items()))


def is_valid_image_url(url: str) -> bool:
    """
    Проверяет, является ли URL допустимой ссылкой на изображение.

    Args:
        url (str): URL для проверки.

    Returns:
        bool: True, если URL заканчивается на изображение, иначе False.
    """
    if not url or not isinstance(url, str):
        return False
    return bool(re.search(r"\.(jpg|jpeg|png|gif|bmp|webp)$", url, re.IGNORECASE))


async def url_exists(url: str) -> bool:
    """
    Асинхронно проверяет доступность URL (HEAD запрос).

    Args:
        url (str): Проверяемый URL.

    Returns:
        bool: True, если статус ответа 200, иначе False.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=5) as resp:
                return resp.status == 200
    except Exception:
        return False


async def send_tour_message(
    update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    image_url: str,
    keyboard: InlineKeyboardMarkup,
):
    """
    Отправляет сообщение с описанием тура и изображением (если доступно).

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
        text (str): Текст сообщения.
        image_url (str): Локальный путь или URL изображения.
        keyboard (InlineKeyboardMarkup): Клавиатура для сообщения.
    """
    logger = context.application.bot_data["logger"]

    if image_url and os.path.isfile(image_url):
        try:
            with open(image_url, "rb") as photo_file:
                await update.message.reply_photo(
                    photo=photo_file,
                    caption=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            return
        except Exception as e:
            logger.error(f"Ошибка отправки локального изображения: {e}")

    if image_url and is_valid_image_url(image_url):
        if await url_exists(image_url):
            try:
                await update.message.reply_photo(
                    photo=image_url,
                    caption=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
                return
            except Exception as e:
                logger.error(f"Ошибка отправки изображения по URL: {e}")

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


def build_dates_keyboard(dates):
    """
    Формирует клавиатуру с кнопками выбора дат туров.

    Args:
        dates (list): Список дат (строк).

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками дат.
    """
    keyboard = [[InlineKeyboardButton(date, callback_data=f"date|{date}")] for date in dates]
    return InlineKeyboardMarkup(keyboard)


def build_tours_keyboard(user_regs, tours):
    """
    Формирует клавиатуру с кнопками туров на выбранную дату,
    учитывая статус регистрации пользователя.

    Args:
        user_regs (set): Множество ID туров, на которые пользователь записан.
        tours (list): Список туров на дату.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками туров и кнопкой назад.
    """
    keyboard = []
    for tour in tours:
        if tour["id"] in user_regs:
            text = f"✅ {tour['time']} - {tour['name']}"
            callback_data = f"unregister|{tour['id']}"
        else:
            text = f"❌ {tour['time']} - {tour['name']}"
            callback_data = f"register|{tour['id']}"
        keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton("⬅️ Назад к датам", callback_data="back_to_dates")])
    return InlineKeyboardMarkup(keyboard)


async def show_tours(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /tours — показывает список дат с турами.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    tours = load_tours()
    if not tours:
        await update.message.reply_text("Туры пока не запланированы.")
        return

    grouped = group_tours_by_date(tours)
    dates = list(grouped.keys())

    # Сохраняем в user_data для навигации
    context.user_data["tours_grouped"] = grouped
    context.user_data["tours_dates"] = dates

    keyboard = build_dates_keyboard(dates)
    await update.message.reply_text("Выберите дату тура:", reply_markup=keyboard)


async def tour_callback_handler(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик callback_query для выбора даты, регистрации и отписки от тура.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    user_regs = get_user_registrations(user_id)
    grouped = context.user_data.get("tours_grouped", {})
    dates = context.user_data.get("tours_dates", [])

    if data.startswith("date|"):
        selected_date = data.split("|", 1)[1]
        tours_on_date = grouped.get(selected_date, [])

        if not tours_on_date:
            await query.answer("Туров на эту дату нет.")
            return

        text = f"Туры на {selected_date}:\n"
        for tr in tours_on_date:
            start = tr.get("time", "")
            end = tr.get("end_time", "")
            time_period = f"{start} - {end}" if end else start
            text += (
                f"\n🕒 {time_period}\n*{tr['name']}*\n_{tr['description']}_\n"
                f"💰 Цена: {tr['price']} ₽"
            )
            if tr.get("link"):
                text += f"\n🔗 [Подробнее]({tr['link']})"
            text += "\n"

        kb = build_tours_keyboard(user_regs, tours_on_date)

        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=kb)
        await query.answer()

    elif data == "back_to_dates":
        keyboard = build_dates_keyboard(dates)
        await query.edit_message_text("Выберите дату тура:", reply_markup=keyboard)
        await query.answer()

    elif data.startswith("register|") or data.startswith("unregister|"):
        action, tour_id = data.split("|", 1)

        if action == "register":
            user_regs.add(tour_id)
            await query.answer("Вы записаны на тур")
        else:
            user_regs.discard(tour_id)
            await query.answer("Вы отписались от тура")

        save_user_registrations(user_id, user_regs)

        # Находим дату тура по ID
        tour_date = None
        for date_key, tours_list in grouped.items():
            if any(t["id"] == tour_id for t in tours_list):
                tour_date = date_key
                break

        if not tour_date:
            keyboard = build_dates_keyboard(dates)
            await query.edit_message_reply_markup(reply_markup=keyboard)
            return

        tours_on_date = grouped.get(tour_date, [])
        kb = build_tours_keyboard(user_regs, tours_on_date)
        await query.edit_message_reply_markup(reply_markup=kb)

    else:
        await query.answer()  # Заглушка для прочих callback_data
