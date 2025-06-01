from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json


async def show_excursions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает команду показа экскурсий.

    Загружает данные экскурсий из файла, формирует клавиатуру с категориями
    и отправляет пользователю список категорий.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    logger = context.application.bot_data["logger"]
    config = context.application.bot_data["config"]
    user = update.effective_user

    try:
        with open(config["excursions_data"], "r", encoding="utf-8") as f:
            excursions = json.load(f)

        categories = {exc["category"] for exc in excursions}
        keyboard = [
            [InlineKeyboardButton(cat, callback_data=f"cat_{cat}")]
            for cat in categories
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🏛 Выберите категорию экскурсий:", reply_markup=reply_markup
        )
        logger.info(f"Пользователь {user.id} запросил список экскурсий")
    except Exception as e:
        logger.error(f"Ошибка загрузки экскурсий: {e}")
        await update.message.reply_text("Ошибка загрузки экскурсий.")
