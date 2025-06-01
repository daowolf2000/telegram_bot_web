# webapp.py

import json
from telegram.ext import ContextTypes
from telegram import ReplyKeyboardRemove
from services.orders import save_order
from services.users import log_user_message
from handlers.souvenirs import get_souvenirs_menu  # Для обновления клавиатуры


async def send_updated_souvenirs_menu(update, context):
    """
    Отправляет пользователю обновлённое меню сувениров с учётом наличия заказа.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    user = update.effective_user
    config = context.application.bot_data["config"]
    logger = context.application.bot_data["logger"]

    from services.orders import read_order

    try:
        order = read_order(user.id, config["orders_dir"])
        has_order = bool(order)
    except Exception as e:
        logger.error(f"Ошибка при проверке заказа пользователя {user.id}: {e}")
        has_order = False

    keyboard = get_souvenirs_menu(config["webapp_url"], has_order)
    await update.message.reply_text("Меню сувениров:", reply_markup=keyboard)


async def webapp_data_handler(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает данные, полученные из Telegram Web App.

    Логирует данные, проверяет команды отмены заказа, сохраняет новый заказ,
    отправляет подтверждения и обновляет меню.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    user = update.effective_user
    config = context.application.bot_data["config"]
    logger = context.application.bot_data["logger"]

    data_str = update.message.web_app_data.data
    log_user_message(user.id, user.username, f"WebApp data: {data_str}", config["logs_dir"], logger)

    try:
        data = json.loads(data_str)
    except Exception:
        await update.message.reply_text("Ошибка: неверный формат данных.")
        return

    if data.get("cancelOrder"):
        from services.orders import remove_order

        if remove_order(user.id, config["orders_dir"], logger):
            await update.message.reply_text("✅ Заказ успешно отменён.")
            await context.bot.send_message(
                chat_id=user.id,
                text="clear_local_storage",
                reply_markup=ReplyKeyboardRemove(),
            )
            # Обновляем меню без кнопок просмотра/отмены заказа
            await send_updated_souvenirs_menu(update, context)
        else:
            await update.message.reply_text("❗ Заказа для отмены не найдено.")
        return

    fio = data.get("fio", "Не указано")
    items = data.get("items", [])
    if not isinstance(items, list) or not items:
        await update.message.reply_text("Корзина пуста. Заказ не оформлен.")
        return

    save_order(user.id, user.username, fio, "", items, config["orders_dir"], logger)

    text = f"Спасибо, {fio}!\nВаш заказ обновлён:\n"
    for item in items:
        text += f"- {item['name']} — {item['qty']} {item['unit']}\n"

    await update.message.reply_text(text)

    # После создания/обновления заказа обновляем меню с кнопками "Посмотреть заказ" и "Отменить заказ"
    await send_updated_souvenirs_menu(update, context)
