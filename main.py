import os
import threading
from flask import Flask
import telebot

TOKEN = os.environ.get('TOKEN')
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
        .card { background: #1e293b; padding: 25px; border-radius: 12px; display: inline-block; width: 85%; max-width: 400px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        h2 { color: #38bdf8; }
        p { color: #94a3b8; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="card">
        <h2>تطبيق أرباح TRX 🚀</h2>
        <p>أهلاً بك يا عمر! تم التحقق بنجاح، يمكنك الآن متابعة الأرباح.</p>
    </div>
</body>
</html>
"""

@server.route('/')
def home():
    return HTML_TEMPLATE

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
        print(f"START ERROR: {e}")

def run_bot():
    try:
        # إلغاء أي ويب هوك قديم لمنع التعارض نهائياً
        bot.remove_webhook()
        print("Bot started polling...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Polling error: {e}")

if __name__ == '__main__':
    # تشغيل البوت في خلفية السيرفر ليعمل بشكل دائم وسلس
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    server.run(host='0.0.0.0', port=port)
