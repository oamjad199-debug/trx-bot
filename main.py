import os
import re
import zlib
import base64
import json
import time
import hmac
import html
import hashlib
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from functools import wraps
from urllib.parse import parse_qsl

import requests
import telebot
from flask import Flask, request, jsonify, Response, g

# ======================================================================
# الإعدادات
# ======================================================================
TOKEN = os.environ["TOKEN"]
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")

# الواجهة الجديدة التي طلبتها (بدلاً من المخفية)
WEBAPP_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>TRX Earn Bot</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        :root { --bg: #121212; --card: #1e1e1e; --gold: #d4af37; --gold-grad: linear-gradient(135deg, #f3e5ab, #d4af37); --text: #fff; --muted: #aaa; }
        body { background-color: var(--bg); color: var(--text); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 15px; padding-bottom: 80px; }
        .header { display: flex; justify-content: space-between; align-items: center; background-color: var(--card); padding: 15px; border-radius: 15px; border: 1px solid #333; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 18px; color: var(--gold); }
        .card { background-color: var(--card); border-radius: 20px; padding: 20px; border: 1px solid #333; text-align: center; }
        .card h2 { color: var(--gold); font-size: 20px; margin-top: 0; }
        .info-text { font-size: 14px; line-height: 1.6; color: var(--muted); margin-bottom: 15px; }
        .warning-text { color: #ff6b6b; font-size: 13px; margin-bottom: 20px; font-weight: bold; }
        .timer { font-size: 24px; font-weight: bold; color: var(--gold); margin-bottom: 15px; display: none; }
        .btn-subscribe { display: block; width: 100%; padding: 15px; background: var(--gold-grad); color: #000; text-decoration: none; border-radius: 12px; font-size: 18px; font-weight: bold; border: none; cursor: pointer; transition: 0.3s; }
        .btn-subscribe:active { transform: scale(0.98); }
        .nav { position: fixed; bottom: 0; left: 0; right: 0; background-color: var(--card); display: flex; justify-content: space-around; padding: 15px 0; border-top: 1px solid #333; }
        .nav-item { color: var(--muted); text-decoration: none; font-size: 12px; display: flex; flex-direction: column; align-items: center; }
        .nav-item.active { color: var(--gold); }
    </style>
</head>
<body>
    <div class="header">
        <h1>الربح من الاشتراك برقم هاتف 📱</h1>
        <div>☰</div>
    </div>

    <div class="card">
        <h2 id="user-greet">مرحباً بك</h2>
        <div class="info-text">
            هذا العرض تربح منه <b>25%</b> ويجب أن عليك الاشتراك للربح.<br><br>
            يتم التحقق من الاشتراك خلال <b>24 إلى 72 ساعة</b> ويضاف الربح مباشرة بعد التحقق.<br><br>
            يجب عليك عدم إلغاء العرض قبل التحقق وإضافة الربح.<br><br>
            العرض يجدد كل ساعة من بعد الاشتراك.
        </div>
        <div class="warning-text">
            ⚠️ إذا تم إلغاء العرض قبل أو بعد الربح سيتم حظرك من البوت.
        </div>
        <div class="timer" id="timer-display">العرض يتجدد بعد: 01:00:00</div>
        <a href="#" class="btn-subscribe" id="btn-start" onclick="startOffer(event)">اشترك لتربح</a>
    </div>

    <div class="nav">
        <a href="#" class="nav-item active">الرئيسية</a>
        <a href="#" class="nav-item">الإحالة</a>
        <a href="#" class="nav-item">المحفظة</a>
        <a href="#" class="nav-item">السحب</a>
        <a href="#" class="nav-item">القائمة</a>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.expand();
        const user = tg.initDataUnsafe?.user;
        if (user) {
            document.getElementById('user-greet').innerText = 'مرحباً بك: ' + user.first_name;
        }

        let timerInterval;
        function startOffer(e) {
            e.preventDefault();
            // فتح رابط العرض
            tg.openLink("https://jnzvlsm.com/cl/6f9309c0648adc27?p1=" + (user ? user.id : ""));
            
            // تشغيل العداد بعد الضغط
            document.getElementById('btn-start').style.display = 'none';
            document.getElementById('timer-display').style.display = 'block';
            
            let timeLeft = 3600; // ساعة واحدة
            clearInterval(timerInterval);
            timerInterval = setInterval(() => {
                if (timeLeft <= 0) {
                    clearInterval(timerInterval);
                    document.getElementById('timer-display').style.display = 'none';
                    document.getElementById('btn-start').style.display = 'block';
                } else {
                    timeLeft--;
                    let h = Math.floor(timeLeft / 3600);
                    let m = Math.floor((timeLeft % 3600) / 60);
                    let s = timeLeft % 60;
                    document.getElementById('timer-display').innerText = `العرض يتجدد بعد: ${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
                }
            }, 1000);
        }
    </script>
</body>
</html>
"""

DB_PATH = os.environ.get("DB_PATH", "bot_database.db")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0") or 0)
POSTBACK_SECRET = os.environ.get("POSTBACK_SECRET", "")
VERIFY_HOURS = min(72, max(24, int(os.environ.get("VERIFY_HOURS", "48"))))
WITHDRAW_HOURS = int(os.environ.get("WITHDRAW_HOURS", "48"))
ADMIN_TZ = int(os.environ.get("ADMIN_TZ_HOURS", "3"))
MIN_WITHDRAW = int(os.environ.get("MIN_WITHDRAW", "100"))
REQUIRE_REFERRAL = os.environ.get("REQUIRE_REFERRAL", "0") == "1"
ADS_ENABLED = os.environ.get("ADS_ENABLED", "1") == "1"
REF_PERCENT = float(os.environ.get("REF_PERCENT", "0.03"))
IPQS_KEY = os.environ.get("IPQS_KEY", "")
MICRO = 1_000_000
TRX_USD_PRICE = float(os.environ.get("TRX_USD_PRICE", "0.34"))

bot = telebot.TeleBot(TOKEN, threaded=False)
server = Flask(__name__)
KINDS = ("phone", "app", "site", "ad")

MONETAG_ZONE = "".join(ch for ch in os.environ.get("MONETAG_ZONE", "12130531") if ch.isdigit()) or "12130531"
MONETAG_SDK_URL = os.environ.get("MONETAG_SDK_URL", "https://libtl.com/sdk.js")
OC_SDK_URL = os.environ.get("OC_SDK_URL", "https://js.onclckvd.com/in-stream-ad-admanager/tma.js")
OC_SPOT = "".join(ch for ch in os.environ.get("OC_SPOT_ID", "6154562") if ch.isalnum()) or "6154562"
ADSGRAM_TOKEN = os.environ.get("ADSGRAM_TOKEN", "").strip()
ADSGRAM_BLOCK = "".join(ch for ch in os.environ.get("ADSGRAM_BLOCK", "57655") if ch.isdigit()) or "57655"
AD_NETS = [x for x in dict.fromkeys(t.strip() for t in os.environ.get("AD_NET", "oc,mt,ab").lower().split(",")) if x in ("mt", "oc") or (x == "ab" and ADSGRAM_TOKEN)] or ["oc", "mt"]
AD_STAGES = [{"fmt": n, "views": int(os.environ.get("AD_VIEWS", "10")), "reward": float(os.environ.get("AD_REWARD", "0.0005")), "min": 6 if n == "ab" else 2} for n in AD_NETS]
AD_COOLDOWN = int(os.environ.get("AD_COOLDOWN_SECONDS", "2"))
AD_LOCK_HOURS = int(os.environ.get("AD_LOCK_HOURS", "24"))

def load_offers():
    return {
        "gg_offers": {
            "id": "gg_offers",
            "kind": "phone",
            "title": "الربح من الاشتراك برقم هاتف",
            "reward": 0,
            "url": "https://jnzvlsm.com/cl/6f9309c0648adc27?p1={user_id}"
        }
    }

OFFERS = load_offers()

# ======================================================================
# قاعدة البيانات
# ======================================================================
@contextmanager
def tx_sqlite():
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        try: conn.execute("ROLLBACK")
        except: pass
        raise
    finally:
        conn.close()

_DBPG_Z = """
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
"""
if DATABASE_URL:
    import types
    db_pg = types.ModuleType("db_pg")
    exec(zlib.decompress(base64.b64decode("".join(_DBPG_Z.split()))).decode("utf-8"), db_pg.__dict__)
    tx = db_pg.make_tx(DATABASE_URL)
else:
    tx = tx_sqlite

def init_db():
    d = os.path.dirname(DB_PATH)
    if d: os.makedirs(d, exist_ok=True)
    schema = """
        CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT DEFAULT '', balance INTEGER NOT NULL DEFAULT 0, referred_by INTEGER, trx_address TEXT DEFAULT '', first_offer_done INTEGER NOT NULL DEFAULT 0, banned INTEGER NOT NULL DEFAULT 0, ban_reason TEXT DEFAULT '', created_at INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, txid TEXT UNIQUE NOT NULL, user_id INTEGER NOT NULL, kind TEXT NOT NULL, offer_id TEXT DEFAULT '', amount INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at INTEGER NOT NULL, release_at INTEGER NOT NULL, approved_at INTEGER);
        CREATE INDEX IF NOT EXISTS idx_tx_status ON transactions(status, release_at);
        CREATE TABLE IF NOT EXISTS withdrawals (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, amount INTEGER NOT NULL, address TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', note TEXT DEFAULT '', created_at INTEGER NOT NULL, processed_at INTEGER);
        CREATE TABLE IF NOT EXISTS ad_sessions (token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, fmt TEXT NOT NULL, created_at INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS ad_progress (user_id INTEGER PRIMARY KEY, stage INTEGER NOT NULL DEFAULT 0, views INTEGER NOT NULL DEFAULT 0, earned INTEGER NOT NULL DEFAULT 0, last_view INTEGER NOT NULL DEFAULT 0, locked_until INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS ad_stage (user_id INTEGER NOT NULL, stage INTEGER NOT NULL, views INTEGER NOT NULL DEFAULT 0, earned INTEGER NOT NULL DEFAULT 0, opened INTEGER NOT NULL DEFAULT 0, locked_until INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (user_id, stage));
        """
    if DATABASE_URL:
        db_pg.init_schema(tx, schema); return
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
                c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (t["id"],)); continue
            c.execute("UPDATE transactions SET status='approved', approved_at=? WHERE id=?", (now, t["id"]))
            c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (t["amount"], u["user_id"]))
            if t["kind"] != "ad" and not u["first_offer_done"]:
                c.execute("UPDATE users SET first_offer_done=1 WHERE user_id=?", (u["user_id"],))
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
                    if cur.rowcount:
                        c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (commission, ref_id))
    for u_id in unbanned_users:
        try: bot.send_message(u_id, "🎉 تم فتح حسابك بنجاح لأنك أحضرت 5 إحالات مكتملة! يمكنك الآن استخدام التطبيق.")
        except: pass

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
    except: return None

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
        _ip_cache[ip] = (time.time(), bad); return bad
    except: return False

TRX_RE = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")
_bot_username = None
_bot_username_ts = 0.0

def bot_username():
    global _bot_username, _bot_username_ts
    now = time.time()
    if _bot_username and now - _bot_username_ts < 3600: return _bot_username
    try:
        got = bot.get_me().username
        _bot_username = got or _bot_username or "TRXEarnBot"
    except: _bot_username = _bot_username or "TRXEarnBot"
    _bot_username_ts = now; return _bot_username

@server.route("/")
def home(): return "TRX Bot is running 🚀"

@server.route("/api/me")
@auth
def api_me():
    try: release_matured()
    except: pass
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or g.user.get("first_name", ""))
        if u["banned"]: return jsonify(success=False, code="banned", reason=u["ban_reason"]), 403
        pending = c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND status='pending'", (uid,)).fetchone()[0]
        refs = active_referrals(c, uid)
        pwd = c.execute("SELECT COALESCE(SUM(amount),0) FROM withdrawals WHERE user_id=? AND status='pending'", (uid,)).fetchone()[0]
        paidwd = c.execute("SELECT COALESCE(SUM(amount),0) FROM withdrawals WHERE user_id=? AND status='paid'", (uid,)).fetchone()[0]
    return jsonify(success=True, pending_wd=pwd / MICRO, paid_wd=paidwd / MICRO, name=g.user.get("first_name", ""), balance=u["balance"] / MICRO, pending=(pending + pwd) / MICRO, active_referrals=refs, ref_link=f"https://t.me/{bot_username()}?start={uid}", trx_address=u["trx_address"] or "", min_withdraw=MIN_WITHDRAW)

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
    resp = dict(success=True, offers=out)
    if kind == "ad" and ADS_ENABLED:
        with tx() as c: resp["ads"] = ad_state(c, uid, int(time.time()))
    return jsonify(resp)

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
        if u["balance"] <= 0 or u["balance"] < MIN_WITHDRAW * MICRO: return jsonify(success=False, code="min_balance")
        if REQUIRE_REFERRAL and active_referrals(c, uid) < 1: return jsonify(success=False, code="need_referral")
        if c.execute("SELECT 1 FROM withdrawals WHERE user_id=? AND status='pending'", (uid,)).fetchone():
            return jsonify(success=False, code="pending_exists")
        amount = u["balance"]
        c.execute("UPDATE users SET balance=0 WHERE user_id=?", (uid,))
        cur = c.execute("INSERT INTO withdrawals(user_id, amount, address, created_at) VALUES(?,?,?,?)", (uid, amount, u["trx_address"], int(time.time())))
        wid = cur.lastrowid
        now_ts = int(time.time())
        address = u["trx_address"]
        uname = u["username"] or ""
    if ADMIN_ID:
        fname = str(g.user.get("first_name") or "").strip() or "-"
        body = ("💸 طلب سحب جديد #%d\n\n👤 الاسم: %s\n🔗 اليوزر: %s\n🆔 الآيدي: %d\n💰 المبلغ: %.4f TRX\n📮 عنوان TRX:\n%s\n\n%s\n\n/paid %d  أو  /reject %d" % (wid, "%s", "%s", uid, amount / MICRO, "%s", wd_deadline(now_ts), wid, wid))
        try: bot.send_message(ADMIN_ID, body % (html.escape(fname), ("@" + html.escape(uname)) if uname else "-", "<code>" + html.escape(address) + "</code>"), parse_mode="HTML", reply_markup=wd_buttons(wid))
        except Exception as e:
            try: bot.send_message(ADMIN_ID, body % (fname, ("@" + uname) if uname else "-", address), reply_markup=wd_buttons(wid))
            except: pass
    return jsonify(success=True)

def ad_stage_row(conn, uid, i, now):
    q = "SELECT * FROM ad_stage WHERE user_id=? AND stage=?"
    r = conn.execute(q, (uid, i)).fetchone()
    if not r:
        conn.execute("INSERT OR IGNORE INTO ad_stage(user_id,stage,opened) VALUES(?,?,?)", (uid, i, 1 if i == 0 else 0))
        r = conn.execute(q, (uid, i)).fetchone()
    if r["locked_until"] and now >= r["locked_until"]:
        conn.execute("UPDATE ad_stage SET views=0, earned=0, locked_until=0 WHERE user_id=? AND stage=?", (uid, i))
        r = conn.execute(q, (uid, i)).fetchone()
    return r

def ad_last_view(conn, uid):
    r = conn.execute("SELECT last_view FROM ad_progress WHERE user_id=?", (uid,)).fetchone()
    if not r:
        conn.execute("INSERT OR IGNORE INTO ad_progress(user_id) VALUES(?)", (uid,))
        return 0
    return r["last_view"]

def ad_state(conn, uid, now):
    last = ad_last_view(conn, uid)
    wait = max(0, AD_COOLDOWN - (now - last)) if last else 0
    stages = []
    for i, cfg in enumerate(AD_STAGES):
        r = ad_stage_row(conn, uid, i, now)
        lock_left = max(0, r["locked_until"] - now) if r["locked_until"] else 0
        stages.append({"idx": i, "id": cfg["fmt"], "target": cfg["views"], "views": r["views"], "earned": r["earned"] / MICRO, "open": bool(r["opened"]), "lock_left": lock_left, "ready": bool(r["views"] >= cfg["views"] and not lock_left)})
    return {"stages": stages, "wait": wait}

def _ad_check(st, wait):
    if st["lock_left"] > 0: return "ad_locked"
    if not st["open"]: return "ad_closed"
    if st["ready"]: return "ad_collect"
    if wait > 0: return "ad_cooldown"
    return None

AB_ERR = [""]
def adsgram_send(uid, lang):
    AB_ERR[0] = ""
    try:
        r = requests.get("https://api.adsgram.ai/advbot", timeout=6, params={"tgid": uid, "blockid": ADSGRAM_BLOCK, "language": lang, "token": ADSGRAM_TOKEN})
        if r.status_code != 200:
            AB_ERR[0] = "adsgram http %s" % r.status_code; return False
        d = r.json()
        text = d.get("text_html") or ""
        if not text or not d.get("click_url"): return False
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton(d.get("button_name") or "Open", url=d["click_url"]))
        if d.get("reward_url"): kb.add(telebot.types.InlineKeyboardButton(d.get("button_reward_name") or "Reward", url=d["reward_url"]))
        img = d.get("image_url")
        kw = dict(parse_mode="HTML", reply_markup=kb)
        try:
            if img and len(text) <= 1000: bot.send_photo(uid, img, caption=text, protect_content=True, **kw)
            else: bot.send_message(uid, text, protect_content=True, **kw)
        except:
            if img and len(text) <= 1000: bot.send_photo(uid, img, caption=text, **kw)
            else: bot.send_message(uid, text, **kw)
        return True
    except: return False

@server.route("/api/ad/start", methods=["POST"])
@auth
def api_ad_start():
    if not ADS_ENABLED: return jsonify(success=False, code="ad_invalid")
    uid = g.user["id"]
    if is_vpn(client_ip()): return jsonify(success=False, code="vpn"), 403
    try: i = int((request.get_json(silent=True) or {}).get("stage", 0))
    except: i = -1
    if not 0 <= i < len(AD_STAGES): return jsonify(success=False, code="ad_invalid")
    now = int(time.time())
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]: return jsonify(success=False, code="banned"), 403
        info = ad_state(c, uid, now)
        err = _ad_check(info["stages"][i], info["wait"])
        if err: return jsonify(success=False, code=err, wait=info["wait"])
        fmt = AD_STAGES[i]["fmt"]
        token = secrets.token_urlsafe(24)
        lang = user_lang(c, uid)
        c.execute("INSERT INTO ad_sessions(token,user_id,fmt,created_at) VALUES(?,?,?,?)", (token, uid, fmt, now))
        c.execute("DELETE FROM ad_sessions WHERE created_at<?", (now - 86400,))
    if fmt == "ab" and not adsgram_send(uid, lang):
        with tx() as c: c.execute("DELETE FROM ad_sessions WHERE token=?", (token,))
        return jsonify(success=False, code="ad_none", detail=(AB_ERR[0] if uid == ADMIN_ID else ""))
    return jsonify(success=True, token=token, fmt=fmt)

@server.route("/api/ad/complete", methods=["POST"])
@auth
def api_ad_complete():
    if not ADS_ENABLED: return jsonify(success=False, code="ad_invalid")
    token = str((request.get_json(silent=True) or {}).get("token", ""))
    uid = g.user["id"]
    now = int(time.time())
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]: return jsonify(success=False, code="banned"), 403
        s = c.execute("SELECT * FROM ad_sessions WHERE token=? AND user_id=?", (token, uid)).fetchone()
        if not s or s["used"] or now - s["created_at"] > 900: return jsonify(success=False, code="ad_invalid")
        idx = [k for k, cfg in enumerate(AD_STAGES) if cfg["fmt"] == s["fmt"]]
        if not idx: return jsonify(success=False, code="ad_invalid")
        i = idx[0]; cfg = AD_STAGES[i]
        if now - s["created_at"] < cfg["min"]: return jsonify(success=False, code="ad_early")
        info = ad_state(c, uid, now)
        err = _ad_check(info["stages"][i], info["wait"])
        if err: return jsonify(success=False, code=err, wait=info["wait"])
        c.execute("UPDATE ad_sessions SET used=1 WHERE token=?", (token,))
        c.execute("UPDATE ad_stage SET views=views+1, earned=earned+? WHERE user_id=? AND stage=?", (int(cfg["reward"] * MICRO), uid, i))
        c.execute("UPDATE ad_progress SET last_view=? WHERE user_id=?", (now, uid))
        out = ad_state(c, uid, now)
    return jsonify(success=True, ads=out)

@server.route("/api/ad/collect", methods=["POST"])
@auth
def api_ad_collect():
    if not ADS_ENABLED: return jsonify(success=False, code="ad_invalid")
    uid = g.user["id"]
    now = int(time.time())
    try: i = int((request.get_json(silent=True) or {}).get("stage", 0))
    except: i = -1
    if not 0 <= i < len(AD_STAGES): return jsonify(success=False, code="ad_notready")
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]: return jsonify(success=False, code="banned"), 403
        r = ad_stage_row(c, uid, i, now)
        st = ad_state(c, uid, now)["stages"][i]
        if st["lock_left"] > 0: return jsonify(success=False, code="ad_locked")
        if not st["open"] or not st["ready"]: return jsonify(success=False, code="ad_notready")
        amount = r["earned"]
        if amount > 0:
            c.execute("INSERT INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at) VALUES(?,?,?,?,?,'pending',?,?)", ("adclaim:%d:%s" % (uid, secrets.token_hex(8)), uid, "ad", "monetag:stage%d" % (i + 1), amount, now, now))
        c.execute("UPDATE ad_stage SET views=0, earned=0, opened=?, locked_until=? WHERE user_id=? AND stage=?", (1 if i == 0 else 0, now + AD_LOCK_HOURS * 3600, uid, i))
        if i + 1 < len(AD_STAGES):
            ad_stage_row(c, uid, i + 1, now)
            c.execute("UPDATE ad_stage SET opened=1 WHERE user_id=? AND stage=?", (uid, i + 1))
        out = ad_state(c, uid, now)
    release_matured()
    return jsonify(success=True, reward=amount / MICRO, ads=out)

def _check_secret():
    if not POSTBACK_SECRET: return Response("postback disabled", 503)
    if not hmac.compare_digest(request.args.get("secret", ""), POSTBACK_SECRET): return Response("forbidden", 403)
    return None

@server.route("/postback")
def postback():
    bad = _check_secret()
    if bad: return bad
    txid = request.args.get("txid", "").strip()
    offer_id = request.args.get("offer_id", "")
    offer = OFFERS.get(offer_id)
    try: uid = int(request.args.get("user_id", ""))
    except: return Response("bad user", 400)
    if not txid or not offer: return Response("bad request", 400)
    now = int(time.time())
    hold = 0 if offer["kind"] == "ad" else VERIFY_HOURS * 3600
    try: platform_payout_usd = float(request.args.get("payout", 0))
    except: platform_payout_usd = 0
    if platform_payout_usd > 0:
        user_usd = platform_payout_usd * 0.25
        user_trx = user_usd / TRX_USD_PRICE if TRX_USD_PRICE > 0 else 0
        user_amount = int(user_trx * MICRO)
    else: user_amount = int(float(offer["reward"]) * MICRO)
    if user_amount <= 0: return Response("no payout", 200)
    with tx() as c:
        u = c.execute("SELECT banned FROM users WHERE user_id=?", (uid,)).fetchone()
        if not u or u["banned"]: return Response("ignored", 200)
        cur = c.execute("INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at) VALUES(?,?,?,?,?,'pending',?,?)", (txid, uid, offer["kind"], offer["id"], user_amount, now, now + hold))
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
        if t["status"] == "approved": c.execute("UPDATE users SET balance=MAX(balance-?,0) WHERE user_id=?", (t["amount"], uid))
        r = c.execute("SELECT * FROM transactions WHERE txid=? AND status='approved'", ("ref:" + txid,)).fetchone()
        if r:
            c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (r["id"],))
            c.execute("UPDATE users SET balance=MAX(balance-?,0) WHERE user_id=?", (r["amount"], r["user_id"]))
        ban_user(c, uid, "offer_reversed")
        lang = user_lang(c, uid)
    try: bot.send_message(uid, "🚫 تم إيقاف حسابك لأنك ألغيت اشتراكاً. لفتح الحساب، يجب أن تجلب 5 إحالات مكتملة.")
    except: pass
    return Response("OK", 200)

HEADS = {"ar": ["🌍 عن البوت", "⚠️ تنبيه مهم جداً", "💰 حد السحب الأدنى", "🚫 المحظورات", "⏳ التحقق من الأرباح", "👥 نظام الإحالة", "💸 السحب"]}
BODIES = {"ar": ["البوت منصة لتحقيق الربح من:\n🎬 مشاهدة الإعلانات\n📱 عروض الاشتراك برقم الهاتف\n📝 عروض التسجيل\n📲 تثبيت التطبيقات", "لا تدفع أي مبلغ لأي منصة أو موقع أو شخص أثناء استخدام البوت. كل المهام مجانية بالكامل. أي جهة تطلب مالاً باسم البوت فهي احتيال، وسيتم حظر أي مستخدم يطلب أموالاً من غيره.", "السحب متاح مهما كان رصيدك.", "❌ استخدام VPN أو البروكسي\n❌ استخدام الواي فاي (المطلوب بيانات الجوال)\n❌ أكثر من حساب للشخص الواحد\n❌ بيانات وهمية أو أرقام غير حقيقية\n❌ التلاعب بالعروض أو برامج الغش", "لا يُضاف رصيد تثبيت التطبيقات أو التسجيل أو الاشتراك برقم الهاتف إلا بعد التحقق، وتستغرق من 24 إلى 72 ساعة (حالياً {h} ساعة). إذا ألغيت الاشتراك أو حذفت التطبيق أو ألغيت التسجيل فسيُلغى حسابك مباشرة مع أرباحه.", "تحصل على 3% من أرباح كل من تدعوه، مدى الحياة. لا تُحتسب الإحالة إلا بعد أن يشترك المدعو ويُكمل عرضاً ناجحاً واحداً على الأقل (اشتراك/تسجيل/تثبيت).", "لا يمكن السحب إلا بعد أن تُحضر مستخدماً حقيقياً يُكمل أول عرض ناجح له، وبعد بلوغ الحد الأدنى. تراجع الإدارة كل طلب قبل الدفع، ويحق لها حظر أي حساب مخالف وإلغاء أرباحه."]}
TERMS_TITLE = {"ar": "📜 شروط وأحكام TRX Earn Bot"}
AGREE_BTN = {"ar": "أوافق وأفتح التطبيق المصغر 🚀"}
LANGS = ["ar"]

def terms_sections(lang):
    lang = lang if lang in HEADS else "ar"
    bodies = [b.replace("{min}", str(MIN_WITHDRAW)).replace("{h}", str(VERIFY_HOURS)) for b in BODIES[lang]]
    return [[h, b] for h, b in zip(HEADS[lang], bodies)]

def terms_html(lang):
    lang = lang if lang in HEADS else "ar"
    parts = [f"<b>{html.escape(TERMS_TITLE[lang])}</b>\n"]
    for h, b in terms_sections(lang):
        parts.append(f"<b>{html.escape(h)}</b>\n{html.escape(b)}\n")
    return "\n".join(parts)

MSG = {"ar": {"banned_start": "🚫 تم حظر حسابك.", "reversed": "🚫 تم إيقاف حسابك لأنك ألغيت اشتراكاً أو عرضاً. لفتح الحساب، يجب أن تجلب 5 إحالات مكتملة.", "paid": "✅ تم دفع {amt} TRX إلى محفظتك.\n{note}", "rejected": "❌ تم رفض طلب السحب #{id} وأُعيد الرصيد لحسابك.\n{note}"}}

def user_lang(conn, uid):
    r = conn.execute("SELECT lang FROM users WHERE user_id=?", (uid,)).fetchone()
    l = (r["lang"] if r else "") or "ar"
    return l if l in MSG else "ar"

def msg_for(lang, key, **kw):
    return MSG.get(lang, MSG["ar"])[key].format(**kw)

@server.route("/api/lang", methods=["POST"])
@auth
def api_lang():
    lang = str((request.get_json(silent=True) or {}).get("lang", ""))[:2]
    if lang in MSG:
        with tx() as c:
            ensure_user(c, g.user["id"], g.user.get("username") or "")
            c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, g.user["id"]))
    return jsonify(success=True)

@server.route("/webapp")
def webapp():
    resp = Response(WEBAPP_HTML, mimetype="text/html")
    resp.headers["Cache-Control"] = "no-store"
    return resp

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
        referrer = None
        parts = (message.text or "").split()
        if len(parts) > 1 and parts[1].isdigit(): referrer = int(parts[1])
        with tx() as c:
            u = ensure_user(c, uid, username, referrer)
            saved_lang = u["lang"]
            if saved_lang in HEADS: lang = saved_lang
            else: lang = "ar"
        if u["banned"]:
            if u["ban_reason"] == 'offer_reversed':
                msg = f"🚫 حسابك موقوف بسبب إلغاء عرض سابق.\n\nلفتح الحساب مرة أخرى، يجب عليك إحضار 5 إحالات مكتملة (أكملن عرضاً ناجحاً).\n\n🔗 رابط الإحالة الخاص بك:\nhttps://t.me/{bot_username()}?start={uid}"
                bot.reply_to(message, msg)
            else: bot.reply_to(message, msg_for(lang, "banned_start"))
            return
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(AGREE_BTN[lang], web_app=telebot.types.WebAppInfo(url=f"{RENDER_URL}/webapp")))
        bot.reply_to(message, terms_html(lang), parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"Error in start handler: {e}", flush=True)

def is_admin(m): return ADMIN_ID and m.from_user.id == ADMIN_ID

def wd_deadline(created):
    end = created + WITHDRAW_HOURS * 3600
    left = end - int(time.time())
    when = time.strftime("%Y-%m-%d %H:%M", time.gmtime(end + ADMIN_TZ * 3600))
    if left <= 0: return "⏰ انتهت المهلة! (كان الموعد %s)" % when
    return "⏳ المهلة: %d ساعة و%d دقيقة\n📅 آخر موعد للتحويل: %s" % (left // 3600, left % 3600 // 60, when)

@bot.message_handler(commands=["myid"])
def cmd_myid(m): bot.reply_to(m, "آيديك: %d" % m.from_user.id)

@bot.message_handler(commands=["withdrawals"])
def cmd_withdrawals(m):
    if not is_admin(m):
        bot.reply_to(m, "هذا الأمر للأدمن فقط. آيديك: %d\nضع هذا الرقم في ADMIN_ID على Render." % m.from_user.id)
        return
    with tx() as c:
        rows = c.execute("SELECT w.*, u.username AS uname FROM withdrawals w LEFT JOIN users u ON u.user_id=w.user_id WHERE w.status='pending' ORDER BY w.id LIMIT 20").fetchall()
    if not rows: bot.reply_to(m, "لا توجد طلبات سحب معلقة ✅"); return
    for r in rows:
        bot.send_message(m.chat.id, "💸 طلب سحب #%d\n👤 %s | 🆔 %d\n💰 %.4f TRX\n📮 عنوان TRX:\n<code>%s</code>\n\n%s\n\n/paid %d  أو  /reject %d" % (r["id"], ("@" + html.escape(r["uname"])) if r["uname"] else "-", r["user_id"], r["amount"] / MICRO, html.escape(r["address"]), wd_deadline(r["created_at"]), r["id"], r["id"]), parse_mode="HTML", reply_markup=wd_buttons(r["id"]))

def wd_buttons(wid):
    mk = telebot.types.InlineKeyboardMarkup()
    mk.add(telebot.types.InlineKeyboardButton("✅ تم الدفع", callback_data="wd:p:%d" % wid), telebot.types.InlineKeyboardButton("❌ إلغاء الطلب", callback_data="wd:r:%d" % wid))
    return mk

def process_withdrawal(wid, paid, note=""):
    with tx() as c:
        w = c.execute("SELECT * FROM withdrawals WHERE id=? AND status='pending'", (wid,)).fetchone()
        if not w: return None
        lang = user_lang(c, w["user_id"])
        c.execute("UPDATE withdrawals SET status=?, note=?, processed_at=? WHERE id=?", ("paid" if paid else "rejected", note, int(time.time()), wid))
        if not paid: c.execute("UPDATE users SET balance=balance+? WHERE user_id=? AND banned=0", (w["amount"], w["user_id"]))
    try:
        if paid: bot.send_message(w["user_id"], msg_for(lang, "paid", amt=(f"{w['amount'] / MICRO:.4f}".rstrip("0").rstrip(".")), note=note))
        else: bot.send_message(w["user_id"], msg_for(lang, "rejected", id=wid, note=note))
    except: pass
    return w

@bot.message_handler(commands=["paid", "reject"])
def cmd_process(m):
    if not is_admin(m): return
    args = (m.text or "").split()
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(m, "الاستخدام: /paid 12 [رقم العملية]  أو  /reject 12"); return
    wid, paid = int(args[1]), args[0].startswith("/paid")
    w = process_withdrawal(wid, paid, " ".join(args[2:]))
    if not w: bot.reply_to(m, "الطلب غير موجود أو تمت معالجته."); return
    bot.reply_to(m, f"تم {'الدفع' if paid else 'الرفض وإرجاع الرصيد'} للطلب #{wid} ✅")

@bot.callback_query_handler(func=lambda call: (call.data or "").startswith("wd:"))
def cb_withdrawal(call):
    if not (ADMIN_ID and call.from_user.id == ADMIN_ID):
        bot.answer_callback_query(call.id, "للأدمن فقط"); return
    try:
        _, kind, wid = call.data.split(":")
        wid, paid = int(wid), kind == "p"
    except:
        bot.answer_callback_query(call.id, "خطأ"); return
    w = process_withdrawal(wid, paid)
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except: pass
    if not w:
        bot.answer_callback_query(call.id, "الطلب غير موجود أو تمت معالجته"); return
    bot.answer_callback_query(call.id, "تم الدفع ✅" if paid else "تم الإلغاء وإرجاع الرصيد ❌")
    bot.send_message(call.message.chat.id, ("✅ تم الدفع للطلب #%d (%.4f TRX) وتم إشعار المستخدم." if paid else "❌ تم إلغاء الطلب #%d وأُرجع %.4f TRX لرصيد المستخدم.") % (wid, w["amount"] / MICRO))

@bot.message_handler(commands=["stats"])
def cmd_stats(m):
    if not is_admin(m): return
    with tx() as c:
        users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        banned = c.execute("SELECT COUNT(*) FROM users WHERE banned=1").fetchone()[0]
        pending = c.execute("SELECT COUNT(*) FROM transactions WHERE status='pending'").fetchone()[0]
        wd = c.execute("SELECT COUNT(*) FROM withdrawals WHERE status='pending'").fetchone()[0]
    bot.reply_to(m, f"👤 المستخدمون: {users}\n🚫 المحظورون: {banned}\n⏳ عمليات قيد التحقق: {pending}\n💸 سحوبات معلقة: {wd}")

@bot.message_handler(commands=["resetads"])
def cmd_resetads(m):
    if not is_admin(m): return
    args = (m.text or "").split()
    uid = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    q1 = "UPDATE ad_stage SET views=0, earned=0, locked_until=0, opened=CASE WHEN stage=0 THEN 1 ELSE 0 END"
    q2 = "UPDATE ad_progress SET last_view=0"
    with tx() as c:
        if uid:
            c.execute(q1 + " WHERE user_id=?", (uid,)); c.execute(q2 + " WHERE user_id=?", (uid,))
        else:
            c.execute(q1); c.execute(q2)
    bot.reply_to(m, "تم تصفير الإعلانات " + ("للمستخدم %d" % uid if uid else "لجميع المستخدمين") + " ✅")

init_db()

if os.environ.get("RUN_RELEASE_LOOP", "1") == "1":
    threading.Thread(target=_release_loop, daemon=True).start()

if RENDER_URL and os.environ.get("AUTO_WEBHOOK", "1") == "1":
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    except Exception as e:
        print("set_webhook error:", e, flush=True)

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
