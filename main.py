import os, re, json, time, hmac, html, hashlib, sqlite3, threading, secrets
from contextlib import contextmanager
from functools import wraps
from urllib.parse import parse_qsl
import requests, telebot
from flask import Flask, request, jsonify, Response, g

TOKEN = os.environ["TOKEN"]
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
DB_PATH = os.environ.get("DB_PATH", "bot_database.db")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0") or 0)
POSTBACK_SECRET = os.environ.get("POSTBACK_SECRET", "")
VERIFY_HOURS = min(72, max(24, int(os.environ.get("VERIFY_HOURS", "48"))))
MIN_WITHDRAW = int(os.environ.get("MIN_WITHDRAW", "100"))
REF_PERCENT = float(os.environ.get("REF_PERCENT", "0.03"))
IPQS_KEY = os.environ.get("IPQS_KEY", "")
MICRO = 1_000_000

bot = telebot.TeleBot(TOKEN, threaded=False)
server = Flask(__name__)
KINDS = ("phone", "app", "site", "ad")

def load_offers():
    try:
        raw = json.loads(os.environ.get("OFFERS_JSON", "[]"))
    except Exception:
        raw = []
    if not isinstance(raw, list): return {}
    offers = {}
    for o in raw:
        if not isinstance(o, dict): continue
        try: reward = float(o.get("reward", 0))
        except (ValueError, TypeError): continue
        if (o.get("id") and o.get("kind") in KINDS and str(o.get("url", "")).startswith("https://") and reward > 0):
            offers[str(o["id"])] = o
    return offers

OFFERS = load_offers()

@contextmanager
def tx():
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        try: conn.execute("ROLLBACK")
        except Exception: pass
        raise
    finally: conn.close()

def init_db():
    d = os.path.dirname(DB_PATH)
    if d: os.makedirs(d, exist_ok=True)
    schema = """
        CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT DEFAULT '', balance INTEGER NOT NULL DEFAULT 0, referred_by INTEGER, trx_address TEXT DEFAULT '', first_offer_done INTEGER NOT NULL DEFAULT 0, banned INTEGER NOT NULL DEFAULT 0, ban_reason TEXT DEFAULT '', created_at INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, txid TEXT UNIQUE NOT NULL, user_id INTEGER NOT NULL, kind TEXT NOT NULL, offer_id TEXT DEFAULT '', amount INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at INTEGER NOT NULL, release_at INTEGER NOT NULL, approved_at INTEGER);
        CREATE INDEX IF NOT EXISTS idx_tx_status ON transactions(status, release_at);
        CREATE TABLE IF NOT EXISTS withdrawals (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, amount INTEGER NOT NULL, address TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', note TEXT DEFAULT '', created_at INTEGER NOT NULL, processed_at INTEGER);
        CREATE TABLE IF NOT EXISTS ad_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, session_token TEXT UNIQUE NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at INTEGER NOT NULL);
    """
    with tx() as c:
        for stmt in schema.split(";"):
            if stmt.strip(): c.execute(stmt)
        cols = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
        if "lang" not in cols: c.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT ''")

def ensure_user(conn, uid, username="", referrer=None):
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    if row: return row
    if referrer:
        ok = referrer != uid and conn.execute("SELECT 1 FROM users WHERE user_id=?", (referrer,)).fetchone()
        referrer = referrer if ok else None
    conn.execute("INSERT INTO users(user_id, username, referred_by, created_at) VALUES(?,?,?,?)", (uid, username or "", referrer, int(time.time())))
    return conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()

def active_referrals(conn, uid):
    return conn.execute("SELECT COUNT(*) FROM users WHERE referred_by=? AND first_offer_done=1 AND banned=0", (uid,)).fetchone()[0]

def ban_user(conn, uid, reason):
    conn.execute("UPDATE users SET banned=1, ban_reason=?, balance=0 WHERE user_id=?", (reason, uid))
    conn.execute("UPDATE transactions SET status='reversed' WHERE user_id=? AND status='pending'", (uid,))

def release_matured():
    now = int(time.time())
    unbanned_users = []
    with tx() as c:
        rows = c.execute("SELECT * FROM transactions WHERE status='pending' AND kind!='referral' AND release_at<=?", (now,)).fetchall()
        for t in rows:
            u = c.execute("SELECT * FROM users WHERE user_id=?", (t["user_id"],)).fetchone()
            if not u or u["banned"]:
                c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (t["id"],))
                continue
            c.execute("UPDATE transactions SET status='approved', approved_at=? WHERE id=?", (now, t["id"]))
            c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (t["amount"], u["user_id"]))
            if t["kind"] != "ad" and not u["first_offer_done"]: c.execute("UPDATE users SET first_offer_done=1 WHERE user_id=?", (u["user_id"],))
            ref_id = u["referred_by"]
            if ref_id:
                ref = c.execute("SELECT banned, ban_reason FROM users WHERE user_id=?", (ref_id,)).fetchone()
                commission = int(t["amount"] * REF_PERCENT)
                if ref and ref["banned"] and ref["ban_reason"] == 'offer_reversed':
                    refs_count = c.execute("SELECT COUNT(*) FROM users WHERE referred_by=? AND first_offer_done=1 AND banned=0", (ref_id,)).fetchone()[0]
                    if refs_count >= 5:
                        c.execute("UPDATE users SET banned=0, ban_reason='' WHERE user_id=?", (ref_id,))
                        unbanned_users.append(ref_id)
                elif ref and not ref["banned"] and commission > 0:
                    cur = c.execute("INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at,approved_at) VALUES(?,?,?,?,?,'approved',?,?,?)", ("ref:" + t["txid"], ref_id, "referral", str(u["user_id"]), commission, now, now, now))
                    if cur.rowcount: c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (commission, ref_id))
    for u_id in unbanned_users:
        try: bot.send_message(u_id, "🎉 تم فتح حسابك بنجاح لأنك أحضرت 5 إحالات مكتملة!")
        except Exception: pass

def _release_loop():
    while True:
        try: release_matured()
        except Exception as e: print("release error:", e, flush=True)
        time.sleep(300)

def verify_init_data(init_data):
    if not init_data: return None
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        received = pairs.pop("hash", None)
        if not received: return None
        check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, received): return None
        if time.time() - int(pairs.get("auth_date", "0")) > 86400: return None
        return json.loads(pairs["user"])
    except Exception: return None

def auth(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        u = verify_init_data(request.headers.get("X-Init-Data", ""))
        if not u or "id" not in u: return jsonify(success=False, code="auth"), 401
        g.user = u
        return fn(*a, **k)
    return wrapper

_ip_cache = {}
def client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    return (xff.split(",")[0].strip() if xff else request.remote_addr) or ""

def is_vpn(ip):
    if not IPQS_KEY or not ip: return False
    hit = _ip_cache.get(ip)
    if hit and time.time() - hit[0] < 3600: return hit[1]
    try:
        r = requests.get(f"https://www.ipqualityscore.com/api/json/ip/{IPQS_KEY}/{ip}", params={"strictness": 1}, timeout=5).json()
        bad = bool(r.get("vpn") or r.get("proxy") or r.get("tor") or r.get("active_vpn"))
        _ip_cache[ip] = (time.time(), bad)
        return bad
    except Exception: return False

TRX_RE = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")
_bot_username, _bot_username_ts = None, 0.0

def bot_username():
    global _bot_username, _bot_username_ts
    now = time.time()
    if _bot_username and now - _bot_username_ts < 3600: return _bot_username
    try: _bot_username = bot.get_me().username or _bot_username or "TRXEarnBot"
    except Exception: _bot_username = _bot_username or "TRXEarnBot"
    _bot_username_ts = now
    return _bot_username

@server.route("/")
def home(): return "TRX Bot is running 🚀"

@server.route("/api/me")
@auth
def api_me():
    try: release_matured()
    except Exception: pass
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or g.user.get("first_name", ""))
        if u["banned"]: return jsonify(success=False, code="banned", reason=u["ban_reason"]), 403
        pending = c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND status='pending'", (uid,)).fetchone()[0]
        refs = active_referrals(c, uid)
    return jsonify(success=True, name=g.user.get("first_name", ""), balance=u["balance"] / MICRO, pending=pending / MICRO, active_referrals=refs, ref_link=f"https://t.me/{bot_username()}?start={uid}", trx_address=u["trx_address"] or "", min_withdraw=MIN_WITHDRAW)

@server.route("/api/offers")
@auth
def api_offers():
    kind = request.args.get("kind", "")
    if kind not in KINDS: return jsonify(success=False, code="err"), 400
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]: return jsonify(success=False, code="banned"), 403
    if is_vpn(client_ip()): return jsonify(success=False, code="vpn"), 403
    out = [{"id": o["id"], "title": o.get("title", o["id"]), "reward": float(o["reward"]), "url": o["url"].replace("{user_id}", str(uid))} for o in OFFERS.values() if o["kind"] == kind]
    return jsonify(success=True, offers=out)

@server.route("/api/address", methods=["POST"])
@auth
def api_address():
    data = request.get_json(silent=True) or {}
    address = str(data.get("address", "")).strip()
    if not TRX_RE.match(address): return jsonify(success=False, code="bad_address")
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]: return jsonify(success=False, code="banned"), 403
        c.execute("UPDATE users SET trx_address=? WHERE user_id=?", (address, uid))
    return jsonify(success=True)

@server.route("/api/withdraw", methods=["POST"])
@auth
def api_withdraw():
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]: return jsonify(success=False, code="banned"), 403
        if not u["trx_address"]: return jsonify(success=False, code="no_address")
        if u["balance"] < MIN_WITHDRAW * MICRO: return jsonify(success=False, code="min_balance")
        if active_referrals(c, uid) < 1: return jsonify(success=False, code="need_referral")
        if c.execute("SELECT 1 FROM withdrawals WHERE user_id=? AND status='pending'", (uid,)).fetchone(): return jsonify(success=False, code="pending_exists")
        amount = u["balance"]
        c.execute("UPDATE users SET balance=0 WHERE user_id=?", (uid,))
        cur = c.execute("INSERT INTO withdrawals(user_id, amount, address, created_at) VALUES(?,?,?,?)", (uid, amount, u["trx_address"], int(time.time())))
        wid = cur.lastrowid
        address = u["trx_address"]
    if ADMIN_ID:
        try: bot.send_message(ADMIN_ID, f"💸 طلب سحب جديد #{wid}\nالمستخدم: {uid}\nالمبلغ: {amount / MICRO:.2f} TRX\nالمحفظة: {address}\n\n/paid {wid}  أو  /reject {wid}")
        except Exception: pass
    return jsonify(success=True)

def _check_secret():
    if not POSTBACK_SECRET: return Response("postback disabled", 503)
    if not hmac.compare_digest(request.args.get("secret", ""), POSTBACK_SECRET): return Response("forbidden", 403)
    return None

@server.route("/postback")
def postback():
    bad = _check_secret()
    if bad: return bad
    txid = request.args.get("txid", "").strip()
    offer = OFFERS.get(request.args.get("offer_id", ""))
    try: uid = int(request.args.get("user_id", ""))
    except ValueError: return Response("bad user", 400)
    if not txid or not offer: return Response("bad request", 400)
    now = int(time.time())
    hold = 0 if offer["kind"] == "ad" else VERIFY_HOURS * 3600
    amount = int(float(offer["reward"]) * MICRO)
    with tx() as c:
        u = c.execute("SELECT banned FROM users WHERE user_id=?", (uid,)).fetchone()
        if not u or u["banned"]: return Response("ignored", 200)
        cur = c.execute("INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at) VALUES(?,?,?,?,?,'pending',?,?)", (txid, uid, offer["kind"], offer["id"], amount, now, now + hold))
        if not cur.rowcount: return Response("duplicate", 200)
    if hold == 0: release_matured()
    return Response("OK", 200)

@server.route("/postback/reverse")
def postback_reverse():
    bad = _check_secret()
    if bad: return bad
    txid = request.args.get("txid", "").strip()
    with tx() as c:
        t = c.execute("SELECT * FROM transactions WHERE txid=? AND kind!='referral'", (txid,)).fetchone()
        if not t or t["status"] == "reversed": return Response("OK", 200)
        uid = t["user_id"]
        c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (t["id"],))
        r = c.execute("SELECT * FROM transactions WHERE txid=? AND status='approved'", ("ref:" + txid,)).fetchone()
        if r:
            c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (r["id"],))
            c.execute("UPDATE users SET balance=MAX(balance-?,0) WHERE user_id=?", (r["amount"], r["user_id"]))
        ban_user(c, uid, "offer_reversed")
        lang = user_lang(c, uid)
    try: bot.send_message(uid, msg_for(lang, "reversed"))
    except Exception: pass
    return Response("OK", 200)

@server.route("/api/ad/start", methods=["POST"])
@auth
def api_ad_start():
    uid = g.user["id"]
    token = secrets.token_hex(16)
    with tx() as c:
        u = c.execute("SELECT banned FROM users WHERE user_id=?", (uid,)).fetchone()
        if u and u["banned"]: return jsonify(success=False, code="banned"), 403
        c.execute("INSERT INTO ad_sessions(user_id, session_token, created_at) VALUES(?,?,?)", (uid, token, int(time.time())))
    return jsonify(success=True, token=token)

@server.route("/api/ad/complete", methods=["POST"])
@auth
def api_ad_complete():
    uid = g.user["id"]
    token = (request.get_json(silent=True) or {}).get("token")
    if not token: return jsonify(success=False, code="err")
    AD_REWARD = int(0.05 * MICRO)
    with tx() as c:
        sess = c.execute("SELECT * FROM ad_sessions WHERE session_token=? AND user_id=? AND status='pending'", (token, uid)).fetchone()
        if not sess: return jsonify(success=False, code="err")
        if time.time() - sess["created_at"] > 3600:
            c.execute("UPDATE ad_sessions SET status='expired' WHERE id=?", (sess["id"],))
            return jsonify(success=False, code="err")
        c.execute("UPDATE ad_sessions SET status='completed' WHERE id=?", (sess["id"],))
        c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (AD_REWARD, uid))
        now = int(time.time())
        c.execute("INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at,approved_at) VALUES(?,?,?,?,?,'approved',?,?,?)", (f"ad_{token}", uid, "ad", "monetag", AD_REWARD, now, now, now))
    return jsonify(success=True, reward=AD_REWARD / MICRO)

HEADS = {"ar": ["🌍 عن البوت", "⚠️ تنبيه", "💰 حد السحب", "🚫 المحظورات", "⏳ التحقق", "👥 الإحالة", "💸 السحب"], "en": ["🌍 About", "⚠️ Warning", "💰 Min withdraw", "🚫 Prohibited", "⏳ Verify", "👥 Referrals", "💸 Withdraw"]}
BODIES = {
    "ar": ["الربح من:\n🎬 الإعلانات\n📱 الاشتراك\n📝 التسجيل\n📲 التطبيقات", "لا تدفع أي مبلغ. المهام مجانية. من يطلب مالاً سيتم حظره.", "الحد الأدنى للسحب: {min} TRX.", "❌ VPN\n❌ الواي فاي\n❌ حسابات متعددة\n❌ بيانات وهمية", "التحقق يستغرق {h} ساعة. إلغاء العرض = حظر الحساب.", "3% من أرباح الإحالات مدى الحياة.", "السحب يتطلب {min} TRX وإحالة حقيقية مكتملة."],
    "en": ["Earn from:\n🎬 Ads\n📱 Subscriptions\n📝 Sign-ups\n📲 Apps", "Never pay money. Tasks are free. Scammers will be banned.", "Min withdrawal: {min} TRX.", "❌ VPN\n❌ Wi-Fi\n❌ Multi-accounts\n❌ Fake data", "Verification takes {h}h. Cancelling = ban.", "3% for life.", "Requires {min} TRX and 1 real referral."]
}
TERMS_TITLE = {"ar": "📜 شروط وأحكام", "en": "📜 Terms & Conditions"}
AGREE_BTN = {"ar": "أوافق وأفتح التطبيق 🚀", "en": "I Agree & Open 🚀"}
LANGS = list(HEADS.keys())
def terms_sections(lang):
    lang = lang if lang in HEADS else "en"
    bodies = [b.replace("{min}", str(MIN_WITHDRAW)).replace("{h}", str(VERIFY_HOURS)) for b in BODIES[lang]]
    return [[h, b] for h, b in zip(HEADS[lang], bodies)]

def terms_html(lang):
    lang = lang if lang in HEADS else "en"
    parts = [f"<b>{html.escape(TERMS_TITLE[lang])}</b>\n"]
    for h, b in terms_sections(lang): parts.append(f"<b>{html.escape(h)}</b>\n{html.escape(b)}\n")
    return "\n".join(parts)

UI = {
    "ar": {"home": "🏠 الرئيسية", "ref": "👥 الإحالة", "phone": "📱 الهاتف", "apps": "📲 التطبيقات", "sites": "🌐 المواقع", "wallet": "💳 المحفظة", "withdraw": "💸 السحب", "watch": "▶️ الإعلانات", "terms": "📜 الشروط", "menu": "القائمة ⚙️", "welcome": "مرحباً", "bal": "الرصيد", "pend": "قيد التحقق", "minline": "الأدنى: {n} TRX", "faqT": "❓ القواعد", "faqD": "💸 **السحب:** حد أدنى {n} TRX وإحالة حقيقية.\n👥 **الإحالة:** اربح 3%.\n🚫 **الإلغاء:** إيقاف الحساب. افتحه بـ 5 إحالات.", "refT": "👥 الإحالة (3%)", "refCnt": "نشط", "refD": "اربح 3% مدى الحياة.", "copy": "نسخ الرابط 🔗", "copied": "تم النسخ! 📋", "noOffers": "لا عروض.", "go": "ابدأ ✅", "reward": "المكافأة", "pendNote": "تضاف بعد 24-72 ساعة.", "wDesc": "أدخل محفظة TRX:", "save": "حفظ 💾", "change": "تغيير 🔄", "wSaved": "المحفوظ:", "noAddr": "لا يوجد عنوان", "wdBtn": "طلب السحب 🚀", "wdInfo": "حد أدنى {n} TRX وإحالة نشطة.", "lang": "🌐 اللغة", "loading": "جارٍ التحميل…", "c_auth": "انتهت الجلسة.", "c_banned": "محظور.", "c_vpn": "VPN مكتشف.", "c_bad_address": "عنوان خاطئ.", "c_ok_addr": "تم الحفظ 💾", "c_no_address": "أضف عنواناً أولاً.", "c_min_balance": "أقل من الحد الأدنى.", "c_need_referral": "تحتاج إحالة حقيقية.", "c_pending_exists": "لديك طلب سحب.", "c_ok_withdraw": "تم التقديم 🚀", "c_err": "خطأ."},
    "en": {"home": "🏠 Home", "ref": "👥 Referrals", "phone": "📱 Phone", "apps": "📲 Apps", "sites": "🌐 Sites", "wallet": "💳 Wallet", "withdraw": "💸 Withdraw", "watch": "▶️ Ads", "terms": "📜 Terms", "menu": "Menu ⚙️", "welcome": "Welcome", "bal": "Balance", "pend": "Pending", "minline": "Min: {n} TRX", "faqT": "❓ Rules & Info", "faqD": "💸 **Withdrawal:** Min {n} TRX and 1 real referral.\n👥 **Referrals:** Earn 3%.\n🚫 **Cancelling:** Account suspended. Unlock with 5 referrals.", "refT": "👥 Referrals (3%)", "refCnt": "Active", "refD": "Earn 3% for life.", "copy": "Copy Link 🔗", "copied": "Copied! 📋", "noOffers": "No offers.", "go": "Start ✅", "reward": "Reward", "pendNote": "Credited after 24-72h.", "wDesc": "Enter TRX wallet:", "save": "Save 💾", "change": "Change 🔄", "wSaved": "Saved:", "noAddr": "No address", "wdBtn": "Withdraw 🚀", "wdInfo": "Min {n} TRX and 1 active referral.", "lang": "🌐 Language", "loading": "Loading…", "c_auth": "Session expired.", "c_banned": "Banned.", "c_vpn": "VPN detected.", "c_bad_address": "Invalid address.", "c_ok_addr": "Saved 💾", "c_no_address": "Add address first.", "c_min_balance": "Below minimum.", "c_need_referral": "Need 1 real referral.", "c_pending_exists": "Pending withdrawal.", "c_ok_withdraw": "Submitted 🚀", "c_err": "Error."}
}
LANG_NAMES = {"ar": "🇸🇦 العربية", "en": "🇬🇧 English"}
MSG = {"ar": {"banned_start": "🚫 محظور.", "reversed": "🚫 تم إيقاف حسابك. افتحه بـ 5 إحالات.", "paid": "✅ دفع {amt} TRX.\n{note}", "rejected": "❌ رفض #{id}.\n{note}"}, "en": {"banned_start": "🚫 Banned.", "reversed": "🚫 Suspended. Unlock with 5 referrals.", "paid": "✅ {amt} TRX sent.\n{note}", "rejected": "❌ #{id} rejected.\n{note}"}}

def user_lang(conn, uid):
    r = conn.execute("SELECT lang FROM users WHERE user_id=?", (uid,)).fetchone()
    l = (r["lang"] if r else "") or "en"
    return l if l in MSG else "en"

def msg_for(lang, key, **kw):
    return MSG.get(lang, MSG["en"])[key].format(**kw)

@server.route("/api/lang", methods=["POST"])
@auth
def api_lang():
    lang = str((request.get_json(silent=True) or {}).get("lang", ""))[:2]
    if lang in MSG:
        with tx() as c:
            ensure_user(c, g.user["id"], g.user.get("username") or "")
            c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, g.user["id"]))
    return jsonify(success=True)

WEBAPP_HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet">
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<!-- ضع كود Monetag هنا -->
<script src="https://yourdomain.com/vignette.min.js" data-zone="XXXXXX" data-sdk="show_XXXXXX"></script>
<style>
 :root{--bg:#060608;--gold:#f5c542;--text:#f6f1e4;--muted:#9a9384;--line:rgba(245,197,66,.22)}
 *{box-sizing:border-box} body{font-family:'Cairo',sans-serif;color:var(--text);padding:15px 15px 108px;background:var(--bg);margin:0}
 .header{display:flex;justify-content:space-between;padding:15px;background:rgba(6,6,8,.74);position:sticky;top:0;border-bottom:1px solid var(--line)}
 .header h2{flex:1;text-align:center;margin:0;color:var(--gold);font-size:16px}
 .card{background:rgba(255,255,255,.05);border:1px solid var(--line);border-radius:15px;padding:15px;margin-bottom:10px;text-align:center}
 .hero{background:linear-gradient(135deg,#221a08,#0b0905);padding:20px;border-radius:20px;text-align:start;border:1px solid var(--gold)}
 .amt{font-size:36px;font-weight:800;color:var(--gold);display:flex;gap:8px;direction:ltr}
 .btn{width:100%;padding:12px;border:none;border-radius:12px;background:var(--gold);color:#000;font-weight:800;margin-top:10px;cursor:pointer}
 .btn.red{background:#e11d48;color:#fff}
 .grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
 .earn{display:flex;flex-direction:column;align-items:center;padding:15px;border:1px solid var(--line);border-radius:15px;cursor:pointer;color:var(--gold)}
 #bottom{position:fixed;bottom:0;left:0;right:0;display:flex;justify-content:space-around;padding:15px;background:rgba(16,13,7,.9);border-top:1px solid var(--line)}
 .nb{background:none;border:none;color:var(--muted);font-weight:bold;cursor:pointer}
 .nb.on{color:var(--gold)}
 input,select{width:100%;padding:10px;border-radius:10px;background:#000;color:var(--gold);border:1px solid var(--line);margin-top:5px;text-align:center}
</style>
</head>
<body>
<div class="header"><button class="nb" onclick="openMenu()">☰</button><h2 id="title"></h2><span style="color:var(--gold)">♦</span></div>
<div id="view" style="margin-top:15px"></div>
<div id="bottom"></div>
<div id="menu" style="display:none;position:fixed;top:0;right:0;bottom:0;width:250px;background:#111;padding:20px;z-index:99;border-left:1px solid var(--gold)">
  <button class="nb" onclick="closeMenu()" style="float:left">✖</button>
  <h3 style="color:var(--gold)">Menu</h3>
  <div id="nav" style="display:flex;flex-direction:column;gap:10px;margin-top:20px"></div>
</div>
<script>
const UI=__UI__, LANG_NAMES=__LANG_NAMES__;
const tg=window.Telegram.WebApp; tg.ready(); tg.expand();
const INIT=tg.initData||"";
let lang=localStorage.getItem('lang')||((tg.initDataUnsafe&&tg.initDataUnsafe.user&&tg.initDataUnsafe.user.language_code)||'ar').slice(0,2);
if(!UI[lang]) lang='ar';
let state={me:null,tab:'home',offers:null,err:null};
const T=k=>(UI[lang]&&UI[lang][k])||UI.en[k]||k;

function h(tag,attrs,...kids){const e=document.createElement(tag); for(const k in (attrs||{})){if(k==='innerHTML')e.innerHTML=attrs[k]; else if(k==='onclick')e.onclick=attrs[k]; else e.setAttribute(k,attrs[k]);} kids.flat().forEach(c=>{if(c!=null) e.append(c.nodeType?c:document.createTextNode(c));}); return e;}
async function api(path,body){const opt={headers:{'X-Init-Data':INIT,'Content-Type':'application/json'}}; if(body){opt.method='POST';opt.body=JSON.stringify(body);} try{const r=await fetch(path,opt);return await r.json();}catch(e){return{success:false,code:'err'};}}
function msg(t){tg.showAlert(t);}

async function loadMe(){const d=await api('/api/me'); if(d.success){state.me=d;state.err=null;}else{state.err=d.code;} render();}
async function go(tab){state.tab=tab; closeMenu(); if(['phone','app','site','ad'].includes(tab)){state.offers=null; render(); const d=await api('/api/offers?kind='+tab); state.offers=d.success?d.offers:[];} render();}
function openMenu(){document.getElementById('menu').style.display='block';}
function closeMenu(){document.getElementById('menu').style.display='none';}

function render(){
  document.documentElement.dir=(lang==='ar')?'rtl':'ltr';
  document.getElementById('title').textContent=T(state.tab);
  const b=document.getElementById('bottom'); b.innerHTML='';
  [['home','🏠'],['ref','👥'],['wallet','💳'],['withdraw','
