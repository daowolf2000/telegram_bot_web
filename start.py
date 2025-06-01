#!/usr/bin/env python3

import os
import yaml
import json
import signal
import subprocess
import threading
import http.server
import socketserver
import re
import csv
import urllib.parse
from functools import partial

CONFIG_FILE = "config.yaml"
PRODUCTS_FILE = "products.yaml"
WEBAPP_DIR = "webapp"
WEBAPP_PORT = 8080
ORDERS_DIR = "orders"


def load_config():
    """
    Загружает конфигурацию из YAML-файла.

    Returns:
        dict: Словарь с конфигурацией.
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {"telegram_token": "", "webapp_url": "", "admin_chat_id": 0}


def save_config(config):
    """
    Сохраняет конфигурацию в YAML-файл.

    Args:
        config (dict): Конфигурация для сохранения.
    """
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    print(f"✅ Конфигурация сохранена в {CONFIG_FILE}")


class WebAppRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    Обработчик HTTP-запросов для веб-сервера.
    Обрабатывает запросы к /get_order и отдаёт данные заказа пользователя.
    """

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path == "/get_order":
            query = urllib.parse.parse_qs(parsed_path.query)
            user_id = query.get("user_id", [None])[0]
            if user_id:
                order_file = os.path.join(ORDERS_DIR, f"{user_id}.csv")
                if os.path.exists(order_file):
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    with open(order_file, encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        items = list(reader)
                    if items:
                        response = {
                            "items": [
                                {
                                    "id": int(i["item_id"]),
                                    "name": i["name"],
                                    "unit": i["unit"],
                                    "qty": int(i["qty"]),
                                }
                                for i in items
                            ],
                            "fio": items[0].get("fio", ""),
                            "packaging": items[0].get("packaging", ""),
                        }
                    else:
                        response = {}
                    self.wfile.write(json.dumps(response).encode())
                    return
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
        super().do_GET()


def start_web_server():
    """
    Запускает HTTP-сервер для обслуживания веб-приложения.

    Returns:
        socketserver.TCPServer: Запущенный сервер.
    """
    handler = partial(WebAppRequestHandler, directory=WEBAPP_DIR)
    httpd = socketserver.TCPServer(("", WEBAPP_PORT), handler)
    print(f"✅ Веб-сервер запущен и обслуживает папку {WEBAPP_DIR} на http://localhost:{WEBAPP_PORT}")

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    return httpd


def start_cloudpub(port):
    """
    Запускает туннель CloudPub для публичного доступа к локальному серверу.

    Args:
        port (int): Локальный порт, который нужно пробросить.

    Returns:
        tuple: (url публичного доступа, процесс CloudPub) или (None, None) при ошибке.
    """
    print(f"🚀 Запускаем CloudPub туннель на порт {port}...")
    proc = subprocess.Popen(
        ["clo", "publish", "http", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    url = None
    for line in proc.stdout:
        print(f"[cloudpub] {line.strip()}")
        match = re.search(r"https://[^\s]+", line)
        if match:
            url = match.group(0)
            print(f"✅ Найден публичный URL CloudPub: {url}")
            break

    if not url:
        print("❌ Не удалось получить публичный URL из вывода CloudPub.")
        proc.terminate()
        return None, None

    return url, proc


def start_telegram_bot(token):
    """
    Запускает Telegram-бота как отдельный процесс.

    Args:
        token (str): Токен Telegram-бота.

    Returns:
        subprocess.Popen или None: Процесс бота или None при ошибке.
    """
    try:
        bot_process = subprocess.Popen(
            ["python", "bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print("✅ Telegram-бот запущен")
        return bot_process
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        return None


def cleanup(processes):
    """
    Останавливает запущенные процессы.

    Args:
        processes (dict): Словарь с именами процессов и объектами subprocess или серверов.
    """
    for name, process in processes.items():
        if process:
            try:
                if name == "web_server":
                    process.shutdown()
                else:
                    process.terminate()
                print(f"✅ Процесс {name} остановлен")
            except Exception:
                pass


def main():
    """
    Главная функция запуска проекта:
    - Загружает конфигурацию.
    - Запускает веб-сервер.
    - Запускает CloudPub туннель.
    - Запускает Telegram-бота.
    - Ожидает сигнала завершения и корректно останавливает процессы.
    """
    print("🚀 Запуск проекта Telegram-бота с Web App (CloudPub)")

    config = load_config()
    os.makedirs(ORDERS_DIR, exist_ok=True)

    web_server = start_web_server()

    cloudpub_url, cloudpub_proc = start_cloudpub(WEBAPP_PORT)
    if not cloudpub_url:
        print("❌ Не удалось запустить CloudPub туннель, остановка.")
        cleanup({"web_server": web_server})
        return

    config["webapp_url"] = cloudpub_url.rstrip("/") + "/index.html"
    save_config(config)

    if not config.get("telegram_token"):
        token = input("Введите токен Telegram-бота: ")
        config["telegram_token"] = token
        save_config(config)

    bot_process = start_telegram_bot(config["telegram_token"])

    print("\n✨ Всё готово! ✨")
    print(f"📱 Telegram Web App доступен по адресу: {config['webapp_url']}")
    print("⚠️ Нажмите Ctrl+C для остановки всех процессов")

    try:
        signal.pause()
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Останавливаем все процессы...")
        cleanup(
            {
                "web_server": web_server,
                "cloudpub": cloudpub_proc,
                "bot": bot_process,
            }
        )
        print("👋 До свидания!")


if __name__ == "__main__":
    main()
