import traceback


async def error_handler(update, context):
    """
    Глобальный обработчик ошибок для бота.

    Логирует исключение и уведомляет пользователя об ошибке.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    logger = context.application.bot_data.get("logger")
    if logger:
        logger.error("Исключение при обработке обновления:\n%s", traceback.format_exc())
    try:
        if update and hasattr(update, "message") and update.message:
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
        elif update and hasattr(update, "callback_query") and update.callback_query:
            await update.callback_query.answer(
                "Произошла ошибка. Попробуйте позже.", show_alert=True
            )
    except Exception as e:
        if logger:
            logger.error(f"Ошибка при отправке сообщения об ошибке: {e}")
