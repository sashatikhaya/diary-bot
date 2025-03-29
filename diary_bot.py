import os
from flask import Flask, request
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import telegram

# Вопросы для дневника тревожности
QUESTION1, QUESTION2, QUESTION3, QUESTION4, QUESTION5, QUESTION6 = range(6)
user_data = {}

# Вопросы для дневника тревожности
questions_male = [
    "1. Опиши ситуацию, в которой ты почувствовал тревогу.",
    "2. Какие эмоции ты испытал в этот момент?",
    "3. Какая автоматическая мысль пришла первой?",
    "4. Что ты сделал в этой ситуации?",
    "5. Как ты можешь взглянуть на неё иначе?"
]

questions_female = [
    "1. Опиши ситуацию, в которой ты почувствовала тревогу.",
    "2. Какие эмоции ты испытала в этот момент?",
    "3. Какая автоматическая мысль пришла первой?",
    "4. Что ты сделала в этой ситуации?",
    "5. Как ты можешь взглянуть на неё иначе?"
]

# Дневник настроения (второй вариант дневника)
mood_diary = [
    "Как часто ты чувствуешь тревогу?",
    "Какие мысли вызывают тревогу?",
    "Что ты обычно делаешь, чтобы справиться с тревогой?",
    "Что бы могло помочь тебе снизить уровень тревоги?"
]

# Создание Flask приложения
app = Flask(__name__)

def start(update, context):
    update.message.reply_text(
        "Привет! Я здесь, чтобы помочь тебе разобраться в мыслях и эмоциях. Для начала скажи, как к тебе лучше обращаться — ты парень или девушка?"
    )
    return QUESTION1

def gender(update, context):
    user_gender = update.message.text.lower()
    if user_gender in ["парень", "мужчина"]:
        user_data[update.effective_user.id] = {"gender": "male", "answers": []}
        update.message.reply_text("Выбери тип дневника: 1 — Дневник тревожности, 2 — Дневник настроения.")
    elif user_gender in ["девушка", "женщина"]:
        user_data[update.effective_user.id] = {"gender": "female", "answers": []}
        update.message.reply_text("Выбери тип дневника: 1 — Дневник тревожности, 2 — Дневник настроения.")
    else:
        update.message.reply_text("Я тебя не понял, напиши 'парень' или 'девушка'.")
        return QUESTION1
    return QUESTION2

def select_diary(update, context):
    user_id = update.effective_user.id
    user_choice = update.message.text

    if user_choice == "1":
        questions = questions_male if user_data[user_id]["gender"] == "male" else questions_female
        update.message.reply_text(questions[0])
        return QUESTION3
    elif user_choice == "2":
        update.message.reply_text(mood_diary[0])
        return QUESTION3
    else:
        update.message.reply_text("Выбери 1 или 2.")
        return QUESTION2

def handle_question(update, context):
    user_id = update.effective_user.id
    state = len(user_data[user_id]["answers"])
    user_data[user_id]["answers"].append(update.message.text)

    if state + 1 < len(questions_male) if user_data[user_id]["gender"] == "male" else len(questions_female):
        next_question = questions_male[state + 1] if user_data[user_id]["gender"] == "male" else questions_female[state + 1]
        update.message.reply_text(next_question)
        return QUESTION3
    elif state + 1 < len(mood_diary):
        update.message.reply_text(mood_diary[state + 1])
        return QUESTION3
    else:
        summary = f"Дата и время: {user_data[user_id].get('date_time')}\n"
        summary += "\n".join(user_data[user_id]["answers"])
        update.message.reply_text(f"Вот твоя запись:\n\n{summary}")
        user_data[user_id]["answers"] = []
        return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text("Заполнение прервано.")
    return ConversationHandler.END

def main():
    # Использование переменной окружения для порта
    port = int(os.environ.get('PORT', 10000))  # Порт по умолчанию 10000

    # Создание Updater и Dispatcher
    updater = Updater("YOUR_BOT_TOKEN", use_context=True)  # Замените YOUR_BOT_TOKEN на ваш реальный токен
    dispatcher = updater.dispatcher

    # Настройка обработчика разговора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUESTION1: [MessageHandler(Filters.text & ~Filters.command, gender)],
            QUESTION2: [MessageHandler(Filters.text & ~Filters.command, select_diary)],
            QUESTION3: [MessageHandler(Filters.text & ~Filters.command, handle_question)],
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
    updater.bot.setWebhook(f'https://diary-bot.onrender.com/webhook')  # Используем реальный URL от Render

    # Запуск Flask приложения на нужном порту
    app.run(host='0.0.0.0', port=port)  # Flask слушает на этом порту

if __name__ == '__main__':
    main()
