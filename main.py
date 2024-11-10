import telebot
import requests
import jsons
from Class_ModelResponse import ModelResponse

API_TOKEN = '7589422109:AAG2LBN4iOhOf-ldei0ps42-bmuOfb69bx8'
bot = telebot.TeleBot(API_TOKEN)

# Хранилище контекста для каждого пользователя
user_context = {}

# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очищает ваш контекст общения\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['model'])
def send_model_name(message):
    # Отправляем запрос к LM Studio для получения информации о модели
    response = requests.get('http://localhost:1234/v1/models')

    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"Используемая модель: {model_name}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')


@bot.message_handler(commands=['clear'])
def clear_context(message):
    user_id = message.from_user.id
    
    # Очищаем контекст пользователя
    if user_id in user_context:
        del user_context[user_id]
        bot.reply_to(message, "Ваш контекст был очищен. Теперь можно начинать новый разговор!")
    else:
        bot.reply_to(message, "Ваш контекст уже пуст.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_query = message.text

    # Если контекст уже существует для этого пользователя, добавляем новый запрос в историю
    if user_id in user_context:
        user_context[user_id].append({"role": "user", "content": user_query})
    else:
        # Если контекста нет, создаем новый список
        user_context[user_id] = [{"role": "user", "content": user_query}]

    # Формируем запрос для модели с учетом контекста
    request = {
        "messages": user_context[user_id]
    }

    # Отправляем запрос к серверу модели
    response = requests.post(
        'http://localhost:1234/v1/chat/completions',
        json=request
    )

    if response.status_code == 200:
        # Получаем и обрабатываем ответ
        model_response: ModelResponse = jsons.loads(response.text, ModelResponse)
        model_message = model_response.choices[0].message.content

        # Добавляем ответ модели в контекст
        user_context[user_id].append({"role": "assistant", "content": model_message})

        # Отправляем ответ пользователю
        bot.reply_to(message, model_message)
    else:
        bot.reply_to(message, 'Произошла ошибка при обращении к модели.')


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
