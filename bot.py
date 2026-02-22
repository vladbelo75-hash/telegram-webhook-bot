import os
from dotenv import load_dotenv
from flask import Flask, request
import telebot
import openai

# --- Загрузка переменных окружения ---
load_dotenv()
TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 5000))

# --- Проверка переменных ---
if not TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    raise ValueError("TOKEN, OPENAI_API_KEY или WEBHOOK_URL не заданы!")

TOKEN = TOKEN.strip()
OPENAI_API_KEY = OPENAI_API_KEY.strip()
WEBHOOK_URL = WEBHOOK_URL.strip()

openai.api_key = OPENAI_API_KEY

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- История сообщений ---
user_history = {}

# --- Функция запроса к OpenAI ---
def ask_ai(chat_id, prompt):
    user_history.setdefault(chat_id, [])
    user_history[chat_id].append({"role": "user", "content": prompt})
    messages = user_history[chat_id][-10:]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )
    answer = response['choices'][0]['message']['content']
    user_history[chat_id].append({"role": "assistant", "content": answer})
    return answer

# --- Команда /start ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я AI бот и могу с тобой общаться 🤖")

# --- Все остальные сообщения ---
@bot.message_handler(func=lambda m: True)
def ai_response(message):
    answer = ask_ai(message.chat.id, message.text)
    bot.send_message(message.chat.id, answer)

# --- Webhook endpoint ---
@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# --- Установка webhook прямо перед запуском ---
def setup_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    print(f"Webhook установлен: {WEBHOOK_URL}/{TOKEN}")

if __name__ == "__main__":
    setup_webhook()  # вызываем вручную
    app.run(host="0.0.0.0", port=PORT)