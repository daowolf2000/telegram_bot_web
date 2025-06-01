# handlers/menu_handler.py

from telegram.ext import ContextTypes
from handlers.events import show_events
from handlers.tours import show_tours
from handlers.commands import send_menu
from handlers.materials import materials_menu
from handlers.souvenirs import souvenirs_menu, souvenirs_menu_handler
from handlers.support import start_support_conversation
from handlers.contacts import contacts_handler
from handlers.guide import guide_handler, guide_category_handler


MENU_ACTIONS = {
    "📅 Мероприятия": show_events,
    "🏛 Экскурсии": show_tours,
    "🛍 Сувениры": souvenirs_menu,
    "📚 Материалы": materials_menu,
    "🧭 Путеводитель": guide_handler,
    "👨💻 Связаться с оператором": start_support_conversation,
    "📞 Контакты": contacts_handler,
}


async def menu_text_handler(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик текстовых сообщений в основном меню.

    Игнорирует все сообщения в чате операторов, кроме ответов (обрабатываются отдельно).
    Перенаправляет пользователя в соответствующий обработчик в зависимости от текста сообщения.

    Args:
        update (telegram.Update): Объект обновления Telegram.
        context (telegram.ext.CallbackContext): Контекст обработчика.
    """
    # Игнорируем все сообщения в чате операторов, кроме ответов (их обрабатывает отдельный handler)
    if update.message.chat.id == context.application.bot_data["config"].get("operators_chat_id"):
        return

    text = update.message.text

    # Если пользователь находится в меню сувениров — перенаправляем в souvenirs_menu_handler
    if context.user_data.get("current_menu") == "souvenirs":
        await souvenirs_menu_handler(update, context)
        return

    if text == "🛍 Сувениры":
        await souvenirs_menu(update, context)
        context.user_data["current_menu"] = "souvenirs"
        return

    handler = MENU_ACTIONS.get(text)
    if handler:
        await handler(update, context)
        context.user_data.pop("current_menu", None)
    else:
        await update.message.reply_text("Пожалуйста, выберите пункт меню из списка.")
