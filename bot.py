from config import BOT_TOKEN, ADMIN_ID
from functions import get_ai_response
from db import db_manager
import telebot
from telebot import types

# ==================== ПРОВЕРКИ ====================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID не найден в .env файле")

bot = telebot.TeleBot(BOT_TOKEN)

def setup_commands():
    commands = [
        telebot.types.BotCommand(
            command="start",
            description="Начать работу с ботом"
        )
    ]
    bot.set_my_commands(commands)
# создаём таблицы при запуске
db_manager.create_tables()

print("🤖 Бот запущен и готов к работе")

# ==================== /START ====================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # добавляем пользователя (если новый)
    is_new_user = db_manager.add_user(message.chat.id)

    # проверяем дневной сброс
    db_manager.reset_daily_requests_if_needed(message.chat.id)

    greeting = "👋 Привет. Я — ассистент с искусственным интеллектом.\n\n"

    if is_new_user:
        greeting += (
            "У вас есть 150 запросов в сутки. Лимит обновляется автоматически в полночь.\n"
            "Чтобы начать диалог, просто напишите сообщение не менее 10 символов\n"
            "Лимит обновляется автоматически каждый день.\n\n"
        )

        total_users = db_manager.get_total_users()
        bot.send_message(
            ADMIN_ID,
            f"Новый пользователь: {message.chat.id}\nВсего пользователей: {total_users}",
            disable_notification=True
        )
    else:
        greeting += (
            "Вы уже пользовались ботом ранее.\n\n"
        )

    greeting += (
        "Просто напишите сообщение (минимум 10 символов), "
        "и я постараюсь помочь.\n\n"
        "Используйте кнопки ниже 👇"
    )

    # инлайн-кнопки (БЕЗ баланса)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("ℹ️ Помощь", callback_data="menu_help"),
        types.InlineKeyboardButton("👨‍💻 О проекте", callback_data="menu_dev"),
    )

    bot.send_message(message.chat.id, greeting, reply_markup=markup)

# ==================== КНОПКИ ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def menu_callback(call):
    bot.answer_callback_query(call.id)

    chat_id = call.message.chat.id
    user_id = call.from_user.id

    db_manager.reset_daily_requests_if_needed(user_id)

    if call.data == "menu_help":
        bot.send_message(
            chat_id,
            "ℹ️ Помощь\n\n"
            "Этот Ai-бот — простой и быстрый способ получать ответы.\n"
            "Интерфейс минималистичен, ответы — мгновенны. За каждым диалогом стоит отлаженный код, написанный с принципами простоты и надёжности. Редкий инструмент, который делает свою работу хорошо: предоставляет информацию быстро и без лишних деталей.\n\n"
            "• До 150 запросов в сутки\n"
            "• 1 сообщение = 1 запрос\n"
            "• Лимит обновляется автоматически\n\n"
            "Просто напишите свой вопрос текстом."
        )

    elif call.data == "menu_dev":
        bot.send_message(
            chat_id,
            "👨‍💻 свежий Telegram AI-бот\n"
            "✅ Абсолютно бесплатный доступ\n"
             "🔹 Бот не сохраняет личную информацию, но быстро обучается и подстраивается под вас"
            "🔹 Никакой рекламы, просто вставляешь запрос\n"
        )

# ==================== ОСНОВНОЙ ОБРАБОТЧИК ====================

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    print(f"📩 {message.chat.id}: {message.text[:50]}")

    if not message.text:
        return

    if len(message.text) < 10:
        bot.reply_to(message, "⚠️ Пожалуйста, напишите не менее 10 символов.")
        return

    if len(message.text) > 4000:
        bot.reply_to(message, "⚠️ Максимум 4000 символов.")
        return

    # 🔄 дневной сброс
    db_manager.reset_daily_requests_if_needed(message.chat.id)

    # ❗ СРАЗУ пытаемся списать запрос
    if not db_manager.use_request(message.chat.id):
        bot.send_message(
            message.chat.id,
            "❌ Дневной лимит исчерпан.\nПопробуйте снова завтра."
        )
        return

    # ✅ запрос успешно списан — идём в AI
    bot.send_chat_action(message.chat.id, "typing")

    try:
        response_text, _, _ = get_ai_response(message.text)

        db_manager.add_result(
            message.chat.id,
            message.text,
            response_text
        )

        bot.reply_to(message, response_text, parse_mode="HTML")

    except Exception as e:
        # 🔄 если AI упал — возвращаем запрос
        db_manager.add_request_back(message.chat.id)
        print("❌ AI error:", e)
        bot.reply_to(message, "❌ Произошла ошибка. Попробуйте позже.")



# ==================== НЕ-ТЕКСТ ====================

@bot.message_handler(content_types=[
    "photo", "video", "document", "sticker",
    "voice", "audio", "video_note", "animation"
])
def reject_non_text(message):
    bot.reply_to(message, "❌ Бот принимает только текстовые сообщения.")

# ==================== ЗАПУСК ====================


if __name__ == "__main__":
    setup_commands()
    bot.infinity_polling(interval=0)