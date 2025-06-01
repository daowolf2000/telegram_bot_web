import os


def load_message(filename: str) -> str:
    """
    Загружает текстовое сообщение из файла в папке 'data'.

    Args:
        filename (str): Имя файла с сообщением.

    Returns:
        str: Содержимое файла без начальных и конечных пробелов.
             Пустая строка, если файл не найден.
    """
    path = os.path.join("data", filename)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read().strip()
