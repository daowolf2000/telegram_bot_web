import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


async def materials_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает команду показа меню материалов.
    Отправляет пользователю список доступных файлов для скачивания в виде кнопок.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    config = context.application.bot_data["config"]
    materials_dir = config.get("materials_dir", "data/materials")
    logger = context.application.bot_data["logger"]

    try:
        files = os.listdir(materials_dir)
        files = [f for f in files if os.path.isfile(os.path.join(materials_dir, f))]
    except Exception as e:
        logger.error(f"Ошибка при чтении папки материалов: {e}")
        await update.message.reply_text("Ошибка при загрузке списка материалов.")
        return

    if not files:
        await update.message.reply_text("Материалы пока отсутствуют.")
        return

    keyboard = [
        [InlineKeyboardButton(text=filename, callback_data=f"material_{filename}")]
        for filename in files
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Вы можете скачать следующие материалы:",
        reply_markup=reply_markup,
    )


async def material_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатие кнопки с материалом.
    Отправляет файл пользователю, если он существует.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("material_"):
        return

    filename = data[len("material_") :]
    config = context.application.bot_data["config"]
    materials_dir = config.get("materials_dir", "data/materials")
    logger = context.application.bot_data["logger"]

    file_path = os.path.join(materials_dir, filename)

    if not os.path.isfile(file_path):
        await query.edit_message_text("Файл не найден.")
        logger.warning(f"Пользователь {query.from_user.id} запросил несуществующий файл: {filename}")
        return

    try:
        with open(file_path, "rb") as f:
            await context.bot.send_document(chat_id=query.from_user.id, document=f, filename=filename)
        logger.info(f"Пользователь {query.from_user.id} скачал материал: {filename}")
    except Exception as e:
        logger.error(f"Ошибка при отправке файла {filename} пользователю {query.from_user.id}: {e}")
        await query.edit_message_text("Не удалось отправить файл. Попробуйте позже.")
