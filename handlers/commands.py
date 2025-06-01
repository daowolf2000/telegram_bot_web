from telegram import ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from services.users import log_user_message


MENU_BUTTONS = [
    ["📅 Мероприятия", "📞 Контакты", "🏛 Экскурсии"],  
    ["🛍 Сувениры", "📚 Материалы", "🧭 Путеводитель"], 
    ["👨💻 Связаться с оператором"]
]


async def send_menu(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет пользователю главное меню с кнопками.

    Логирует вызов меню.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    user = update.effective_user
    logger = context.application.bot_data["logger"]
    config = context.application.bot_data["config"]

    log_user_message(user.id, user.username, "/start (menu)", config["logs_dir"], logger)

    keyboard = ReplyKeyboardMarkup(MENU_BUTTONS, resize_keyboard=True)
    await update.message.reply_text("Главное меню:", reply_markup=keyboard)
    logger.info(f"Показано меню пользователю {user.id}")
