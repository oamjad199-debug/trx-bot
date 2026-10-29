import os
import re
import json
import time
import hmac
import html
import hashlib
import sqlite3
import threading
from contextlib import contextmanager
from functools import wraps
from urllib.parse import parse_qsl

import requests
import telebot
from flask import Flask, request, jsonify, Response, g

# ======================================================================
# الإعدادات (كلها من متغيرات البيئة)
# ======================================================================
TOKEN = os.environ["TOKEN"]
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
DB_PATH = os.environ.get("DB_PATH", "bot_database.db")      # على Render ضعه داخل Persistent Disk مثل /var/data/bot.db
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0") or 0)        # معرّفك الرقمي في تيليجرام
POSTBACK_SECRET = os.environ.get("POSTBACK_SECRET", "")     # كلمة سر طويلة تضعها في رابط Postback عند شبكة العروض
VERIFY_HOURS = min(72, max(24, int(os.environ.get("VERIFY_HOURS", "48"))))   # فترة التحقق 24-72 ساعة
MIN_WITHDRAW = int(os.environ.get("MIN_WITHDRAW", "100"))   # TRX
REF_PERCENT = float(os.environ.get("REF_PERCENT", "0.03"))  # 3%
IPQS_KEY = os.environ.get("IPQS_KEY", "")                   # اختياري: فحص VPN عبر ipqualityscore.com
MICRO = 1_000_000                                           # الأرصدة تُخزَّن كأعداد صحيحة (1 TRX = 1,000,000)

bot = telebot.TeleBot(TOKEN, threaded=False)
server = Flask(__name__)

KINDS = ("phone", "app", "site", "ad")


def load_offers():
    """OFFERS_JSON مثال:
    [{"id":"app1","kind":"app","title":"Game X","reward":2.5,"url":"https://network.com/click?aff=1&sub={user_id}"}]
    """
    try:
        raw = json.loads(os.environ.get("OFFERS_JSON", "[]"))
    except Exception:
        raw = []
    offers = {}
    for o in raw:
        if (isinstance(o, dict) and o.get("id") and o.get("kind") in KINDS
                and str(o.get("url", "")).startswith("https://") and float(o.get("reward", 0)) > 0):
            offers[str(o["id"])] = o
    return offers


OFFERS = load_offers()

# ======================================================================
# قاعدة البيانات
# ======================================================================
@contextmanager
def tx():
    """اتصال مع معاملة (BEGIN IMMEDIATE) تمنع التعارض والسباق بين الطلبات."""
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()


def init_db():
    d = os.path.dirname(DB_PATH)
    if d:
        os.makedirs(d, exist_ok=True)
    with tx() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            balance INTEGER NOT NULL DEFAULT 0,
            referred_by INTEGER,
            trx_address TEXT DEFAULT '',
            first_offer_done INTEGER NOT NULL DEFAULT 0,
            banned INTEGER NOT NULL DEFAULT 0,
            ban_reason TEXT DEFAULT '',
            created_at INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txid TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            offer_id TEXT DEFAULT '',
            amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',   -- pending / approved / reversed
            created_at INTEGER NOT NULL,
            release_at INTEGER NOT NULL,
            approved_at INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_tx_status ON transactions(status, release_at);
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            address TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',   -- pending / paid / rejected
            note TEXT DEFAULT '',
            created_at INTEGER NOT NULL,
            processed_at INTEGER
        );
        """)


def ensure_user(conn, uid, username="", referrer=None):
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    if row:
        return row
    if referrer:
        ok = referrer != uid and conn.execute("SELECT 1 FROM users WHERE user_id=?", (referrer,)).fetchone()
        referrer = referrer if ok else None
    conn.execute(
        "INSERT INTO users(user_id, username, referred_by, created_at) VALUES(?,?,?,?)",
        (uid, username or "", referrer, int(time.time())),
    )
    return conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()


def active_referrals(conn, uid):
    return conn.execute(
        "SELECT COUNT(*) FROM users WHERE referred_by=? AND first_offer_done=1 AND banned=0", (uid,)
    ).fetchone()[0]


def ban_user(conn, uid, reason):
    """إلغاء الحساب: حظر + تصفير الرصيد + إلغاء كل العمليات المعلقة."""
    conn.execute("UPDATE users SET banned=1, ban_reason=?, balance=0 WHERE user_id=?", (reason, uid))
    conn.execute("UPDATE transactions SET status='reversed' WHERE user_id=? AND status='pending'", (uid,))


# ======================================================================
# تحرير الأرباح بعد فترة التحقق + عمولة الإحالة 3%
# ======================================================================
def release_matured():
    now = int(time.time())
    with tx() as c:
        rows = c.execute(
            "SELECT * FROM transactions WHERE status='pending' AND kind!='referral' AND release_at<=?", (now,)
        ).fetchall()
        for t in rows:
            u = c.execute("SELECT * FROM users WHERE user_id=?", (t["user_id"],)).fetchone()
            if not u or u["banned"]:
                c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (t["id"],))
                continue
            c.execute("UPDATE transactions SET status='approved', approved_at=? WHERE id=?", (now, t["id"]))
            c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (t["amount"], u["user_id"]))
            if t["kind"] != "ad" and not u["first_offer_done"]:
                c.execute("UPDATE users SET first_offer_done=1 WHERE user_id=?", (u["user_id"],))
            ref_id = u["referred_by"]
            if ref_id:
                ref = c.execute("SELECT banned FROM users WHERE user_id=?", (ref_id,)).fetchone()
                commission = int(t["amount"] * REF_PERCENT)
                if ref and not ref["banned"] and commission > 0:
                    cur = c.execute(
                        "INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at,approved_at) "
                        "VALUES(?,?,?,?,?,'approved',?,?,?)",
                        ("ref:" + t["txid"], ref_id, "referral", str(u["user_id"]), commission, now, now, now),
                    )
                    if cur.rowcount:
                        c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (commission, ref_id))


def _release_loop():
    while True:
        try:
            release_matured()
        except Exception as e:
            print("release error:", e, flush=True)
        time.sleep(300)


# ======================================================================
# التحقق من هوية مستخدم Telegram (initData) + فحص VPN
# ======================================================================
def verify_init_data(init_data):
    if not init_data:
        return None
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        received = pairs.pop("hash", None)
        if not received:
            return None
        check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, received):
            return None
        if time.time() - int(pairs.get("auth_date", "0")) > 86400:
            return None
        return json.loads(pairs["user"])
    except Exception:
        return None


def auth(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        u = verify_init_data(request.headers.get("X-Init-Data", ""))
        if not u or "id" not in u:
            return jsonify(success=False, code="auth"), 401
        g.user = u
        return fn(*a, **k)
    return wrapper


_ip_cache = {}


def client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    return (xff.split(",")[0].strip() if xff else request.remote_addr) or ""


def is_vpn(ip):
    """يعمل فقط إذا وضعت IPQS_KEY. عند فشل الخدمة لا نحجب المستخدم."""
    if not IPQS_KEY or not ip:
        return False
    hit = _ip_cache.get(ip)
    if hit and time.time() - hit[0] < 3600:
        return hit[1]
    try:
        r = requests.get(
            f"https://www.ipqualityscore.com/api/json/ip/{IPQS_KEY}/{ip}", params={"strictness": 1}, timeout=5
        ).json()
        bad = bool(r.get("vpn") or r.get("proxy") or r.get("tor") or r.get("active_vpn"))
        _ip_cache[ip] = (time.time(), bad)
        return bad
    except Exception as e:
        print("ipqs error:", e, flush=True)
        return False


TRX_RE = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")
_bot_username = None


def bot_username():
    global _bot_username
    if not _bot_username:
        try:
            _bot_username = bot.get_me().username
        except Exception:
            return "TRXEarnBot"
    return _bot_username


# ======================================================================
# API الخاص بالتطبيق المصغر
# ======================================================================
@server.route("/")
def home():
    return "TRX Bot is running 🚀"


@server.route("/api/me")
@auth
def api_me():
    try:
        release_matured()
    except Exception as e:
        print("release error:", e, flush=True)
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or g.user.get("first_name", ""))
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        pending = c.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND status='pending'", (uid,)
        ).fetchone()[0]
        refs = active_referrals(c, uid)
    return jsonify(
        success=True,
        name=g.user.get("first_name", ""),
        balance=u["balance"] / MICRO,
        pending=pending / MICRO,
        active_referrals=refs,
        ref_link=f"https://t.me/{bot_username()}?start={uid}",
        trx_address=u["trx_address"] or "",
        min_withdraw=MIN_WITHDRAW,
    )


@server.route("/api/offers")
@auth
def api_offers():
    kind = request.args.get("kind", "")
    if kind not in KINDS:
        return jsonify(success=False, code="err"), 400
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
    if is_vpn(client_ip()):
        return jsonify(success=False, code="vpn"), 403
    out = [
        {
            "id": o["id"],
            "title": o.get("title", o["id"]),
            "reward": float(o["reward"]),
            "url": o["url"].replace("{user_id}", str(uid)),
        }
        for o in OFFERS.values() if o["kind"] == kind
    ]
    return jsonify(success=True, offers=out)


@server.route("/api/address", methods=["POST"])
@auth
def api_address():
    data = request.get_json(silent=True) or {}
    address = str(data.get("address", "")).strip()
    if not TRX_RE.match(address):
        return jsonify(success=False, code="bad_address")
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        c.execute("UPDATE users SET trx_address=? WHERE user_id=?", (address, uid))
    return jsonify(success=True)


@server.route("/api/withdraw", methods=["POST"])
@auth
def api_withdraw():
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        if not u["trx_address"]:
            return jsonify(success=False, code="no_address")
        if u["balance"] < MIN_WITHDRAW * MICRO:
            return jsonify(success=False, code="min_balance")
        if active_referrals(c, uid) < 1:
            return jsonify(success=False, code="need_referral")
        if c.execute("SELECT 1 FROM withdrawals WHERE user_id=? AND status='pending'", (uid,)).fetchone():
            return jsonify(success=False, code="pending_exists")
        amount = u["balance"]
        c.execute("UPDATE users SET balance=0 WHERE user_id=?", (uid,))
        cur = c.execute(
            "INSERT INTO withdrawals(user_id, amount, address, created_at) VALUES(?,?,?,?)",
            (uid, amount, u["trx_address"], int(time.time())),
        )
        wid = cur.lastrowid
        address = u["trx_address"]
    if ADMIN_ID:
        try:
            bot.send_message(
                ADMIN_ID,
                f"💸 طلب سحب جديد #{wid}\nالمستخدم: {uid}\nالمبلغ: {amount / MICRO:.2f} TRX\nالمحفظة: {address}\n\n"
                f"/paid {wid}  أو  /reject {wid}",
            )
        except Exception as e:
            print("admin notify error:", e, flush=True)
    return jsonify(success=True)


# ======================================================================
# Postback من شبكة العروض (هذا هو المصدر الوحيد لإضافة الأرباح)
# ======================================================================
def _check_secret():
    if not POSTBACK_SECRET:
        return Response("postback disabled", 503)
    if not hmac.compare_digest(request.args.get("secret", ""), POSTBACK_SECRET):
        return Response("forbidden", 403)
    return None


@server.route("/postback")
def postback():
    bad = _check_secret()
    if bad:
        return bad
    txid = request.args.get("txid", "").strip()
    offer = OFFERS.get(request.args.get("offer_id", ""))
    try:
        uid = int(request.args.get("user_id", ""))
    except ValueError:
        return Response("bad user", 400)
    if not txid or not offer:
        return Response("bad request", 400)
    now = int(time.time())
    hold = 0 if offer["kind"] == "ad" else VERIFY_HOURS * 3600
    amount = int(float(offer["reward"]) * MICRO)
    with tx() as c:
        u = c.execute("SELECT banned FROM users WHERE user_id=?", (uid,)).fetchone()
        if not u or u["banned"]:
            return Response("ignored", 200)
        cur = c.execute(
            "INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at) "
            "VALUES(?,?,?,?,?,'pending',?,?)",
            (txid, uid, offer["kind"], offer["id"], amount, now, now + hold),
        )
        if not cur.rowcount:
            return Response("duplicate", 200)
    if hold == 0:
        release_matured()
    return Response("OK", 200)


@server.route("/postback/reverse")
def postback_reverse():
    """تستدعيه الشبكة عند إلغاء العرض (إلغاء اشتراك / حذف تطبيق / احتيال)."""
    bad = _check_secret()
    if bad:
        return bad
    txid = request.args.get("txid", "").strip()
    uid = None
    with tx() as c:
        t = c.execute("SELECT * FROM transactions WHERE txid=? AND kind!='referral'", (txid,)).fetchone()
        if not t or t["status"] == "reversed":
            return Response("OK", 200)
        uid = t["user_id"]
        c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (t["id"],))
        r = c.execute("SELECT * FROM transactions WHERE txid=? AND status='approved'", ("ref:" + txid,)).fetchone()
        if r:
            c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (r["id"],))
            c.execute("UPDATE users SET balance=MAX(balance-?,0) WHERE user_id=?", (r["amount"], r["user_id"]))
        ban_user(c, uid, "offer_reversed")
    try:
        bot.send_message(uid, "🚫 تم إلغاء حسابك لأنك ألغيت اشتراكاً/تطبيقاً/تسجيلاً مخالفاً للشروط.")
    except Exception:
        pass
    return Response("OK", 200)


# ======================================================================
# النصوص: الشروط والأحكام + واجهة التطبيق (9 لغات)
# ======================================================================
HEADS = {
    "ar": ["🌍 عن البوت", "⚠️ تنبيه مهم جداً", "💰 حد السحب الأدنى", "🚫 المحظورات", "⏳ التحقق من الأرباح", "👥 نظام الإحالة", "💸 السحب"],
    "en": ["🌍 About", "⚠️ Important warning", "💰 Minimum withdrawal", "🚫 Prohibited", "⏳ Earnings verification", "👥 Referrals", "💸 Withdrawals"],
    "es": ["🌍 Sobre el bot", "⚠️ Aviso importante", "💰 Retiro mínimo", "🚫 Prohibido", "⏳ Verificación", "👥 Referidos", "💸 Retiros"],
    "de": ["🌍 Über den Bot", "⚠️ Wichtige Warnung", "💰 Mindestauszahlung", "🚫 Verboten", "⏳ Verifizierung", "👥 Empfehlungen", "💸 Auszahlungen"],
    "fr": ["🌍 À propos", "⚠️ Avertissement important", "💰 Retrait minimum", "🚫 Interdit", "⏳ Vérification", "👥 Parrainage", "💸 Retraits"],
    "ru": ["🌍 О боте", "⚠️ Важное предупреждение", "💰 Минимум для вывода", "🚫 Запрещено", "⏳ Проверка начислений", "👥 Рефералы", "💸 Вывод"],
    "pt": ["🌍 Sobre o bot", "⚠️ Aviso importante", "💰 Saque mínimo", "🚫 Proibido", "⏳ Verificação", "👥 Indicações", "💸 Saques"],
    "nl": ["🌍 Over de bot", "⚠️ Belangrijke waarschuwing", "💰 Minimum opname", "🚫 Verboden", "⏳ Verificatie", "👥 Referrals", "💸 Opnames"],
    "pl": ["🌍 O bocie", "⚠️ Ważne ostrzeżenie", "💰 Minimalna wypłata", "🚫 Zakazy", "⏳ Weryfikacja", "👥 Polecenia", "💸 Wypłaty"],
}

BODIES = {
    "ar": [
        "البوت منصة لتحقيق الربح من:\n🎬 مشاهدة الإعلانات\n📱 عروض الاشتراك برقم الهاتف\n📝 عروض التسجيل\n📲 تثبيت التطبيقات",
        "لا تدفع أي مبلغ لأي منصة أو موقع أو شخص أثناء استخدام البوت. كل المهام مجانية بالكامل. أي جهة تطلب مالاً باسم البوت فهي احتيال، وسيتم حظر أي مستخدم يطلب أموالاً من غيره.",
        "الحد الأدنى لسحب الأرباح هو {min} TRX.",
        "❌ استخدام VPN أو البروكسي\n❌ استخدام الواي فاي (المطلوب بيانات الجوال)\n❌ أكثر من حساب للشخص الواحد\n❌ بيانات وهمية أو أرقام غير حقيقية\n❌ التلاعب بالعروض أو برامج الغش",
        "لا يُضاف رصيد تثبيت التطبيقات أو التسجيل أو الاشتراك برقم الهاتف إلا بعد التحقق، وتستغرق من 24 إلى 72 ساعة (حالياً {h} ساعة). إذا ألغيت الاشتراك أو حذفت التطبيق أو ألغيت التسجيل فسيُلغى حسابك مباشرة مع أرباحه.",
        "تحصل على 3% من أرباح كل من تدعوه، مدى الحياة. لا تُحتسب الإحالة إلا بعد أن يشترك المدعو ويُكمل عرضاً ناجحاً واحداً على الأقل (اشتراك/تسجيل/تثبيت).",
        "لا يمكن السحب إلا بعد أن تُحضر مستخدماً حقيقياً يُكمل أول عرض ناجح له، وبعد بلوغ الحد الأدنى. تراجع الإدارة كل طلب قبل الدفع، ويحق لها حظر أي حساب مخالف وإلغاء أرباحه.",
    ],
    "en": [
        "A platform to earn from:\n🎬 Watching ads\n📱 Phone-number subscription offers\n📝 Registration offers\n📲 App installs",
        "Never pay any money to any platform, website or person while using the bot. All tasks are completely free. Anyone asking for money in the bot's name is a scammer, and users who ask others for money will be banned.",
        "The minimum withdrawal is {min} TRX.",
        "❌ VPN or proxy of any kind\n❌ Wi-Fi (mobile data is required)\n❌ More than one account per person\n❌ Fake data or unreal numbers\n❌ Cheating or manipulating offers",
        "Rewards for app installs, registrations and phone subscriptions are credited only after verification, which takes 24 to 72 hours (currently {h}h). If you cancel the subscription, uninstall the app or cancel the registration, your account and its earnings are cancelled immediately.",
        "Earn 3% of your referrals' earnings for life. A referral counts only after the invited user completes at least one successful offer (subscription/registration/install).",
        "You can withdraw only after bringing a real user who completes their first successful offer, and after reaching the minimum. Every request is reviewed before payment, and accounts that break the rules may be banned and their earnings cancelled.",
    ],
    "es": [
        "Plataforma para ganar con:\n🎬 Ver anuncios\n📱 Suscripciones con número de teléfono\n📝 Registros\n📲 Instalar apps",
        "No pagues dinero a ninguna plataforma, sitio o persona. Todas las tareas son gratuitas. Quien pida dinero en nombre del bot es un estafador y será bloqueado.",
        "El retiro mínimo es de {min} TRX.",
        "❌ VPN o proxy\n❌ Wi-Fi (usa datos móviles)\n❌ Más de una cuenta por persona\n❌ Datos falsos\n❌ Trampas",
        "El saldo de instalaciones, registros y suscripciones telefónicas se acredita solo tras verificar (24–72 h, ahora {h} h). Si cancelas la suscripción, borras la app o anulas el registro, tu cuenta y ganancias se cancelan de inmediato.",
        "Ganas 3% de por vida de lo que ganen tus referidos. Un referido cuenta solo cuando completa al menos una oferta exitosa.",
        "Solo puedes retirar después de traer a un usuario real que complete su primera oferta exitosa y alcanzar el mínimo. Cada solicitud se revisa antes de pagar.",
    ],
    "de": [
        "Plattform zum Verdienen durch:\n🎬 Werbung ansehen\n📱 Telefon-Abos\n📝 Registrierungen\n📲 App-Installationen",
        "Zahlen Sie niemals Geld an Plattformen, Websites oder Personen. Alle Aufgaben sind kostenlos. Wer im Namen des Bots Geld verlangt, ist ein Betrüger und wird gesperrt.",
        "Die Mindestauszahlung beträgt {min} TRX.",
        "❌ VPN oder Proxy\n❌ WLAN (Mobilfunkdaten nutzen)\n❌ Mehrere Konten pro Person\n❌ Falsche Daten\n❌ Betrug",
        "Belohnungen für Installationen, Registrierungen und Telefon-Abos werden erst nach Prüfung gutgeschrieben (24–72 Std., aktuell {h} Std.). Bei Kündigung, Deinstallation oder Abmeldung wird Ihr Konto sofort gelöscht.",
        "3% lebenslang auf die Einnahmen Ihrer Empfehlungen. Eine Empfehlung zählt erst nach mindestens einem erfolgreichen Angebot.",
        "Auszahlung nur, nachdem ein echter Nutzer sein erstes erfolgreiches Angebot abgeschlossen hat und das Minimum erreicht ist. Jeder Antrag wird vorher geprüft.",
    ],
    "fr": [
        "Plateforme pour gagner avec :\n🎬 Pubs\n📱 Abonnements par téléphone\n📝 Inscriptions\n📲 Installations d'apps",
        "Ne payez jamais d'argent à une plateforme, un site ou une personne. Tout est gratuit. Quiconque demande de l'argent au nom du bot est un escroc et sera banni.",
        "Le retrait minimum est de {min} TRX.",
        "❌ VPN ou proxy\n❌ Wi-Fi (utilisez les données mobiles)\n❌ Plusieurs comptes par personne\n❌ Fausses données\n❌ Triche",
        "Les gains d'installation, d'inscription et d'abonnement téléphonique sont crédités après vérification (24–72 h, actuellement {h} h). Si vous annulez l'abonnement, désinstallez l'app ou annulez l'inscription, votre compte est supprimé immédiatement.",
        "3% à vie sur les gains de vos filleuls. Un filleul compte seulement après au moins une offre réussie.",
        "Retrait possible uniquement après qu'un vrai utilisateur parrainé a terminé sa première offre réussie et que le minimum est atteint. Chaque demande est examinée avant paiement.",
    ],
    "ru": [
        "Платформа для заработка на:\n🎬 Просмотре рекламы\n📱 Подписках по номеру телефона\n📝 Регистрациях\n📲 Установке приложений",
        "Никому не платите деньги. Все задания бесплатны. Тот, кто просит деньги от имени бота, — мошенник и будет заблокирован.",
        "Минимальная сумма вывода — {min} TRX.",
        "❌ VPN или прокси\n❌ Wi-Fi (используйте мобильный интернет)\n❌ Несколько аккаунтов\n❌ Фейковые данные\n❌ Обман",
        "Начисления за установки, регистрации и подписки по телефону зачисляются только после проверки (24–72 ч, сейчас {h} ч). Если вы отмените подписку, удалите приложение или отмените регистрацию, аккаунт будет аннулирован сразу.",
        "3% пожизненно от заработка рефералов. Реферал засчитывается после хотя бы одного успешного задания.",
        "Вывод возможен только после того, как реальный приглашённый пользователь выполнит первое успешное задание, и при достижении минимума. Каждая заявка проверяется.",
    ],
    "pt": [
        "Plataforma para ganhar com:\n🎬 Anúncios\n📱 Assinaturas por telefone\n📝 Registros\n📲 Instalação de apps",
        "Não pague dinheiro a nenhuma plataforma, site ou pessoa. Tudo é gratuito. Quem pedir dinheiro em nome do bot é golpista e será banido.",
        "O saque mínimo é de {min} TRX.",
        "❌ VPN ou proxy\n❌ Wi-Fi (use dados móveis)\n❌ Contas múltiplas\n❌ Dados falsos\n❌ Trapaças",
        "Os ganhos de instalações, registros e assinaturas por telefone só são creditados após verificação (24–72 h, atualmente {h} h). Se cancelar a assinatura, desinstalar o app ou cancelar o registro, sua conta será cancelada imediatamente.",
        "3% vitalício sobre os ganhos dos seus indicados. A indicação só conta após ao menos uma oferta bem-sucedida.",
        "O saque só é possível depois que um usuário real indicado concluir a primeira oferta bem-sucedida e o mínimo for atingido. Cada pedido é revisado antes do pagamento.",
    ],
    "nl": [
        "Platform om te verdienen met:\n🎬 Advertenties\n📱 Telefoonabonnementen\n📝 Registraties\n📲 App-installaties",
        "Betaal nooit geld aan een platform, website of persoon. Alles is gratis. Wie namens de bot geld vraagt is een oplichter en wordt geblokkeerd.",
        "Minimum opname is {min} TRX.",
        "❌ VPN of proxy\n❌ Wi-Fi (gebruik mobiele data)\n❌ Meerdere accounts\n❌ Nepgegevens\n❌ Valsspelen",
        "Beloningen voor installaties, registraties en telefoonabonnementen worden pas na verificatie bijgeschreven (24–72 uur, nu {h} uur). Bij opzeggen, verwijderen van de app of annuleren van de registratie wordt je account direct geannuleerd.",
        "3% levenslang van de winst van je referrals. Een referral telt pas na minstens één geslaagde aanbieding.",
        "Opnemen kan pas nadat een echte genodigde zijn eerste geslaagde aanbieding heeft voltooid en het minimum is bereikt. Elk verzoek wordt eerst beoordeeld.",
    ],
    "pl": [
        "Platforma do zarabiania na:\n🎬 Reklamach\n📱 Subskrypcjach telefonicznych\n📝 Rejestracjach\n📲 Instalacji aplikacji",
        "Nigdy nie płać żadnej platformie, stronie ani osobie. Wszystko jest darmowe. Kto żąda pieniędzy w imieniu bota, jest oszustem i zostanie zablokowany.",
        "Minimalna wypłata to {min} TRX.",
        "❌ VPN lub proxy\n❌ Wi-Fi (używaj danych mobilnych)\n❌ Wiele kont\n❌ Fałszywe dane\n❌ Oszustwa",
        "Nagrody za instalacje, rejestracje i subskrypcje telefoniczne są dodawane dopiero po weryfikacji (24–72 godz., obecnie {h} godz.). Anulowanie subskrypcji, usunięcie aplikacji lub rejestracji natychmiast anuluje konto.",
        "3% dożywotnio od zarobków poleconych. Polecenie liczy się po co najmniej jednej udanej ofercie.",
        "Wypłata możliwa dopiero po tym, jak prawdziwy zaproszony użytkownik ukończy pierwszą udaną ofertę i osiągniesz minimum. Każdy wniosek jest sprawdzany.",
    ],
}

TERMS_TITLE = {
    "ar": "📜 شروط وأحكام TRX Earn Bot", "en": "📜 TRX Earn Bot Terms & Conditions",
    "es": "📜 Términos de TRX Earn Bot", "de": "📜 AGB von TRX Earn Bot", "fr": "📜 Conditions de TRX Earn Bot",
    "ru": "📜 Условия TRX Earn Bot", "pt": "📜 Termos do TRX Earn Bot", "nl": "📜 Voorwaarden van TRX Earn Bot",
    "pl": "📜 Regulamin TRX Earn Bot",
}

AGREE_BTN = {
    "ar": "أوافق وأفتح التطبيق المصغر 🚀", "en": "I Agree & Open Mini App 🚀", "es": "Aceptar y abrir Mini App 🚀",
    "de": "Zustimmen & Mini App öffnen 🚀", "fr": "Accepter et ouvrir l'App 🚀", "ru": "Согласен, открыть Mini App 🚀",
    "pt": "Concordar e abrir Mini App 🚀", "nl": "Akkoord & Mini App openen 🚀", "pl": "Zgadzam się i otwórz 🚀",
}

LANGS = list(HEADS.keys())


def terms_sections(lang):
    lang = lang if lang in HEADS else "en"
    bodies = [b.replace("{min}", str(MIN_WITHDRAW)).replace("{h}", str(VERIFY_HOURS)) for b in BODIES[lang]]
    return [[h, b] for h, b in zip(HEADS[lang], bodies)]


def terms_html(lang):
    lang = lang if lang in HEADS else "en"
    parts = [f"<b>{html.escape(TERMS_TITLE[lang])}</b>\n"]
    for h, b in terms_sections(lang):
        parts.append(f"<b>{html.escape(h)}</b>\n{html.escape(b)}\n")
    return "\n".join(parts)


UI = {
    "en": {
        "home": "🏠 Home", "ref": "👥 Referrals", "phone": "📱 Phone Subscription", "apps": "📲 Install Apps",
        "sites": "🌐 Register on Sites", "wallet": "💳 Wallet", "withdraw": "💸 Withdraw", "watch": "▶️ Watch & Earn",
        "terms": "📜 Terms", "menu": "Menu ⚙️", "welcome": "Welcome", "bal": "Current TRX balance",
        "pend": "Pending verification", "minline": "Minimum withdrawal: {n} TRX",
        "faqT": "❓ When do I get paid?",
        "faqD": "Rewards for installs, sign-ups and phone subscriptions are credited after verification (24–72 hours). Withdrawals are reviewed by the admin and require one real referral who completed a first successful offer.",
        "refT": "👥 Referral system (3%)", "refCnt": "Active referrals",
        "refD": "Share your link and earn 3% of your referrals' earnings for life. A referral counts only after they complete one successful offer.",
        "copy": "Copy referral link 🔗", "copied": "Copied! 📋", "noOffers": "No offers available right now.",
        "go": "Start ✅", "reward": "Reward", "pendNote": "Credited after verification (24–72h). Cancelling = account ban.",
        "wDesc": "Enter your TRX (TRC20) wallet address:", "save": "Save 💾", "change": "Change 🔄",
        "wSaved": "Saved address:", "noAddr": "No address added yet", "wdBtn": "Request withdrawal 🚀",
        "wdInfo": "Your whole balance is withdrawn. Needs min {n} TRX and one real active referral.",
        "lang": "🌐 Language", "loading": "Loading…",
        "c_auth": "Session expired. Please close and reopen the app from the bot.",
        "c_banned": "Your account has been banned for breaking the terms.",
        "c_vpn": "VPN/Proxy detected. Turn it off and use mobile data.",
        "c_bad_address": "Invalid TRX address.", "c_ok_addr": "Address saved 💾",
        "c_no_address": "Please add your TRX wallet address first.",
        "c_min_balance": "Your balance is below the minimum withdrawal.",
        "c_need_referral": "You need one real referral who completed their first successful offer.",
        "c_pending_exists": "You already have a pending withdrawal.",
        "c_ok_withdraw": "Withdrawal request submitted 🚀", "c_err": "Something went wrong. Try again.",
    },
    "ar": {
        "home": "🏠 الرئيسية", "ref": "👥 الإحالة", "phone": "📱 الربح من الاشتراك برقم هاتف",
        "apps": "📲 الربح من تثبيت تطبيقات", "sites": "🌐 الربح من التسجيل في المواقع", "wallet": "💳 المحفظة",
        "withdraw": "💸 السحب", "watch": "▶️ الربح من المشاهدة", "terms": "📜 الشروط والأحكام",
        "menu": "القائمة ⚙️", "welcome": "مرحباً بك", "bal": "رصيد TRX الحالي", "pend": "قيد التحقق",
        "minline": "الحد الأدنى للسحب: {n} TRX",
        "faqT": "❓ متى يتم سحب الأرباح؟",
        "faqD": "تُضاف أرباح التثبيت والتسجيل والاشتراك بعد التحقق (24–72 ساعة). تراجع الإدارة طلب السحب، ويشترط وجود إحالة حقيقية أكملت أول عرض ناجح لها.",
        "refT": "👥 نظام الإحالة (3%)", "refCnt": "عدد إحالاتك النشطة",
        "refD": "شارك رابطك وخذ 3% من أرباح من تدعوه مدى الحياة. لا تُحتسب الإحالة إلا بعد إكمال المدعو عرضاً ناجحاً.",
        "copy": "نسخ رابط الإحالة 🔗", "copied": "تم النسخ! 📋", "noOffers": "لا توجد عروض متاحة حالياً.",
        "go": "ابدأ ✅", "reward": "المكافأة", "pendNote": "تُضاف بعد التحقق (24–72 ساعة). الإلغاء = حظر الحساب.",
        "wDesc": "أدخل عنوان محفظة TRX (TRC20) الخاصة بك:", "save": "حفظ 💾", "change": "تغيير 🔄",
        "wSaved": "العنوان المحفوظ:", "noAddr": "لم تضف عنواناً بعد", "wdBtn": "طلب السحب 🚀",
        "wdInfo": "يتم سحب كامل رصيدك. الشرط: {n} TRX كحد أدنى + إحالة حقيقية نشطة.",
        "lang": "🌐 اللغة", "loading": "جارٍ التحميل…",
        "c_auth": "انتهت الجلسة. أغلق التطبيق وافتحه من البوت من جديد.",
        "c_banned": "تم حظر حسابك لمخالفة الشروط.",
        "c_vpn": "تم اكتشاف VPN/بروكسي. أطفئه واستخدم بيانات الجوال.",
        "c_bad_address": "عنوان TRX غير صحيح.", "c_ok_addr": "تم حفظ العنوان 💾",
        "c_no_address": "أضف عنوان محفظة TRX أولاً.",
        "c_min_balance": "رصيدك أقل من الحد الأدنى للسحب.",
        "c_need_referral": "يجب أن تُحضر مستخدماً حقيقياً أكمل أول عرض ناجح له.",
        "c_pending_exists": "لديك طلب سحب قيد المراجعة.",
        "c_ok_withdraw": "تم تقديم طلب السحب 🚀", "c_err": "حدث خطأ. حاول مرة أخرى.",
    },
    "es": {"home": "🏠 Inicio", "ref": "👥 Referidos", "phone": "📱 Suscripción telefónica", "apps": "📲 Instalar apps",
           "sites": "🌐 Registrarse", "wallet": "💳 Billetera", "withdraw": "💸 Retirar", "watch": "▶️ Ver y ganar",
           "terms": "📜 Términos", "menu": "Menú ⚙️", "welcome": "Bienvenido", "bal": "Saldo TRX", "copy": "Copiar enlace 🔗",
           "go": "Empezar ✅", "save": "Guardar 💾", "change": "Cambiar 🔄", "wdBtn": "Solicitar retiro 🚀", "lang": "🌐 Idioma"},
    "de": {"home": "🏠 Start", "ref": "👥 Empfehlungen", "phone": "📱 Telefon-Abo", "apps": "📲 Apps installieren",
           "sites": "🌐 Registrieren", "wallet": "💳 Wallet", "withdraw": "💸 Auszahlen", "watch": "▶️ Ansehen",
           "terms": "📜 AGB", "menu": "Menü ⚙️", "welcome": "Willkommen", "bal": "TRX-Guthaben", "copy": "Link kopieren 🔗",
           "go": "Start ✅", "save": "Speichern 💾", "change": "Ändern 🔄", "wdBtn": "Auszahlung anfordern 🚀", "lang": "🌐 Sprache"},
    "fr": {"home": "🏠 Accueil", "ref": "👥 Parrainage", "phone": "📱 Abonnement téléphone", "apps": "📲 Installer des apps",
           "sites": "🌐 Inscriptions", "wallet": "💳 Portefeuille", "withdraw": "💸 Retirer", "watch": "▶️ Regarder",
           "terms": "📜 Conditions", "menu": "Menu ⚙️", "welcome": "Bienvenue", "bal": "Solde TRX", "copy": "Copier le lien 🔗",
           "go": "Commencer ✅", "save": "Enregistrer 💾", "change": "Modifier 🔄", "wdBtn": "Demander le retrait 🚀", "lang": "🌐 Langue"},
    "ru": {"home": "🏠 Главная", "ref": "👥 Рефералы", "phone": "📱 Подписка по телефону", "apps": "📲 Установка приложений",
           "sites": "🌐 Регистрации", "wallet": "💳 Кошелёк", "withdraw": "💸 Вывод", "watch": "▶️ Смотреть",
           "terms": "📜 Условия", "menu": "Меню ⚙️", "welcome": "Добро пожаловать", "bal": "Баланс TRX", "copy": "Копировать ссылку 🔗",
           "go": "Начать ✅", "save": "Сохранить 💾", "change": "Изменить 🔄", "wdBtn": "Запросить вывод 🚀", "lang": "🌐 Язык"},
    "pt": {"home": "🏠 Início", "ref": "👥 Indicações", "phone": "📱 Assinatura por telefone", "apps": "📲 Instalar apps",
           "sites": "🌐 Registros", "wallet": "💳 Carteira", "withdraw": "💸 Sacar", "watch": "▶️ Assistir",
           "terms": "📜 Termos", "menu": "Menu ⚙️", "welcome": "Bem-vindo", "bal": "Saldo TRX", "copy": "Copiar link 🔗",
           "go": "Começar ✅", "save": "Salvar 💾", "change": "Alterar 🔄", "wdBtn": "Solicitar saque 🚀", "lang": "🌐 Idioma"},
    "nl": {"home": "🏠 Home", "ref": "👥 Referrals", "phone": "📱 Telefoonabonnement", "apps": "📲 Apps installeren",
           "sites": "🌐 Registreren", "wallet": "💳 Wallet", "withdraw": "💸 Opnemen", "watch": "▶️ Kijken",
           "terms": "📜 Voorwaarden", "menu": "Menu ⚙️", "welcome": "Welkom", "bal": "TRX-saldo", "copy": "Link kopiëren 🔗",
           "go": "Start ✅", "save": "Opslaan 💾", "change": "Wijzigen 🔄", "wdBtn": "Opname aanvragen 🚀", "lang": "🌐 Taal"},
    "pl": {"home": "🏠 Start", "ref": "👥 Polecenia", "phone": "📱 Subskrypcja tel.", "apps": "📲 Instaluj aplikacje",
           "sites": "🌐 Rejestracje", "wallet": "💳 Portfel", "withdraw": "💸 Wypłata", "watch": "▶️ Oglądaj",
           "terms": "📜 Regulamin", "menu": "Menu ⚙️", "welcome": "Witaj", "bal": "Saldo TRX", "copy": "Kopiuj link 🔗",
           "go": "Start ✅", "save": "Zapisz 💾", "change": "Zmień 🔄", "wdBtn": "Złóż wniosek 🚀", "lang": "🌐 Język"},
}

LANG_NAMES = {"ar": "🇸🇦 العربية", "en": "🇬🇧 English", "es": "🇪🇸 Español", "de": "🇩🇪 Deutsch", "fr": "🇫🇷 Français",
              "ru": "🇷🇺 Русский", "pt": "🇧🇷 Português", "nl": "🇳🇱 Nederlands", "pl": "🇵🇱 Polski"}

# ======================================================================
# صفحة التطبيق المصغر
# ======================================================================
WEBAPP_HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TRX Earn</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
 body{font-family:Tahoma,Arial,sans-serif;background:#0f172a;color:#fff;margin:0;padding:15px}
 .header{display:flex;justify-content:space-between;align-items:center;background:#1e293b;padding:12px 15px;border-radius:12px;margin-bottom:15px}
 .header h2{color:#38bdf8;font-size:17px;margin:0;text-align:center;flex:1}
 .menu-btn{background:none;border:none;color:#38bdf8;font-size:24px;cursor:pointer;width:32px}
 .card{background:#1e293b;padding:15px;border-radius:12px;margin:10px 0;text-align:center;box-shadow:0 4px 15px rgba(0,0,0,.3)}
 .card h3{color:#38bdf8;font-size:16px;margin:0 0 8px}
 .muted{font-size:12px;color:#94a3b8;line-height:1.6}
 .big{font-size:26px;font-weight:bold;color:#4ade80;margin:6px 0}
 .btn{background:#0284c7;color:#fff;border:none;padding:11px;border-radius:8px;cursor:pointer;font-size:15px;width:100%;margin-top:8px}
 .btn:active{background:#0369a1}.btn.green{background:#16a34a}.btn.red{background:#e11d48}
 input{width:100%;padding:10px;border-radius:6px;border:1px solid #475569;background:#0f172a;color:#fff;text-align:center;margin-top:8px;box-sizing:border-box;direction:ltr}
 input[readonly]{opacity:.8}
 details.card{text-align:start}
 summary{color:#38bdf8;font-weight:bold;cursor:pointer;font-size:15px}
 .pre{white-space:pre-line;text-align:start;font-size:13px;color:#cbd5e1;line-height:1.7;margin:4px 0 12px}
 h4{color:#38bdf8;text-align:start;margin:12px 0 2px;font-size:14px}
 .offer{display:flex;justify-content:space-between;align-items:center;gap:10px;background:#0f172a;border:1px solid #334155;border-radius:10px;padding:10px;margin-top:8px;text-align:start}
 .offer b{display:block;font-size:14px}.offer .btn{width:auto;margin:0;padding:8px 14px}
 .overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:999;display:none}.overlay.on{display:block}
 .drawer{position:fixed;top:0;inset-inline-end:-290px;width:270px;height:100%;background:#1e293b;z-index:1000;transition:.3s;padding:15px 10px;box-sizing:border-box;overflow-y:auto;display:flex;flex-direction:column}
 .drawer.on{inset-inline-end:0}
 .dhead{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #334155;padding-bottom:10px;margin-bottom:10px;color:#38bdf8;font-weight:bold}
 .dhead button{background:none;border:none;color:#ef4444;font-size:22px;cursor:pointer}
 .item{background:#0f172a;border:1px solid #334155;color:#cbd5e1;font-size:13px;text-align:start;padding:10px 12px;cursor:pointer;border-radius:8px;margin-bottom:6px;width:100%}
 .item.active{background:#334155;color:#38bdf8;border-color:#38bdf8;font-weight:bold}
 select{background:#0f172a;color:#fff;border:1px solid #475569;padding:7px;border-radius:6px;width:100%;margin-top:6px}
</style>
</head>
<body>
<div class="header"><button class="menu-btn" id="menu-open">☰</button><h2 id="title"></h2><span style="width:32px"></span></div>
<div class="overlay" id="overlay"></div>
<div class="drawer" id="drawer"><div class="dhead"><button id="menu-close">✕</button><span id="menu-title"></span></div><div id="nav"></div></div>
<p id="welcome" class="muted" style="text-align:center;margin:0"></p>
<div id="view"></div>
<script>
const UI=__UI__, TERMS=__TERMS__, LANG_NAMES=__LANG_NAMES__;
const tg=window.Telegram.WebApp; tg.ready(); tg.expand();
const INIT=tg.initData||"";
const $=id=>document.getElementById(id);
const NAVKEY={home:'home',ref:'ref',phone:'phone',app:'apps',site:'sites',ad:'watch',wallet:'wallet',withdraw:'withdraw',terms:'terms'};
const OFFER_KINDS=['phone','app','site','ad'];
let lang=localStorage.getItem('lang')||((tg.initDataUnsafe&&tg.initDataUnsafe.user&&tg.initDataUnsafe.user.language_code)||'ar').slice(0,2);
if(!UI[lang]) lang='ar';
let state={me:null,tab:'home',offers:null,offerErr:null,err:null,editing:false};

const T=k=>(UI[lang]&&UI[lang][k])||UI.en[k]||k;
function h(tag,attrs,...kids){const e=document.createElement(tag);
  for(const k in (attrs||{})){const v=attrs[k];
    if(k==='class') e.className=v; else if(k in e) e[k]=v; else e.setAttribute(k,v);}
  kids.flat().forEach(c=>{if(c==null)return; e.append(c.nodeType?c:document.createTextNode(String(c)));});
  return e;}
function msg(t){ if(tg.showAlert) tg.showAlert(t); else alert(t); }
async function api(path,body){
  const opt={headers:{'X-Init-Data':INIT,'Content-Type':'application/json'}};
  if(body!==undefined){opt.method='POST';opt.body=JSON.stringify(body);}
  try{const r=await fetch(path,opt);return await r.json();}catch(e){return{success:false,code:'err'};}
}
function codeMsg(code){return T('c_'+(code||'err'));}
async function copyText(s){
  try{await navigator.clipboard.writeText(s);}catch(e){const i=h('input',{value:s});document.body.append(i);i.select();document.execCommand('copy');i.remove();}
  msg(T('copied'));
}
function card(...kids){return h('div',{class:'card'},...kids);}

async function loadMe(){const d=await api('/api/me'); if(d.success){state.me=d;state.err=null;}else{state.err=d.code||'err';} render();}
async function go(tab){
  state.tab=tab; closeDrawer(); state.editing=false;
  if(OFFER_KINDS.includes(tab)){
    state.offers=null; state.offerErr=null; render();
    const d=await api('/api/offers?kind='+tab);
    if(d.success) state.offers=d.offers; else {state.offers=[];state.offerErr=d.code;}
  }
  render();
}
function openDrawer(){$('drawer').classList.add('on');$('overlay').classList.add('on');}
function closeDrawer(){$('drawer').classList.remove('on');$('overlay').classList.remove('on');}
$('menu-open').onclick=openDrawer; $('menu-close').onclick=closeDrawer; $('overlay').onclick=closeDrawer;

function buildNav(){
  const nav=$('nav'); nav.replaceChildren();
  Object.keys(NAVKEY).forEach(tab=>{
    nav.append(h('button',{class:'item'+(state.tab===tab?' active':''),onclick:()=>go(tab)},T(NAVKEY[tab])));
  });
  const sel=h('select',{onchange:e=>{lang=e.target.value;localStorage.setItem('lang',lang);render();}},
    Object.keys(LANG_NAMES).map(l=>h('option',{value:l,selected:l===lang},LANG_NAMES[l])));
  nav.append(h('div',{class:'muted',style:'margin-top:14px'},T('lang')),sel);
}

const VIEWS={
 home(v){
  const m=state.me;
  v.append(card(h('h3',{},T('bal')),h('div',{class:'big'},'TRX '+m.balance.toFixed(2)),
    h('div',{class:'muted'},T('pend')+': TRX '+m.pending.toFixed(2)),
    h('div',{class:'muted'},T('minline').replace('{n}',m.min_withdraw))));
  v.append(h('details',{class:'card'},h('summary',{},T('faqT')),h('p',{class:'muted'},T('faqD'))));
 },
 ref(v){
  const m=state.me;
  v.append(card(h('h3',{},T('refT')),
    h('p',{},T('refCnt')+': ',h('b',{style:'color:#38bdf8'},m.active_referrals)),
    h('p',{class:'muted'},T('refD')),
    h('input',{value:m.ref_link,readOnly:true,onclick:e=>e.target.select()}),
    h('button',{class:'btn',onclick:()=>copyText(m.ref_link)},T('copy'))));
 },
 offers(v,kind){
  const titleKey=NAVKEY[kind];
  const c=card(h('h3',{},T(titleKey)));
  if(kind!=='ad') c.append(h('p',{class:'muted'},T('pendNote')));
  if(state.offers===null) c.append(h('p',{class:'muted'},T('loading')));
  else if(state.offerErr) c.append(h('p',{style:'color:#fca5a5'},codeMsg(state.offerErr)));
  else if(!state.offers.length) c.append(h('p',{class:'muted'},T('noOffers')));
  else state.offers.forEach(o=>{
    c.append(h('div',{class:'offer'},h('div',{},h('b',{},o.title),h('span',{class:'muted'},T('reward')+': '+o.reward+' TRX')),
      h('button',{class:'btn green',onclick:()=>{ if(tg.openLink) tg.openLink(o.url); else window.open(o.url,'_blank'); }},T('go'))));
  });
  v.append(c);
 },
 wallet(v){
  const m=state.me, has=!!m.trx_address;
  const inp=h('input',{id:'addr',placeholder:'T...',value:m.trx_address,readOnly:has&&!state.editing});
  const btn=h('button',{class:'btn',onclick:async()=>{
    if(has&&!state.editing){state.editing=true;render();return;}
    const d=await api('/api/address',{address:inp.value.trim()});
    if(d.success){state.editing=false;msg(T('c_ok_addr'));await loadMe();} else msg(codeMsg(d.code));
  }},(has&&!state.editing)?T('change'):T('save'));
  v.append(card(h('h3',{},T('wallet')),h('p',{class:'muted'},has&&!state.editing?T('wSaved'):T('wDesc')),inp,btn));
 },
 withdraw(v){
  const m=state.me;
  v.append(card(h('h3',{},T('withdraw')),
    h('div',{class:'big'},'TRX '+m.balance.toFixed(2)),
    h('p',{class:'muted'},T('wSaved')),
    h('p',{style:'color:#fbbf24;font-weight:bold;word-break:break-all;direction:ltr'},m.trx_address||T('noAddr')),
    h('p',{class:'muted'},T('wdInfo').replace('{n}',m.min_withdraw)),
    h('button',{class:'btn red',onclick:async()=>{
      const d=await api('/api/withdraw',{});
      msg(d.success?T('c_ok_withdraw'):codeMsg(d.code)); await loadMe();
    }},T('wdBtn'))));
 },
 terms(v){
  const t=TERMS[lang]||TERMS.en;
  const c=card(h('h3',{},t.title));
  t.sections.forEach(s=>{c.append(h('h4',{},s[0]),h('div',{class:'pre'},s[1]));});
  c.style.textAlign='start'; v.append(c);
 }
};

function render(){
  document.documentElement.lang=lang; document.documentElement.dir=(lang==='ar')?'rtl':'ltr';
  $('title').textContent=T(NAVKEY[state.tab]); $('menu-title').textContent=T('menu'); buildNav();
  const v=$('view'); v.replaceChildren();
  if(state.err){v.append(card(h('p',{},codeMsg(state.err)))); return;}
  if(!state.me){v.append(h('p',{class:'muted',style:'text-align:center'},T('loading'))); return;}
  $('welcome').textContent=T('welcome')+(state.me.name?': '+state.me.name:'');
  if(OFFER_KINDS.includes(state.tab)) VIEWS.offers(v,state.tab); else VIEWS[state.tab](v);
}
if(!INIT){state.err='auth';}
render(); if(INIT) loadMe();
</script>
</body>
</html>
"""


@server.route("/webapp")
def webapp():
    terms = {l: {"title": TERMS_TITLE[l], "sections": terms_sections(l)} for l in LANGS}
    page = (WEBAPP_HTML
            .replace("__UI__", json.dumps(UI, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__TERMS__", json.dumps(terms, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__LANG_NAMES__", json.dumps(LANG_NAMES, ensure_ascii=False)))
    resp = Response(page, mimetype="text/html")
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ======================================================================
# بوت تيليجرام
# ======================================================================
@server.route("/" + TOKEN, methods=["POST"])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
        bot.process_new_updates([update])
    except Exception as e:
        print(f"Error processing update: {e}", flush=True)
    return "OK", 200


@bot.message_handler(commands=["start"])
def start(message):
    try:
        uid = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or ""
        lang = (message.from_user.language_code or "en")[:2].lower()
        if lang not in HEADS:
            lang = "en"
        referrer = None
        parts = (message.text or "").split()
        if len(parts) > 1 and parts[1].isdigit():
            referrer = int(parts[1])
        with tx() as c:
            u = ensure_user(c, uid, username, referrer)
        if u["banned"]:
            bot.reply_to(message, "🚫 تم حظر حسابك / Your account is banned.")
            return
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            AGREE_BTN[lang], web_app=telebot.types.WebAppInfo(url=f"{RENDER_URL}/webapp")))
        bot.reply_to(message, terms_html(lang), parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"Error in start handler: {e}", flush=True)


def is_admin(m):
    return ADMIN_ID and m.from_user.id == ADMIN_ID


@bot.message_handler(commands=["withdrawals"])
def cmd_withdrawals(m):
    if not is_admin(m):
        return
    with tx() as c:
        rows = c.execute("SELECT * FROM withdrawals WHERE status='pending' ORDER BY id LIMIT 20").fetchall()
    if not rows:
        bot.reply_to(m, "لا توجد طلبات سحب معلقة ✅")
        return
    bot.reply_to(m, "\n\n".join(
        f"#{r['id']} | user {r['user_id']} | {r['amount'] / MICRO:.2f} TRX\n{r['address']}" for r in rows))


@bot.message_handler(commands=["paid", "reject"])
def cmd_process(m):
    if not is_admin(m):
        return
    args = (m.text or "").split()
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(m, "الاستخدام: /paid 12 [رقم العملية]  أو  /reject 12")
        return
    wid, paid = int(args[1]), args[0].startswith("/paid")
    note = " ".join(args[2:])
    with tx() as c:
        w = c.execute("SELECT * FROM withdrawals WHERE id=? AND status='pending'", (wid,)).fetchone()
        if not w:
            bot.reply_to(m, "الطلب غير موجود أو تمت معالجته.")
            return
        c.execute("UPDATE withdrawals SET status=?, note=?, processed_at=? WHERE id=?",
                  ("paid" if paid else "rejected", note, int(time.time()), wid))
        if not paid:
            c.execute("UPDATE users SET balance=balance+? WHERE user_id=? AND banned=0", (w["amount"], w["user_id"]))
    bot.reply_to(m, f"تم {'الدفع' if paid else 'الرفض وإرجاع الرصيد'} للطلب #{wid} ✅")
    try:
        if paid:
            bot.send_message(w["user_id"], f"✅ تم دفع {w['amount'] / MICRO:.2f} TRX إلى محفظتك.\n{note}")
        else:
            bot.send_message(w["user_id"], f"❌ تم رفض طلب السحب #{wid} وأُعيد الرصيد لحسابك.\n{note}")
    except Exception:
        pass


@bot.message_handler(commands=["stats"])
def cmd_stats(m):
    if not is_admin(m):
        return
    with tx() as c:
        users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        banned = c.execute("SELECT COUNT(*) FROM users WHERE banned=1").fetchone()[0]
        pending = c.execute("SELECT COUNT(*) FROM transactions WHERE status='pending'").fetchone()[0]
        wd = c.execute("SELECT COUNT(*) FROM withdrawals WHERE status='pending'").fetchone()[0]
    bot.reply_to(m, f"👤 المستخدمون: {users}\n🚫 المحظورون: {banned}\n⏳ عمليات قيد التحقق: {pending}\n💸 سحوبات معلقة: {wd}")


# ======================================================================
# التشغيل (يعمل مع gunicorn أيضاً)
# ======================================================================
init_db()
threading.Thread(target=_release_loop, daemon=True).start()

if RENDER_URL and os.environ.get("AUTO_WEBHOOK", "1") == "1":
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    except Exception as e:
        print("set_webhook error:", e, flush=True)

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
