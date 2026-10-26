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
            active_referrals INTEGER DEFAULT 0,
            trx_address TEXT DEFAULT '',
            completed_offer INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@server.route('/')
def home():
    return "TRX Bot with Change Wallet button is running successfully! 🚀"

@server.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"Error processing update: {e}", flush=True)
    return 'OK', 200

@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "No Username"
        
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

        terms_message = (
            "📜 **شروط وأحكام استخدام بوت TRX Earn:**\n\n"
            "1. يلتزم المستخدم بقوانين الاستخدام وعدم إنشاء حسابات وهمية.\n"
            "2. لا تُحتسب الإحالة نشطة إلا بعد أن يقوم الشخص المدعو **بإتمام عرض ناجح**.\n"
            "3. نسبة الإحالة (3%) تُحتسب للأبد بناءً على نشاط الأصدقاء.\n"
            "4. يمكنك تغيير وتحديث عنوان محفظة TRX الخاص بك بأي وقت من قسم المحفظة.\n\n"
            "اضغط على الزر أدناه للموافقة وفتح التطبيق المصغر:"
        )

        markup = telebot.types.InlineKeyboardMarkup()
        web_app = telebot.types.WebAppInfo(url=f"{RENDER_URL}/webapp")
        webapp_button = telebot.types.InlineKeyboardButton("أوافق وفتح التطبيق المصغر 🚀", web_app=web_app)
        markup.add(webapp_button)
        
        bot.reply_to(message, terms_message, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(f"Error in start handler: {e}", flush=True)

@server.route('/api/user/<int:user_id>')
def get_user_data(user_id):
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, active_referrals, trx_address, completed_offer FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, "WebUser"))
        conn.commit()
        balance = 0.0
        active_referrals = 0
        trx_address = ""
        completed_offer = 0
    else:
        balance, active_referrals, trx_address, completed_offer = row
    conn.close()

    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    return jsonify({
        "user_id": user_id,
        "balance": balance,
        "active_referrals": active_referrals,
        "ref_link": ref_link,
        "trx_address": trx_address or "",
        "completed_offer": completed_offer
    })

@server.route('/api/update_address', methods=['POST'])
def update_address():
    data = request.json
    user_id = data.get('user_id')
    address = data.get('address')
    if not user_id or not address:
        return jsonify({"success": False, "message": "يرجى إدخال عنوان صحيح"})
    
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET trx_address = ? WHERE user_id = ?", (address, user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "تم تغيير محفظة TRX بنجاح!"})

@server.route('/api/complete_offer', methods=['POST'])
def complete_offer():
    data = request.json
    user_id = data.get('user_id')
    
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT completed_offer, referred_by FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"success": False, "message": "المستخدم غير موجود"})
    
    completed_offer, referred_by = row
    if completed_offer == 1:
        conn.close()
        return jsonify({"success": False, "message": "لقد قمت بإتمام العرض مسبقاً!"})
    
    cursor.execute("UPDATE users SET completed_offer = 1, balance = balance + 1.0 WHERE user_id = ?", (user_id,))
    if referred_by:
        cursor.execute(
            "UPDATE users SET active_referrals = active_referrals + 1 WHERE user_id = ?",
            (referred_by,)
        )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "تهانينا! تم التحقق وإتمام العرض بنجاح!"})

@server.route('/api/withdraw', methods=['POST'])
def withdraw():
    data = request.json
    user_id = data.get('user_id')
    
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, trx_address FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"success": False, "message": "المستخدم غير موجود"})
    
    balance, address = row
    if not address:
        conn.close()
        return jsonify({"success": False, "message": "يرجى إضافة عنوان محفظة TRX في قسم المحفظة أولاً!"})
    
    if balance <= 0:
        conn.close()
        return jsonify({"success": False, "message": "عذراً، ليس لديك رصيد كافي للسحب"})
    
    cursor.execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "تم تقديم طلب السحب بنجاح وسيتم المعالجة قريبًا!"})

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
                padding: 10px;
                padding-bottom: 70px;
            }
            .container {
                max-width: 420px;
                margin: auto;
                background: #1e293b;
                padding: 15px;
                border-radius: 15px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }
            h2 { color: #38bdf8; font-size: 20px; text-align: center; }
            .section { display: none; }
            .section.active { display: block; }
            .card {
                background: #334155;
                padding: 12px;
                border-radius: 10px;
                margin: 10px 0;
                text-align: center;
            }
            .btn {
                background: #0284c7;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 15px;
                width: 100%;
                margin-top: 8px;
            }
            .btn:active { background: #0369a1; }
            input {
                width: 100%;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #475569;
                background: #0f172a;
                color: white;
                text-align: center;
                margin-top: 8px;
                box-sizing: border-box;
            }
            .nav-bar {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: #0f172a;
                border-top: 1px solid #334155;
                display: flex;
                justify-content: space-around;
                padding: 8px 0;
                z-index: 100;
            }
            .nav-item {
                background: none;
                border: none;
                color: #94a3b8;
                font-size: 11px;
                cursor: pointer;
                text-align
