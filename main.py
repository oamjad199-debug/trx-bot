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
        <!-- كود Monetag SDK الذي أرسلته -->
        <script src='//libtl.com/sdk.js' data-zone='12130531' data-sdk='show_12130531'></script>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                font-family: Tahoma, sans-serif;
                background-color: #0f172a;
                color: #ffffff;
                margin: 0;
                padding: 10px;
                padding-bottom: 135px;
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
            #ref-link {
                background: #ffffff !important;
                color: #0f172a !important;
                font-weight: bold;
                font-size: 11px;
                direction: ltr !important;
                text-align: center !important;
            }
            input:read-only {
                border-color: #475569;
            }
            .nav-bar {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: #0f172a;
                border-top: 1px solid #334155;
                display: flex;
                justify-content: space-between;
                padding: 6px 2px;
                z-index: 100;
            }
            .nav-item {
                background: none;
                border: none;
                color: #94a3b8;
                font-size: 9px;
                cursor: pointer;
                text-align: center;
                flex: 1;
                padding: 0 1px;
                white-space: nowrap;
                overflow: hidden;
            }
            .nav-item.active {
                color: #38bdf8;
                font-weight: bold;
            }
            .nav-item span { display: block; font-size: 14px; margin-bottom: 2px; }
            
            .footer-lang-container {
                position: fixed;
                bottom: 48px;
                left: 0;
                right: 0;
                background: #1e293b;
                border-top: 1px solid #334155;
                padding: 5px 15px;
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 99;
            }
            .footer-lang-container select {
                background: #0f172a;
                color: white;
                border: 1px solid #475569;
                padding: 3px 8px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 11px;
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

        <div class="container">
            <h2 id="page-title">💰 Balance</h2>
            <p id="welcome" style="text-align:center; font-size: 13px; color: #94a3b8;"></p>

            <div id="tab-balance" class="section active">
                <div class="card">
                    <h3 id="txt-bal-title">Your Current TRX Balance</h3>
                    <p id="balance-val" style="font-size: 26px; font-weight: bold; color: #4ade80;">0.0 TRX</p>
                    <p id="txt-bal-desc" style="font-size: 12px; color: #94a3b8;">Continuous earning allows instant withdrawal upon reaching the minimum limit.</p>
                </div>
            </div>

            <div id="tab-ref" class="section">
                <div class="card">
                    <h3 id="txt-ref-title">👥 Active Referral System (3%)</h3>
                    <p><span id="txt-ref-count-label">Active Referrals:</span> <span id="ref-count" style="color: #38bdf8; font-weight: bold;">0</span></p>
                    <p id="txt-ref-desc" style="font-size: 13px; color: #94a3b8;">Share your link and earn 3% lifetime profits:</p>
                    <input type="text" id="ref-link" readonly onclick="this.select();">
                    <button id="txt-copy-btn" class="btn" onclick="copyRefLink()">Copy Referral Link 🔗</button>
                </div>
            </div>

            <div id="tab-offers" class="section">
                <div class="card">
                    <h3 id="txt-offer-title">🎯 Point Earning Offers</h3>
                    <p id="txt-offer-desc" style="font-size: 13px; color: #cbd5e1;">Complete the verification offer below to make your referral active:</p>
                    <!-- تم ربط زر فتح العرض بعرض إعلان المكافأة الذي أرسلته -->
                    <button id="txt-open-offer" class="btn" style="background: #16a34a;" onclick="watchAdAndComplete()">Watch Ad & Earn 🚀</button>
                    <button id="txt-confirm-offer" class="btn" style="background: #eab308; margin-top: 10px;" onclick="completeOffer()">Confirm Completion ✅</button>
                </div>
            </div>

            <div id="tab-wallet" class="section">
                <div class="card">
                    <h3 id="txt-wallet-title">💳 Wallet Management</h3>
                    <p id="wallet-desc" style="font-size: 13px; color: #94a3b8;">Enter your TRX wallet address:</p>
                    <input type="text" id="trx-input" placeholder="Enter TRX address here...">
                    <button id="wallet-btn" class="btn" onclick="handleWalletAction()">Save Address 💾</button>
                </div>
            </div>

            <div id="tab-withdraw" class="section">
                <div class="card">
                    <h3 id="txt-withdraw-title">💸 Withdraw Earnings</h3>
                    <p id="txt-wallet-label" style="font-size: 13px; color: #94a3b8;">Registered Wallet Address:</p>
                    <p id="current-address" style="font-size: 12px; color: #fbbf24; word-break: break-all;"></p>
                    <button id="txt-withdraw-btn" class="btn" style="background: #e11d48;" onclick="requestWithdraw()">Confirm Withdrawal 🚀</button>
                </div>
            </div>

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

        <div class="footer-lang-container">
            <span style="font-size: 11px; color: #94a3b8; margin-inline-end: 6px;">🌐 Language:</span>
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

        <div class="nav-bar">
            <button class="nav-item active" onclick="switchTab('balance', currentTitles.balance, this)"><span>💰</span><span id="nav-txt-bal">Balance</span></button>
            <button class="nav-item" onclick="switchTab('ref', currentTitles.ref, this)"><span>👥</span><span id="nav-txt-ref">Referrals</span></button>
            <button class="nav-item" onclick="switchTab('offers', currentTitles.offers, this)"><span>🎯</span><span id="nav-txt-offers">Offers</span></button>
            <button class="nav-item" onclick="switchTab('wallet', currentTitles.wallet, this)"><span>💳</span><span id="nav-txt-wallet">Wallet</span></button>
            <button class="nav-item" onclick="switchTab('withdraw', currentTitles.withdraw, this)"><span>💸</span><span id="nav-txt-withdraw">Withdraw</span></button>
            <button class="nav-item" onclick="switchTab('terms', currentTitles.terms, this)"><span>📜</span><span id="nav-txt-terms">Terms</span></button>
        </div>

        <script>
            let tg = window.Telegram.WebApp;
            tg.expand();

            let userId = 123456789;
            if (tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.id) {
                userId = tg.initDataUnsafe.user.id;
            }

            const translations = {
                en: { 
                    balance: "💰 Balance", ref: "👥 Referrals", offers: "🎯 Offers", wallet: "💳 Wallet", withdraw: "💸 Withdraw", terms: "📜 Terms",
                    welcome: "Welcome: ", preview: "Preview Mode",
                    balTitle: "Your Current TRX Balance", balDesc: "Continuous earning allows instant withdrawal upon reaching the minimum limit.",
                    refTitle: "👥 Active Referral System (3%)", refCountLbl: "Active Referrals:", refDesc: "Share your link and earn 3% lifetime profits:", copyBtn: "Copy Referral Link 🔗",
                    offerTitle: "🎯 Point Earning Offers", offerDesc: "Complete the verification offer below to make your referral active:", openOffer: "Watch Ad & Earn 🚀", confirmOffer: "Confirm Completion ✅",
                    walletTitle: "💳 Wallet Management", walletDesc: "Enter your TRX wallet address:", walletPlaceholder: "Enter TRX address here...", saveBtn: "Save Address 💾", changeBtn: "Change Wallet 🔄", saveChangeBtn: "Save Changes 💾", walletSavedDesc: "Current saved address:",
                    withdrawTitle: "💸 Withdraw Earnings", walletLabel: "Registered Wallet Address:", noAddress: "No address added yet!", withdrawBtn: "Confirm Withdrawal 🚀",
                    termsTitle: "📜 Terms & Conditions", termsContent: "1. Using Wi-Fi or VPN is strictly prohibited.<br>2. Referrals are active only after the invited user completes an offer.<br>3. 3% referral bonus is lifetime.<br>4. You can save or change your TRX wallet anytime.",
                    warnTitle: "⚠️ Network Connection Warning", warnDesc: "Wi-Fi or VPN usage is strictly prohibited. Please use your Mobile Data only to proceed.",
                    navBal: "Balance", navRef: "Referrals", navOffers: "Offers", navWallet: "Wallet", navWithdraw: "Withdraw", navTerms: "Terms"
                },
                es: { 
                    balance: "💰 Saldo", ref: "👥 Referidos", offers: "🎯 Ofertas", wallet: "💳 Billetera", withdraw: "💸 Retirar", terms: "📜 Términos",
                    welcome: "Bienvenido: ", preview: "Modo de Vista Previa",
                    balTitle: "Tu Saldo Actual de TRX", balDesc: "Las ganancias continuas permiten el retiro instantáneo al alcanzar el mínimo.",
                    refTitle: "👥 Sistema de Referidos Activos (3%)", refCountLbl: "Referidos Activos:", refDesc: "Comparte tu enlace y gana 3% de por vida:", copyBtn: "Copiar Enlace 🔗",
                    offerTitle: "🎯 Ofertas de Puntos", offerDesc: "Completa la oferta de verificación a continuación:", openOffer: "Ver Anuncio y Ganar 🚀", confirmOffer: "Confirmar Oferta ✅",
                    walletTitle: "💳 Gestión de Billetera", walletDesc: "Ingresa tu dirección de billetera TRX:", walletPlaceholder: "Ingresa TRX aquí...", saveBtn: "Guardar 💾", changeBtn: "Cambiar 🔄", saveChangeBtn: "Guardar Cambios 💾", walletSavedDesc: "Dirección guardada actual:",
                    withdrawTitle: "💸 Retirar Ganancias", walletLabel: "Dirección registrada:", noAddress: "¡Aún no hay dirección!", withdrawBtn: "Confirmar Retiro 🚀",
                    termsTitle: "📜 Términos y Condiciones", termsContent: "1. El uso de Wi-Fi o VPN está estrictamente prohibido.<br>2. Los referidos son activos tras completar una oferta.<br>3. Bono del 3% de por vida.<br>4. Puedes cambiar tu billetera TRX cuando quieras.",
                    warnTitle: "⚠️ Advertencia de Red", warnDesc: "¡El uso de Wi-Fi o VPN está prohibido! Usa tus datos móviles (Mobile Data).",
                    navBal: "Saldo", navRef: "Referidos", navOffers: "Ofertas", navWallet: "Billetera", navWithdraw: "Retirar", navTerms: "Términos"
                },
                de: { 
                    balance: "💰 Guthaben", ref: "👥 Empfehlungen", offers: "🎯 Angebote", wallet: "💳 Geldbörse", withdraw: "💸 Auszahlen", terms: "📜 AGB",
                    welcome: "Willkommen: ", preview: "Vorschau-Modus",
                    balTitle: "Ihr aktuelles TRX-Guthaben", balDesc: "Kontinuierliches Verdienen ermöglicht sofortige Auszahlung.",
                    refTitle: "👥 Aktives Empfehlungssystem (3%)", refCountLbl: "Aktive Empfehlungen:", refDesc: "Teilen Sie Ihren Link und verdienen Sie 3%:", copyBtn: "Link kopieren 🔗",
                    offerTitle: "🎯 Punkte-Angebote", offerDesc: "Schließen Sie das Verifizierungsangebot ab:", openOffer: "Anzeige ansehen 🚀", confirmOffer: "Bestätigen ✅",
                    walletTitle: "💳 Wallet-Verwaltung", walletDesc: "Geben Sie Ihre TRX-Adresse ein:", walletPlaceholder: "TRX-Adresse eingeben...", saveBtn: "Speichern 💾", changeBtn: "Ändern 🔄", saveChangeBtn: "Änderung speichern 💾", walletSavedDesc: "Aktuelle Adresse:",
                    withdrawTitle: "💸 Guthaben auszahlen", walletLabel: "Registrierte Adresse:", noAddress: "Keine Adresse hinzugefügt!", withdrawBtn: "Auszahlung bestätigen 🚀",
                    termsTitle: "📜 Geschäftsbedingungen", termsContent: "1. WLAN oder VPN ist strengstens verboten.<br>2. Empfehlungen gelten nach erfolgreichem Angebot.<br>3. 3% Bonus auf Lebenszeit.<br>4. Wallet jederzeit änderbar.",
                    warnTitle: "⚠️ Netzwerk-Warnung", warnDesc: "WLAN oder VPN sind verboten! Bitte nutzen Sie mobile Daten (Mobile Data).",
                    navBal: "Guthaben", navRef: "Empfehl.", navOffers: "Angebote", navWallet: "Wallet", navWithdraw: "Auszahlen", navTerms: "AGB"
                },
                fr: { 
                    balance: "💰 Solde", ref: "👥 Parrainages", offers: "🎯 Offres", wallet: "💳 Portefeuille", withdraw: "💸 Retirer", terms: "📜 Conditions",
                    welcome: "Bienvenue : ", preview: "Mode Aperçu",
                    balTitle: "Votre solde TRX actuel", balDesc: "Gagnez et retirez instantanément.",
                    refTitle: "👥 Système de parrainage (3%)", refCountLbl: "Filleuls actifs :", refDesc: "Partagez votre lien et gagnez 3% à vie :", copyBtn: "Copier le lien 🔗",
                    offerTitle: "🎯 Offres de points", offerDesc: "Complétez l'offre de vérification ci-dessous :", openOffer: "Voir l'annonce 🚀", confirmOffer: "Confirmer ✅",
                    walletTitle: "💳 Gestion du portefeuille", walletDesc: "Entrez votre adresse TRX :", walletPlaceholder: "Entrez l'adresse TRX...", saveBtn: "Enregistrer 💾", changeBtn: "Modifier 🔄", saveChangeBtn: "Enregistrer 💾", walletSavedDesc: "Adresse enregistrée :",
                    withdrawTitle: "💸 Retirer les gains", walletLabel: "Adresse enregistrée :", noAddress: "Aucune adresse !", withdrawBtn: "Confirmer le retrait 🚀",
                    termsTitle: "📜 Conditions Générales", termsContent: "1. L'utilisation du Wi-Fi ou d'un VPN est interdite.<br>2. Les parrainages sont actifs après une offre.<br>3. Bonus de 3% à vie.<br>4. Modifiez votre portefeuille à tout moment.",
                    warnTitle: "⚠️ Alerte Réseau", warnDesc: "Le Wi-Fi ou les VPN sont interdits ! Utilisez vos données mobiles (Mobile Data).",
                    navBal: "Solde", navRef: "Parrainage", navOffers: "Offres", navWallet: "Portefeuille", navWithdraw: "Retirer", navTerms: "Termes"
                },
                ru: { 
                    balance: "💰 Баланс", ref: "👥 Рефералы", offers: "🎯 Офферы", wallet: "💳 Кошелек", withdraw: "💸 Вывод", terms: "📜 Условия",
                    welcome: "Добро пожаловать: ", preview: "Режим предпросмотра",
                    balTitle: "Ваш текущий баланс TRX", balDesc: "Накапливайте и выводите мгновенно.",
                    refTitle: "👥 Реферальная система (3%)", refCountLbl: "Активные рефералы:", refDesc: "Делитесь ссылкой и получайте 3% навсегда:", copyBtn: "Копировать ссылку 🔗",
                    offerTitle: "🎯 Зарабатывайте баллы", offerDesc: "Выполните верификационный оффер ниже:", openOffer: "Смотреть рекламу 🚀", confirmOffer: "Подтвердить ✅",
                    walletTitle: "💳 Управление кошельком", walletDesc: "Введите адрес вашего TRX кошелька:", walletPlaceholder: "Введите TRX адрес...", saveBtn: "Сохранить 💾", changeBtn: "Изменить 🔄", saveChangeBtn: "Сохранить 💾", walletSavedDesc: "Текущий адрес:",
                    withdrawTitle: "💸 Вывод средств", walletLabel: "Зарегистрированный адрес:", noAddress: "Адрес не добавлен!", withdrawBtn: "Подтвердить вывод 🚀",
                    termsTitle: "📜 Условия использования", termsContent: "1. Использование Wi-Fi или VPN строго запрещено.<br>2. Рефералы активируются после выполнения оффера.<br>3. 3% бонус навсегда.<br>4. Изменяйте кошелек в любое время.",
                    warnTitle: "⚠️ Предупреждение сети", warnDesc: "Использование Wi-Fi или VPN запрещено! Используйте мобильные данные (Mobile Data).",
                    navBal: "Баланс", navRef: "Рефералы", navOffers: "Офферы", navWallet: "Кошелек", navWithdraw: "Вывод", navTerms: "Условия"
                },
                pt: { 
                    balance: "💰 Saldo", ref: "👥 Indicações", offers: "🎯 Ofertas", wallet: "💳 Carteira", withdraw: "💸 Sacar", terms: "📜 Termos",
                    welcome: "Bem-vindo: ", preview: "Modo de Visualização",
                    balTitle: "Seu Saldo TRX Atual", balDesc: "Ganhos contínuos permitem saque instantâneo.",
                    refTitle: "👥 Sistema de Indicações (3%)", refCountLbl: "Indicações Ativas:", refDesc: "Compartilhe seu link وganhe 3% vitalício:", copyBtn: "Copiar Link 🔗",
                    offerTitle: "🎯 Ofertas de Pontos", offerDesc: "Complete a oferta de verificação abaixo:", openOffer: "Ver Anúncio 🚀", confirmOffer: "Confirmar ✅",
                    walletTitle: "💳 Gestão da Carteira", walletDesc: "Insira seu endereço de carteira TRX:", walletPlaceholder: "Insira o TRX aqui...", saveBtn: "Salvar 💾", changeBtn: "Alterar 🔄", saveChangeBtn: "Salvar 💾", walletSavedDesc: "Endereço atual:",
                    withdrawTitle: "💸 Sacar Ganhos", walletLabel: "Endereço registrado:", noAddress: "Nenhum endereço adicionado!", withdrawBtn: "Confirmar Saque 🚀",
                    termsTitle: "📜 Termos e Condições", termsContent: "1. O uso de Wi-Fi أو VPN é estritamente proibido.<br>2. Indicações ativas após conclusão da oferta.<br>3. Bônus de 3% vitalício.<br>4. Altere sua carteira quando quiser.",
                    warnTitle: "⚠️ Alerta de Rede", warnDesc: "Uso de Wi-Fi أو VPN proibido! Use apenas seus dados móveis (Mobile Data).",
                    navBal: "Saldo", navRef: "Indicações", navOffers: "Ofertas", navWallet: "Carteira", navWithdraw: "Sacar", navTerms: "Termos"
                },
                nl: { 
                    balance: "💰 Saldo", ref: "👥 Referrals", offers: "🎯 Aanbiedingen", wallet: "💳 Portemonnee", withdraw: "💸 Opnemen", terms: "📜 Voorwaarden",
                    welcome: "Welkom: ", preview: "Voorbeeldmodus",
                    balTitle: "Jouw TRX Saldo", balDesc: "Direct opnemen bij het minimum.",
                    refTitle: "👥 Referral Systeem (3%)", refCountLbl: "Actieve Referrals:", refDesc: "Deel je link en verdien 3%:", copyBtn: "Kopieer Link 🔗",
                    offerTitle: "🎯 Verdien Aanbiedingen", offerDesc: "Voltooi de verificatie hieronder:", openOffer: "Bekijk Advertentie 🚀", confirmOffer: "Bevestigen ✅",
                    walletTitle: "💳 Portemonnee Beheer", walletDesc: "Voer je TRX adres in:", walletPlaceholder: "Voer TRX adres in...", saveBtn: "Opslaan 💾", changeBtn: "Wijzigen 🔄", saveChangeBtn: "Opslaan 💾", walletSavedDesc: "Huidig adres:",
                    withdrawTitle: "💸 Saldo Opnemen", walletLabel: "Geregistreerd adres:", noAddress: "Geen adres toegevoegd!", withdrawBtn: "Bevestig Opname 🚀",
                    termsTitle: "📜 Voorwaarden", termsContent: "1. Wi-Fi أو VPN gebruik is streng verboden.<br>2. Referrals zijn actief na voltooiing.<br>3. 3% levenslange bonus.<br>4. Wijzig je wallet wanneer je wilt.",
                    warnTitle: "⚠️ Netwerk Waarschuwing", warnDesc: "Wi-Fi أو VPN is verboden! Gebruik uitsluitend mobiele data (Mobile Data).",
                    navBal: "Saldo", navRef: "Referrals", navOffers: "Offers", navWallet: "Wallet", navWithdraw: "Opnemen", navTerms: "Voorwaarde"
                },
                pl: { 
                    balance: "💰 Saldo", ref: "👥 Polecenia", offers: "🎯 Oferty", wallet: "💳 Portfel", withdraw: "💸 Wypłata", terms: "📜 Regulamin",
                    welcome: "Witaj: ", preview: "Tryb podglądu",
                    balTitle: "Twoje saldo TRX", balDesc: "Ciągłe zarobki i natychmiastowa wypłata.",
                    refTitle: "👥 System poleceń (3%)", refCountLbl: "Aktywne polecenia:", refDesc: "Udostępnij link وzarabiaj 3%:", copyBtn: "Kopiuj link 🔗",
                    offerTitle: "🎯 Oferty punktowe", offerDesc: "Ukończ ofertę weryfikacyjną poniżej:", openOffer: "Oglądaj reklamę 🚀", confirmOffer: "Potwierdź ✅",
                    walletTitle: "💳 Zarządzanie portfelem", walletDesc: "Wpisz adres portfela TRX:", walletPlaceholder: "Wpisz adres TRX...", saveBtn: "Zapisz 💾", changeBtn: "Zmień 🔄", saveChangeBtn: "Zapisz 💾", walletSavedDesc: "Aktualny adres:",
                    withdrawTitle: "💸 Wypłata środków", walletLabel: "Zarejestrowany adres:", noAddress: "Brak adresu!", withdrawBtn: "Potwierdź wypłatę 🚀",
                    termsTitle: "📜 Regulamin", termsContent: "1. Używanie Wi-Fi أو VPN jest surowo zabronione.<br>2. Polecenia aktywne po ukończeniu oferty.<br>3. 3% dożywotniej prowizji.<br>4. Zmieniaj portfel w dowolnym momencie.",
                    warnTitle: "⚠️ Ostrzeżenie sieci", warnDesc: "Używanie Wi-Fi أو VPN jest zabronione! Używaj wyłącznie danych komórkowych (Mobile Data).",
                    navBal: "Saldo", navRef: "Polecenia", navOffers: "Oferty", navWallet: "Portfel", navWithdraw: "Wypłata", navTerms: "Regulamin"
                },
                ar: { 
                    balance: "💰 الرصيد", ref: "👥 الإحالة", offers: "🎯 العروض", wallet: "💳 المحفظة", withdraw: "💸 السحب", terms: "📜 الشروط",
                    welcome: "مرحباً بك: ", preview: "وضع المعاينة التجريبي",
                    balTitle: "رصيدك الحالي من TRX", balDesc: "تجميعك المستمر يتيح لك السحب الفوري عند الوصول للحد الأدنى.",
                    refTitle: "👥 نظام الإحالات النشطة (3%)", refCountLbl: "عدد إحالاتك النشطة:", refDesc: "شارك رابطك وخذ 3% أرباح للأبد:", copyBtn: "نسخ رابط الإحالة 🔗",
                    offerTitle: "🎯 عروض تجميع النقاط", offerDesc: "قم بإتمام عرض التحقق أدناه لتصبح إحالتك نشطة:", openOffer: "مشاهدة الإعلان والربح 🚀", confirmOffer: "تأكيد إتمام العرض ✅",
                    walletTitle: "💳 إدارة المحفظة", walletDesc: "أدخل عنوان محفظة TRX الخاصة بك:", walletPlaceholder: "أدخل عنوان TRX هنا...", saveBtn: "حفظ العنوان 💾", changeBtn: "تغيير المحفظة 🔄", saveChangeBtn: "حفظ التغيير 💾", walletSavedDesc: "العنوان المحفوظ حالياً:",
                    withdrawTitle: "💸 سحب الأرباح", walletLabel: "عنوان المحفظة المسجل للسحب:", noAddress: "لم تقم بإضافة عنوان بعد!", withdrawBtn: "تأكيد طلب السحب 🚀",
                    termsTitle: "📜 الشروط والأحكام", termsContent: "1. يمنع منعاً باتاً استخدام الواي فاي أو الـ VPN.<br>2. لا تُحتسب الإحالة نشطة إلا بعد إتمام الشخص المدعو لعرض ناجح.<br>3. نسبة الإحالة (3%) تُحتسب للأبد.<br>4. يمكنك حفظ أو تغيير عنوان محفظة TRX بأي وقت.",
                    warnTitle: "⚠️ تنبيه شبكة الاتصال", warnDesc: "عذراً! يمنع استخدام الواي فاي أو الـ VPN. يرجى استخدام بيانات الهاتف المحمول (Mobile Data) فقط.",
                    navBal: "الرصيد", navRef: "الإحالة", navOffers: "العروض", navWallet: "المحفظة", navWithdraw: "السحب", navTerms: "الشروط"
                }
            };

            let currentLang = 'en';
            let currentTitles = translations[currentLang];

            function changeLanguage(lang) {
                currentLang = lang;
                let t = translations[lang];
                currentTitles = t;

                if (lang === 'ar') {
                    document.getElementById('html-root').setAttribute('dir', 'rtl');
                    document.getElementById('html-root').setAttribute('lang', 'ar');
                } else {
                    document.getElementById('html-root').setAttribute('dir', 'ltr');
                    document.getElementById('html-root').setAttribute('lang', lang);
                }

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

                if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
                    document.getElementById('welcome').innerText = t.welcome + (tg.initDataUnsafe.user.first_name || "User");
                } else {
                    document.getElementById('welcome').innerText = t.preview;
                }

                loadUserData();
            }

            let initialLang = 'en';
            if (tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.language_code) {
                let code = tg.initDataUnsafe.user.language_code.toLowerCase();
                for (let key in translations) {
                    if (code.startsWith(key)) {
                        initialLang = key;
                        break;
                    }
                }
            }
            document.getElementById('language-select').value = initialLang;
            changeLanguage(initialLang);

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
                let t = translations[currentLang];
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
                let t = translations[currentLang];
                let input = document.getElementById('trx-input');
                let btn = document.getElementById('wallet-btn');
                let address = input.value.trim();

                if (!address) {
                    alert(currentLang === 'ar' ? "الرجاء إدخال عنوان صحيح!" : "Please enter a valid address!");
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
                alert(currentLang === 'ar' ? "تم نسخ رابط الإحالة بنجاح! 📋" : "Referral link copied successfully! 📋");
            }

            // وظيفة تشغيل إعلان Monetag وإتمام العرض تلقائياً عند إنهاء المشاهدة
            function watchAdAndComplete() {
                if (typeof show_12130531 === 'function') {
                    show_12130531().then(() => {
                        // تنفيذ دالة إتمام العرض وإضافة الرصيد بعد مشاهدة الإعلان
                        completeOffer();
                    }).catch(err => {
                        alert("Ad failed to load or was closed. Please try again!");
                    });
                } else {
                    alert("Ad SDK is still loading, please wait a second and try again.");
                }
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
