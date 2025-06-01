import os
from datetime import datetime


def log_user_message(user_id: int, username: str, text: str, logs_dir: str, logger) -> None:
    """
    Логирует сообщение пользователя в файл с именем по user_id.

    Args:
        user_id (int): Идентификатор пользователя.
        username (str): Имя пользователя в Telegram (может быть None).
        text (str): Текст сообщения пользователя.
        logs_dir (str): Путь к директории с логами.
        logger (logging.Logger): Объект логгера для отладки.
    """
    log_file = os.path.join(logs_dir, f"{user_id}.log")
    timestamp = datetime.now().isoformat()
    user_tag = f"@{username}" if username else "@unknown"
    log_entry = f"{timestamp} - {user_tag}: {text}\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)

    logger.debug(f"Лог пользователя {user_id} обновлен: {text}")
