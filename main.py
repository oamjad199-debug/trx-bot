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
    return "TRX Bot is running! 🚀"

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
            "📜 **TRX Earn Bot Terms & Conditions:**\n\n"
            "1. Using Wi-Fi or VPN is strictly prohibited.\n"
            "2. Referrals are active only after the invited user completes an offer.\n"
            "3. 3% referral bonus is lifetime based on friends' activity.\n"
            "4. You can save or change your TRX wallet address anytime.\n\n"
            "Click the button below to agree and open the Mini App:"
        )

        markup = telebot.types.InlineKeyboardMarkup()
        web_app = telebot.types.WebAppInfo(url=f"{RENDER_URL}/webapp")
        webapp_button = telebot.types.InlineKeyboardButton("I Agree & Open Mini App 🚀", web_app=web_app)
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

    bot_username = "TRXEarnBot"
    try:
        bot_info = bot.get_me()
        if bot_info and bot_info.username:
            bot_username = bot_info.username
    except Exception:
        pass

    ref_link = f"https://t.me/{bot_username}?start={user_id}"

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
        return jsonify({"success": False, "message": "الرجاء إدخال عنوان صحيح!"})
    
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET trx_address = ? WHERE user_id = ?", (address, user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "تم حفظ عنوان المحفظة بنجاح! 💾"})

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
    
    cursor.execute("UPDATE users SET balance = balance + 0.5 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "مبروك! تمت إضافة المكافأة إلى رصيدك بنجاح! 🎉"})

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
        return jsonify({"success": False, "message": "الرجاء إضافة عنوان محفظة TRX في قسم المحفظة أولاً!"})
    
    if balance <= 0:
        conn.close()
        return jsonify({"success": False, "message": "عذراً، ليس لديك رصيد كافي للسحب"})
    
    cursor.execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "تم تقديم طلب السحب بنجاح وسيتم المعالجة قريباً! 🚀"})

@server.route('/webapp')
def webapp():
    html_content = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl" id="html-root">
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
                padding: 15px;
            }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: #1e293b;
                padding: 12px 15px;
                border-radius: 12px;
                margin-bottom: 15px;
            }
            .menu-btn {
                background: none;
                border: none;
                color: #38bdf8;
                font-size: 24px;
                cursor: pointer;
            }
            h2 { color: #38bdf8; font-size: 18px; margin: 0; text-align: center; }
            .section { display: none; }
            .section.active { display: block; }
            .card {
                background: #1e293b;
                padding: 15px;
                border-radius: 12px;
                margin: 10px 0;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
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
            #ref-link {
                background: #ffffff !important;
                color: #0f172a !important;
                font-weight: bold;
                font-size: 11px;
                direction: ltr !important;
                text-align: center !important;
            }
            input:read-only { border-color: #475569; opacity: 0.8; }

            /* القائمة الجانبية المرتّبة وغير المكررة */
            .drawer {
                position: fixed;
                top: 0;
                right: -260px;
                width: 250px;
                height: 100%;
                background: #1e293b;
                z-index: 1000;
                transition: 0.3s ease;
                box-shadow: -5px 0 15px rgba(0,0,0,0.5);
                display: flex;
                flex-direction: column;
                padding: 20px 10px;
                box-sizing: border-box;
            }
            .drawer.open { right: 0; }
            .drawer-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #334155;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }
            .close-drawer {
                background: none;
                border: none;
                color: #ef4444;
                font-size: 22px;
                cursor: pointer;
            }
            .drawer-item {
                background: none;
                border: none;
                color: #cbd5e1;
                font-size: 13px;
                text-align: right;
                padding: 10px;
                cursor: pointer;
                border-radius: 8px;
                margin-bottom: 5px;
                display: flex;
                align-items: center;
                justify-content: flex-start;
                gap: 8px;
                width: 100%;
            }
            .drawer-item:hover, .drawer-item.active {
                background: #334155;
                color: #38bdf8;
                font-weight: bold;
            }
            .overlay {
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: 999;
                display: none;
            }
            .overlay.active { display: block; }

            .terms-text {
                font-size: 13px;
                color: #cbd5e1;
                text-align: right;
                line-height: 1.6;
            }
        </style>
    </head>
    <body>

        <!-- الهيدر -->
        <div class="header">
            <button class="menu-btn" onclick="toggleDrawer()">☰</button>
            <h2 id="page-title">🏠 الرئيسية</h2>
            <div style="width: 24px;"></div>
        </div>

        <!-- القائمة الجانبية المرتبة نهائياً -->
        <div class="overlay" id="overlay" onclick="toggleDrawer()"></div>
        <div class="drawer" id="drawer">
            <div class="drawer-header">
                <button class="close-drawer" onclick="toggleDrawer()">✕</button>
                <span style="font-weight: bold; color: #38bdf8;">القائمة ⚙️</span>
            </div>
            <button class="drawer-item active" onclick="switchTab('home', '🏠 الرئيسية', this)"><span>🏠</span> الرئيسية</button>
            <button class="drawer-item" onclick="switchTab('ref', '👥 الإحالة', this)"><span>👥</span> الإحالة</button>
            <button class="drawer-item" onclick="switchTab('phone_sub', '📱 الربح من الاشتراك في رقم هاتف', this)"><span>📱</span> الربح من الاشتراك في رقم هاتف</button>
            <button class="drawer-item" onclick="switchTab('install_apps', '📲 الربح من تثبيت تطبيقات', this)"><span>📲</span> الربح من تثبيت تطبيقات</button>
            <button class="drawer-item" onclick="switchTab('register_sites', '🌐 الربح من التسجيل في المواقع', this)"><span>🌐</span> الربح من التسجيل في المواقع</button>
            <button class="drawer-item" onclick="switchTab('wallet', '💳 المحفظة', this)"><span>💳</span> المحفظة</button>
            <button class="drawer-item" onclick="switchTab('withdraw', '💸 السحب', this)"><span>💸</span> السحب</button>
            <button class="drawer-item" onclick="switchTab('watch', '▶️ الربح من المشاهدة', this)"><span>▶️</span> الربح من المشاهدة</button>
            <button class="drawer-item" onclick="switchTab('terms', '📜 الشروط والأحكام', this)"><span>📜</span> الشروط والأحكام</button>
        </div>

        <div class="container">
            <p id="welcome" style="text-align:center; font-size: 13px; color: #94a3b8; margin-top:0;"></p>

            <!-- 1. الرئيسية -->
            <div id="tab-home" class="section active">
                <div class="card">
                    <h3>رصيد TRX الحالي</h3>
                    <p id="balance-val" style="font-size: 26px; font-weight: bold; color: #4ade80;">0.0 TRX</p>
                    <p style="font-size: 12px; color: #94a3b8;">تجميعك المستمر يتيح لك السحب الفوري عند الوصول للحد الأدنى.</p>
                </div>
                <div class="card" style="text-align: right;">
                    <h3 style="color: #38bdf8; text-align: center; margin-bottom: 10px;">📜 الشروط والأحكام</h3>
                    <div class="terms-text">
                        1. يمنع منعاً باتاً استخدام الواي فاي أو الـ VPN.<br>
                        2. لا تُحتسب الإحالة نشطة إلا بعد إتمام الشخص المدعو لعرض ناجح.<br>
                        3. نسبة الإحالة (3%) تُحتسب للأبد.<br>
                        4. يمكنك حفظ أو تغيير عنوان محفظة TRX بأي وقت.
                    </div>
                </div>
            </div>

            <!-- 2. الإحالة -->
            <div id="tab-ref" class="section">
                <div class="card">
                    <h3>👥 نظام الإحالات النشطة (3%)</h3>
                    <p>عدد إحالاتك النشطة: <span id="ref-count" style="color: #38bdf8; font-weight: bold;">0</span></p>
                    <p style="font-size: 13px; color: #94a3b8;">شارك رابطك وخذ 3% أرباح للأبد:</p>
                    <input type="text" id="ref-link" readonly onclick="this.select();">
                    <button class="btn" onclick="copyRefLink()">نسخ رابط الإحالة 🔗</button>
                </div>
            </div>

            <!-- 3. اشتراك رقم هاتف -->
            <div id="tab-phone_sub" class="section">
                <div class="card">
                    <h3>📱 الربح من الاشتراك في رقم هاتف</h3>
                    <p style="font-size: 13px; color: #cbd5e1;">اشترك برقم هاتفك في العروض المتاحة أدناه لكسب نقاط TRX:</p>
                    <button class="btn" style="background: #eab308; margin-top: 10px;" onclick="completeTask()">تنفيذ الاشتراك ✅</button>
                </div>
            </div>

            <!-- 4. تثبيت تطبيقات -->
            <div id="tab-install_apps" class="section">
                <div class="card">
                    <h3>📲 الربح من تثبيت تطبيقات</h3>
                    <p style="font-size: 13px; color: #cbd5e1;">قم بتثبيت التطبيقات المطلوبة وافتحها لكسب نقاط TRX:</p>
                    <button class="btn" style="background: #16a34a; margin-top: 10px;" onclick="completeTask()">تثبيت التطبيق ✅</button>
                </div>
            </div>

            <!-- 5. التسجيل في المواقع -->
            <div id="tab-register_sites" class="section">
                <div class="card">
                    <h3>🌐 الربح من التسجيل في المواقع</h3>
                    <p style="font-size: 13px; color: #cbd5e1;">سجل في المواقع الإلكترونية المتاحة لكسب نقاط TRX:</p>
                    <button class="btn" style="background: #0284c7; margin-top: 10px;" onclick="completeTask()">التسجيل في الموقع ✅</button>
                </div>
            </div>

            <!-- 6. المحفظة (مع خيار الحفظ والتعديل الدائم) -->
            <div id="tab-wallet" class="section">
                <div class="card">
                    <h3>💳 إدارة المحفظة</h3>
                    <p id="wallet-desc" style="font-size: 13px; color: #94a3b8;">أدخل عنوان محفظة TRX الخاصة بك:</p>
                    <input type="text" id="trx-input" placeholder="أدخل عنوان TRX هنا...">
                    <button id="wallet-btn" class="btn" onclick="handleWalletAction()">حفظ العنوان 💾</button>
                </div>
            </div>

            <!-- 7. السحب -->
            <div id="tab-withdraw" class="section">
                <div class="card">
                    <h3>💸 سحب الأرباح</h3>
                    <p style="font-size: 13px; color: #94a3b8;">عنوان المحفظة المسجل للسحب:</p>
                    <p id="current-address" style="font-size: 12px; color: #fbbf24; word-break: break-all; margin: 10px 0;"></p>
                    <button class="btn" style="background: #e11d48;" onclick="requestWithdraw()">تأكيد طلب السحب 🚀</button>
                </div>
            </div>

            <!-- 8. الربح من المشاهدة -->
            <div id="tab-watch" class="section">
                <div class="card">
                    <h3>▶️ الربح من المشاهدة</h3>
                    <p style="font-size: 13px; color: #cbd5e1;">قم بمشاهدة الإعلانات لكسب نقاط TRX إضافية:</p>
                    <button class="btn" style="background: #16a34a;" onclick="completeTask()">مشاهدة الإعلان والربح 🚀</button>
                </div>
            </div>

            <!-- 9. الشروط والأحكام -->
            <div id="tab-terms" class="section">
                <div class="card" style="text-align: right;">
                    <h3 style="color: #38bdf8; text-align: center; margin-bottom: 10px;">📜 الشروط والأحكام</h3>
                    <div class="terms-text">
                        1. يمنع منعاً باتاً استخدام الواي فاي أو الـ VPN.<br>
                        2. لا تُحتسب الإحالة نشطة إلا بعد إتمام الشخص المدعو لعرض ناجح.<br>
                        3. نسبة الإحالة (3%) تُحتسب للأبد.<br>
                        4. يمكنك حفظ أو تغيير عنوان محفظة TRX بأي وقت.
                    </div>
                </div>
            </div>

        </div>

        <script>
            let tg = window.Telegram.WebApp;
            tg.expand();

            let userId = 123456789;
            let userName = "Omar";
            if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
                if (tg.initDataUnsafe.user.id) userId = tg.initDataUnsafe.user.id;
                if (tg.initDataUnsafe.user.first_name) userName = tg.initDataUnsafe.user.first_name;
            }
            document.getElementById('welcome').innerText = "مرحباً بك: " + userName;

            function toggleDrawer() {
                document.getElementById('drawer').classList.toggle('open');
                document.getElementById('overlay').classList.toggle('active');
            }

            let savedTrxAddress = "";

            function loadUserData() {
                fetch('/api/user/' + userId)
                    .then(res => res.json())
                    .then(data => {
                        document.getElementById('balance-val').innerText = data.balance.toFixed(2) + " TRX";
                        document.getElementById('ref-count').innerText = data.active_referrals;
                        document.getElementById('ref-link').value = data.ref_link;
                        
                        savedTrxAddress = data.trx_address || "";
                        let input = document.getElementById('trx-input');
                        let btn = document.getElementById('wallet-btn');
                        let desc = document.getElementById('wallet-desc');

                        if (savedTrxAddress) {
                            input.value = savedTrxAddress;
                            input.readOnly = true;
                            btn.innerText = "تغيير المحفظة 🔄";
                            desc.innerText = "العنوان المحفوظ حالياً (اضغط تغيير لتعديله):";
                            document.getElementById('current-address').innerText = savedTrxAddress;
                        } else {
                            input.value = "";
                            input.readOnly = false;
                            btn.innerText = "حفظ العنوان 💾";
                            desc.innerText = "أدخل عنوان محفظة TRX الخاصة بك:";
                            document.getElementById('current-address').innerText = "لم تقم باضافة عنوان بعد!";
                        }
                    })
                    .catch(err => console.error("Error:", err));
            }

            function handleWalletAction() {
                let input = document.getElementById('trx-input');
                let btn = document.getElementById('wallet-btn');
                let address = input.value.trim();

                if (!address) {
                    alert("الرجاء إدخال عنوان محفظة صحيح!");
                    return;
                }

                if (input.readOnly) {
                    input.readOnly = false;
                    input.focus();
                    btn.innerText = "حفظ التغيير 💾";
                } else {
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
            }

            function switchTab(tabName, titleText, btnElement) {
                document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.drawer-item').forEach(el => el.classList.remove('active'));
                
                document.getElementById('tab-' + tabName).classList.add('active');
                btnElement.classList.add('active');
                document.getElementById('page-title').innerText = titleText;
                toggleDrawer();
            }

            function copyRefLink() {
                var copyText = document.getElementById("ref-link");
                copyText.select();
                copyText.setSelectionRange(0, 99999);
                navigator.clipboard.writeText(copyText.value);
                alert("تم نسخ رابط الإحالة بنجاح! 📋");
            }

            function completeTask() {
                fetch('/api/complete_offer', {
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

            loadUserData();
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
