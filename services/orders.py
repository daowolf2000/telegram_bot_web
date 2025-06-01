import os
import csv
from datetime import datetime


def save_order(
    user_id: int,
    username: str,
    fio: str,
    packaging: str,
    items: list,
    orders_dir: str,
    logger,
) -> None:
    """
    Сохраняет заказ пользователя в CSV-файл.

    Args:
        user_id (int): Идентификатор пользователя.
        username (str): Имя пользователя Telegram (может быть пустым).
        fio (str): ФИО пользователя.
        packaging (str): Тип упаковки.
        items (list): Список товаров (каждый — словарь с ключами id, name, unit, qty, price).
        orders_dir (str): Путь к директории с заказами.
        logger (logging.Logger): Логгер для записи информации.
    """
    logger.debug(f"Сохранение заказа: user_id={user_id}, fio={fio}, items_count={len(items)}")
    order_file = os.path.join(orders_dir, f"{user_id}.csv")

    with open(order_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "user_id",
                "username",
                "fio",
                "packaging",
                "item_id",
                "name",
                "unit",
                "qty",
                "price",
                "timestamp",
            ]
        )
        timestamp = datetime.now().isoformat()
        for item in items:
            writer.writerow(
                [
                    user_id,
                    username or "",
                    fio,
                    packaging,
                    item.get("id", ""),
                    item.get("name", ""),
                    item.get("unit", ""),
                    item.get("qty", ""),
                    item.get("price", ""),
                    timestamp,
                ]
            )
    logger.info(f"Заказ пользователя {user_id} успешно сохранён")


def read_order(user_id: int, orders_dir: str) -> list | None:
    """
    Читает заказ пользователя из CSV-файла.

    Args:
        user_id (int): Идентификатор пользователя.
        orders_dir (str): Путь к директории с заказами.

    Returns:
        list[dict] | None: Список строк заказа в виде словарей или None, если файл не найден.
    """
    order_file = os.path.join(orders_dir, f"{user_id}.csv")
    if not os.path.exists(order_file):
        return None

    with open(order_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def remove_order(user_id: int, orders_dir: str, logger) -> bool:
    """
    Удаляет файл заказа пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
        orders_dir (str): Путь к директории с заказами.
        logger (logging.Logger): Логгер для записи информации.

    Returns:
        bool: True, если файл был удалён, False если файла не было.
    """
    order_file = os.path.join(orders_dir, f"{user_id}.csv")
    if os.path.exists(order_file):
        os.remove(order_file)
        logger.info(f"Заказ пользователя {user_id} удалён")
        return True
    return False
