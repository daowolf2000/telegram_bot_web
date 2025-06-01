# handlers/support.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from handlers.commands import send_menu  # Импорт функции показа главного меню

ASKING_QUESTION = 1
CANCEL_CALLBACK = "cancel_support"


async def start_support_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запускает разговор с поддержкой при нажатии кнопки "Связаться с оператором".

    Отправляет пользователю сообщение с просьбой описать вопрос и кнопкой отмены.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.

    Returns:
        int: Константа состояния ASKING_QUESTION для ConversationHandler.
    """
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Отменить", callback_data=CANCEL_CALLBACK)]]
    )
    await update.message.reply_text(
        "Пожалуйста, опишите ваш вопрос или проблему.\n"
        "Вы можете отменить отправку, нажав кнопку ниже.",
        reply_markup=keyboard,
    )
    return ASKING_QUESTION


async def receive_support_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает полученный вопрос пользователя и пересылает его в чат операторов.

    Сохраняет связь между ID сообщения оператора и пользователем для ответа.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.

    Returns:
        int: ConversationHandler.END для завершения разговора.
    """
    user = update.effective_user
    logger = context.application.bot_data.get("logger")
    config = context.application.bot_data.get("config")

    question = update.message.text
    chat_id = config.get("operators_chat_id") if config else None
    if not chat_id:
        await update.message.reply_text("Ошибка конфигурации — обратитесь к администратору.")
        return ConversationHandler.END

    message = f"📩 Запрос от @{user.username or user.first_name} (ID: {user.id}):\n{question}"

    try:
        sent_message = await context.bot.send_message(chat_id=chat_id, text=message)

        # Сохраняем соответствие operator_message_id -> (user_id, вопрос)
        operator_msg_map = context.application.bot_data.setdefault("operator_msg_map", {})
        operator_msg_map[sent_message.message_id] = {"user_id": user.id, "question": question}

        await update.message.reply_text("✅ Ваш запрос отправлен оператору. Возвращаемся в главное меню.")
        if logger:
            logger.info(f"Пользователь {user.id} отправил запрос оператору: {question}")
    except Exception as e:
        if logger:
            logger.error(f"Ошибка при отправке сообщения оператору: {e}")
        await update.message.reply_text("Не удалось отправить запрос оператору. Попробуйте позже.")

    await send_menu(update, context)  # Показываем главное меню
    return ConversationHandler.END


async def cancel_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает отмену отправки запроса пользователем.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.

    Returns:
        int: ConversationHandler.END для завершения разговора.
    """
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Отправка запроса отменена.")
    return ConversationHandler.END


async def operator_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ответ оператора в чате операторов и пересылает его пользователю.

    Игнорирует сообщения не из чата операторов или не являющиеся ответом.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    message = update.message
    logger = context.application.bot_data.get("logger")
    config = context.application.bot_data.get("config")

    if not config or message.chat.id != config.get("operators_chat_id"):
        return  # Игнорируем сообщения не из чата операторов

    if not message.reply_to_message:
        return  # Игнорируем, если это не ответ на сообщение

    operator_msg_id = message.reply_to_message.message_id
    operator_msg_map = context.application.bot_data.get("operator_msg_map", {})
    data = operator_msg_map.get(operator_msg_id)

    if not data:
        if logger:
            logger.warning(f"Не найдена связь для operator_msg_id={operator_msg_id}")
        return

    user_id = data["user_id"]
    question = data["question"]
    answer = message.text

    try:
        text = (
            "Получен ответ от оператора\n"
            f"*Ваш вопрос*: {question}\n"
            f"*Ответ:* {answer}"
        )
        await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
        if logger:
            logger.info(f"Переслан ответ оператора пользователю {user_id}")
    except Exception as e:
        if logger:
            logger.error(f"Ошибка при пересылке ответа операторов пользователю {user_id}: {e}")
