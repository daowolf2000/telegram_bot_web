## Структура проекта

```
telegram_bot_web/
│
├── bot.py                # Основной файл бота
├── start.py              # Точка входа (запус WebApp, CloudPub и бота)
├── config.yaml           # Файл конфигурации
├── requirements.txt      # Зависимости Python
│
├── core/                 # Базовая логика и утилиты
├── data/                 # Работа с данными (БД, хранилища)
├── handlers/             # Обработчики команд и событий
├── logs/                 # Логи работы
├── orders/               # Заказы пользователей сувениров
├── registrations/        # Регистрация пользователей на экскурсии
├── services/             # Вспомогательные сервисы
└── webapp/               # Веб-интерфейс (HTML, CSS, Python)
```


---

## Установка

```bash
# Клонируйте репозиторий
git clone https://github.com/daowolf2000/telegram_bot_web.git
cd telegram_bot_web

# Создайте и активируйте виртуальное окружение (рекомендуется)
python3 -m venv venv
source venv/bin/activate  # Для Windows: venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
```

Для WebApp используется CloudPub для публикации локально запущенного web сервера.
Необходимо зарегистрироваться на https://cloudpub.ru

После регистрации установите клиента и авторизуйтесь.
Для Linux:
```bash
wget https://cloudpub.ru/download/stable/clo-1.7.0-stable-linux-x86_64.tar.gz
tar -xvf clo-1.7.0-stable-linux-x86_64.tar.gz
sudo mv clo /usr/local/bin

# Ключ авторизации можно взять на https://cloudpub.ru/dashboard
clo set token ВАШ_ТОКЕН
```

Для запуска используйте скрипт start.py (если с webapp) или bot.py (если без каталога сувениров)
Не забудьте активировать виртуальное окружение.
```bash
source venv/bin/activate
python3 start.py
```


---

## Настройка

1. **config.yaml**

Откройте файл `config.yaml` и укажите необходимые параметры:
    - Токен Telegram-бота (`telegram_token`).
    - ID для группы техподдержки (`operators_chat_id`) - для групп будет отрицательным числом. Бот должен иметь права администратора в группе, чтобы писать сообщения в группу.

Остальные настройки можно оставить по умолчанию.

2. **data**

Все данные расположенны в соответствующих файлах в каталоге `data`. Смотрите пример для заполнения.

3. **webapp**

Каталог сувениров. Все товары описаны в `products.json`. 

4. **Оформление**

Используйте https://t.me/BotFather для настройки имени, описания, аватарки и т.д.

