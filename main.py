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
            trx_address TEXT DEFAULT ''
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@server.route('/')
def home():
    return "TRX Bot with Terms on Start is running successfully! 🚀"

@server.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"Error processing update: {e}", flush=True)
    return 'OK', 200

# أمر /start يرسل الشروط والأحكام أولاً في المحادثة
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

        # نص الشروط والأحكام الذي يظهر قبل الدخول للتطبيق
        terms_message = (
            "📜 **شروط وأحكام استخدام بوت TRX Earn:**\n\n"
            "1. يلتزم المستخدم بقوانين الاستخدام وعدم إنشاء حسابات وهمية.\n"
            "2. نسبة الإحالة (3%) تُحتسب للأبد بناءً على نشاط الأصدقاء المدعوين.\n"
            "3. يجب التأكد من صحة عنوان محفظة TRX الخاصة بك قبل طلب السحب.\n"
            "4. الاستمرار في استخدام البوت يعني موافقتك التامة على كافة الشروط.\n\n"
            "اضغط على الزر أدناه للموافقة وفتح لوحة التحكم والتطبيق المصغر:"
        )

        markup = telebot.types.InlineKeyboardMarkup()
        web_app = telebot.types.WebAppInfo(url=f"{RENDER_URL}/webapp")
        webapp_button = telebot.types.InlineKeyboardButton("أوافق وفتح التطبيق المصغر 🚀", web_app=web_app)
        markup.add(webapp_button)
        
        bot.reply_to(message, terms_message, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(f"Error in start handler: {e}", flush=True)

# --- مسارات الـ API والتطبيق المصغر ---
@server.route('/api/user/<int:user_id>')
def get_user_data(user_id):
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, active_referrals, trx_address FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, "WebUser"))
        conn.commit()
        balance = 0.0
        active_referrals = 0
        trx_address = ""
    else:
        balance, active_referrals, trx_address = row
    conn.close()

    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    return jsonify({
        "user_id": user_id,
        "balance": balance,
        "active_referrals": active_referrals,
        "ref_link": ref_link,
        "trx_address": trx_address or ""
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
    return jsonify({"success": True, "message": "تم حفظ عنوان المحفظة بنجاح!"})

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
                text-align: center;
                flex: 1;
            }
            .nav-item.active {
                color: #38bdf8;
                font-weight: bold;
            }
            .nav-item span { display: block; font-size: 18px; }
            .terms-text {
                font-size: 13px;
                color: #cbd5e1;
                text-align: right;
                line-height: 1.6;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2 id="page-title">💰 الرصيد</h2>
            <p id="welcome" style="text-align:center; font-size: 13px; color: #94a3b8;"></p>

            <div id="tab-balance" class="section active">
                <div class="card">
                    <h3>رصيدك الحالي من TRX</h3>
                    <p id="balance-val" style="font-size: 26px; font-weight: bold; color: #4ade80;">0.0 TRX</p>
                    <p style="font-size: 12px; color: #94a3b8;">تجميعك المستمر يتيح لك السحب الفوري عند الوصول للحد الأدنى.</p>
                </div>
            </div>

            <div id="tab-ref" class="section">
                <div class="card">
                    <h3>نظام الإحالات الأبدي (3%)</h3>
                    <p>الإحالات النشطة: <span id="ref-count" style="color: #38bdf8; font-weight: bold;">0</span></p>
                    <p style="font-size: 13px; color: #94a3b8;">شارك رابطك وخذ 3% أرباح أصدقائك للأبد:</p>
                    <input type="text" id="ref-link" readonly onclick="this.select();">
                    <button class="btn" onclick="copyRefLink()">نسخ رابط الإحالة 🔗</button>
                </div>
            </div>

            <div id="tab-offers" class="section">
                <div class="card">
                    <h3>🎯 عروض تجميع النقاط</h3>
                    <p style="font-size: 13px; color: #cbd5e1;">قم بإتمام المهام والعروض أدناه لزيادة رصيدك:</p>
                    <button class="btn" style="background: #16a34a;" onclick="window.open('http://bc.vc/Dc4Boi8', '_blank')">فتح عرض التحقق والربح 🚀</button>
                </div>
            </div>

            <div id="tab-wallet" class="section">
                <div class="card">
                    <h3>💳 إدارة محفظة السحب</h3>
                    <p style="font-size: 13px; color: #94a3b8;">أدخل عنوان محفظة TRX الخاصة بك لتتمكن من السحب عليها:</p>
                    <input type="text" id="trx-input" placeholder="أدخل عنوان TRX هنا...">
                    <button class="btn" onclick="saveAddress()">حفظ العنوان 💾</button>
                </div>
            </div>

            <div id="tab-withdraw" class="section">
                <div class="card">
                    <h3>💸 سحب الأرباح</h3>
                    <p style="font-size: 13px; color: #94a3b8;">عنوان المحفظة المسجل:</p>
                    <p id="current-address" style="font-size: 12px; color: #fbbf24; word-break: break-all;"></p>
                    <button class="btn" style="background: #e11d48;" onclick="requestWithdraw()">تأكيد طلب السحب 🚀</button>
                </div>
            </div>

            <div id="tab-terms" class="section">
                <div class="card">
                    <h3>📜 الشروط والأحكام</h3>
                    <div class="terms-text">
                        1. يلتزم المستخدم بقوانين الاستخدام وعدم استنساخ الحسابات الوهمية.<br>
                        2. نسبة الإحالة (3%) تُحتسب وتُضاف للأبد بناءً على نشاط الإحالات النشطة.<br>
                        3. يجب التأكد من صحة عنوان محفظة TRX قبل طلب السحب، فالإدارة غير مسؤولة عن العناوين الخاطئة.<br>
                        4. يحق لإدارة البوت تعديل أو تحديث القوانين والشروط في أي وقت لضمان استمرارية المنصة.
                    </div>
                </div>
            </div>

        </div>

        <div class="nav-bar">
            <button class="nav-item active" onclick="switchTab('balance', '💰 الرصيد', this)"><span>💰</span>الرصيد</button>
            <button class="nav-item" onclick="switchTab('ref', '👥 الإحالات', this)"><span>👥</span>الإحالة</button>
            <button class="nav-item" onclick="switchTab('offers', '🎯 العروض', this)"><span>🎯</span>العروض</button>
            <button class="nav-item" onclick="switchTab('wallet', '💳 المحفظة', this)"><span>💳</span>المحفظة</button>
            <button class="nav-item" onclick="switchTab('withdraw', '💸 السحب', this)"><span>💸</span>السحب</button>
            <button class="nav-item" onclick="switchTab('terms', '📜 الشروط والأحكام', this)"><span>📜</span>الشروط</button>
        </div>

        <script>
            let tg = window.Telegram.WebApp;
            tg.expand();

            let userId = 123456789;
            if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
                userId = tg.initDataUnsafe.user.id;
                document.getElementById('welcome').innerText = "مرحباً بك: " + (tg.initDataUnsafe.user.first_name || "مستخدم");
            } else {
                document.getElementById('welcome').innerText = "وضع المعاينة التجريبي";
            }

            let globalData = {};

            function loadUserData() {
                fetch('/api/user/' + userId)
                    .then(res => res.json())
                    .then(data => {
                        globalData = data;
                        document.getElementById('balance-val').innerText = data.balance.toFixed(2) + " TRX";
                        document.getElementById('ref-count').innerText = data.active_referrals;
                        document.getElementById('ref-link').value = data.ref_link;
                        document.getElementById('trx-input').value = data.trx_address || "";
                        document.getElementById('current-address').innerText = data.trx_address ? data.trx_address : "لم تقم بإضافة عنوان بعد!";
                    })
                    .catch(err => console.error("Error:", err));
            }

            loadUserData();

            function switchTab(tabName, titleText, btnElement) {
                document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                
                document.getElementById('tab-' + tabName).classList.add('active');
                btnElement.classList.add('active');
                document.getElementById('page-title').innerText = titleText;
            }

            function copyRefLink() {
                var copyText = document.getElementById("ref-link");
                copyText.select();
                copyText.setSelectionRange(0, 99999);
                navigator.clipboard.writeText(copyText.value);
                alert("تم نسخ رابط الإحالة بنجاح! 📋");
            }

            function saveAddress() {
                let address = document.getElementById('trx-input').value.trim();
                if(!address) {
                    alert("الرجاء إدخال عنوان صحيح!");
                    return;
                }
                fetch('/api/update_address', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: userId, address: address})
                })
                .then(res => res.json())
                .then(data => {
                    alert(data.message);
                    loadUserData();
                });
            }

            function requestWithdraw() {
                fetch('/api/withdraw', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: userId})
                })
                .then(res => res.json())
                .then(data => {
                    alert(data.message);
                    loadUserData();
                });
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
