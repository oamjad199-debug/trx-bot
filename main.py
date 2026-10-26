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
        print(f"-> وصل تحديث من تيليجرام: {json_string}", flush=True)
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"-> خطأ في الويب هوك: {e}", flush=True)
    return 'OK', 200

@bot.message_handler(commands=['start'])
def start(message):
    try:
        print("-> تم استلام أمر /start بنجاح وجاري الرد...", flush=True)
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
        print("-> تم إرسال الرد إلى تيليجرام بنجاح!", flush=True)
    except Exception as e:
        print(f"-> خطأ داخل دالة البداية (Start): {e}", flush=True)

if __name__ == '__main__':
    bot.remove_webhook()
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"-> تم ضبط الويب هوك على: {webhook_url}", flush=True)
    
    port = int(os.environ.get('PORT', 10000))
    server.run(host='0.0.0.0', port=port)
