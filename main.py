import os
from flask import Flask, request
import telebot

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# الرابط الصحيح والفعلي لمشروعك على رندر من السجلات
RENDER_URL = "https://trx-bot-e61j.onrender.com"

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

# استقبال الرسائل عبر الـ Webhook من تيليجرام
@server.route('/' + TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK', 200

@bot.message_handler(commands=['start'])
def start(message):
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

if __name__ == '__main__':
    # ربط الويب هوك تلقائياً بالرابط الصحيح
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    
    port = int(os.environ.get('PORT', 10000))
    server.run(host='0.0.0.0', port=port)
