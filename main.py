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
        return jsonify({"success": False, "message": "Please enter a valid address"})
    
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET trx_address = ? WHERE user_id = ?", (address, user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "TRX wallet updated successfully!"})

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
        return jsonify({"success": False, "message": "User not found"})
    
    completed_offer, referred_by = row
    if completed_offer == 1:
        conn.close()
        return jsonify({"success": False, "message": "You have already completed the offer!"})
    
    cursor.execute("UPDATE users SET completed_offer = 1, balance = balance + 1.0 WHERE user_id = ?", (user_id,))
    if referred_by:
        cursor.execute(
            "UPDATE users SET active_referrals = active_referrals + 1 WHERE user_id = ?",
            (referred_by,)
        )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Congratulations! Offer verified and completed successfully!"})

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
        return jsonify({"success": False, "message": "User not found"})
    
    balance, address = row
    if not address:
        conn.close()
        return jsonify({"success": False, "message": "Please add a TRX wallet address in the wallet section first!"})
    
    if balance <= 0:
        conn.close()
        return jsonify({"success": False, "message": "Sorry, you do not have enough balance to withdraw"})
    
    cursor.execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Withdrawal request submitted successfully and will be processed soon!"})

@server.route('/webapp')
def webapp():
    html_content = """
    <!DOCTYPE html>
    <html lang="en" dir="ltr" id="html-root">
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
            input:read-only { border-color: #475569; }

            /* القائمة الجانبية (Drawer Menu) */
            .drawer {
                position: fixed;
                top: 0;
                left: -260px;
                width: 250px;
                height: 100%;
                background: #1e293b;
                z-index: 1000;
                transition: 0.3s ease;
                box-shadow: 5px 0 15px rgba(0,0,0,0.5);
                display: flex;
                flex-direction: column;
                padding: 20px 10px;
                box-sizing: border-box;
            }
            .drawer.open { left: 0; }
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
                text-align: left;
                padding: 10px;
                cursor: pointer;
                border-radius: 8px;
                margin-bottom: 5px;
                display: flex;
                align-items: center;
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
                text-align: left;
                line-height: 1.6;
            }
            #network-warning {
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(15, 23, 42, 0.95);
                z-index: 9999;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                padding: 20px;
                text-align: center;
            }
        </style>
    </head>
    <body>

        <div id="network-warning" style="display: none;">
            <h2 id="warn-title" style="color: #ef4444;">⚠️ Network Warning</h2>
            <p id="warn-desc" style="font-size: 14px; color: #cbd5e1; line-height: 1.6; margin: 15px 0;">
                Wi-Fi or VPN usage is strictly prohibited. Please use your Mobile Data only to proceed.
            </p>
            <button class="btn" style="background: #e11d48;" onclick="checkNetwork()">Re-check 🔄</button>
        </div>

        <!-- الهيدر مع زر القائمة الجانبية -->
        <div class="header">
            <button class="menu-btn" onclick="toggleDrawer()">☰</button>
            <h2 id="page-title">🏠 Home</h2>
            <div style="width: 24px;"></div>
        </div>

        <!-- القائمة الجانبية المحدثة -->
        <div class="overlay" id="overlay" onclick="toggleDrawer()"></div>
        <div class="drawer" id="drawer">
            <div class="drawer-header">
                <span style="font-weight: bold; color: #38bdf8;" id="menu-title">Menu ⚙️</span>
                <button class="close-drawer" onclick="toggleDrawer()">✕</button>
            </div>
            <button class="drawer-item active" onclick="switchTab('home', currentTitles.home, this)"><span>🏠</span> <span id="nav-txt-home">Home</span></button>
            <button class="drawer-item" onclick="switchTab('ref', currentTitles.ref, this)"><span>👥</span> <span id="nav-txt-ref">Referrals</span></button>
            
            <!-- الأقسام الثلاثة الجديدة بدلاً من زر العروض القديم -->
            <button class="drawer-item" onclick="switchTab('phone_sub', currentTitles.phoneSub, this)"><span>📱</span> <span id="nav-txt-phonesub">الربح من الاشتراك في رقم هاتف</span></button>
            <button class="drawer-item" onclick="switchTab('install_apps', currentTitles.installApps, this)"><span>📲</span> <span id="nav-txt-installapps">الربح من تثبيت تطبيقات</span></button>
            <button class="drawer-item" onclick="switchTab('register_sites', currentTitles.registerSites, this)"><span>🌐</span> <span id="nav-txt-registersites">الربح من التسجيل في المواقع</span></button>

            <button class="drawer-item" onclick="switchTab('wallet', currentTitles.wallet, this)"><span>💳</span> <span id="nav-txt-wallet">Wallet</span></button>
            <button class="drawer-item" onclick="switchTab('withdraw', currentTitles.withdraw, this)"><span>💸</span> <span id="nav-txt-withdraw">Withdraw</span></button>
            <button class="drawer-item" onclick="switchTab('watch', currentTitles.watch, this)"><span>▶️</span> <span id="nav-txt-watch">Watch & Earn</span></button>
            <button class="drawer-item" onclick="switchTab('terms', currentTitles.terms, this)"><span>📜</span> <span id="nav-txt-terms">Terms</span></button>
            
            <div class="lang-container">
                <span style="font-size: 11px; color: #94a3b8; display: block; margin-bottom: 5px;">🌐 Language:</span>
                <select id="language-select" onchange="changeLanguage(this.value)">
                    <option value="en">🇬🇧 English</option>
                    <option value="es">🇪🇸 Español</option>
                    <option value="de">🇩🇪 Deutsch</option>
                    <option value="fr">🇫🇷 Français</option>
                    <option value="ru">🇷🇺 Русский</option>
                    <option value="pt">🇧🇷/🇵🇹 Português</option>
                    <option value="nl">🇳🇱 Nederlands</option>
                    <option value="pl">🇵🇱 Polski</option>
                    <option value="ar">🇸🇦 العربية</option>
                </select>
            </div>
        </div>

        <div class="container">
            <p id="welcome" style="text-align:center; font-size: 13px; color: #94a3b8; margin-top:0;"></p>

            <!-- 1. الرئيسية -->
            <div id="tab-home" class="section active">
                <div class="card">
                    <h3 id="txt-bal-title">Your Current TRX Balance</h3>
                    <p id="balance-val" style="font-size: 26px; font-weight: bold; color: #4ade80;">0.0 TRX</p>
                    <p id="txt-bal-desc" style="font-size: 12px; color: #94a3b8;">Continuous earning allows instant withdrawal upon reaching the minimum limit.</p>
                </div>
                <div class="card" style="text-align: left;">
                    <h3 id="txt-home-terms-title" style="color: #38bdf8; text-align: center; margin-bottom: 10px;">📜 Terms & Conditions</h3>
                    <div id="txt-home-terms-content" class="terms-text">
                        1. Using Wi-Fi or VPN is strictly prohibited.<br>
                        2. Referrals are active only after the invited user completes an offer.<br>
                        3. 3% referral bonus is lifetime.<br>
                        4. You can save or change your TRX wallet anytime.
                    </div>
                </div>
            </div>

            <!-- 2. الإحالة -->
            <div id="tab-ref" class="section">
                <div class="card">
                    <h3 id="txt-ref-title">👥 Active Referral System (3%)</h3>
                    <p><span id="txt-ref-count-label">Active Referrals:</span> <span id="ref-count" style="color: #38bdf8; font-weight: bold;">0</span></p>
                    <p id="txt-ref-desc" style="font-size: 13px; color: #94a3b8;">Share your link and earn 3% lifetime profits:</p>
                    <input type="text" id="ref-link" readonly onclick="this.select();">
                    <button id="txt-copy-btn" class="btn" onclick="copyRefLink()">Copy Referral Link 🔗</button>
                </div>
            </div>

            <!-- 3. القسم الأول الجديد: الربح من الاشتراك في رقم هاتف -->
            <div id="tab-phone_sub" class="section">
                <div class="card">
                    <h3 id="txt-phonesub-title">📱 الربح من الاشتراك في رقم هاتف</h3>
                    <p id="txt-phonesub-desc" style="font-size: 13px; color: #cbd5e1;">اشترك برقم هاتفك في العروض المتاحة أدناه لكسب نقاط TRX:</p>
                    <button class="btn" style="background: #eab308; margin-top: 10px;" onclick="completeCustomAction('phone_sub')">تنفيذ الاشتراك ✅</button>
                </div>
            </div>

            <!-- 4. القسم الثاني الجديد: الربح من تثبيت تطبيقات -->
            <div id="tab-install_apps" class="section">
                <div class="card">
                    <h3 id="txt-installapps-title">📲 الربح من تثبيت تطبيقات</h3>
                    <p id="txt-installapps-desc" style="font-size: 13px; color: #cbd5e1;">قم بتثبيت التطبيقات المطلوبة وافتحها لكسب نقاط TRX:</p>
                    <button class="btn" style="background: #16a34a; margin-top: 10px;" onclick="completeCustomAction('install_apps')">تثبيت التطبيق ✅</button>
                </div>
            </div>

            <!-- 5. القسم الثالث الجديد: الربح من التسجيل في المواقع -->
            <div id="tab-register_sites" class="section">
                <div class="card">
                    <h3 id="txt-registersites-title">🌐 الربح من التسجيل في المواقع</h3>
                    <p id="txt-registersites-desc" style="font-size: 13px; color: #cbd5e1;">سجل في المواقع الإلكترونية المتاحة لكسب نقاط TRX:</p>
                    <button class="btn" style="background: #0284c7; margin-top: 10px;" onclick="completeCustomAction('register_sites')">التسجيل في الموقع ✅</button>
                </div>
            </div>

            <!-- المحفظة -->
            <div id="tab-wallet" class="section">
                <div class="card">
                    <h3 id="txt-wallet-title">💳 Wallet Management</h3>
                    <p id="wallet-desc" style="font-size: 13px; color: #94a3b8;">Enter your TRX wallet address:</p>
                    <input type="text" id="trx-input" placeholder="Enter TRX address here...">
                    <button id="wallet-btn" class="btn" onclick="handleWalletAction()">Save Address 💾</button>
                </div>
            </div>

            <!-- السحب -->
            <div id="tab-withdraw" class="section">
                <div class="card">
                    <h3 id="txt-withdraw-title">💸 Withdraw Earnings</h3>
                    <p id="txt-wallet-label" style="font-size: 13px; color: #94a3b8;">Registered Wallet Address:</p>
                    <p id="current-address" style="font-size: 12px; color: #fbbf24; word-break: break-all;"></p>
                    <button id="txt-withdraw-btn" class="btn" style="background: #e11d48;" onclick="requestWithdraw()">Confirm Withdrawal 🚀</button>
                </div>
            </div>

            <!-- الربح من المشاهدة -->
            <div id="tab-watch" class="section">
                <div class="card">
                    <h3 id="txt-watch-title">▶️ Watch & Earn</h3>
                    <p id="txt-watch-desc" style="font-size: 13px; color: #cbd5e1;">Watch ads to earn bonus TRX points:</p>
                    <button id="txt-watch-btn" class="btn" style="background: #16a34a;" onclick="customAdAction()">Watch Ad & Earn 🚀</button>
                </div>
            </div>

            <!-- الشروط -->
            <div id="tab-terms" class="section">
                <div class="card">
                    <h3 id="txt-terms-title">📜 Terms & Conditions</h3>
                    <div id="txt-terms-content" class="terms-text">
                        1. Using Wi-Fi or VPN is strictly prohibited.<br>
                        2. Referrals are active only after the invited user completes an offer.<br>
                        3. 3% referral bonus is lifetime.<br>
                        4. You can save or change your TRX wallet anytime.
                    </div>
                </div>
            </div>

        </div>

        <script>
            let tg = window.Telegram.WebApp;
            tg.expand();

            let userId = 123456789;
            if (tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.id) {
                userId = tg.initDataUnsafe.user.id;
            }

            function toggleDrawer() {
                document.getElementById('drawer').classList.toggle('open');
                document.getElementById('overlay').classList.toggle('active');
            }

            function customAdAction() {
                alert("Your ad code / action goes here!");
            }

            function completeCustomAction(type) {
                fetch('/api/complete_offer', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: userId, action_type: type})
                })
                .then(res => res.json())
                .then(data => {
                    alert(data.message);
                    loadUserData();
                });
            }

            const translations = {
                en: { 
                    home: "🏠 Home", ref: "👥 Referrals", 
                    phoneSub: "📱 Phone Number Sub", installApps: "📲 Install Apps", registerSites: "🌐 Register Sites",
                    wallet: "💳 Wallet", withdraw: "💸 Withdraw", watch: "▶️ Watch & Earn", terms: "📜 Terms",
                    welcome: "Welcome: ", preview: "Preview Mode", menu: "Menu ⚙️",
                    balTitle: "Your Current TRX Balance", balDesc: "Continuous earning allows instant withdrawal upon reaching the minimum limit.",
                    refTitle: "👥 Active Referral System (3%)", refCountLbl: "Active Referrals:", refDesc: "Share your link and earn 3% lifetime profits:", copyBtn: "Copy Referral Link 🔗",
                    walletTitle: "💳 Wallet Management", walletDesc: "Enter your TRX wallet address:", walletPlaceholder: "Enter TRX address here...", saveBtn: "Save Address 💾", changeBtn: "Change Wallet 🔄", saveChangeBtn: "Save Changes 💾", walletSavedDesc: "Current saved address:",
                    withdrawTitle: "💸 Withdraw Earnings", walletLabel: "Registered Wallet Address:", noAddress: "No address added yet!", withdrawBtn: "Confirm Withdrawal 🚀",
                    watchTitle: "▶️ Watch & Earn", watchDesc: "Watch ads to earn bonus TRX points:", watchBtn: "Watch Ad & Earn 🚀",
                    termsTitle: "📜 Terms & Conditions", termsContent: "1. Using Wi-Fi or VPN is strictly prohibited.<br>2. Referrals are active only after the invited user completes an offer.<br>3. 3% referral bonus is lifetime.<br>4. You can save or change your TRX wallet anytime.",
                    warnTitle: "⚠️ Network Connection Warning", warnDesc: "Wi-Fi or VPN usage is strictly prohibited. Please use your Mobile Data only to proceed.",
                    navHome: "Home", navRef: "Referrals", navPhoneSub: "الربح من الاشتراك في رقم هاتف", navInstallApps: "الربح من تثبيت تطبيقات", navRegisterSites: "الربح من التسجيل في المواقع", navWallet: "Wallet", navWithdraw: "Withdraw", navWatch: "Watch & Earn", navTerms: "Terms"
                },
                ar: { 
                    home: "🏠 الرئيسية", ref: "👥 الإحالة", 
                    phoneSub: "📱 الربح من الاشتراك في رقم هاتف", installApps: "📲 الربح من تثبيت تطبيقات", registerSites: "🌐 الربح من التسجيل في المواقع",
                    wallet: "💳 المحفظة", withdraw: "💸 السحب", watch: "▶️ الربح من المشاهدة", terms: "📜 الشروط",
                    welcome: "مرحباً بك: ", preview: "وضع المعاينة التجريبي", menu: "القائمة ⚙️",
                    balTitle: "رصيدك الحالي من TRX", balDesc: "تجميعك المستمر يتيح لك السحب الفوري عند الوصول للحد الأدنى.",
                    refTitle: "👥 نظام الإحالات النشطة (3%)", refCountLbl: "عدد إحالاتك النشطة:", refDesc: "شارك رابطك وخذ 3% أرباح للأبد:", copyBtn: "نسخ رابط الإحالة 🔗",
                    walletTitle: "💳 إدارة المحفظة", walletDesc: "أدخل عنوان محفظة TRX الخاصة بك:", walletPlaceholder: "أدخل عنوان TRX هنا...", saveBtn: "حفظ العنوان 💾", changeBtn: "تغيير المحفظة 🔄", saveChangeBtn: "حفظ التغيير 💾", walletSavedDesc: "العنوان المحفوظ حالياً:",
                    withdrawTitle: "💸 سحب الأرباح", walletLabel: "عنوان المحفظة المسجل للسحب:", noAddress: "لم تقم بإضافة عنوان بعد!", withdrawBtn: "تأكيد طلب السحب 🚀",
                    watchTitle: "▶️ الربح من المشاهدة", watchDesc: "قم بمشاهدة الإعلانات لكسب نقاط TRX إضافية:", watchBtn: "مشاهدة الإعلان والربح 🚀",
                    termsTitle: "📜 الشروط والأحكام", termsContent: "1. يمنع منعاً باتاً استخدام الواي فاي أو الـ VPN.<br>2. لا تُحتسب الإحالة نشطة إلا بعد إتمام الشخص المدعو لعرض ناجح.<br>3. نسبة الإحالة (3%) تُحتسب للأبد.<br>4. يمكنك حفظ أو تغيير عنوان محفظة TRX بأي وقت.",
                    warnTitle: "⚠️ تنبيه شبكة الاتصال", warnDesc: "عذراً! يمنع استخدام الواي فاي أو الـ VPN. يرجى استخدام بيانات الهاتف المحمول (Mobile Data) فقط.",
                    navHome: "الرئيسية", navRef: "الإحالة", navPhoneSub: "الربح من الاشتراك في رقم هاتف", navInstallApps: "الربح من تثبيت تطبيقات", navRegisterSites: "الربح من التسجيل في المواقع", navWallet: "المحفظة", navWithdraw: "السحب", navWatch: "الربح من المشاهدة", navTerms: "الشروط"
                }
            };

            let currentLang = 'ar';
            let currentTitles = translations[currentLang];

            function changeLanguage(lang) {
                currentLang = lang;
                let t = translations[lang] || translations['en'];
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
                document.getElementById('txt-home-terms-title').innerText = t.termsTitle;
                document.getElementById('txt-home-terms-content').innerHTML = t.termsContent;
                document.getElementById('txt-ref-title').innerText = t.refTitle;
                document.getElementById('txt-ref-count-label').innerText = t.refCountLbl;
                document.getElementById('txt-ref-desc').innerText = t.refDesc;
                document.getElementById('txt-copy-btn').innerText = t.copyBtn;
                document.getElementById('txt-wallet-title').innerText = t.walletTitle;
                document.getElementById('wallet-desc').innerText = t.walletDesc;
                document.getElementById('trx-input').placeholder = t.walletPlaceholder;
                document.getElementById('wallet-btn').innerText = t.saveBtn;
                document.getElementById('txt-withdraw-title').innerText = t.withdrawTitle;
                document.getElementById('txt-wallet-label').innerText = t.walletLabel;
                document.getElementById('txt-withdraw-btn').innerText = t.withdrawBtn;
                document.getElementById('txt-watch-title').innerText = t.watchTitle;
                document.getElementById('txt-watch-desc').innerText = t.watchDesc;
                document.getElementById('txt-watch-btn').innerText = t.watchBtn;
                document.getElementById('txt-terms-title').innerText = t.termsTitle;
                document.getElementById('txt-terms-content').innerHTML = t.termsContent;
                document.getElementById('warn-title').innerText = t.warnTitle;
                document.getElementById('warn-desc').innerText = t.warnDesc;
                
                document.getElementById('nav-txt-home').innerText = t.home;
                document.getElementById('nav-txt-ref').innerText = t.ref;
                document.getElementById('nav-txt-phonesub').innerText = t.phoneSub;
                document.getElementById('nav-txt-installapps').innerText = t.installApps;
                document.getElementById('nav-txt-registersites').innerText = t.registerSites;
                document.getElementById('nav-txt-wallet').innerText = t.wallet;
                document.getElementById('nav-txt-withdraw').innerText = t.withdraw;
                document.getElementById('nav-txt-watch').innerText = t.watch;
                document.getElementById('nav-txt-terms').innerText = t.terms;

                if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
                    document.getElementById('welcome').innerText = t.welcome + (tg.initDataUnsafe.user.first_name || "User");
                } else {
                    document.getElementById('welcome').innerText = t.preview;
                }

                loadUserData();
            }

            document.getElementById('language-select').value = 'ar';
            changeLanguage('ar');

            function checkNetwork() {
                let warningScreen = document.getElementById('network-warning');
                let connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
                if (connection) {
                    if (connection.type === 'wifi' || connection.type === 'ethernet') {
                        warningScreen.style.display = 'flex';
                        return;
                    }
                }
                warningScreen.style.display = 'none';
            }

            checkNetwork();

            let savedTrxAddress = "";

            function loadUserData() {
                let t = translations[currentLang] || translations['en'];
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
                            btn.innerText = t.changeBtn;
                            desc.innerText = t.walletSavedDesc;
                        } else {
                            input.value = "";
                            input.readOnly = false;
                            btn.innerText = t.saveBtn;
                            desc.innerText = t.walletDesc;
                        }

                        document.getElementById('current-address').innerText = savedTrxAddress ? savedTrxAddress : t.noAddress;
                    })
                    .catch(err => console.error("Error:", err));
            }

            function handleWalletAction() {
                let t = translations[currentLang] || translations['en'];
                let input = document.getElementById('trx-input');
                let btn = document.getElementById('wallet-btn');
                let address = input.value.trim();

                if (!address) {
                    alert("الرجاء إدخال عنوان صحيح!");
                    return;
                }

                if (input.readOnly) {
                    input.readOnly = false;
                    input.focus();
                    btn.innerText = t.saveChangeBtn;
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
