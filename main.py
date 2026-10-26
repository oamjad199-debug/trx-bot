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
        print(f"Error processing update: {e}", flush=True)
    return 'OK', 200

# الخطوة الأولى: استقبال أمر /start وإرسال رسالة التحقق مع رابط المختصر
@bot.message_handler(commands=['start'])
def start(message):
    try:
        markup = telebot.types.InlineKeyboardMarkup()
        # زر يوجه المستخدم لرابط التحقق الخارجي
        verify_button = telebot.types.InlineKeyboardButton(
            "تحقق أنك إنسان 🤖", 
            url="http://bc.vc/Dc4Boi8"
        )
        # زر ثانٍ لتأكيد التحقق وفتح التطبيق المصغر (أو نقله للمرحلة التالية)
        confirmed_button = telebot.types.InlineKeyboardButton(
            "تم التأكيد (فتح التطبيق المصغر) 🚀", 
            callback_data="open_webapp"
        )
        
        markup.add(verify_button)
        markup.add(confirmed_button)
        
        bot.reply_to(
            message, 
            "أهلاً بك يا عمر!\nالرجاء إتمام التحقق أولاً بأنك لست روبوت عبر الرابط أدناه، ثم اضغط على 'تم التأكيد':", 
            reply_markup=markup
        )
    except Exception as e:
        print(f"Error in start handler: {e}", flush=True)

# الخطوة الثانية: عند الضغط على زر تم التأكيد، يظهر التطبيق المصغر
@bot.callback_query_handler(func=lambda call: call.data == "open_webapp")
def verified_callback(call):
    try:
        markup = telebot.types.InlineKeyboardMarkup()
        web_app = telebot.types.WebAppInfo(url="https://trx-earn-bot-1.onrender.com") # أو رابط الواجهة الخاصة بك
        webapp_button = telebot.types.InlineKeyboardButton(
            "فتح التطبيق المصغر الآن 🚀", 
            web_app=web_app
        )
        markup.add(webapp_button)
        
        bot.answer_callback_query(call.id, "تم التحقق بنجاح!")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="تم التأكيد بنجاح! اضغط أدناه لفتح التطبيق المصغر:",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Error in callback handler: {e}", flush=True)

if __name__ == '__main__':
    bot.remove_webhook()
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    
    port = int(os.environ.get('PORT', 10000))
    server.run(host='0.0.0.0', port=port)
