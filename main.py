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
    return "TRX Bot with Multi-language Support is running! 🚀"

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
        lang_code = message.from_user.language_code or 'en'
        
        # تحديد اللغة (عربي أو إنجليزي افتراضي لبقية لغات العالم)
        is_arabic = lang_code.startswith('ar')

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

        # نصوص الشروط والأحكام حسب لغة تليجرام الخاصة بالمستخدم
        if is_arabic:
            terms_message = (
                "📜 **شروط وأحكام استخدام بوت TRX Earn:**\n\n"
                "1. يمنع استخدام الواي فاي (Wi-Fi) أو برامج الـ (VPN) نهائياً.\n"
                "2. لا تُحتسب الإحالة نشطة إلا بعد إتمام الشخص المدعو لعرض ناجح.\n"
                "3. نسبة الإحالة (3%) تُحتسب للأبد بناءً على نشاط الأصدقاء.\n"
                "4. يمكنك حفظ أو تغيير عنوان محفظة TRX الخاص بك بأي وقت.\n\n"
                "اضغط على الزر أدناه للموافقة وفتح التطبيق المصغر:"
            )
            btn_text = "أوافق وفتح التطبيق المصغر 🚀"
        else:
            terms_message = (
                "📜 **TRX Earn Bot Terms & Conditions:**\n\n"
                "1. Using Wi-Fi or VPN is strictly prohibited.\n"
                "2. Referrals are active only after the invited user completes an offer.\n"
                "3. 3% referral bonus is lifetime.\n"
                "4. You can save or change your TRX wallet anytime.\n\n"
                "Click the button below to agree and open the Mini App:"
            )
            btn_text = "I Agree & Open Mini App 🚀"

        markup = telebot.types.InlineKeyboardMarkup()
        web_app = telebot.types.WebAppInfo(url=f"{RENDER_URL}/webapp")
        webapp_button = telebot.types.InlineKeyboardButton(btn_text, web_app=web_app)
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
    return jsonify({"success": True, "message": "تم حفظ وتحديث محفظة TRX بنجاح!"})

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
            input:read-only {
                background: #1e293b;
                color: #94a3b8;
                border-color: #334155;
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

        <!-- شاشة حظر الواي فاي والـ VPN -->
        <div id="network-warning" style="display: none;">
            <h2 id="warn-title" style="color: #ef4444;">⚠️ تنبيه شبكة الاتصال</h2>
            <p id="warn-desc" style="font-size: 14px; color: #cbd5e1; line-height: 1.6; margin: 15px 0;">
                يرجى إيقاف تشغيل الـ VPN واستخدام بيانات الهاتف المحمول (Mobile Data) حصراً. لا يُسمح باستخدام الواي فاي أو الـ VPN.
            </p>
            <button class="btn" style="background: #e11d48;" onclick="checkNetwork()">إعادة الفحص 🔄</button>
        </div>

        <div class="container">
            <h2 id="page-title">💰 الرصيد</h2>
            <p id="welcome" style="text-align:center; font-size: 13px; color: #94a3b8;"></p>

            <div id="tab-balance" class="section active">
                <div class="card">
                    <h3 id="txt-bal-title">رصيدك الحالي من TRX</h3>
                    <p id="balance-val" style="font-size: 26px; font-weight: bold; color: #4ade80;">0.0 TRX</p>
                    <p id="txt-bal-desc" style="font-size: 12px; color: #94a3b8;">تجميعك المستمر يتيح لك السحب الفوري عند الوصول للحد الأدنى.</p>
                </div>
            </div>

            <div id="tab-ref" class="section">
                <div class="card">
                    <h3 id="txt-ref-title">👥 نظام الإحالات النشطة (3%)</h3>
                    <p><span id="txt-ref-count-label">عدد إحالاتك النشطة:</span> <span id="ref-count" style="color: #38bdf8; font-weight: bold;">0</span></p>
                    <p id="txt-ref-desc" style="font-size: 13px; color: #94a3b8;">شارك رابطك وخذ 3% أرباح للأبد (لا تُحتسب إلا بعد إتمام أصدقائك للعرض):</p>
                    <input type="text" id="ref-link" readonly onclick="this.select();">
                    <button id="txt-copy-btn" class="btn" onclick="copyRefLink()">نسخ رابط الإحالة 🔗</button>
                </div>
            </div>

            <div id="tab-offers" class="section">
                <div class="card">
                    <h3 id="txt-offer-title">🎯 عروض تجميع النقاط</h3>
                    <p id="txt-offer-desc" style="font-size: 13px; color: #cbd5e1;">قم بإتمام عرض التحقق أدناه لتصبح إحالتك نشطة:</p>
                    <button id="txt-open-offer" class="btn" style="background: #16a34a;" onclick="window.open('http://bc.vc/Dc4Boi8', '_blank')">فتح رابط العرض 🚀</button>
                    <button id="txt-confirm-offer" class="btn" style="background: #eab308; margin-top: 10px;" onclick="completeOffer()">تأكيد إتمام العرض ✅</button>
                </div>
            </div>

            <div id="tab-wallet" class="section">
                <div class="card">
                    <h3 id="txt-wallet-title">💳 إدارة المحفظة</h3>
                    <p id="wallet-desc" style="font-size: 13px; color: #94a3b8;">أدخل عنوان محفظة TRX الخاصة بك:</p>
                    <input type="text" id="trx-input" placeholder="أدخل عنوان TRX هنا...">
                    <button id="wallet-btn" class="btn" onclick="handleWalletAction()">حفظ العنوان 💾</button>
                </div>
            </div>

            <div id="tab-withdraw" class="section">
                <div class="card">
                    <h3 id="txt-withdraw-title">💸 سحب الأرباح</h3>
                    <p id="txt-wallet-label" style="font-size: 13px; color: #94a3b8;">عنوان المحفظة المسجل للسحب:</p>
                    <p id="current-address" style="font-size: 12px; color: #fbbf24; word-break: break-all;"></p>
                    <button id="txt-withdraw-btn" class="btn" style="background: #e11d48;" onclick="requestWithdraw()">تأكيد طلب السحب 🚀</button>
                </div>
            </div>

            <div id="tab-terms" class="section">
                <div class="card">
                    <h3 id="txt-terms-title">📜 الشروط والأحكام</h3>
                    <div id="txt-terms-content" class="terms-text">
                        1. يمنع منعاً باتاً استخدام الواي فاي أو الـ VPN.<br>
                        2. لا تُحتسب الإحالة نشطة إلا بعد إتمام الشخص المدعو لعرض ناجح.<br>
                        3. نسبة الإحالة (3%) تُحتسب للأبد بناءً على نشاط الإحالات.<br>
                        4. يمكنك حفظ أو تغيير عنوان محفظة TRX بأي وقت.
                    </div>
                </div>
            </div>

        </div>

        <div class="nav-bar">
            <button class="nav-item active" onclick="switchTab('balance', navTitles.balance, this)"><span>💰</span><span id="nav-txt-bal">الرصيد</span></button>
            <button class="nav-item" onclick="switchTab('ref', navTitles.ref, this)"><span>👥</span><span id="nav-txt-ref">الإحالة</span></button>
            <button class="nav-item" onclick="switchTab('offers', navTitles.offers, this)"><span>🎯</span><span id="nav-txt-offers">العروض</span></button>
            <button class="nav-item" onclick="switchTab('wallet', navTitles.wallet, this)"><span>💳</span><span id="nav-txt-wallet">المحفظة</span></button>
            <button class="nav-item" onclick="switchTab('withdraw', navTitles.withdraw, this)"><span>💸</span><span id="nav-txt-withdraw">السحب</span></button>
            <button class="nav-item" onclick="switchTab('terms', navTitles.terms, this)"><span>📜</span><span id="nav-txt-terms">الشروط</span></button>
        </div>

        <script>
            let tg = window.Telegram.WebApp;
            tg.expand();

            let userLang = 'ar';
            if (tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.language_code) {
                userLang = tg.initDataUnsafe.user.language_code.startsWith('ar') ? 'ar' : 'en';
            } else {
                userLang = navigator.language.startsWith('ar') ? 'ar' : 'en';
            }

            if (userLang === 'en') {
                document.getElementById('html-root').setAttribute('dir', 'ltr');
                document.getElementById('html-root').setAttribute('lang', 'en');
            } else {
                document.getElementById('html-root').setAttribute('dir', 'rtl');
                document.getElementById('html-root').setAttribute('lang', 'ar');
            }

            const translations = {
                ar: {
                    welcome: "مرحباً بك: ",
                    preview: "وضع المعاينة التجريبي",
                    balance: "💰 الرصيد",
                    ref: "👥 الإحالات",
                    offers: "🎯 العروض",
                    wallet: "💳 المحفظة",
                    withdraw: "💸 السحب",
                    terms: "📜 الشروط",
                    balTitle: "رصيدك الحالي من TRX",
                    balDesc: "تجميعك المستمر يتيح لك السحب الفوري عند الوصول للحد الأدنى.",
                    refTitle: "👥 نظام الإحالات النشطة (3%)",
                    refCountLbl: "عدد إحالاتك النشطة:",
                    refDesc: "شارك رابطك وخذ 3% أرباح للأبد (لا تُحتسب إلا بعد إتمام أصدقائك للعرض):",
                    copyBtn: "نسخ رابط الإحالة 🔗",
                    offerTitle: "🎯 عروض تجميع النقاط",
                    offerDesc: "قم بإتمام عرض التحقق أدناه لتصبح إحالتك نشطة:",
                    openOffer: "فتح رابط العرض 🚀",
                    confirmOffer: "تأكيد إتمام العرض ✅",
                    walletTitle: "💳 إدارة المحفظة",
                    walletDesc: "أدخل عنوان محفظة TRX الخاصة بك:",
                    walletPlaceholder: "أدخل عنوان TRX هنا...",
                    saveBtn: "حفظ العنوان 💾",
                    changeBtn: "تغيير المحفظة 🔄",
                    saveChangeBtn: "حفظ التغيير 💾",
                    walletSavedDesc: "العنوان المحفوظ حالياً (اضغط تغيير المحفظة لتعديله):",
                    withdrawTitle: "💸 سحب الأرباح",
                    walletLabel: "عنوان المحفظة المسجل للسحب:",
                    noAddress: "لم تقم بإضافة عنوان بعد!",
                    withdrawBtn: "تأكيد طلب السحب 🚀",
                    termsTitle: "📜 الشروط والأحكام",
                    termsContent: "1. يمنع منعاً باتاً استخدام الواي فاي أو الـ VPN.<br>2. لا تُحتسب الإحالة نشطة إلا بعد إتمام الشخص المدعو لعرض ناجح.<br>3. نسبة الإحالة (3%) تُحتسب وتُضاف للأبد بناءً على نشاط الإحالات.<br>4. يمكنك حفظ أو تغيير عنوان محفظة TRX بأي وقت.",
                    warnTitle: "⚠️ تنبيه شبكة الاتصال",
                    warnDesc: "عذراً! يمنع استخدام الواي فاي (Wi-Fi) أو برامج الـ (VPN). يرجى استخدام بيانات الهاتف المحمول (Mobile Data) الخاصة بك فقط للمتابعة.",
                    navBal: "الرصيد", navRef: "الإحالة", navOffers: "العروض", navWallet: "المحفظة", navWithdraw: "السحب", navTerms: "الشروط"
                },
                en: {
                    welcome: "Welcome: ",
                    preview: "Preview Mode",
                    balance: "💰 Balance",
                    ref: "👥 Referrals",
                    offers: "🎯 Offers",
                    wallet: "💳 Wallet",
                    withdraw: "💸 Withdraw",
                    terms: "📜 Terms",
                    balTitle: "Your Current TRX Balance",
                    balDesc: "Continuous earning allows instant withdrawal upon reaching the minimum limit.",
                    refTitle: "👥 Active Referral System (3%)",
                    refCountLbl: "Active Referrals:",
                    refDesc: "Share your link and earn 3% lifetime profits (Counted after friends complete an offer):",
                    copyBtn: "Copy Referral Link 🔗",
                    offerTitle: "🎯 Point Earning Offers",
                    offerDesc: "Complete the verification offer below to make your referral active:",
                    openOffer: "Open Offer Link 🚀",
                    confirmOffer: "Confirm Offer Completion ✅",
                    walletTitle: "💳 Wallet Management",
                    walletDesc: "Enter your TRX wallet address:",
                    walletPlaceholder: "Enter TRX address here...",
                    saveBtn: "Save Address 💾",
                    changeBtn: "Change Wallet 🔄",
                    saveChangeBtn: "Save Changes 💾",
                    walletSavedDesc: "Current saved address (click change wallet to edit):",
                    withdrawTitle: "💸 Withdraw Earnings",
                    walletLabel: "Registered Wallet Address:",
                    noAddress: "No address added yet!",
                    withdrawBtn: "Confirm Withdrawal 🚀",
                    termsTitle: "📜 Terms & Conditions",
                    termsContent: "1. Using Wi-Fi or VPN is strictly prohibited.<br>2. Referrals are active only after the invited user completes an offer.<br>3. 3% referral bonus is lifetime.<br>4. You can save or change your TRX wallet anytime.",
                    warnTitle: "⚠️ Network Connection Warning",
                    warnDesc: "Sorry! Wi-Fi or VPN usage is prohibited. Please use your Mobile Data only to proceed.",
                    navBal: "Balance", navRef: "Referrals", navOffers: "Offers", navWallet: "Wallet", navWithdraw: "Withdraw", navTerms: "Terms"
                }
            };

            let t = translations[userLang];
            let navTitles = { balance: t.balance, ref: t.ref, offers: t.offers, wallet: t.wallet, withdraw: t.withdraw, terms: t.terms };

            document.getElementById('page-title').innerText = t.balance;
            document.getElementById('txt-bal-title').innerText = t.balTitle;
            document.getElementById('txt-bal-desc').innerText = t.balDesc;
            document.getElementById('txt-ref-title').innerText = t.refTitle;
            document.getElementById('txt-ref-count-label').innerText = t.refCountLbl;
            document.getElementById('txt-ref-desc').innerText = t.refDesc;
            document.getElementById('txt-copy-btn').innerText = t.copyBtn;
            document.getElementById('txt-offer-title').innerText = t.offerTitle;
            document.getElementById('txt-offer-desc').innerText = t.offerDesc;
            document.getElementById('txt-open-offer').innerText = t.openOffer;
            document.getElementById('txt-confirm-offer').innerText = t.confirmOffer;
            document.getElementById('txt-wallet-title').innerText = t.walletTitle;
            document.getElementById('wallet-desc').innerText = t.walletDesc;
            document.getElementById('trx-input').placeholder = t.walletPlaceholder;
            document.getElementById('wallet-btn').innerText = t.saveBtn;
            document.getElementById('txt-withdraw-title').innerText = t.withdrawTitle;
            document.getElementById('txt-wallet-label').innerText = t.walletLabel;
            document.getElementById('txt-withdraw-btn').innerText = t.withdrawBtn;
            document.getElementById('txt-terms-title').innerText = t.termsTitle;
            document.getElementById('txt-terms-content').innerHTML = t.termsContent;
            document.getElementById('warn-title').innerText = t.warnTitle;
            document.getElementById('warn-desc').innerText = t.warnDesc;
            document.getElementById('nav-txt-bal').innerText = t.navBal;
            document.getElementById('nav-txt-ref').innerText = t.navRef;
            document.getElementById('nav-txt-offers').innerText = t.navOffers;
            document.getElementById('nav-txt-wallet').innerText = t.navWallet;
            document.getElementById('nav-txt-withdraw').innerText = t.navWithdraw;
            document.getElementById('nav-txt-terms').innerText = t.navTerms;

            let userId = 123456789;
            if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
                userId = tg.initDataUnsafe.user.id;
                document.getElementById('welcome').innerText = t.welcome + (tg.initDataUnsafe.user.first_name || "User");
            } else {
                document.getElementById('welcome').innerText = t.preview;
            }

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
                            btn.style.background = "#0284c7";
                            desc.innerText = t.walletSavedDesc;
                        } else {
                            input.value = "";
                            input.readOnly = false;
                            btn.innerText = t.saveBtn;
                            btn.style.background = "#16a34a";
                            desc.innerText = t.walletDesc;
                        }

                        document.getElementById('current-address').innerText = savedTrxAddress ? savedTrxAddress : t.noAddress;
                    })
                    .catch(err => console.error("Error:", err));
            }

            loadUserData();

            function handleWalletAction() {
                let input = document.getElementById('trx-input');
                let btn = document.getElementById('wallet-btn');
                let address = input.value.trim();

                if (!address) {
                    alert(userLang === 'ar' ? "الرجاء إدخال عنوان صحيح!" : "Please enter a valid address!");
                    return;
                }

                if (input.readOnly) {
                    input.readOnly = false;
                    input.focus();
                    btn.innerText = t.saveChangeBtn;
                    btn.style.background = "#16a34a";
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
                alert(userLang === 'ar' ? "تم نسخ رابط الإحالة بنجاح! 📋" : "Referral link copied successfully! 📋");
            }

            function completeOffer() {
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
