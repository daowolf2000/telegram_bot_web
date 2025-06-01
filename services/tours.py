# services/excursions.py

import json
import os
from core.logger import get_logger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(BASE_DIR, "..", "logs", "bot.log")  # или путь к вашему логу

logger = get_logger(LOG_FILE_PATH)

EXCURSIONS_FILE = os.path.join(BASE_DIR, "..", "data", "tours.json")


def load_tours():
    """
    Загружает список экскурсий из JSON-файла.

    Возвращает пустой список в случае отсутствия файла, пустого содержимого
    или ошибки парсинга.

    Returns:
        list: Список экскурсий (словарей).
    """
    abs_path = os.path.abspath(EXCURSIONS_FILE)
    logger.info(f"Загрузка файла экскурсий: {abs_path}")

    if not os.path.exists(EXCURSIONS_FILE):
        logger.error(f"Файл {abs_path} не найден")
        return []

    with open(EXCURSIONS_FILE, encoding="utf-8") as f:
        content = f.read()

    logger.info(f"Содержимое файла ({len(content)} байт)")

    if not content.strip():
        logger.warning(f"Файл {abs_path} пуст")
        return []

    try:
        excursions = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON в {abs_path}: {e}")
        return []

    return excursions
