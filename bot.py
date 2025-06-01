# main.py

import os
import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from telegram import BotCommand

from core.config import load_config
from core.logger import get_logger

from handlers.commands import send_menu
from handlers.menu_handler import menu_text_handler
from handlers.souvenirs import souvenirs_menu, souvenirs_menu_handler
from handlers.support import (
    ASKING_QUESTION,
    CANCEL_CALLBACK,
    start_support_conversation,
    receive_support_question,
    cancel_support,
    operator_reply_handler,
)
from handlers.materials import materials_menu, material_button_handler
from handlers.buttons import button_handler
from handlers.errors import error_handler
from handlers.webapp import webapp_data_handler
from handlers.events import show_events, event_callback_handler
from handlers.contacts import contacts_handler, contacts_category_handler, contacts_back_handler
from handlers.guide import guide_handler, guide_category_handler, guide_back_handler
from handlers.tours import show_tours, tour_callback_handler

from services.messages import load_message

from warnings import filterwarnings
from telegram.warnings import PTBUserWarning


filterwarnings(
    action="ignore",
    message=r".*CallbackQueryHandler",
    category=PTBUserWarning,
)


def ensure_dirs(config, logger):
    """
    Проверяет наличие необходимых директорий, создает их при отсутствии.

    Args:
        config (dict): Конфигурация с путями к директориям.
        logger (logging.Logger): Логгер для записи информации.
    """
    logger.debug("Проверка и создание необходимых директорий...")
    required_dirs = [
        config["orders_dir"],
        config["logs_dir"],
        config["materials_dir"],
    ]
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Создана директория: {directory}")
        else:
            logger.debug(f"Директория уже существует: {directory}")


async def set_bot_commands(application, logger):
    """
    Устанавливает команды бота, отображаемые в интерфейсе Telegram.

    Args:
        application (telegram.ext.Application): Экземпляр бота.
        logger (logging.Logger): Логгер для записи информации.
    """
    commands = [
        BotCommand("start", "Главное меню"),
        BotCommand("events", "Мероприятия"),
        BotCommand("contacts", "Контакты"),
        BotCommand("tours", "Экскурсии"),
        BotCommand("souvenirs", "Сувениры"),
        BotCommand("materials", "Материалы"),
        BotCommand("guide", "Путеводитель"),
        BotCommand("support", "Связаться с оператором"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Команды бота успешно установлены")


def main():
    """
    Основная функция запуска бота:
    - Загружает конфигурацию и логгер.
    - Проверяет необходимые директории.
    - Регистрирует обработчики команд и сообщений.
    - Запускает polling для обработки обновлений.
    """
    print("Загрузка конфигурации...")
    config = load_config()

    print("Настройка логгера...")
    log_file_path = os.path.join(config["logs_dir"], config["log_file"])
    logger = get_logger(log_file_path)

    logger.info("=== Запуск бота ===")

    token = config.get("telegram_token")
    if not token:
        logger.error("telegram_token не указан в config.yaml. Завершение работы.")
        exit(1)
    logger.info("Токен Telegram загружен успешно")

    application = ApplicationBuilder().token(token).build()
    application.bot_data["config"] = config
    application.bot_data["logger"] = logger

    ensure_dirs(config, logger)

    logger.info("Регистрация обработчиков...")

    # --- Обработчики команд ---

    async def start_handler(update, context):
        """
        Обрабатывает команду /start — приветствует пользователя и показывает главное меню.
        """
        config = context.application.bot_data.get("config", {})
        welcome_text = load_message("welcome.txt") or config.get(
            "welcome_text", "Добро пожаловать!"
        )

        await update.message.reply_text(welcome_text)
        await send_menu(update, context)
        context.user_data.pop("current_menu", None)

    application.add_handler(CommandHandler("start", start_handler))

    # Регистрация основных команд
    main_commands = [
        ("events", show_events),
        ("contacts", contacts_handler),
        ("tours", show_tours),
        ("souvenirs", souvenirs_menu),
        ("materials", materials_menu),
        ("guide", guide_handler),
        ("support", start_support_conversation),
    ]

    for cmd, handler in main_commands:
        application.add_handler(CommandHandler(cmd, handler))

    # --- ConversationHandler для поддержки ---
    support_conversation_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^👨💻 Связаться с оператором$"), start_support_conversation
            )
        ],
        states={
            ASKING_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_support_question),
                CallbackQueryHandler(cancel_support, pattern=f"^{CANCEL_CALLBACK}$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_support, pattern=f"^{CANCEL_CALLBACK}$")],
        allow_reentry=True,
    )
    application.add_handler(support_conversation_handler)

    # --- Обработчик ответов операторов ---
    operators_chat_id = config.get("operators_chat_id")
    if operators_chat_id:
        application.add_handler(
            MessageHandler(
                filters.Chat(operators_chat_id) & filters.REPLY & filters.TEXT,
                operator_reply_handler,
            )
        )

    # --- Обработчики меню и кнопок ---
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_text_handler))

    # Обработчики callback_query для туров
    application.add_handler(
        CallbackQueryHandler(
            tour_callback_handler, pattern=r"^(date|register|unregister|back_to_dates)\|?"
        )
    )

    # Дополнительные команды и обработчики для материалов и сувениров
    application.add_handler(CommandHandler("material", materials_menu))
    application.add_handler(CommandHandler("myorder", souvenirs_menu_handler))
    application.add_handler(CommandHandler("cancelorder", souvenirs_menu_handler))

    application.add_handler(MessageHandler(filters.Regex("^🛍 Сувениры$"), souvenirs_menu))
    application.add_handler(
        MessageHandler(
            filters.Regex("^(Посмотреть заказ|Отменить заказ|Назад)$"), souvenirs_menu_handler
        )
    )

    application.add_handler(MessageHandler(filters.Regex("^📚 Материалы$"), materials_menu))
    application.add_handler(CallbackQueryHandler(material_button_handler, pattern=r"^material_"))

    # Обработчики мероприятий
    application.add_handler(MessageHandler(filters.Regex("^📅 Мероприятия$"), show_events))
    application.add_handler(CallbackQueryHandler(event_callback_handler, pattern=r"^event_date\|"))

    # Обработчики путеводителя
    application.add_handler(CallbackQueryHandler(guide_category_handler, pattern=r"^guide_cat\|"))
    application.add_handler(CallbackQueryHandler(guide_back_handler, pattern=r"^guide_back$"))

    # Обработчики контактов
    application.add_handler(MessageHandler(filters.Regex("^📞 Контакты$"), contacts_handler))
    application.add_handler(CallbackQueryHandler(contacts_category_handler, pattern=r"^contacts_cat\|"))
    application.add_handler(CallbackQueryHandler(contacts_back_handler, pattern=r"^contacts_back$"))

    # Обработчик данных веб-приложения
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data_handler))

    # Универсальный обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_handler))

    # Глобальный обработчик ошибок
    application.add_error_handler(error_handler)

    logger.info("Инициализация завершена, запуск polling...")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_bot_commands(application, logger))
    loop.run_until_complete(application.run_polling())

    logger.info("Бот остановлен")


if __name__ == "__main__":
    main()
