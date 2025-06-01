# souvenirs.py

from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import ContextTypes
from services.messages import load_message
from services.orders import read_order


def get_souvenirs_menu(webapp_url: str, has_order: bool) -> ReplyKeyboardMarkup:
    """
    Формирует клавиатуру меню сувениров.

    Args:
        webapp_url (str): URL WebApp для оформления заказа.
        has_order (bool): Флаг наличия текущего заказа.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопками меню.
    """
    keyboard = [
        [KeyboardButton(text="Сделать/обновить заказ", web_app=WebAppInfo(url=webapp_url))]
    ]
    if has_order:
        keyboard.append(["Посмотреть заказ", "Отменить заказ"])
    keyboard.append(["Назад"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def souvenirs_menu(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды меню сувениров.

    Отправляет информацию о сувенирах и отображает меню с кнопками.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    user = update.effective_user
    config = context.application.bot_data["config"]
    logger = context.application.bot_data["logger"]

    info_text = load_message("souvenirs.txt")
    if not info_text:
        info_text = "Информация о сувенирах временно недоступна."
    await update.message.reply_text(info_text)

    try:
        order = read_order(user.id, config["orders_dir"])
        has_order = bool(order)
    except Exception as e:
        logger.error(f"Ошибка при проверке заказа пользователя {user.id}: {e}")
        has_order = False

    keyboard = get_souvenirs_menu(config["webapp_url"], has_order)
    await update.message.reply_text("Меню сувениров:", reply_markup=keyboard)


async def souvenirs_menu_handler(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик текстовых сообщений меню сувениров.

    Обрабатывает команды просмотра заказа, отмены заказа и возврата в главное меню.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    text = update.message.text
    config = context.application.bot_data["config"]
    user = update.effective_user
    logger = context.application.bot_data["logger"]

    async def update_keyboard():
        try:
            order = read_order(user.id, config["orders_dir"])
            has_order = bool(order)
        except Exception as e:
            logger.error(f"Ошибка при проверке заказа пользователя {user.id}: {e}")
            has_order = False

        keyboard = get_souvenirs_menu(config["webapp_url"], has_order)
        await update.message.reply_text("Меню сувениров:", reply_markup=keyboard)

    if text == "Посмотреть заказ":
        try:
            order = read_order(user.id, config["orders_dir"])
            if not order:
                await update.message.reply_text("У вас нет текущих заказов.")
                await update_keyboard()
                return

            total_sum = 0
            lines = []
            for row in order:
                try:
                    qty = int(row["qty"])
                    price = float(row.get("price", 0))
                except (ValueError, TypeError):
                    qty = 0
                    price = 0.0
                name = row["name"]
                unit = row["unit"]
                lines.append(f"{name} — {qty} {unit} × {price} ₽ = {qty * price} ₽")
                total_sum += qty * price

            text = "Ваш текущий заказ:\n" + "\n".join(lines)
            text += f"\n\n💰 Итоговая сумма: {total_sum} ₽"
            await update.message.reply_text(text)
            await update_keyboard()

        except Exception as e:
            logger.error(f"Ошибка при чтении заказа пользователя {user.id}: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
            await update_keyboard()

    elif text == "Отменить заказ":
        from services.orders import remove_order

        if remove_order(user.id, config["orders_dir"], logger):
            await update.message.reply_text("Ваш заказ успешно удалён.")
        else:
            await update.message.reply_text("У вас нет заказов для удаления.")
        await update_keyboard()

    elif text == "Назад":
        from handlers.commands import send_menu

        context.user_data.pop("current_menu", None)
        await send_menu(update, context)

    else:
        await update.message.reply_text("Пожалуйста, выберите пункт из меню.")
