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
    try: raw = json.loads(os.environ.get("OFFERS_JSON", "[]"))
    except Exception: raw = []
    if not isinstance(raw, list): return {}
    offers = {}
    for o in raw:
        if not isinstance(o, dict): continue
        try: reward = float(o.get("reward", 0))
        except (ValueError, TypeError): continue
        if (o.get("id") and o.get("kind") in KINDS and str(o.get("url", "")).startswith("https://") and reward > 0): offers[str(o["id"])] = o
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
    schema = """CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT DEFAULT '', balance INTEGER NOT NULL DEFAULT 0, referred_by INTEGER, trx_address TEXT DEFAULT '', first_offer_done INTEGER NOT NULL DEFAULT 0, banned INTEGER NOT NULL DEFAULT 0, ban_reason TEXT DEFAULT '', created_at INTEGER NOT NULL DEFAULT 0); CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, txid TEXT UNIQUE NOT NULL, user_id INTEGER NOT NULL, kind TEXT NOT NULL, offer_id TEXT DEFAULT '', amount INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at INTEGER NOT NULL, release_at INTEGER NOT NULL, approved_at INTEGER); CREATE INDEX IF NOT EXISTS idx_tx_status ON transactions(status, release_at); CREATE TABLE IF NOT EXISTS withdrawals (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, amount INTEGER NOT NULL, address TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', note TEXT DEFAULT '', created_at INTEGER NOT NULL, processed_at INTEGER); CREATE TABLE IF NOT EXISTS ad_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, session_token TEXT UNIQUE NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at INTEGER NOT NULL);"""
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

def active_referrals(conn, uid): return conn.execute("SELECT COUNT(*) FROM users WHERE referred_by=? AND first_offer_done=1 AND banned=0", (uid,)).fetchone()[0]

def ban_user(conn, uid, reason):
    conn.execute("UPDATE users SET banned=1, ban_reason=?, balance=0 WHERE user_id=?", (reason, uid))
    conn.execute("UPDATE transactions SET status='reversed' WHERE user_id=? AND status='pending'", (uid,))

def release_matured():
    now, unbanned_users = int(time.time()), []
    with tx() as c:
        rows = c.execute("SELECT * FROM transactions WHERE status='pending' AND kind!='referral' AND release_at<=?", (now,)).fetchall()
        for t in rows:
            u = c.execute("SELECT * FROM users WHERE user_id=?", (t["user_id"],)).fetchone()
            if not u or u["banned"]:
                c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (t["id"],)); continue
            c.execute("UPDATE transactions SET status='approved', approved_at=? WHERE id=?", (now, t["id"]))
            c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (t["amount"], u["user_id"]))
            if t["kind"] != "ad" and not u["first_offer_done"]: c.execute("UPDATE users SET first_offer_done=1 WHERE user_id=?", (u["user_id"],))
            if u["referred_by"]:
                ref = c.execute("SELECT banned, ban_reason FROM users WHERE user_id=?", (u["referred_by"],)).fetchone()
                comm = int(t["amount"] * REF_PERCENT)
                if ref and ref["banned"] and ref["ban_reason"] == 'offer_reversed':
                    cnt = c.execute("SELECT COUNT(*) FROM users WHERE referred_by=? AND first_offer_done=1 AND banned=0", (u["referred_by"],)).fetchone()[0]
                    if cnt >= 5:
                        c.execute("UPDATE users SET banned=0, ban_reason='' WHERE user_id=?", (u["referred_by"],)); unbanned_users.append(u["referred_by"])
                elif ref and not ref["banned"] and comm > 0:
                    cur = c.execute("INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at,approved_at) VALUES(?,?,?,?,?,'approved',?,?,?)", ("ref:" + t["txid"], u["referred_by"], "referral", str(u["user_id"]), comm, now, now, now))
                    if cur.rowcount: c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (comm, u["referred_by"]))
    for uid in unbanned_users:
        try: bot.send_message(uid, "🎉 Account unlocked! You brought 5 referrals.")
        except Exception: pass

def _release_loop():
    while True:
        try: release_matured()
        except Exception: pass
        time.sleep(300)

def verify_init_data(init_data):
    if not init_data: return None
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True)); rec = pairs.pop("hash", None)
        if not rec: return None
        chk = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        sec = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(hmac.new(sec, chk.encode(), hashlib.sha256).hexdigest(), rec): return None
        if time.time() - int(pairs.get("auth_date", "0")) > 86400: return None
        return json.loads(pairs["user"])
    except Exception: return None

def auth(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        u = verify_init_data(request.headers.get("X-Init-Data", ""))
        if not u or "id" not in u: return jsonify(success=False, code="auth"), 401
        g.user = u; return fn(*a, **k)
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
        _ip_cache[ip] = (time.time(), bad); return bad
    except Exception: return False

TRX_RE = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")
_bot_username, _bot_username_ts = None, 0.0
def bot_username():
    global _bot_username, _bot_username_ts
    now = time.time()
    if _bot_username and now - _bot_username_ts < 3600: return _bot_username
    try: _bot_username = bot.get_me().username or _bot_username or "TRXEarnBot"
    except Exception: _bot_username = _bot_username or "TRXEarnBot"
    _bot_username_ts = now; return _bot_username

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
        pend = c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND status='pending'", (uid,)).fetchone()[0]
        refs = active_referrals(c, uid)
    return jsonify(success=True, name=g.user.get("first_name", ""), balance=u["balance"]/MICRO, pending=pend/MICRO, active_referrals=refs, ref_link=f"https://t.me/{bot_username()}?start={uid}", trx_address=u["trx_address"] or "", min_withdraw=MIN_WITHDRAW)

@server.route("/api/offers")
@auth
def api_offers():
    kind = request.args.get("kind", "")
    if kind not in KINDS: return jsonify(success=False, code="err"), 400
    with tx() as c:
        if ensure_user(c, g.user["id"], g.user.get("username") or "")["banned"]: return jsonify(success=False, code="banned"), 403
    if is_vpn(client_ip()): return jsonify(success=False, code="vpn"), 403
    out = [{"id": o["id"], "title": o.get("title", o["id"]), "reward": float(o["reward"]), "url": o["url"].replace("{user_id}", str(g.user["id"]))} for o in OFFERS.values() if o["kind"] == kind]
    return jsonify(success=True, offers=out)

@server.route("/api/address", methods=["POST"])
@auth
def api_address():
    addr = str((request.get_json(silent=True) or {}).get("address", "")).strip()
    if not TRX_RE.match(addr): return jsonify(success=False, code="bad_address")
    with tx() as c:
        if ensure_user(c, g.user["id"], g.user.get("username") or "")["banned"]: return jsonify(success=False, code="banned"), 403
        c.execute("UPDATE users SET trx_address=? WHERE user_id=?", (addr, g.user["id"]))
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
        amt = u["balance"]; c.execute("UPDATE users SET balance=0 WHERE user_id=?", (uid,))
        wid = c.execute("INSERT INTO withdrawals(user_id, amount, address, created_at) VALUES(?,?,?,?)", (uid, amt, u["trx_address"], int(time.time()))).lastrowid
    if ADMIN_ID:
        try: bot.send_message(ADMIN_ID, f"💸 New Withdrawal #{wid}\nUser: {uid}\nAmt: {amt/MICRO:.2f} TRX\nAddr: {u['trx_address']}\n/paid {wid} أو /reject {wid}")
        except Exception: pass
    return jsonify(success=True)

def _check_secret():
    if not POSTBACK_SECRET: return Response("disabled", 503)
    if not hmac.compare_digest(request.args.get("secret", ""), POSTBACK_SECRET): return Response("forbidden", 403)

@server.route("/postback")
def postback():
    bad = _check_secret()
    if bad: return bad
    txid, off = request.args.get("txid", "").strip(), OFFERS.get(request.args.get("offer_id", ""))
    try: uid = int(request.args.get("user_id", ""))
    except ValueError: return Response("bad", 400)
    if not txid or not off: return Response("bad", 400)
    now, hold = int(time.time()), 0 if off["kind"] == "ad" else VERIFY_HOURS * 3600
    amt = int(float(off["reward"]) * MICRO)
    with tx() as c:
        u = c.execute("SELECT banned FROM users WHERE user_id=?", (uid,)).fetchone()
        if not u or u["banned"]: return Response("ignored", 200)
        cur = c.execute("INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at) VALUES(?,?,?,?,?,'pending',?,?)", (txid, uid, off["kind"], off["id"], amt, now, now+hold))
        if not cur.rowcount: return Response("dup", 200)
    if hold == 0: release_matured()
    return Response("OK", 200)

@server.route("/postback/reverse")
def postback_reverse():
    bad = _check_secret()
    if bad: return bad
    txid = request.args.get("txid", "").strip(); uid = None
    with tx() as c:
        t = c.execute("SELECT * FROM transactions WHERE txid=? AND kind!='referral'", (txid,)).fetchone()
        if not t or t["status"] == "reversed": return Response("OK", 200)
        uid = t["user_id"]; c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (t["id"],))
        r = c.execute("SELECT * FROM transactions WHERE txid=? AND status='approved'", ("ref:"+txid,)).fetchone()
        if r:
            c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (r["id"],))
            c.execute("UPDATE users SET balance=MAX(balance-?,0) WHERE user_id=?", (r["amount"], r["user_id"]))
        ban_user(c, uid, "offer_reversed")
    try: bot.send_message(uid, "🚫 Account suspended. Bring 5 refs to unlock.")
    except Exception: pass
    return Response("OK", 200)

@server.route("/api/ad/start", methods=["POST"])
@auth
def api_ad_start():
    tok = secrets.token_hex(16)
    with tx() as c:
        if ensure_user(c, g.user["id"], g.user.get("username") or "")["banned"]: return jsonify(success=False, code="banned"), 403
        c.execute("INSERT INTO ad_sessions(user_id, session_token, created_at) VALUES(?,?,?)", (g.user["id"], tok, int(time.time())))
    return jsonify(success=True, token=tok)

@server.route("/api/ad/complete", methods=["POST"])
@auth
def api_ad_complete():
    tok = (request.get_json(silent=True) or {}).get("token")
    if not tok: return jsonify(success=False, code="err")
    AD_REWARD = int(0.05 * MICRO)
    with tx() as c:
        sess = c.execute("SELECT * FROM ad_sessions WHERE session_token=? AND user_id=? AND status='pending'", (tok, g.user["id"])).fetchone()
        if not sess or time.time() - sess["created_at"] > 3600: return jsonify(success=False, code="err")
        c.execute("UPDATE ad_sessions SET status='completed' WHERE id=?", (sess["id"],))
        c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (AD_REWARD, g.user["id"]))
        c.execute("INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at,approved_at) VALUES(?,?,?,?,?,'approved',?,?,?)", (f"ad_{tok}", g.user["id"], "ad", "monetag", AD_REWARD, int(time.time()), int(time.time()), int(time.time())))
    return jsonify(success=True, reward=AD_REWARD/MICRO)

HEADS = {"ar": ["🌍 عن البوت", "⚠️ تنبيه", "💰 حد السحب", "🚫 المحظورات", "⏳ التحقق", "👥 الإحالة", "💸 السحب"], "en": ["🌍 About", "⚠️ Warning", "💰 Min withdraw", "🚫 Prohibited", "⏳ Verify", "👥 Referrals", "💸 Withdraw"]}
BODIES = {"ar": ["الربح:\n🎬 إعلانات\n📱 اشتراك\n📝 تسجيل\n📲 تطبيقات", "لا تدفع. المهام مجانية. من يطلب مالاً سيحظر.", "الأدنى: {min} TRX.", "❌ VPN\n❌ واي فاي\n❌ حسابات متعددة", "التحقق {h} ساعة. الإلغاء = حظر.", "3% مدى الحياة.", "السحب يتطلب {min} TRX وإحالة."], "en": ["Earn:\n🎬 Ads\n📱 Subs\n📝 Sign-ups\n📲 Apps", "Never pay. Tasks are free. Scammers banned.", "Min: {min} TRX.", "❌ VPN\n❌ Wi-Fi\n❌ Multi-accounts", "Verify {h}h. Cancel = ban.", "3% for life.", "Need {min} TRX and 1 ref."]}
TERMS_TITLE = {"ar": "📜 الشروط", "en": "📜 Terms"}
AGREE_BTN = {"ar": "أوافق وأفتح التطبيق 🚀", "en": "I Agree & Open 🚀"}
LANGS = list(HEADS.keys())

def terms_html(lang):
    lang = lang if lang in HEADS else "en"
    parts = [f"<b>{html.escape(TERMS_TITLE[lang])}</b>\n"]
    for h, b in zip(HEADS[lang], BODIES[lang]):
        parts.append(f"<b>{html.escape(h)}</b>\n{html.escape(b.replace('{min}', str(MIN_WITHDRAW)).replace('{h}', str(VERIFY_HOURS)))}\n")
    return "\n".join(parts)

UI = {"ar": {"home": "🏠 الرئيسية", "ref": "👥 الإحالة", "phone": "📱 الهاتف", "apps": "📲 التطبيقات", "sites": "🌐 المواقع", "wallet": "💳 المحفظة", "withdraw": "💸 السحب", "watch": "▶️ الإعلانات", "terms": "📜 الشروط", "menu": "القائمة ⚙️", "welcome": "مرحباً", "bal": "الرصيد", "pend": "قيد التحقق", "minline": "الأدنى: {n} TRX", "faqT": "❓ القواعد", "faqD": "💸 **السحب:** حد أدنى {n} TRX وإحالة حقيقية.\n👥 **الإحالة:** اربح 3%.\n🚫 **الإلغاء:** إيقاف الحساب. افتحه بـ 5 إحالات.", "refT": "👥 الإحالة (3%)", "refCnt": "نشط", "refD": "اربح 3% مدى الحياة.", "copy": "نسخ الرابط 🔗", "copied": "تم النسخ! 📋", "noOffers": "لا عروض.", "go": "ابدأ ✅", "reward": "المكافأة", "pendNote": "تضاف بعد 24-72 ساعة.", "wDesc": "أدخل محفظة TRX:", "save": "حفظ 💾", "change": "تغيير 🔄", "wSaved": "المحفوظ:", "noAddr": "لا يوجد عنوان", "wdBtn": "طلب السحب 🚀", "wdInfo": "حد أدنى {n} TRX وإحالة نشطة.", "lang": "🌐 اللغة", "loading": "جارٍ التحميل…", "c_auth": "انتهت الجلسة.", "c_banned": "محظور.", "c_vpn": "VPN مكتشف.", "c_bad_address": "عنوان خاطئ.", "c_ok_addr": "تم الحفظ 💾", "c_no_address": "أضف عنواناً أولاً.", "c_min_balance": "أقل من الحد الأدنى.", "c_need_referral": "تحتاج إحالة حقيقية.", "c_pending_exists": "لديك طلب سحب.", "c_ok_withdraw": "تم التقديم 🚀", "c_err": "خطأ."}, "en": {"home": "🏠 Home", "ref": "👥 Referrals", "phone": "📱 Phone", "apps": "📲 Apps", "sites": "🌐 Sites", "wallet": "💳 Wallet", "withdraw": "💸 Withdraw", "watch": "▶️ Ads", "terms": "📜 Terms", "menu": "Menu ⚙️", "welcome": "Welcome", "bal": "Balance", "pend": "Pending", "minline": "Min: {n} TRX", "faqT": "❓ Rules", "faqD": "💸 **Withdrawal:** Min {n} TRX and 1 real referral.\n👥 **Referrals:** Earn 3%.\n🚫 **Cancelling:** Account suspended. Unlock with 5 referrals.", "refT": "👥 Referrals (3%)", "refCnt": "Active", "refD": "Earn 3% for life.", "copy": "Copy Link 🔗", "copied": "Copied! 📋", "noOffers": "No offers.", "go": "Start ✅", "reward": "Reward", "pendNote": "Credited after 24-72h.", "wDesc": "Enter TRX wallet:", "save": "Save 💾", "change": "Change 🔄", "wSaved": "Saved:", "noAddr": "No address", "wdBtn": "Withdraw 🚀", "wdInfo": "Min {n} TRX and 1 active referral.", "lang": "🌐 Language", "loading": "Loading…", "c_auth": "Session expired.", "c_banned": "Banned.", "c_vpn": "VPN detected.", "c_bad_address": "Invalid address.", "c_ok_addr": "Saved 💾", "c_no_address": "Add address first.", "c_min_balance": "Below minimum.", "c_need_referral": "Need 1 real referral.", "c_pending_exists": "Pending withdrawal.", "c_ok_withdraw": "Submitted 🚀", "c_err": "Error."}}
LANG_NAMES = {"ar": "🇸🇦 العربية", "en": "🇬🇧 English"}
MSG = {"ar": {"banned_start": "🚫 محظور.", "reversed": "🚫 تم إيقاف حسابك. افتحه بـ 5 إحالات.", "paid": "✅ دفع {amt} TRX.\n{note}", "rejected": "❌ رفض #{id}.\n{note}"}, "en": {"banned_start": "🚫 Banned.", "reversed": "🚫 Suspended. Unlock with 5 refs.", "paid": "✅ {amt} TRX sent.\n{note}", "rejected": "❌ #{id} rejected.\n{note}"}}

def user_lang(conn, uid):
    r = conn.execute("SELECT lang FROM users WHERE user_id=?", (uid,)).fetchone()
    return (r["lang"] if r and r["lang"] in MSG else "en")

def msg_for(lang, key, **kw): return MSG.get(lang, MSG["en"])[key].format(**kw)

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
  [['home','🏠'],['ref','👥'],['wallet','💳'],['withdraw','💸']].forEach(([k,ic])=>{ b.append(h('button',{class:'nb'+(state.tab===k?' on':''),onclick:()=>go(k)}, ic+' '+T(k))); });
  b.append(h('button',{class:'nb'+(['phone','app','site','ad','terms'].includes(state.tab)?' on':''),onclick:openMenu}, '☰ '+T('menu')));

  const n=document.getElementById('nav'); n.innerHTML='';
  ['phone','app','site','ad','terms'].forEach(k=>n.append(h('button',{class:'nb',onclick:()=>go(k)}, T(k))));

  const v=document.getElementById('view'); v.innerHTML='';
  if(!state.me){ loadMe(); v.append(h('div',{class:'card'},T('loading'))); return; }
  if(state.err){ v.append(h('div',{class:'card red'},T('c_'+state.err)||state.err)); return; }
  const me=state.me;

  if(state.tab==='home'){
    v.append(h('div',{class:'hero'},
      h('div',{},T('welcome')+', '+me.name+'!'),
      h('div',{class:'amt'},me.balance.toFixed(2)+' TRX'),
      h('div',{style:'font-size:12px;color:var(--muted)'},T('pend')+': '+me.pending.toFixed(2)+' TRX')
    ));
    const g_div=h('div',{class:'grid',style:'margin-top:15px'});
    [['phone',T('phone'),'📱'],['app',T('apps'),'📲'],['site',T('sites'),'🌐'],['ad',T('watch'),'▶️']].forEach(([k,t,ic])=>{
      g_div.append(h('div',{class:'earn',onclick:()=>go(k)},h('span',{style:'font-size:24px'},ic),h('span',{},t)));
    });
    v.append(g_div);
  } else if(state.tab==='ref'){
    v.append(h('div',{class:'card'},
      h('h3',{},T('refT')),
      h('p',{},T('refD')),
      h('div',{style:'font-size:18px;color:var(--gold);margin:10px 0'},T('refCnt')+': '+me.active_referrals),
      h('button',{class:'btn',onclick:()=>{navigator.clipboard.writeText(me.ref_link); msg(T('copied'));}},T('copy'))
    ));
  } else if(state.tab==='wallet'){
    const inp=h('input',{value:me.trx_address,placeholder:'T...'});
    v.append(h('div',{class:'card'},
      h('h3',{},T('wDesc')),
      inp,
      h('button',{class:'btn',onclick:async()=>{
        const res=await api('/api/address',{address:inp.value});
        if(res.success){msg(T('c_ok_addr')); loadMe();}else{msg(T('c_'+res.code)||res.code);}
      }},T('save'))
    ));
  } else if(state.tab==='withdraw'){
    v.append(h('div',{class:'card'},
      h('h3',{},me.balance.toFixed(2)+' TRX'),
      h('p',{style:'color:var(--muted);font-size:12px'},T('wdInfo').replace('{n}',me.min_withdraw)),
      h('button',{class:'btn',onclick:async()=>{
        const res=await api('/api/withdraw',{});
        if(res.success){msg(T('c_ok_withdraw')); loadMe();}else{msg(T('c_'+res.code)||res.code);}
      }},T('wdBtn'))
    ));
  } else if(['phone','app','site','ad'].includes(state.tab)){
    if(!state.offers){ v.append(h('div',{class:'card'},T('loading'))); return; }
    if(state.offers.length===0){ v.append(h('div',{class:'card'},T('noOffers'))); return; }
    state.offers.forEach(o=>{
      v.append(h('div',{class:'card',style:'text-align:start;display:flex;justify-content:space-between;align-items:center'},
        h('div',{},h('b',{},o.title),h('div',{style:'font-size:12px;color:var(--gold)'},T('reward')+': '+o.reward+' TRX')),
        h('button',{class:'btn',style:'width:auto;margin:0;padding:8px 15px',onclick:async()=>{
          if(state.tab==='ad'){
            const st=await api('/api/ad/start',{});
            if(st.success && typeof window['show_'+'XXXXXX'] === 'function'){
              window['show_'+'XXXXXX']().then(async()=>{
                await api('/api/ad/complete',{token:st.token});
                loadMe(); go('home');
              });
            } else { msg(T('c_err')); }
          } else { window.open(o.url,'_blank'); }
        }},T('go'))
      ));
    });
  } else if(state.tab==='terms'){
    v.append(h('div',{class:'card',style:'text-align:start'},
      h('h3',{style:'color:var(--gold)'},T('terms')),
      h('p',{},'Rules & Details...')
    ));
  }
}
loadMe();
</script>
</body>
</html>
"""

@server.route("/webapp")
def webapp_page():
    return WEBAPP_HTML.replace("__UI__", json.dumps(UI)).replace("__LANG_NAMES__", json.dumps(LANG_NAMES))

@bot.message_handler(commands=["start"])
def cmd_start(message):
    uid = message.from_user.id
    args = message.text.split()
    ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    with tx() as c:
        u = ensure_user(c, uid, message.from_user.username or "", ref)
        if u["banned"]:
            bot.send_message(uid, msg_for(user_lang(c, uid), "banned_start"))
            return
        lang = user_lang(c, uid)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text=AGREE_BTN.get(lang, AGREE_BTN["en"]), web_app=telebot.types.WebAppInfo(url=f"{RENDER_URL}/webapp")))
    bot.send_message(uid, terms_html(lang), parse_mode="HTML", reply_markup=markup)

@bot.message_handler(commands=["paid"])
def cmd_paid(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit(): return
    wid = int(args[1])
    note = " ".join(args[2:])
    with tx() as c:
        w = c.execute("SELECT * FROM withdrawals WHERE id=? AND status='pending'", (wid,)).fetchone()
        if not w:
            bot.reply_to(message, "Withdrawal not found or already processed.")
            return
        c.execute("UPDATE withdrawals SET status='paid', note=?, processed_at=? WHERE id=?", (note, int(time.time()), wid))
        uid = w["user_id"]; amt = w["amount"] / MICRO
        lang = user_lang(c, uid)
    try: bot.send_message(uid, msg_for(lang, "paid", amt=amt, note=note))
    except Exception: pass
    bot.reply_to(message, f"Successfully marked withdrawal #{wid} as paid.")

@bot.message_handler(commands=["reject"])
def cmd_reject(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit(): return
    wid = int(args[1])
    note = " ".join(args[2:])
    with tx() as c:
        w = c.execute("SELECT * FROM withdrawals WHERE id=? AND status='pending'", (wid,)).fetchone()
        if not w:
            bot.reply_to(message, "Withdrawal not found or already processed.")
            return
        c.execute("UPDATE withdrawals SET status='rejected', note=?, processed_at=? WHERE id=?", (note, int(time.time()), wid))
        uid = w["user_id"]; amt = w["amount"]
        c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amt, uid))
        lang = user_lang(c, uid)
    try: bot.send_message(uid, msg_for(lang, "rejected", id=wid, note=note))
    except Exception: pass
    bot.reply_to(message, f"Rejected withdrawal #{wid} and refunded balance.")

if __name__ == "__main__":
    init_db()
    threading.Thread(target=_release_loop, daemon=True).start()
    if RENDER_URL:
        threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
        server.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
    else:
        bot.infinity_polling(skip_pending=True)
