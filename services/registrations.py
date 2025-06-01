# services/registrations.py

import os
import json

REG_DIR = "registrations"


def ensure_reg_dir():
    """
    Проверяет наличие директории для регистраций, создаёт при отсутствии.
    """
    if not os.path.exists(REG_DIR):
        os.makedirs(REG_DIR)


def get_user_registrations(user_id: int) -> set:
    """
    Загружает регистрации пользователя из JSON-файла.

    Args:
        user_id (int): Идентификатор пользователя.

    Returns:
        set: Множество зарегистрированных значений (например, ID мероприятий).
             Пустое множество, если файл не найден или пуст.
    """
    ensure_reg_dir()
    path = os.path.join(REG_DIR, f"{user_id}.json")
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data)


def save_user_registrations(user_id: int, registrations: set) -> None:
    """
    Сохраняет регистрации пользователя в JSON-файл.

    Args:
        user_id (int): Идентификатор пользователя.
        registrations (set): Множество зарегистрированных значений.
    """
    ensure_reg_dir()
    path = os.path.join(REG_DIR, f"{user_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(registrations), f)
