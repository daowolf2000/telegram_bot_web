import logging
from logging.handlers import RotatingFileHandler


def get_logger(log_file_path: str) -> logging.Logger:
    """
    Создаёт и настраивает логгер для Telegram-бота с ротацией файлов.

    Логирует все уровни в файл, INFO и выше — в консоль.

    Args:
        log_file_path (str): Путь к файлу лога.

    Returns:
        logging.Logger: Настроенный объект логгера.
    """
    logger = logging.getLogger("telegram_bot")
    logger.setLevel(logging.DEBUG)  # Логируем все уровни

    if not logger.hasHandlers():
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
