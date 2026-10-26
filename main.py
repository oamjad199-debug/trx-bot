import os
from flask import Flask, request
import telebot

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://trx-bot-e61j.onrender.com')

@server.route('/')
def home():
    return "TRX Bot is active and running successfully! 🚀"

@server.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"Error processing update: {e}")
    return 'OK', 200

@bot.message_handler(commands=['start'])
def start(message):
    try:
        markup = telebot.types.InlineKeyboardMarkup()
        web_app = telebot.types.WebAppInfo(url="http://bc.vc/Dc4Boi8")
        webapp_button = telebot.types.InlineKeyboardButton(
            "فتح التطبيق المصغر 🚀", 
            web_app=web_app
        )
        markup.add(webapp_button)

        bot.reply_to(
            message, 
            "أهلاً بك يا عمر! اضغط أدناه لإتمام التحقق وفتح التطبيق المصغر:", 
            reply_markup=markup
        )
    except Exception as e:
        print(f"Error in start handler: {e}")

if __name__ == '__main__':
    bot.remove_webhook()
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"Webhook set to: {webhook_url}")

    port = int(os.environ.get('PORT', 10000))
    server.run(host='0.0.0.0', port=port)
