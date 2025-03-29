import os
import subprocess
import sys
from flask import Flask
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import telegram

# Установка зависимостей
def install_requirements():
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'Flask==2.1.1', 'python-telegram-bot==13.15'])

# Проверка и установка зависимостей
install_requirements()

# Вопросы для дневника
QUESTION1, QUESTION2, QUESTION3, QUESTION4, QUESTION5 = range(5)
user_data = {}

questions = [
    "1. Опиши ситуацию, в которой появилась тревога.",
    "2. Какие эмоции ты испытала в этот момент?",
    "3. Какая автоматическая мысль пришла первой?",
    "4. Что ты сделала в этой ситуации?",
    "5. Как ты можешь взглянуть на неё иначе?"
]

# Создание Flask приложения
app = Flask(__name__)

def start(update, context):
    update.message.reply_text(
        "Привет! Это дневник автоматических мыслей.\nДавай заполним одну запись.\n\n" + questions[0]
    )
    user_data[update.effective_user.id] = {"answers": []}
    context.user_data["state"] = 0
    return QUESTION1

def handle_question(update, context):
    user_id = update.effective_user.id
    state = context.user_data.get("state", 0)
    user_data[user_id]["answers"].append(update.message.text)

    if state + 1 < len(questions):
        context.user_data["state"] = state + 1
        update.message.reply_text(questions[state + 1])
        return state + 1
    else:
        answers = user_data[user_id]["answers"]
        summary = "\n".join([f"{questions[i]}\n{answers[i]}" for i in range(len(answers))])
        update.message.reply_text("Готово! Вот твоя запись:\n\n" + summary)
        user_data[user_id]["answers"] = []
        context.user_data["state"] = 0
        return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text("Заполнение прервано.")
    return ConversationHandler.END

def main():
    # Использование переменной окружения для порта
    port = int(os.environ.get('PORT', 10000))  # Порт по умолчанию 10000

    # Создание Updater и Dispatcher
    updater = Updater("7609459910:AAHLUbrNIQTtxYDnThloG5U7T38bNuuycZ8", use_context=True)
    dispatcher = updater.dispatcher

    # Настройка обработчика разговора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUESTION1: [MessageHandler(Filters.text & ~Filters.command, handle_question)],
            QUESTION2: [MessageHandler(Filters.text & ~Filters.command, handle_question)],
            QUESTION3: [MessageHandler(Filters.text & ~Filters.command, handle_question)],
            QUESTION4: [MessageHandler(Filters.text & ~Filters.command, handle_question)],
            QUESTION5: [MessageHandler(Filters.text & ~Filters.command, handle_question)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Flask route для вебхука
    @app.route('/webhook', methods=['POST'])
    def webhook():
        json_str = request.get_data().decode('UTF-8')  # Получаем сообщение от Telegram
        update = telegram.Update.de_json(json_str, updater.bot)  # Обрабатываем сообщение
        dispatcher.process_update(update)  # Отправляем его в диспетчер
        return 'ok', 200  # Отправляем ответ Telegram

    # Устанавливаем Webhook
    updater.bot.setWebhook(f'https://yourdomain.com/webhook')  # Замените на свой реальный URL

    # Запуск Flask приложения на нужном порту
    app.run(host='0.0.0.0', port=port)  # Flask слушает на этом порту

if __name__ == '__main__':
    main()