import os
from flask import Flask
import telebot
import threading
import time

TOKEN = 8742073577:AAFhQIaBwT8m9zJpb1V6QSM8mrm7ldWXKuA
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تطبيق الأرباح</title>
    <style>
        body { background: #0f172a; color: #fff; font-family: Tahoma, sans-serif; text-align: center; padding-top: 50px; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; display: inline-block; width: 80%; max-width: 400px; }
        h2 { color: #38bdf8; }
    </style>
</head>
<body>
    <div class="card">
        <h2>مرحباً بك في التطبيق المصغر! 🚀</h2>
        <p>البوت والتطبيق يعملان بنجاح تام.</p>
    </div>
</body>
</html>
"""

@server.route('/')
def home():
    return HTML_TEMPLATE

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    # سيتم ربط رابط التطبيق المصغر لاحقاً
    web_app = telebot.types.WebAppInfo(url="https://trx-bot.onrender.com")
    markup.add(telebot.types.InlineKeyboardButton("فتح التطبيق المصغر 🚀", web_app=web_app))
    bot.reply_to(message, "أهلاً بك يا عمر! اضغط أدناه لفتح التطبيق المصغر:", reply_markup=markup)

if __name__ == '__main__':
    def run_bot():
        while True:
            try:
                bot.polling(none_stop=True)
            except Exception as e:
                time.sleep(5)
    
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get('PORT', 5000))
    server.run(host='0.0.0.0', port=port)
