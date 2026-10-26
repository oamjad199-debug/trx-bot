import os
import sqlite3
from flask import Flask, request
import telebot

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://trx-bot-e61j.onrender.com')

# --- إعداد قاعدة بيانات SQLite ---
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0.0,
            referred_by INTEGER,
            active_referrals INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@server.route('/')
def home():
    return "TRX Bot with SQLite & Referral System is running successfully! 🚀"

@server.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"Error processing update: {e}", flush=True)
    return 'OK', 200

# أمر /start مع دعم نظام الإحالات وحفظ المستخدم
@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "No Username"
        
        # استخراج كود الإحالة إن وجد (مثال: /start 123456)
        text_parts = message.text.split()
        referrer_id = None
        if len(text_parts) > 1:
            try:
                referrer_id = int(text_parts[1])
            except ValueError:
                pass

        # حفظ المستخدم في قاعدة البيانات إذا كان جديداً
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        existing_user = cursor.fetchone()
        
        if not existing_user:
            # التأكد أن المستخدم لا يحيل نفسه
            if referrer_id and referrer_id != user_id:
                # التحقق أن المُحيل موجود فعلاً
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (referrer_id,))
                if cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO users (user_id, username, referred_by) VALUES (?, ?, ?)",
                        (user_id, username, referrer_id)
                    )
                    # زيادة عدد الإحالات النشطة للمُحيل
                    cursor.execute(
                        "UPDATE users SET active_referrals = active_referrals + 1 WHERE user_id = ?",
                        (referrer_id,)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO users (user_id, username) VALUES (?, ?)",
                        (user_id, username)
                    )
            else:
                cursor.execute(
                    "INSERT INTO users (user_id, username) VALUES (?, ?)",
                    (user_id, username)
                )
            conn.commit()
        conn.close()

        # توليد رابط الإحالة الخاص بالمستخدم
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

        # إعداد الأزرار والترحيب
        markup = telebot.types.InlineKeyboardMarkup()
        web_app = telebot.types.WebAppInfo(url="https://trx-earn-bot-1.onrender.com")
        webapp_button = telebot.types.InlineKeyboardButton("فتح التطبيق المصغر 🚀", web_app=web_app)
        markup.add(webapp_button)
        
        welcome_msg = (
            f"أهلاً بك يا عمر في بوت مكافآت TRX! 🚀\n\n"
            f"💰 نظام الإحالات: احصل على **3% أرباح للأبد** من كل إحالة نشطة تدعوها!\n"
            f"🔗 رابط الإحالة الخاص بك:\n`{ref_link}`\n\n"
            f"اضغط أدناه لفتح التطبيق المصغر والبدء:"
        )
        
        bot.reply_to(message, welcome_msg, parse_mode="Markdown", reply_markup=markup)
        
    except Exception as e:
        print(f"Error in start handler: {e}", flush=True)

if __name__ == '__main__':
    bot.remove_webhook()
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    
    port = int(os.environ.get('PORT', 10000))
    server.run(host='0.0.0.0', port=port)
