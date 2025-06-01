import yaml


def load_config(path: str = "config.yaml") -> dict:
    """
    Загружает конфигурацию из YAML-файла.

    Args:
        path (str): Путь к YAML-файлу конфигурации. По умолчанию "config.yaml".

    Returns:
        dict: Словарь с конфигурационными данными.
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
