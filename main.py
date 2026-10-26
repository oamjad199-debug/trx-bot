import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string
import telebot

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://trx-bot-e61j.onrender.com')

# --- إعداد قاعدة بيانات SQLite ---
def init_db():
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
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
    return "TRX Bot & Mini App is active and running successfully! 🚀"

@server.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"Error processing update: {e}", flush=True)
    return 'OK', 200

# أمر /start النظيف (يرسل زر فتح التطبيق المصغر فقط بدون زحمة في الشات)
@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "No Username"
        
        # معالجة الإحالة إن وجدت في الـ start
        text_parts = message.text.split()
        referrer_id = None
        if len(text_parts) > 1:
            try:
                referrer_id = int(text_parts[1])
            except ValueError:
                pass

        conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            if referrer_id and referrer_id != user_id:
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (referrer_id,))
                if cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO users (user_id, username, referred_by) VALUES (?, ?, ?)",
                        (user_id, username, referrer_id)
                    )
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

        # زر فتح التطبيق المصغر الموجه لرابط الـ webapp على السيرفر
        markup = telebot.types.InlineKeyboardMarkup()
        web_app = telebot.types.WebAppInfo(url=f"{RENDER_URL}/webapp")
        webapp_button = telebot.types.InlineKeyboardButton("فتح التطبيق المصغر 🚀", web_app=web_app)
        markup.add(webapp_button)
        
        bot.reply_to(
            message, 
            "أهلاً بك يا عمر في بوت مكافآت TRX! 🚀\nاضغط على الزر أدناه لفتح لوحة التحكم وإدارة أرباحك وإحالاتك:", 
            reply_markup=markup
        )
    except Exception as e:
        print(f"Error in start handler: {e}", flush=True)

# --- مسار API لجلب بيانات المستخدم وعرضها داخل التطبيق المصغر ---
@server.route('/api/user/<int:user_id>')
def get_user_data(user_id):
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, active_referrals FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, "WebUser"))
        conn.commit()
        balance = 0.0
        active_referrals = 0
    else:
        balance, active_referrals = row
    conn.close()

    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    return jsonify({
        "user_id": user_id,
        "balance": balance,
        "active_referrals": active_referrals,
        "ref_link": ref_link
    })

# --- صفحة التطبيق المصغر (تصميم أنيق ومرتب داخل السيرفر) ---
@server.route('/webapp')
def webapp():
    html_content = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TRX Earn Mini App</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                font-family: Tahoma, sans-serif;
                background-color: #0f172a;
                color: #ffffff;
                margin: 0;
                padding: 20px;
                text-align: center;
            }
            .container {
                max-width: 400px;
                margin: auto;
                background: #1e293b;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }
            h2 { color: #38bdf8; font-size: 22px; }
            .card {
                background: #334155;
                padding: 15px;
                border-radius: 10px;
                margin: 15px 0;
            }
            .btn {
                background: #0284c7;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                width: 100%;
                margin-top: 10px;
            }
            .btn:active { background: #0369a1; }
            input {
                width: 100%;
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #475569;
                background: #0f172a;
                color: white;
                text-align: center;
                margin-top: 5px;
                box-sizing: border-box;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🚀 لوحة تحكم أرباح TRX</h2>
            <p id="welcome">جاري تحميل بياناتك...</p>
            
            <div class="card">
                <h3>💰 رصيدك الحالي</h3>
                <p id="balance" style="font-size: 24px; font-weight: bold; color: #4ade80;">0.0 TRX</p>
            </div>
            
            <div class="card">
                <h3>👥 نظام الإحالات (3% للأبد)</h3>
                <p>عدد الإحالات النشطة: <span id="ref-count" style="color: #38bdf8; font-weight: bold;">0</span></p>
                <p style="font-size: 14px; color: #94a3b8;">شارك رابطك وخذ 3% من أرباح أصدقائك للأبد:</p>
                <input type="text" id="ref-link" readonly onclick="this.select();">
                <button class="btn" onclick="copyRefLink()">نسخ رابط الإحالة 🔗</button>
            </div>
        </div>

        <script>
            let tg = window.Telegram.WebApp;
            tg.expand();

            let userId = 123456789;
            if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
                userId = tg.initDataUnsafe.user.id;
                document.getElementById('welcome').innerText = "أهلاً بك، " + (tg.initDataUnsafe.user.first_name || "مستخدمنا");
            } else {
                document.getElementById('welcome').innerText = "وضع المعاينة (مستخدم تجريبي)";
            }

            fetch('/api/user/' + userId)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('balance').innerText = data.balance.toFixed(2) + " TRX";
                    document.getElementById('ref-count').innerText = data.active_referrals;
                    document.getElementById('ref-link').value = data.ref_link;
                })
                .catch(err => {
                    console.error("Error fetching user data:", err);
                });

            function copyRefLink() {
                var copyText = document.getElementById("ref-link");
                copyText.select();
                copyText.setSelectionRange(0, 99999);
                navigator.clipboard.writeText(copyText.value);
                alert("تم نسخ رابط الإحالة بنجاح! 📋");
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

if __name__ == '__main__':
    bot.remove_webhook()
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    
    port = int(os.environ.get('PORT', 10000))
    server.run(host='0.0.0.0', port=port)
