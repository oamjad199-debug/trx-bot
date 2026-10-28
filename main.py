import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string
import telebot

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://trx-bot-e61j.onrender.com')

# --- إعداد قاعدة بيانات SQLite المحلية ---
def init_db():
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 4.50,
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
    return "TRX Bot is running perfectly! 🚀"

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
                        "INSERT INTO users (user_id, username, referred_by, balance) VALUES (?, ?, ?, ?)",
                        (user_id, username, referrer_id, 4.50)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
                        (user_id, username, 4.50)
                    )
            else:
                cursor.execute(
                    "INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
                    (user_id, username, 4.50)
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
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, balance) VALUES (?, ?, ?)", (user_id, "Omar", 4.50))
        conn.commit()
        balance = 4.50
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
        return jsonify({"success": False, "message": "Invalid address!"})
    
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, "Omar"))
    cursor.execute("UPDATE users SET trx_address = ? WHERE user_id = ?", (address, user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Wallet address saved successfully! 💾"})

@server.route('/api/complete_offer', methods=['POST'])
def complete_offer():
    data = request.json
    user_id = data.get('user_id')
    
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, "Omar"))
    cursor.execute("UPDATE users SET balance = balance + 0.5 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Reward added to your balance successfully! 🎉"})

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
        return jsonify({"success": False, "message": "User not registered"})
    
    balance, address = row
    if not address:
        conn.close()
        return jsonify({"success": False, "message": "Please add your TRX wallet address first!"})
    
    if balance <= 0:
        conn.close()
        return jsonify({"success": False, "message": "Insufficient balance"})
    
    cursor.execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Withdrawal request submitted successfully! 🚀"})

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

            /* تصميم الأكورديون (القائمة المنسدلة للأسئلة مثل الفيديو) */
            .accordion-card {
                background: #1e293b;
                border-radius: 12px;
                margin: 10px 0;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }
            .accordion-header {
                padding: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: pointer;
                user-select: none;
                background: #1e293b;
            }
            .accordion-header h3 {
                color: #38bdf8;
                font-size: 15px;
                margin: 0;
            }
            .accordion-arrow {
                font-size: 18px;
                color: #38bdf8;
                transition: transform 0.3s ease;
            }
            .accordion-content {
                max-height: 0;
                overflow: hidden;
                transition: max-height 0.3s ease, padding 0.3s ease;
                background: #0f172a;
                padding: 0 15px;
                text-align: right;
                font-size: 13px;
                color: #cbd5e1;
                line-height: 1.6;
            }
            .accordion-card.open .accordion-content {
                max-height: 150px;
                padding: 12px 15px;
            }
            .accordion-card.open .accordion-arrow {
                transform: rotate(180deg);
            }

            .drawer {
                position: fixed;
                top: 0;
                right: -280px;
                width: 270px;
                height: 100%;
                background: #1e293b;
                z-index: 1000;
                transition: 0.3s ease;
                box-shadow: -5px 0 15px rgba(0,0,0,0.5);
                display: flex;
                flex-direction: column;
                padding: 15px 10px;
                box-sizing: border-box;
                overflow-y: auto;
            }
            .drawer.open { right: 0; }
            .drawer-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #334155;
                padding-bottom: 10px;
                margin-bottom: 10px;
            }
            .close-drawer {
                background: none;
                border: none;
                color: #ef4444;
                font-size: 22px;
                cursor: pointer;
            }
            .drawer-item {
                background: #0f172a;
                border: 1px solid #334155;
                color: #cbd5e1;
                font-size: 13px;
                text-align: right;
                padding: 10px 12px;
                cursor: pointer;
                border-radius: 8px;
                margin-bottom: 6px;
                display: flex;
                align-items: center;
                justify-content: flex-start;
                gap: 10px;
                width: 100%;
                box-sizing: border-box;
            }
            .drawer-item:hover, .drawer-item.active {
                background: #334155;
                color: #38bdf8;
                border-color: #38bdf8;
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

            .lang-container {
                margin-top: auto;
                border-top: 1px solid #334155;
                padding-top: 15px;
                text-align: center;
            }
            .lang-container select {
                background: #0f172a;
                color: white;
                border: 1px solid #475569;
                padding: 6px 12px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                width: 100%;
            }

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

        <!-- القائمة الجانبية -->
        <div class="overlay" id="overlay" onclick="toggleDrawer()"></div>
        <div class="drawer" id="drawer">
            <div class="drawer-header">
                <button class="close-drawer" onclick="toggleDrawer()">✕</button>
                <span id="menu-title" style="font-weight: bold; color: #38bdf8; font-size: 15px;">القائمة ⚙️</span>
            </div>
            <button class="drawer-item active" onclick="switchTab('home', currentTitles.home, this)"><span id="nav-txt-home">🏠 الرئيسية</span></button>
            <button class="drawer-item" onclick="switchTab('ref', currentTitles.ref, this)"><span id="nav-txt-ref">👥 الإحالة</span></button>
            <button class="drawer-item" onclick="switchTab('phone_sub', currentTitles.phoneSub, this)"><span id="nav-txt-phonesub">📱 الربح من الاشتراك في رقم هاتف</span></button>
            <button class="drawer-item" onclick="switchTab('install_apps', currentTitles.installApps, this)"><span id="nav-txt-installapps">📲 الربح من تثبيت تطبيقات</span></button>
            <button class="drawer-item" onclick="switchTab('register_sites', currentTitles.registerSites, this)"><span id="nav-txt-registersites">🌐 الربح من التسجيل في المواقع</span></button>
            <button class="drawer-item" onclick="switchTab('wallet', currentTitles.wallet, this)"><span id="nav-txt-wallet">💳 المحفظة</span></button>
            <button class="drawer-item" onclick="switchTab('withdraw', currentTitles.withdraw, this)"><span id="nav-txt-withdraw">💸 السحب</span></button>
            <button class="drawer-item" onclick="switchTab('watch', currentTitles.watch, this)"><span id="nav-txt-watch">▶️ الربح من المشاهدة</span></button>
            <button class="drawer-item" onclick="switchTab('terms', currentTitles.terms, this)"><span id="nav-txt-terms">📜 الشروط والأحكام</span></button>
            
            <!-- قائمة اللغات والترجمة -->
            <div class="lang-container">
                <span style="font-size: 11px; color: #94a3b8; display: block; margin-bottom: 5px;">🌐 Language / اللغة:</span>
                <select id="language-select" onchange="changeLanguage(this.value)">
                    <option value="ar">🇸🇦 العربية</option>
                    <option value="en">🇬🇧 English</option>
                    <option value="es">🇪🇸 Español</option>
                    <option value="de">🇩🇪 Deutsch</option>
                    <option value="fr">🇫🇷 Français</option>
                    <option value="ru">🇷🇺 Русский</option>
                    <option value="pt">🇧🇷/🇵🇹 Português</option>
                    <option value="nl">🇳🇱 Nederlands</option>
                    <option value="pl">🇵🇱 Polski</option>
                </select>
            </div>
        </div>

        <div class="container">
            <p id="welcome" style="text-align:center; font-size: 13px; color: #94a3b8; margin-top:0;"></p>

            <!-- 1. الرئيسية مع شريط السحب والإجابة (أكورديون) -->
            <div id="tab-home" class="section active">
                <div class="card">
                    <h3 id="txt-bal-title">رصيد TRX الحالي</h3>
                    <p id="balance-val" style="font-size: 26px; font-weight: bold; color: #4ade80;">TRX 4.50</p>
                    <p id="txt-bal-desc" style="font-size: 12px; color: #94a3b8;">تجميعك المستمر يتيح لك السحب الفوري عند الوصول للحد الأدنى.</p>
                </div>

                <!-- الأكورديون (السهم المنسدل مثل الفيديو) -->
                <div class="accordion-card" id="faq-accordion">
                    <div class="accordion-header" onclick="toggleAccordion()">
                        <h3 id="txt-faq-title">❓ كيف العمل على البوت؟</h3>
                        <span class="accordion-arrow">⌄</span>
                    </div>
                    <div class="accordion-content">
                        <p id="txt-faq-desc" style="margin: 0;">العمل على البوت سهل جدا يمكنك الربح من المشاهده الاعلانات فقط</p>
                    </div>
                </div>
            </div>

            <!-- 2. الإحالة -->
            <div id="tab-ref" class="section">
                <div class="card">
                    <h3 id="txt-ref-title">👥 نظام الإحالات النشطة (3%)</h3>
                    <p><span id="txt-ref-count-label">عدد إحالاتك النشطة:</span> <span id="ref-count" style="color: #38bdf8; font-weight: bold;">0</span></p>
                    <p id="txt-ref-desc" style="font-size: 13px; color: #94a3b8;">شارك رابطك وخذ 3% أرباح للأبد:</p>
                    <input type="text" id="ref-link" readonly onclick="this.select();">
                    <button id="txt-copy-btn" class="btn" onclick="copyRefLink()">نسخ رابط الإحالة 🔗</button>
                </div>
            </div>

            <!-- 3. اشتراك رقم هاتف -->
            <div id="tab-phone_sub" class="section">
                <div class="card">
                    <h3 id="txt-phonesub-title">📱 الربح من الاشتراك في رقم هاتف</h3>
                    <p id="txt-phonesub-desc" style="font-size: 13px; color: #cbd5e1;">اشترك برقم هاتفك في العروض المتاحة أدناه لكسب نقاط TRX:</p>
                    <button id="txt-phonesub-btn" class="btn" style="background: #eab308; margin-top: 10px;" onclick="completeTask()">تنفيذ الاشتراك ✅</button>
                </div>
            </div>

            <!-- 4. تثبيت تطبيقات -->
            <div id="tab-install_apps" class="section">
                <div class="card">
                    <h3 id="txt-installapps-title">📲 الربح من تثبيت تطبيقات</h3>
                    <p id="txt-installapps-desc" style="font-size: 13px; color: #cbd5e1;">قم بتثبيت التطبيقات المطلوبة وافتحها لكسب نقاط TRX:</p>
                    <button id="txt-installapps-btn" class="btn" style="background: #16a34a; margin-top: 10px;" onclick="completeTask()">تثبيت التطبيق ✅</button>
                </div>
            </div>

            <!-- 5. التسجيل في المواقع -->
            <div id="tab-register_sites" class="section">
                <div class="card">
                    <h3 id="txt-registersites-title">🌐 الربح من التسجيل في المواقع</h3>
                    <p id="txt-registersites-desc" style="font-size: 13px; color: #cbd5e1;">سجل في المواقع الإلكترونية المتاحة لكسب نقاط TRX:</p>
                    <button id="txt-registersites-btn" class="btn" style="background: #0284c7; margin-top: 10px;" onclick="completeTask()">التسجيل في الموقع ✅</button>
                </div>
            </div>

            <!-- 6. المحفظة -->
            <div id="tab-wallet" class="section">
                <div class="card">
                    <h3 id="txt-wallet-title">💳 إدارة المحفظة</h3>
                    <p id="wallet-desc" style="font-size: 13px; color: #94a3b8;">أدخل عنوان محفظة TRX الخاصة بك:</p>
                    <input type="text" id="trx-input" placeholder="أدخل عنوان TRX هنا...">
                    <button id="wallet-btn" class="btn" onclick="handleWalletAction()">حفظ العنوان 💾</button>
                </div>
            </div>

            <!-- 7. السحب -->
            <div id="tab-withdraw" class="section">
                <div class="card">
                    <h3 id="txt-withdraw-title">💸 سحب الأرباح</h3>
                    <p id="txt-wallet-label" style="font-size: 13px; color: #94a3b8;">عنوان المحفظة المسجل للسحب:</p>
                    <p id="current-address" style="font-size: 14px; font-weight: bold; color: #fbbf24; word-break: break-all; margin: 10px 0;"></p>
                    <button id="txt-withdraw-btn" class="btn" style="background: #e11d48;" onclick="requestWithdraw()">تأكيد طلب السحب 🚀</button>
                </div>
            </div>

            <!-- 8. المشاهدة -->
            <div id="tab-watch" class="section">
                <div class="card">
                    <h3 id="txt-watch-title">▶️ الربح من المشاهدة</h3>
                    <p id="txt-watch-desc" style="font-size: 13px; color: #cbd5e1;">قم بمشاهدة الإعلانات لكسب نقاط TRX إضافية:</p>
                    <button id="txt-watch-btn" class="btn" style="background: #16a34a;" onclick="completeTask()">مشاهدة الإعلان والربح 🚀</button>
                </div>
            </div>

            <!-- 9. الشروط والأحكام -->
            <div id="tab-terms" class="section">
                <div class="card" style="text-align: right;">
                    <h3 id="txt-terms-title" style="color: #38bdf8; text-align: center; margin-bottom: 10px;">📜 الشروط والأحكام</h3>
                    <div id="txt-terms-content" class="terms-text">
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

            if (tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.id) {
                userId = tg.initDataUnsafe.user.id;
                if (tg.initDataUnsafe.user.first_name) {
                    userName = tg.initDataUnsafe.user.first_name;
                }
            }

            function toggleDrawer() {
                document.getElementById('drawer').classList.toggle('open');
                document.getElementById('overlay').classList.toggle('active');
            }

            function toggleAccordion() {
                document.getElementById('faq-accordion').classList.toggle('open');
            }

            const translations = {
                ar: {
                    home: "🏠 الرئيسية", ref: "👥 الإحالة",
                    phoneSub: "📱 الربح من الاشتراك في رقم هاتف", installApps: "📲 الربح من تثبيت تطبيقات", registerSites: "🌐 الربح من التسجيل في المواقع",
                    wallet: "💳 المحفظة", withdraw: "💸 السحب", watch: "▶️ الربح من المشاهدة", terms: "📜 الشروط والأحكام",
                    menu: "القائمة ⚙️", welcome: "مرحباً بك: ",
                    balTitle: "رصيد TRX الحالي", balDesc: "تجميعك المستمر يتيح لك السحب الفوري عند الوصول للحد الأدنى.",
                    faqTitle: "❓ كيف العمل على البوت؟", faqDesc: "العمل على البوت سهل جدا يمكنك الربح من المشاهده الاعلانات فقط",
                    refTitle: "👥 نظام الإحالات النشطة (3%)", refCountLbl: "عدد إحالاتك النشطة:", refDesc: "شارك رابطك وخذ 3% أرباح للأبد:", copyBtn: "نسخ رابط الإحالة 🔗",
                    phoneSubTitle: "📱 الربح من الاشتراك في رقم هاتف", phoneSubDesc: "اشترك برقم هاتفك في العروض المتاحة أدناه لكسب نقاط TRX:", phoneSubBtn: "تنفيذ الاشتراك ✅",
                    installAppsTitle: "📲 الربح من تثبيت تطبيقات", installAppsDesc: "قم بتثبيت التطبيقات المطلوبة وافتحها لكسب نقاط TRX:", installAppsBtn: "تثبيت التطبيق ✅",
                    registerSitesTitle: "🌐 الربح من التسجيل في المواقع", registerSitesDesc: "سجل في المواقع الإلكترونية المتاحة لكسب نقاط TRX:", registerSitesBtn: "التسجيل في الموقع ✅",
                    walletTitle: "💳 إدارة المحفظة", walletDesc: "أدخل عنوان محفظة TRX الخاصة بك:", walletPlaceholder: "أدخل عنوان TRX هنا...", saveBtn: "حفظ العنوان 💾", changeBtn: "تغيير المحفظة 🔄", saveChangeBtn: "حفظ التغيير 💾", walletSavedDesc: "العنوان المحفوظ حالياً (اضغط تغيير لتعديله):",
                    withdrawTitle: "💸 سحب الأرباح", walletLabel: "عنوان المحفظة المسجل للسحب:", noAddress: "لم تقم باضافة عنوان بعد!", withdrawBtn: "تأكيد طلب السحب 🚀",
                    watchTitle: "▶️ الربح من المشاهدة", watchDesc: "قم بمشاهدة الإعلانات لكسب نقاط TRX إضافية:", watchBtn: "مشاهدة الإعلان والربح 🚀",
                    termsTitle: "📜 الشروط والأحكام", termsContent: "1. يمنع منعاً باتاً استخدام الواي فاي أو الـ VPN.<br>2. لا تُحتسب الإحالة نشطة إلا بعد إتمام الشخص المدعو لعرض ناجح.<br>3. نسبة الإحالة (3%) تُحتسب للأبد.<br>4. يمكنك حفظ أو تغيير عنوان محفظة TRX بأي وقت.",
                    alertCopy: "تم نسخ رابط الإحالة بنجاح! 📋",
                    alertAddressReq: "الرجاء إدخال عنوان صحيح!",
                    alertOfferDone: "مبروك! تمت إضافة المكافأة إلى رصيدك بنجاح! 🎉",
                    alertNoAddress: "الرجاء إضافة عنوان محفظة TRX في قسم المحفظة أولاً!",
                    alertNoBalance: "عذراً، ليس لديك رصيد كافي للسحب",
                    alertWithdrawDone: "تم تقديم طلب السحب بنجاح وسيتم المعالجة قريباً! 🚀"
                },
                en: {
                    home: "🏠 Home", ref: "👥 Referrals",
                    phoneSub: "📱 Phone Number Sub", installApps: "📲 Install Apps", registerSites: "🌐 Register Sites",
                    wallet: "💳 Wallet", withdraw: "💸 Withdraw", watch: "▶️ Watch & Earn", terms: "📜 Terms",
                    menu: "Menu ⚙️", welcome: "Welcome: ",
                    balTitle: "Your Current TRX Balance", balDesc: "Continuous earning allows instant withdrawal upon reaching the minimum limit.",
                    faqTitle: "❓ How to work on bot?", faqDesc: "Working on the bot is very easy, you can earn by watching ads only.",
                    refTitle: "👥 Active Referral System (3%)", refCountLbl: "Active Referrals:", refDesc: "Share your link and earn 3% lifetime profits:", copyBtn: "Copy Referral Link 🔗",
                    phoneSubTitle: "📱 Phone Number Sub", phoneSubDesc: "Subscribe with your phone number in available offers to earn TRX:", phoneSubBtn: "Complete Subscription ✅",
                    installAppsTitle: "📲 Install Apps", installAppsDesc: "Install required apps and open them to earn TRX points:", installAppsBtn: "Install App ✅",
                    registerSitesTitle: "🌐 Register Sites", registerSitesDesc: "Register on available websites to earn TRX points:", registerSitesBtn: "Register on Site ✅",
                    walletTitle: "💳 Wallet Management", walletDesc: "Enter your TRX wallet address:", walletPlaceholder: "Enter TRX address here...", saveBtn: "Save Address 💾", changeBtn: "Change Wallet 🔄", saveChangeBtn: "Save Changes 💾", walletSavedDesc: "Current saved address:",
                    withdrawTitle: "💸 Withdraw Earnings", walletLabel: "Registered Wallet Address:", noAddress: "No address added yet!", withdrawBtn: "Confirm Withdrawal 🚀",
                    watchTitle: "▶️ Watch & Earn", watchDesc: "Watch ads to earn bonus TRX points:", watchBtn: "Watch Ad & Earn 🚀",
                    termsTitle: "📜 Terms & Conditions", termsContent: "1. Using Wi-Fi or VPN is strictly prohibited.<br>2. Referrals are active only after the invited user completes an offer.<br>3. 3% referral bonus is lifetime.<br>4. You can save or change your TRX wallet anytime.",
                    alertCopy: "Referral link copied successfully! 📋",
                    alertAddressReq: "Please enter a valid address!",
                    alertOfferDone: "Congratulations! Reward added to your balance successfully! 🎉",
                    alertNoAddress: "Please add your TRX wallet address in the wallet section first!",
                    alertNoBalance: "Sorry, you don't have enough balance to withdraw",
                    alertWithdrawDone: "Withdrawal request submitted successfully and will be processed soon! 🚀"
                },
                es: {
                    home: "🏠 Inicio", ref: "👥 Referidos", phoneSub: "📱 Suscripción", installApps: "📲 Instalar Apps", registerSites: "🌐 Registrarse", wallet: "💳 Billetera", withdraw: "💸 Retirar", watch: "▶️ Ver y Ganar", terms: "📜 Términos",
                    menu: "Menú ⚙️", welcome: "Bienvenido: ",
                    balTitle: "Saldo Actual", balDesc: "Retiro instantáneo al alcanzar el mínimo.",
                    faqTitle: "❓ ¿Cómo trabajar en el bot?", faqDesc: "Es muy fácil, puedes ganar viendo anuncios únicamente.",
                    refTitle: "👥 Referidos (3%)", refCountLbl: "Activos:", refDesc: "Comparte tu enlace:", copyBtn: "Copiar Enlace 🔗",
                    phoneSubTitle: "📱 Suscripción", phoneSubDesc: "Suscríbete con tu número:", phoneSubBtn: "Suscribirse ✅",
                    installAppsTitle: "📲 Instalar Apps", installAppsDesc: "Instala apps requeridas:", installAppsBtn: "Instalar App ✅",
                    registerSitesTitle: "🌐 Registrarse", registerSitesDesc: "Regístrate en sitios:", registerSitesBtn: "Registrarse ✅",
                    walletTitle: "💳 Billetera", walletDesc: "Ingresa tu dirección TRX:", walletPlaceholder: "Ingresa TRX...", saveBtn: "Guardar 💾", changeBtn: "Cambiar 🔄", saveChangeBtn: "Guardar 💾", walletSavedDesc: "Dirección guardada:",
                    withdrawTitle: "💸 Retirar", walletLabel: "Dirección:", noAddress: "¡Sin dirección!", withdrawBtn: "Confirmar Retiro 🚀",
                    watchTitle: "▶️ Ver y Ganar", watchDesc: "Mira anuncios:", watchBtn: "Ver Anuncio 🚀",
                    termsTitle: "📜 Términos", termsContent: "1. No VPN.<br>2. Referidos activos.<br>3. 3% bono.<br>4. Cambia tu billetera cuando quieras.",
                    alertCopy: "¡Enlace copiado con éxito! 📋",
                    alertAddressReq: "¡Por favor ingresa una dirección válida!",
                    alertOfferDone: "¡Felicitaciones! Recompensa añadida con éxito. 🎉",
                    alertNoAddress: "¡Por favor añade tu dirección TRX en la billetera primero!",
                    alertNoBalance: "Lo siento, no tienes suficiente saldo para retirar",
                    alertWithdrawDone: "¡Solicitud de retiro enviada con éxito! 🚀"
                },
                de: {
                    home: "🏠 Startseite", ref: "👥 Empfehlungen", phoneSub: "📱 Telefon-Abo", installApps: "📲 Apps installieren", registerSites: "🌐 Websites", wallet: "💳 Wallet", withdraw: "💸 Auszahlen", watch: "▶️ Ansehen", terms: "📜 AGB",
                    menu: "Menü ⚙️", welcome: "Willkommen: ",
                    balTitle: "Aktuelles Guthaben", balDesc: "Sofortige Auszahlung möglich.",
                    faqTitle: "❓ Wie arbeite ich am Bot?", faqDesc: "Sehr einfach, Sie können nur durch das Ansehen von Anzeigen verdienen.",
                    refTitle: "👥 Empfehlungen (3%)", refCountLbl: "Aktiv:", refDesc: "Link teilen:", copyBtn: "Link kopieren 🔗",
                    phoneSubTitle: "📱 Telefon-Abo", phoneSubDesc: "Abonnieren Sie mit Ihrer Nummer:", phoneSubBtn: "Abonnieren ✅",
                    installAppsTitle: "📲 Apps installieren", installAppsDesc: "Apps installieren:", installAppsBtn: "App installieren ✅",
                    registerSitesTitle: "🌐 Websites", registerSitesDesc: "Auf Websites registrieren:", registerSitesBtn: "Registrieren ✅",
                    walletTitle: "💳 Wallet", walletDesc: "TRX-Adresse eingeben:", walletPlaceholder: "TRX eingeben...", saveBtn: "Speichern 💾", changeBtn: "Ändern 🔄", saveChangeBtn: "Speichern 💾", walletSavedDesc: "Gespeicherte Adresse:",
                    withdrawTitle: "💸 Auszahlen", walletLabel: "Adresse:", noAddress: "Keine Adresse!", withdrawBtn: "Bestätigen 🚀",
                    watchTitle: "▶️ Ansehen", watchDesc: "Anzeigen ansehen:", watchBtn: "Anzeigen 🚀",
                    termsTitle: "📜 AGB", termsContent: "1. Kein VPN.<br>2. Aktive Empfehlungen.<br>3. 3% Bonus.<br>4. Wallet änderbar.",
                    alertCopy: "Empfehlungslink erfolgreich kopiert! 📋",
                    alertAddressReq: "Bitte geben Sie eine gültige Adresse ein!",
                    alertOfferDone: "Glückwunsch! Belohnung erfolgreich hinzugefügt! 🎉",
                    alertNoAddress: "Bitte fügen Sie zuerst Ihre TRX-Adresse im Wallet hinzu!",
                    alertNoBalance: "Entschuldigung, Sie haben nicht genug Guthaben zum Abheben",
                    alertWithdrawDone: "Auszahlungsantrag erfolgreich eingereicht! 🚀"
                },
                fr: {
                    home: "🏠 Accueil", ref: "👥 Parrainages", phoneSub: "📱 Abonn. Téléphone", installApps: "📲 Installer Apps", registerSites: "🌐 Inscription", wallet: "💳 Portefeuille", withdraw: "💸 Retirer", watch: "▶️ Regarder", terms: "📜 Conditions",
                    menu: "Menu ⚙️", welcome: "Bienvenue : ",
                    balTitle: "Solde Actuel", balDesc: "Retrait instantané.",
                    faqTitle: "❓ Comment travailler sur le bot?", faqDesc: "C'est très facile, vous pouvez gagner en regardant des publicités.",
                    refTitle: "👥 Parrainage (3%)", refCountLbl: "Actifs :", refDesc: "Partagez :", copyBtn: "Copier 🔗",
                    phoneSubTitle: "📱 Abonn. Téléphone", phoneSubDesc: "Abonnez-vous avec votre numéro:", phoneSubBtn: "S'abonner ✅",
                    installAppsTitle: "📲 Installer Apps", installAppsDesc: "Installez les apps requises:", installAppsBtn: "Installer ✅",
                    registerSitesTitle: "🌐 Inscription", registerSitesDesc: "Inscrivez-vous sur les sites:", registerSitesBtn: "S'inscrire ✅",
                    walletTitle: "💳 Portefeuille", walletDesc: "Adresse TRX :", walletPlaceholder: "Entrez TRX...", saveBtn: "Enregistrer 💾", changeBtn: "Modifier 🔄", saveChangeBtn: "Enregistrer 💾", walletSavedDesc: "Adresse :",
                    withdrawTitle: "💸 Retirer", walletLabel: "Adresse :", noAddress: "Aucune !", withdrawBtn: "Confirmer 🚀",
                    watchTitle: "▶️ Regarder", watchDesc: "Regardez :", watchBtn: "Voir 🚀",
                    termsTitle: "📜 Conditions", termsContent: "1. Pas de VPN.<br>2. Parrainage actif.<br>3. 3% bonus.<br>4. Modifiable.",
                    alertCopy: "Lien de parrainage copié avec succès ! 📋",
                    alertAddressReq: "Veuillez entrer une adresse valide !",
                    alertOfferDone: "Félicitations ! Récompense ajoutée avec succès ! 🎉",
                    alertNoAddress: "Veuillez d'abord ajouter votre adresse TRX dans le portefeuille !",
                    alertNoBalance: "Désolé, vous n'avez pas assez de solde pour retirer",
                    alertWithdrawDone: "Demande de retrait soumise avec succès ! 🚀"
                },
                ru: {
                    home: "🏠 Главная", ref: "👥 Рефералы", phoneSub: "📱 Подписка по тел.", installApps: "📲 Установка апп", registerSites: "🌐 Сайты", wallet: "💳 Кошелек", withdraw: "💸 Вывод", watch: "▶️ Смотреть", terms: "📜 Условия",
                    menu: "Меню ⚙️", welcome: "Добро пожаловать: ",
                    balTitle: "Баланс TRX", balDesc: "Мгновенный вывод.",
                    faqTitle: "❓ Как работать в боте?", faqDesc: "Очень просто, вы можете зарабатывать только просматривая рекламу.",
                    refTitle: "👥 Рефералы (3%)", refCountLbl: "Активные:", refDesc: "Ссылка:", copyBtn: "Копировать 🔗",
                    phoneSubTitle: "📱 Подписка по тел.", phoneSubDesc: "Подпишитесь с номером:", phoneSubBtn: "Подписаться ✅",
                    installAppsTitle: "📲 Установка апп", installAppsDesc: "Установите нужные приложения:", installAppsBtn: "Установить ✅",
                    registerSitesTitle: "🌐 Сайты", registerSitesDesc: "Регистрируйтесь на сайтах:", registerSitesBtn: "Регистрация ✅",
                    walletTitle: "💳 Кошелек", walletDesc: "Введите TRX адрес:", walletPlaceholder: "TRX адрес...", saveBtn: "Сохранить 💾", changeBtn: "Изменить 🔄", saveChangeBtn: "Сохранить 💾", walletSavedDesc: "Адрес:",
                    withdrawTitle: "💸 Вывод", walletLabel: "Адрес:", noAddress: "Нет адреса!", withdrawBtn: "Подтвердить 🚀",
                    watchTitle: "▶️ Смотреть", watchDesc: "Смотрите рекламу:", watchBtn: "Смотреть 🚀",
                    termsTitle: "📜 Условия", termsContent: "1. Без VPN.<br>2. Рефералы активны.<br>3. 3% бонус.<br>4. Кошелек изменяем.",
                    alertCopy: "Реферальная ссылка успешно скопирована! 📋",
                    alertAddressReq: "Пожалуйста, введите правильный адрес!",
                    alertOfferDone: "Поздравляем! Награда успешно добавлена на ваш баланс! 🎉",
                    alertNoAddress: "Пожалуйста, сначала добавьте адрес кошелька TRX в разделе кошелька!",
                    alertNoBalance: "Извините, у вас недостаточно средств для вывода",
                    alertWithdrawDone: "Запрос на вывод успешно отправлен и скоро будет обработан! 🚀"
                },
                pt: {
                    home: "🏠 Início", ref: "👥 Indicações", phoneSub: "📱 Sub. de Telefone", installApps: "📲 Instalar Apps", registerSites: "🌐 Registrar", wallet: "💳 Carteira", withdraw: "💸 Sacar", watch: "▶️ Assistir", terms: "📜 Termos",
                    menu: "Menu ⚙️", welcome: "Bem-vindo: ",
                    balTitle: "Saldo TRX", balDesc: "Saque rápido.",
                    faqTitle: "❓ Como trabalhar no bot?", faqDesc: "É muito fácil, você pode ganhar assistindo a anúncios.",
                    refTitle: "👥 Indicações (3%)", refCountLbl: "Ativas:", refDesc: "Link:", copyBtn: "Copiar 🔗",
                    phoneSubTitle: "📱 Sub. de Telefone", phoneSubDesc: "Inscreva-se com seu número:", phoneSubBtn: "Inscrever-se ✅",
                    installAppsTitle: "📲 Instalar Apps", installAppsDesc: "Instale os aplicativos:", installAppsBtn: "Instalar ✅",
                    registerSitesTitle: "🌐 Registrar", registerSitesDesc: "Registre-se nos sites:", registerSitesBtn: "Registrar ✅",
                    walletTitle: "💳 Carteira", walletDesc: "Endereço TRX:", walletPlaceholder: "Insira TRX...", saveBtn: "Salvar 💾", changeBtn: "Alterar 🔄", saveChangeBtn: "Salvar 💾", walletSavedDesc: "Endereço:",
                    withdrawTitle: "💸 Sacar", walletLabel: "Endereço:", noAddress: "Nenhum!", withdrawBtn: "Confirmar 🚀",
                    watchTitle: "▶️ Assistir", watchDesc: "Assista:", watchBtn: "Ver 🚀",
                    termsTitle: "📜 Termos", termsContent: "1. Sem VPN.<br>2. Indicações ativas.<br>3. 3% bônus.<br>4. Alterável.",
                    alertCopy: "Link de indicação copiado com sucesso! 📋",
                    alertAddressReq: "Por favor, insira um endereço válido!",
                    alertOfferDone: "Parabéns! Recompensa adicionada ao saldo com sucesso! 🎉",
                    alertNoAddress: "Por favor, adicione seu endereço TRX na carteira primeiro!",
                    alertNoBalance: "Desculpe, você não tem saldo suficiente para sacar",
                    alertWithdrawDone: "Solicitação de saque enviada com sucesso! 🚀"
                },
                nl: {
                    home: "🏠 Home", ref: "👥 Referrals", phoneSub: "📱 Telefoon Sub", installApps: "📲 Apps Installeren", registerSites: "🌐 Sites", wallet: "💳 Wallet", withdraw: "💸 Opnemen", watch: "▶️ Kijken", terms: "📜 Voorwaarden",
                    menu: "Menu ⚙️", welcome: "Welkom: ",
                    balTitle: "Saldo", balDesc: "Direct opnemen.",
                    faqTitle: "❓ Hoe werken met de bot?", faqDesc: "Heel eenvoudig, je kunt verdienen door alleen advertenties te bekijken.",
                    refTitle: "👥 Referrals (3%)", refCountLbl: "Actief:", refDesc: "Deel:", copyBtn: "Kopieer 🔗",
                    phoneSubTitle: "📱 Telefoon Sub", phoneSubDesc: "Abonneer met je nummer:", phoneSubBtn: "Abonneren ✅",
                    installAppsTitle: "📲 Apps Installeren", installAppsDesc: "Installeer vereiste apps:", installAppsBtn: "Installeren ✅",
                    registerSitesTitle: "🌐 Sites", registerSitesDesc: "Registreer op sites:", registerSitesBtn: "Registreren ✅",
                    walletTitle: "💳 Wallet", walletDesc: "TRX adres:", walletPlaceholder: "Voer TRX in...", saveBtn: "Opslaan 💾", changeBtn: "Wijzigen 🔄", saveChangeBtn: "Opslaan 💾", walletSavedDesc: "Adres:",
                    withdrawTitle: "💸 Opnemen", walletLabel: "Adres:", noAddress: "Geen adres!", withdrawBtn: "Bevestigen 🚀",
                    watchTitle: "▶️ Kijken", watchDesc: "Bekijk advertenties:", watchBtn: "Kijk 🚀",
                    termsTitle: "📜 Voorwaarden", termsContent: "1. Geen VPN.<br>2. Actieve referrals.<br>3. 3% bonus.<br>4. Wijzigbaar.",
                    alertCopy: "Verwijzingslink succesvol gekopieerd! 📋",
                    alertAddressReq: "Vul alstublieft een geldig adres in!",
                    alertOfferDone: "Gefeliciteerd! Beloning successfully toegevoegd! 🎉",
                    alertNoAddress: "Voeg eerst je TRX wallet adres toe in de wallet sectie!",
                    alertNoBalance: "Sorry, je hebt niet genoeg saldo om op te nemen",
                    alertWithdrawDone: "Opnameverzoek succesvol ingediend! 🚀"
                },
                pl: {
                    home: "🏠 Strona główna", ref: "👥 Polecenia", phoneSub: "📱 Subskrypcja tel.", installApps: "📲 Instaluj aplikacje", registerSites: "🌐 Strony", wallet: "💳 Portfel", withdraw: "💸 Wypłata", watch: "▶️ Oglądaj", terms: "📜 Regulamin",
                    menu: "Menu ⚙️", welcome: "Witaj: ",
                    balTitle: "Saldo TRX", balDesc: "Szybka wypłata.",
                    faqTitle: "❓ Jak pracować z botem?", faqDesc: "Bardzo proste, możesz zarabiać tylko oglądając reklamy.",
                    refTitle: "👥 Polecenia (3%)", refCountLbl: "Aktywne:", refDesc: "Link:", copyBtn: "Kopiuj 🔗",
                    phoneSubTitle: "📱 Subskrypcja tel.", phoneSubDesc: "Subskrybuj numerem:", phoneSubBtn: "Subskrybuj ✅",
                    installAppsTitle: "📲 Instaluj aplikacje", installAppsDesc: "Zainstaluj aplikacje:", installAppsBtn: "Zainstaluj ✅",
                    registerSitesTitle: "🌐 Strony", registerSitesDesc: "Zarejestruj się na stronach:", registerSitesBtn: "Zarejestruj ✅",
                    walletTitle: "💳 Portfel", walletDesc: "Adres TRX:", walletPlaceholder: "Wpisz TRX...", saveBtn: "Zapisz 💾", changeBtn: "Zmień 🔄", saveChangeBtn: "Zapisz 💾", walletSavedDesc: "Adres:",
                    withdrawTitle: "💸 Wypłata", walletLabel: "Adres:", noAddress: "Brak adresu!", withdrawBtn: "Potwierdź 🚀",
                    watchTitle: "▶️ Oglądaj", watchDesc: "Oglądaj reklamy:", watchBtn: "Oglądaj 🚀",
                    termsTitle: "📜 Regulamin", termsContent: "1. Bez VPN.<br>2. Polecenia aktywne.<br>3. 3% bonus.<br>4. Zmieniaj portfel.",
                    alertCopy: "Link polecający skopiowany pomyślnie! 📋",
                    alertAddressReq: "Proszę wpisać poprawny adres!",
                    alertOfferDone: "Gratulacje! Nagroda dodana pomyślnie! 🎉",
                    alertNoAddress: "Najpierw dodaj adres portfela TRX w zakładce portfela!",
                    alertNoBalance: "Przepraszamy, nie masz wystarczającego salda do wypłaty",
                    alertWithdrawDone: "Wniosek o wypłatę został pomyślnie złożony! 🚀"
                }
            };

            let currentLang = 'ar';
            let currentTitles = translations[currentLang];

            function changeLanguage(lang) {
                currentLang = lang;
                let t = translations[lang] || translations['ar'];
                currentTitles = t;

                if (lang === 'ar') {
                    document.getElementById('html-root').setAttribute('dir', 'rtl');
                    document.getElementById('html-root').setAttribute('lang', 'ar');
                } else {
                    document.getElementById('html-root').setAttribute('dir', 'ltr');
                    document.getElementById('html-root').setAttribute('lang', lang);
                }

                document.getElementById('page-title').innerText = t.home;
                document.getElementById('menu-title').innerText = t.menu;
                
                document.getElementById('txt-bal-title').innerText = t.balTitle;
                document.getElementById('txt-bal-desc').innerText = t.balDesc;
                document.getElementById('txt-faq-title').innerText = t.faqTitle;
                document.getElementById('txt-faq-desc').innerText = t.faqDesc;

                document.getElementById('txt-ref-title').innerText = t.refTitle;
                document.getElementById('txt-ref-count-label').innerText = t.refCountLbl;
                document.getElementById('txt-ref-desc').innerText = t.refDesc;
                document.getElementById('txt-copy-btn').innerText = t.copyBtn;

                document.getElementById('txt-phonesub-title').innerText = t.phoneSubTitle;
                document.getElementById('txt-phonesub-desc').innerText = t.phoneSubDesc;
                document.getElementById('txt-phonesub-btn').innerText = t.phoneSubBtn;

                document.getElementById('txt-installapps-title').innerText = t.installAppsTitle;
                document.getElementById('txt-installapps-desc').innerText = t.installAppsDesc;
                document.getElementById('txt-installapps-btn').innerText = t.installAppsBtn;

                document.getElementById('txt-registersites-title').innerText = t.registerSitesTitle;
                document.getElementById('txt-registersites-desc').innerText = t.registerSitesDesc;
                document.getElementById('txt-registersites-btn').innerText = t.registerSitesBtn;

                document.getElementById('txt-wallet-title').innerText = t.walletTitle;
                document.getElementById('wallet-desc').innerText = t.walletDesc;
                document.getElementById('trx-input').placeholder = t.walletPlaceholder;
                document.getElementById('txt-withdraw-title').innerText = t.withdrawTitle;
                document.getElementById('txt-wallet-label').innerText = t.walletLabel;
                document.getElementById('txt-withdraw-btn').innerText = t.withdrawBtn;
                document.getElementById('txt-watch-title').innerText = t.watchTitle;
                document.getElementById('txt-watch-desc').innerText = t.watchDesc;
                document.getElementById('txt-watch-btn').innerText = t.watchBtn;

                document.getElementById('txt-terms-title').innerText = t.termsTitle;
                document.getElementById('txt-terms-content').innerHTML = t.termsContent;

                document.getElementById('nav-txt-home').innerText = t.home;
                document.getElementById('nav-txt-ref').innerText = t.ref;
                document.getElementById('nav-txt-phonesub').innerText = t.phoneSub;
                document.getElementById('nav-txt-installapps').innerText = t.installApps;
                document.getElementById('nav-txt-registersites').innerText = t.registerSites;
                document.getElementById('nav-txt-wallet').innerText = t.wallet;
                document.getElementById('nav-txt-withdraw').innerText = t.withdraw;
                document.getElementById('nav-txt-watch').innerText = t.watch;
                document.getElementById('nav-txt-terms').innerText = t.terms;

                document.getElementById('welcome').innerText = t.welcome + userName;
                loadUserData();
            }

            let savedTrxAddress = "";

            function loadUserData() {
                let t = translations[currentLang] || translations['ar'];
                let localAddress = localStorage.getItem('trx_address_' + userId) || "";

                fetch('/api/user/' + userId)
                    .then(res => res.json())
                    .then(data => {
                        document.getElementById('balance-val').innerText = "TRX " + data.balance.toFixed(2);
                        document.getElementById('ref-count').innerText = data.active_referrals;
                        document.getElementById('ref-link').value = data.ref_link;
                        
                        savedTrxAddress = data.trx_address || localAddress || "";
                        let input = document.getElementById('trx-input');
                        let btn = document.getElementById('wallet-btn');
                        let desc = document.getElementById('wallet-desc');

                        if (savedTrxAddress) {
                            input.value = savedTrxAddress;
                            input.readOnly = true;
                            btn.innerText = t.changeBtn;
                            desc.innerText = t.walletSavedDesc;
                            document.getElementById('current-address').innerText = savedTrxAddress;
                        } else {
                            input.value = "";
                            input.readOnly = false;
                            btn.innerText = t.saveBtn;
                            desc.innerText = t.walletDesc;
                            document.getElementById('current-address').innerText = t.noAddress;
                        }
                    })
                    .catch(err => {
                        console.error("Error:", err);
                        if (localAddress) {
                            savedTrxAddress = localAddress;
                            document.getElementById('trx-input').value = savedTrxAddress;
                            document.getElementById('trx-input').readOnly = true;
                            document.getElementById('current-address').innerText = savedTrxAddress;
                        }
                    });
            }

            function handleWalletAction() {
                let t = translations[currentLang] || translations['ar'];
                let input = document.getElementById('trx-input');
                let btn = document.getElementById('wallet-btn');
                let address = input.value.trim();

                if (!address) {
                    alert(t.alertAddressReq);
                    return;
                }

                if (input.readOnly) {
                    input.readOnly = false;
                    input.focus();
                    btn.innerText = t.saveChangeBtn;
                } else {
                    localStorage.setItem('trx_address_' + userId, address);

                    fetch('/api/update_address', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({user_id: userId, address: address})
                    })
                    .then(res => res.json())
                    .then(data => {
                        alert(currentLang === 'ar' ? "تم حفظ عنوان المحفظة بنجاح! 💾" : "Wallet address saved successfully! 💾");
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
                let t = translations[currentLang] || translations['ar'];
                var copyText = document.getElementById("ref-link");
                copyText.select();
                copyText.setSelectionRange(0, 99999);
                navigator.clipboard.writeText(copyText.value);
                alert(t.alertCopy);
            }

            function completeTask() {
                let t = translations[currentLang] || translations['ar'];
                fetch('/api/complete_offer', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: userId})
                })
                .then(res => res.json())
                .then(data => {
                    alert(t.alertOfferDone);
                    loadUserData();
                });
            }

            function requestWithdraw() {
                let t = translations[currentLang] || translations['ar'];
                fetch('/api/withdraw', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: userId})
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        alert(t.alertWithdrawDone);
                    } else {
                        if (data.message.includes("address")) {
                            alert(t.alertNoAddress);
                        } else {
                            alert(t.alertNoBalance);
                        }
                    }
                    loadUserData();
                });
            }

            document.getElementById('language-select').value = 'ar';
            changeLanguage('ar');
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
