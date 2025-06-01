from services.orders import read_order, remove_order
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Импортируем функцию построения клавиатуры (укажите свой путь)
from handlers.events import build_dates_keyboard


async def button_handler(update, context):
    """
    Обрабатывает callback_query от inline-кнопок.

    В зависимости от данных callback выполняет действия:
    - Показ текущего заказа
    - Отмена заказа
    - Возврат к выбору даты мероприятий
    - Обработка неизвестных команд

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    query = update.callback_query
    await query.answer()
    logger = context.application.bot_data["logger"]
    config = context.application.bot_data["config"]
    user = update.effective_user
    data = query.data

    logger.debug(f"Обработка callback {data} от пользователя {user.id} (@{user.username})")

    if data == "myorder":
        order = read_order(user.id, config["orders_dir"])
        if not order:
            await query.edit_message_text("У вас нет текущих заказов.")
            logger.info(f"Пользователь {user.id} запросил заказ, но файл не найден")
            return
        lines = [f"{row['name']} — {row['qty']} {row['unit']}" for row in order]
        text = "Ваш текущий заказ:\n" + "\n".join(lines) if lines else "Ваш заказ пуст."
        await query.edit_message_text(text)
        logger.info(f"Пользователь {user.id} просмотрел заказ через кнопку")

    elif data == "cancelorder":
        if remove_order(user.id, config["orders_dir"], logger):
            await query.edit_message_text("Ваш заказ успешно удалён.")
            logger.info(f"Пользователь {user.id} удалил заказ через кнопку")
        else:
            await query.edit_message_text("У вас нет заказов для удаления.")
            logger.info(f"Пользователь {user.id} попытался удалить несуществующий заказ")

    elif data == "event_back":
        dates = context.user_data.get("events_dates")
        if not dates:
            await query.edit_message_text("Пожалуйста, заново вызовите команду /events")
            logger.warning(f"Пользователь {user.id} вызвал event_back, но даты не найдены")
            return
        keyboard = build_dates_keyboard(dates)
        await query.edit_message_text("Выберите дату мероприятия:", reply_markup=keyboard)
        logger.info(f"Пользователь {user.id} вернулся к выбору даты")

    else:
        await query.edit_message_text("Неизвестная команда.")
        logger.warning(f"Пользователь {user.id} прислал неизвестный callback: {data}")
