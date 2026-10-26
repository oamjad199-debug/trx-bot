import os
from flask import Flask
import telebot
import threading
import time

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# تصميم صفحة التطبيق المصغر داخل التيليجرام
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تطبيق الأرباح</title>
    <style>
        body { background: #0f172a; color: #fff; font-family: Tahoma, sans-serif; text-align: center; padding-top: 50px; }
        .card { background: #1e293b; padding: 25px; border-radius: 12px; display: inline-block; width: 85%; max-width: 400px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        h2 { color: #38bdf8; }
        p { color: #94a3b8; line-height: 1.6; }
        .btn { display: inline-block; margin-top: 15px; padding: 10px 20px; background: #38bdf8; color: #0f172a; text-decoration: none; border-radius: 8px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>تطبيق أرباح TRX 🚀</h2>
        <p>أهلاً بك يا عمر! تم التحقق بنجاح. يمكنك الآن البدء وتصفح الأرباح.</p>
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
    
    # 1. زر التحقق (رابط التحقق الخاص بك)
    verify_button = telebot.types.InlineKeyboardButton(
        "تحقق أنك إنسان 🤖", 
        url="http://bc.vc/GnhfJyX"
    )
    
    # 2. زر فتح التطبيق المصغر (تأكد أن الرابط أدناه مطابق لرابط مشروعك الفعلي على رندر)
    web_app = telebot.types.WebAppInfo(url="https://trx-earn-bot-1.onrender.com")
    webapp_button = telebot.types.InlineKeyboardButton(
        "فتح التطبيق المصغر 🚀", 
        web_app=web_app
    )
    
    markup.add(verify_button)
    markup.add(webapp_button)
    
    bot.reply_to(
        message, 
        "أهلاً بك يا عمر! يرجى إتمام التحقق أولاً عبر الرابط، ثم افتح التطبيق المصغر:", 
        reply_markup=markup
    )

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
    
    port = int(os.environ.get('PORT', 10000))
    server.run(host='0.0.0.0', port=port)
