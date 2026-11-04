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
_WEBAPP_Z = """
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
ujeN57PDB/8XWW3DGA==
"""
WEBAPP_HTML = zlib.decompress(base64.b64decode("".join(_WEBAPP_Z.split()))).decode("utf-8")

DB_PATH = os.environ.get("DB_PATH", "bot_database.db")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()   # رابط PostgreSQL الخارجي: يحفظ البيانات بعد كل نشر
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0") or 0)
POSTBACK_SECRET = os.environ.get("POSTBACK_SECRET", "")
VERIFY_HOURS = min(72, max(24, int(os.environ.get("VERIFY_HOURS", "48"))))
WITHDRAW_HOURS = int(os.environ.get("WITHDRAW_HOURS", "48"))   # مهلة تنفيذ السحب يدوياً
ADMIN_TZ = int(os.environ.get("ADMIN_TZ_HOURS", "3"))          # فرق التوقيت لعرض الموعد (الأردن +3)
MIN_WITHDRAW = int(os.environ.get("MIN_WITHDRAW", "100"))   # الحد الأدنى للسحب 100 ترون
REQUIRE_REFERRAL = os.environ.get("REQUIRE_REFERRAL", "0") == "1"   # شرط الإحالة للسحب: ضع 1 لتفعيله
ADS_ENABLED = os.environ.get("ADS_ENABLED", "1") == "1"             # ضع 0 لإيقاف الإعلانات مؤقتاً
REF_PERCENT = float(os.environ.get("REF_PERCENT", "0.03"))
REF_ON_AD = os.environ.get("REF_ON_AD", "1") == "1"   # 1: تُحتسب الإحالة بعد أول مشاهدة إعلان
IPQS_KEY = os.environ.get("IPQS_KEY", "")
MICRO = 1_000_000
TRX_USD_PRICE = float(os.environ.get("TRX_USD_PRICE", "0.34")) # سعر التترون مقابل الدولار

bot = telebot.TeleBot(TOKEN, threaded=False)
server = Flask(__name__)

KINDS = ("phone", "app", "site", "ad")

MONETAG_ZONE = "".join(ch for ch in os.environ.get("MONETAG_ZONE", "12130531") if ch.isdigit()) or "12130531"
MONETAG_SDK_URL = os.environ.get("MONETAG_SDK_URL", "https://libtl.com/sdk.js")
OC_SDK_URL = os.environ.get("OC_SDK_URL", "https://js.onclckvd.com/in-stream-ad-admanager/tma.js")   # Onclicka
OC_SPOT = "".join(ch for ch in os.environ.get("OC_SPOT_ID", "6154562") if ch.isalnum()) or "6154562"
ADSGRAM_TOKEN = os.environ.get("ADSGRAM_TOKEN", "").strip()
ADSGRAM_BLOCK = "".join(ch for ch in os.environ.get("ADSGRAM_BLOCK", "57655") if ch.isdigit()) or "57655"
AD_NETS = [x for x in dict.fromkeys(t.strip() for t in os.environ.get("AD_NET", "oc,mt,ab").lower().split(",")) if x in ("mt", "oc") or (x == "ab" and ADSGRAM_TOKEN)] or ["oc", "mt"]
AD_STAGES = [{"fmt": n, "views": int(os.environ.get("AD_VIEWS", "10")), "reward": float(os.environ.get("AD_REWARD", "0.0005")), "min": 6 if n == "ab" else 2} for n in AD_NETS]
AD_COOLDOWN = int(os.environ.get("AD_COOLDOWN_SECONDS", "2"))   # الفاصل بين مشاهدة وأخرى
AD_LOCK_HOURS = int(os.environ.get("AD_LOCK_HOURS", "24"))        # قفل كل مرحلة بعد جمع رصيدها

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
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()

_DBPG_Z = """
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
"""
DB_PG_SRC = zlib.decompress(base64.b64decode("".join(_DBPG_Z.split()))).decode("utf-8")

if DATABASE_URL:
    import types
    db_pg = types.ModuleType("db_pg")
    exec(DB_PG_SRC, db_pg.__dict__)
    tx = db_pg.make_tx(DATABASE_URL)
else:
    tx = tx_sqlite

def init_db():
    d = os.path.dirname(DB_PATH)
    if d:
        os.makedirs(d, exist_ok=True)
    schema = """
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
            status TEXT NOT NULL DEFAULT 'pending',
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
            status TEXT NOT NULL DEFAULT 'pending',
            note TEXT DEFAULT '',
            created_at INTEGER NOT NULL,
            processed_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS ad_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            fmt TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            used INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS ad_progress (
            user_id INTEGER PRIMARY KEY,
            stage INTEGER NOT NULL DEFAULT 0,
            views INTEGER NOT NULL DEFAULT 0,
            earned INTEGER NOT NULL DEFAULT 0,
            last_view INTEGER NOT NULL DEFAULT 0,
            locked_until INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS ad_stage (
            user_id INTEGER NOT NULL,
            stage INTEGER NOT NULL,
            views INTEGER NOT NULL DEFAULT 0,
            earned INTEGER NOT NULL DEFAULT 0,
            opened INTEGER NOT NULL DEFAULT 0,
            locked_until INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, stage)
        );
        """
    if DATABASE_URL:
        db_pg.init_schema(tx, schema)
        return
    with tx() as c:
        for stmt in schema.split(";"):
            if stmt.strip():
                c.execute(stmt)
        cols = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
        if "lang" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT ''")

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
    conn.execute("UPDATE users SET banned=1, ban_reason=?, balance=0 WHERE user_id=?", (reason, uid))
    conn.execute("UPDATE transactions SET status='reversed' WHERE user_id=? AND status='pending'", (uid,))

def release_matured():
    now = int(time.time())
    unbanned_users = []
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
                ref = c.execute("SELECT banned, ban_reason FROM users WHERE user_id=?", (ref_id,)).fetchone()
                commission = int(t["amount"] * REF_PERCENT)
                
                if ref and ref["banned"] and ref["ban_reason"] == 'offer_reversed':
                    refs_count = c.execute("SELECT COUNT(*) FROM users WHERE referred_by=? AND first_offer_done=1 AND banned=0", (ref_id,)).fetchone()[0]
                    if refs_count >= 5:
                        c.execute("UPDATE users SET banned=0, ban_reason='' WHERE user_id=?", (ref_id,))
                        unbanned_users.append(ref_id)
                elif ref and not ref["banned"] and commission > 0:
                    cur = c.execute(
                        "INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at,approved_at) "
                        "VALUES(?,?,?,?,?,'approved',?,?,?)",
                        ("ref:" + t["txid"], ref_id, "referral", str(u["user_id"]), commission, now, now, now),
                    )
                    if cur.rowcount:
                        c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (commission, ref_id))
    
    for u_id in unbanned_users:
        try:
            bot.send_message(u_id, "🎉 تم فتح حسابك بنجاح لأنك أحضرت 5 إحالات مكتملة! يمكنك الآن استخدام التطبيق.")
        except Exception:
            pass

def _release_loop():
    while True:
        try:
            release_matured()
        except Exception as e:
            print("release error:", e, flush=True)
        time.sleep(300)

# ======================================================================
# التحقق من الهوية
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
    except Exception:
        return False

TRX_RE = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")
_bot_username = None
_bot_username_ts = 0.0

def bot_username():
    global _bot_username, _bot_username_ts
    now = time.time()
    if _bot_username and now - _bot_username_ts < 3600:
        return _bot_username
    try:
        got = bot.get_me().username
        _bot_username = got or _bot_username or "TRXEarnBot"
    except Exception:
        _bot_username = _bot_username or "TRXEarnBot"
    _bot_username_ts = now
    return _bot_username

# ======================================================================
# API
# ======================================================================
@server.route("/")
def home():
    return "TRX Bot is running 🚀"

@server.route("/api/me")
@auth
def api_me():
    try:
        release_matured()
    except Exception:
        pass
    uid = g.user["id"]
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or g.user.get("first_name", ""))
        if u["banned"]:
            return jsonify(success=False, code="banned", reason=u["ban_reason"]), 403
        pending = c.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND status='pending'", (uid,)
        ).fetchone()[0]
        refs = active_referrals(c, uid)
        pwd = c.execute("SELECT COALESCE(SUM(amount),0) FROM withdrawals WHERE user_id=? AND status='pending'", (uid,)).fetchone()[0]
        paidwd = c.execute("SELECT COALESCE(SUM(amount),0) FROM withdrawals WHERE user_id=? AND status='paid'", (uid,)).fetchone()[0]
    return jsonify(
        success=True, pending_wd=pwd / MICRO, paid_wd=paidwd / MICRO, name=g.user.get("first_name", ""), balance=u["balance"] / MICRO,
        pending=(pending + pwd) / MICRO, active_referrals=refs, ref_link=f"https://t.me/{bot_username()}?start={uid}",
        trx_address=u["trx_address"] or "", min_withdraw=MIN_WITHDRAW,
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
    out = [{"id": o["id"], "title": o.get("title", o["id"]), "reward": float(o["reward"]), "url": o["url"].replace("{user_id}", str(uid))} for o in OFFERS.values() if o["kind"] == kind]
    resp = dict(success=True, offers=out)
    if kind == "ad" and ADS_ENABLED:
        with tx() as c:
            resp["ads"] = ad_state(c, uid, int(time.time()))
    return jsonify(resp)

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
    if not ADMIN_ID:
        print("WARNING: ADMIN_ID غير مضبوط، لن يصلك إشعار السحب. استخدم /withdrawals", flush=True)
    else:
        fname = str(g.user.get("first_name") or "").strip() or "-"
        body = ("💸 طلب سحب جديد #%d\n\n👤 الاسم: %s\n🔗 اليوزر: %s\n🆔 الآيدي: %d\n💰 المبلغ: %.4f TRX\n📮 عنوان TRX:\n%s\n\n%s\n\n/paid %d  أو  /reject %d"
                % (wid, "%s", "%s", uid, amount / MICRO, "%s", wd_deadline(now_ts), wid, wid))
        try:
            bot.send_message(ADMIN_ID, body % (html.escape(fname), ("@" + html.escape(uname)) if uname else "-", "<code>" + html.escape(address) + "</code>"), parse_mode="HTML", reply_markup=wd_buttons(wid))
        except Exception as e:
            print("admin notify (html) failed:", e, flush=True)
            try:
                bot.send_message(ADMIN_ID, body % (fname, ("@" + uname) if uname else "-", address), reply_markup=wd_buttons(wid))
            except Exception as e2:
                print("admin notify failed:", e2, flush=True)
    return jsonify(success=True)

# ======================================================================
# إعلانات Monetag: مراحل مشاهدة، الأرباح تتراكم ثم تُجمع بزر، وبعد آخر مرحلة قفل 24 ساعة
# ======================================================================
def ad_stage_row(conn, uid, i, now):
    """صف تقدم مرحلة واحدة؛ المرحلة الأولى مفتوحة دائماً والتالية تُفتح بعد جمع السابقة، ويُفك القفل بعد 24 ساعة."""
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
        stages.append({
            "idx": i, "id": cfg["fmt"], "target": cfg["views"], "views": r["views"],
            "earned": r["earned"] / MICRO, "open": bool(r["opened"]), "lock_left": lock_left,
            "ready": bool(r["views"] >= cfg["views"] and not lock_left),
        })
    return {"stages": stages, "wait": wait}

def _ad_check(st, wait):
    """يرجع رمز الخطأ إن كانت المرحلة لا تقبل مشاهدة الآن."""
    if st["lock_left"] > 0: return "ad_locked"
    if not st["open"]: return "ad_closed"
    if st["ready"]: return "ad_collect"
    if wait > 0: return "ad_cooldown"
    return None

AB_ERR = [""]   # سبب آخر فشل (يظهر للمدير فقط)
def adsgram_send(uid, lang):
    """يطلب إعلاناً من AdsGram ويرسله لمحادثة المستخدم مع البوت. يرجع True عند النجاح."""
    AB_ERR[0] = ""
    try:
        r = requests.get("https://api.adsgram.ai/advbot", timeout=6,
                         params={"tgid": uid, "blockid": ADSGRAM_BLOCK, "language": lang, "token": ADSGRAM_TOKEN})
        if r.status_code != 200:
            AB_ERR[0] = "adsgram http %s: %s" % (r.status_code, (r.text or "")[:140].replace(ADSGRAM_TOKEN, "***")); return False
        d = r.json()
        text = d.get("text_html") or ""
        if not text or not d.get("click_url"):
            AB_ERR[0] = "adsgram empty: %s" % str(d)[:140].replace(ADSGRAM_TOKEN, "***"); return False
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton(d.get("button_name") or "Open", url=d["click_url"]))
        if d.get("reward_url"):
            kb.add(telebot.types.InlineKeyboardButton(d.get("button_reward_name") or "Reward", url=d["reward_url"]))
        img = d.get("image_url")
        kw = dict(parse_mode="HTML", reply_markup=kb)
        try:
            if img and len(text) <= 1000: bot.send_photo(uid, img, caption=text, protect_content=True, **kw)
            else: bot.send_message(uid, text, protect_content=True, **kw)
        except TypeError:
            if img and len(text) <= 1000: bot.send_photo(uid, img, caption=text, **kw)
            else: bot.send_message(uid, text, **kw)
        return True
    except Exception as e:
        AB_ERR[0] = ("error: %s" % e)[:160].replace(ADSGRAM_TOKEN, "***")
        return False

@server.route("/api/ad/start", methods=["POST"])
@auth
def api_ad_start():
    if not ADS_ENABLED:
        return jsonify(success=False, code="ad_invalid")
    uid = g.user["id"]
    if is_vpn(client_ip()):
        return jsonify(success=False, code="vpn"), 403
    try:
        i = int((request.get_json(silent=True) or {}).get("stage", 0))
    except Exception:
        i = -1
    if not 0 <= i < len(AD_STAGES):
        return jsonify(success=False, code="ad_invalid")
    now = int(time.time())
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        info = ad_state(c, uid, now)
        err = _ad_check(info["stages"][i], info["wait"])
        if err:
            return jsonify(success=False, code=err, wait=info["wait"])
        fmt = AD_STAGES[i]["fmt"]
        token = secrets.token_urlsafe(24)
        lang = user_lang(c, uid)
        c.execute("INSERT INTO ad_sessions(token,user_id,fmt,created_at) VALUES(?,?,?,?)", (token, uid, fmt, now))
        c.execute("DELETE FROM ad_sessions WHERE created_at<?", (now - 86400,))
    if fmt == "ab" and not adsgram_send(uid, lang):   # الإرسال خارج المعاملة حتى لا نقفل القاعدة أثناء طلب الشبكة
        with tx() as c:
            c.execute("DELETE FROM ad_sessions WHERE token=?", (token,))
        return jsonify(success=False, code="ad_none", detail=(AB_ERR[0] if uid == ADMIN_ID else ""))
    return jsonify(success=True, token=token, fmt=fmt)

@server.route("/api/ad/complete", methods=["POST"])
@auth
def api_ad_complete():
    if not ADS_ENABLED:
        return jsonify(success=False, code="ad_invalid")
    token = str((request.get_json(silent=True) or {}).get("token", ""))
    uid = g.user["id"]
    now = int(time.time())
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        s = c.execute("SELECT * FROM ad_sessions WHERE token=? AND user_id=?", (token, uid)).fetchone()
        if not s or s["used"] or now - s["created_at"] > 900:
            return jsonify(success=False, code="ad_invalid")
        idx = [k for k, cfg in enumerate(AD_STAGES) if cfg["fmt"] == s["fmt"]]
        if not idx:
            return jsonify(success=False, code="ad_invalid")
        i = idx[0]; cfg = AD_STAGES[i]
        if now - s["created_at"] < cfg["min"]:
            return jsonify(success=False, code="ad_early")
        info = ad_state(c, uid, now)
        err = _ad_check(info["stages"][i], info["wait"])
        if err:
            return jsonify(success=False, code=err, wait=info["wait"])
        c.execute("UPDATE ad_sessions SET used=1 WHERE token=?", (token,))
        c.execute("UPDATE ad_stage SET views=views+1, earned=earned+? WHERE user_id=? AND stage=?",
                  (int(cfg["reward"] * MICRO), uid, i))
        c.execute("UPDATE ad_progress SET last_view=? WHERE user_id=?", (now, uid))
        if REF_ON_AD:
            c.execute("UPDATE users SET first_offer_done=1 WHERE user_id=? AND first_offer_done=0", (uid,))
        out = ad_state(c, uid, now)
    return jsonify(success=True, ads=out)

@server.route("/api/ad/collect", methods=["POST"])
@auth
def api_ad_collect():
    if not ADS_ENABLED:
        return jsonify(success=False, code="ad_invalid")
    uid = g.user["id"]
    now = int(time.time())
    try:
        i = int((request.get_json(silent=True) or {}).get("stage", 0))
    except Exception:
        i = -1
    if not 0 <= i < len(AD_STAGES):
        return jsonify(success=False, code="ad_notready")
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        r = ad_stage_row(c, uid, i, now)
        st = ad_state(c, uid, now)["stages"][i]
        if st["lock_left"] > 0:
            return jsonify(success=False, code="ad_locked")
        if not st["open"] or not st["ready"]:
            return jsonify(success=False, code="ad_notready")
        amount = r["earned"]
        if amount > 0:
            c.execute(
                "INSERT INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at) "
                "VALUES(?,?,?,?,?,'pending',?,?)",
                ("adclaim:%d:%s" % (uid, secrets.token_hex(8)), uid, "ad", "monetag:stage%d" % (i + 1), amount, now, now))
        c.execute("UPDATE ad_stage SET views=0, earned=0, opened=?, locked_until=? WHERE user_id=? AND stage=?",
                  (1 if i == 0 else 0, now + AD_LOCK_HOURS * 3600, uid, i))
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

# ================= دوال استقبال أرباح GG Agency المعدلة =================
@server.route("/postback")
def postback():
    bad = _check_secret()
    if bad: return bad
    txid = request.args.get("txid", "").strip()
    offer_id = request.args.get("offer_id", "")
    offer = OFFERS.get(offer_id)
    
    try:
        uid = int(request.args.get("user_id", ""))
    except ValueError:
        return Response("bad user", 400)
    
    if not txid or not offer: return Response("bad request", 400)
    
    now = int(time.time())
    hold = 0 if offer["kind"] == "ad" else VERIFY_HOURS * 3600
    
    # قراءة مبلغ العمولة بالدولار من المنصة
    try:
        platform_payout_usd = float(request.args.get("payout", 0))
    except (ValueError, TypeError):
        platform_payout_usd = 0

    # حساب 25% للمستخدم وتحويلها إلى ترون بناءً على سعر الصرف المتغير
    if platform_payout_usd > 0:
        user_usd = platform_payout_usd * 0.25
        user_trx = user_usd / TRX_USD_PRICE if TRX_USD_PRICE > 0 else 0
        user_amount = int(user_trx * MICRO)
    else:
        user_amount = int(float(offer["reward"]) * MICRO)

    # تم إلغاء شرط الـ 5 ترون كما طلبت، يضاف أي مبلغ
    if user_amount <= 0: return Response("no payout", 200)

    with tx() as c:
        u = c.execute("SELECT banned FROM users WHERE user_id=?", (uid,)).fetchone()
        if not u or u["banned"]: return Response("ignored", 200)
        
        cur = c.execute(
            "INSERT OR IGNORE INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at) "
            "VALUES(?,?,?,?,?,'pending',?,?)", 
            (txid, uid, offer["kind"], offer["id"], user_amount, now, now + hold)
        )
        if not cur.rowcount: return Response("duplicate", 200)
        
    if hold == 0: release_matured()
    return Response("OK", 200)

@server.route("/postback/reverse")
def postback_reverse():
    bad = _check_secret()
    if bad: return bad
    txid = request.args.get("txid", "").strip()
    uid = None
    with tx() as c:
        t = c.execute("SELECT * FROM transactions WHERE txid=? AND kind!='referral'", (txid,)).fetchone()
        if not t or t["status"] == "reversed": return Response("OK", 200)
        
        uid = t["user_id"]
        # 1. إلغاء العملية
        c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (t["id"],))
        
        # 2. إذا كان المستخدم قد استلم الرصيد، نسحبه منه
        if t["status"] == "approved":
            c.execute("UPDATE users SET balance=MAX(balance-?,0) WHERE user_id=?", (t["amount"], uid))
        
        # 3. سحب عمولة الإحالة إن وجدت
        r = c.execute("SELECT * FROM transactions WHERE txid=? AND status='approved'", ("ref:" + txid,)).fetchone()
        if r:
            c.execute("UPDATE transactions SET status='reversed' WHERE id=?", (r["id"],))
            c.execute("UPDATE users SET balance=MAX(balance-?,0) WHERE user_id=?", (r["amount"], r["user_id"]))
            
        # 4. حظر المستخدم (كما طلبت ليفتح الحساب بجلب 5 إحالات)
        ban_user(c, uid, "offer_reversed")
        lang = user_lang(c, uid)
    try:
        # إرسال رسالة للمستخدم
        bot.send_message(uid, "🚫 تم إيقاف حسابك لأنك ألغيت اشتراكاً. لفتح الحساب، يجب أن تجلب 5 إحالات مكتملة.")
    except Exception:
        pass
    return Response("OK", 200)
# ======================================================================

# ======================================================================
# النصوص والترجمات
# ======================================================================
HEADS = {"ar": ["🌍 عن البوت", "⚠️ تنبيه مهم جداً", "💰 حد السحب الأدنى", "🚫 المحظورات", "⏳ التحقق من الأرباح", "👥 نظام الإحالة", "💸 السحب"], "en": ["🌍 About", "⚠️ Important warning", "💰 Minimum withdrawal", "🚫 Prohibited", "⏳ Earnings verification", "👥 Referrals", "💸 Withdrawals"], "es": ["🌍 Sobre el bot", "⚠️ Aviso importante", "💰 Retiro mínimo", "🚫 Prohibido", "⏳ Verificación", "👥 Referidos", "💸 Retiros"], "de": ["🌍 Über den Bot", "⚠️ Wichtige Warnung", "💰 Mindestauszahlung", "🚫 Verboten", "⏳ Verifizierung", "👥 Empfehlungen", "💸 Auszahlungen"], "fr": ["🌍 À propos", "⚠️ Avertissement important", "💰 Retrait minimum", "🚫 Interdit", "⏳ Vérification", "👥 Parrainage", "💸 Retraits"], "ru": ["🌍 О боте", "⚠️ Важное предупреждение", "💰 Минимум для вывода", "🚫 Запрещено", "⏳ Проверка начислений", "👥 Рефералы", "💸 Вывод"], "pt": ["🌍 Sobre o bot", "⚠️ Aviso importante", "💰 Saque mínimo", "🚫 Proibido", "⏳ Verificação", "👥 Indicações", "💸 Saques"], "nl": ["🌍 Over de bot", "⚠️ Belangrijke waarschuwing", "💰 Minimum opname", "🚫 Verboden", "⏳ Verificatie", "👥 Referrals", "💸 Opnames"], "pl": ["🌍 O bocie", "⚠️ Ważne ostrzeżenie", "💰 Minimalna wypłata", "🚫 Zakazy", "⏳ Weryfikacja", "👥 Polecenia", "💸 Wypłaty"]}

BODIES = {
    "ar": ["البوت منصة لتحقيق الربح من:\n🎬 مشاهدة الإعلانات\n📱 عروض الاشتراك برقم الهاتف\n📝 عروض التسجيل\n📲 تثبيت التطبيقات", "لا تدفع أي مبلغ لأي منصة أو موقع أو شخص أثناء استخدام البوت. كل المهام مجانية بالكامل. أي جهة تطلب مالاً باسم البوت فهي احتيال، وسيتم حظر أي مستخدم يطلب أموالاً من غيره.", "السحب متاح مهما كان رصيدك.", "❌ استخدام VPN أو البروكسي\n❌ استخدام الواي فاي (المطلوب بيانات الجوال)\n❌ أكثر من حساب للشخص الواحد\n❌ بيانات وهمية أو أرقام غير حقيقية\n❌ التلاعب بالعروض أو برامج الغش", "لا يُضاف رصيد تثبيت التطبيقات أو التسجيل أو الاشتراك برقم الهاتف إلا بعد التحقق، وتستغرق من 24 إلى 72 ساعة (حالياً {h} ساعة). إذا ألغيت الاشتراك أو حذفت التطبيق أو ألغيت التسجيل فسيُلغى حسابك مباشرة مع أرباحه.", "تحصل على 3% من أرباح كل من تدعوه، مدى الحياة. لا تُحتسب الإحالة إلا بعد أن يشترك المدعو ويُكمل عرضاً ناجحاً واحداً على الأقل (اشتراك/تسجيل/تثبيت).", "لا يمكن السحب إلا بعد أن تُحضر مستخدماً حقيقياً يُكمل أول عرض ناجح له، وبعد بلوغ الحد الأدنى. تراجع الإدارة كل طلب قبل الدفع، ويحق لها حظر أي حساب مخالف وإلغاء أرباحه."],
    "en": ["A platform to earn from:\n🎬 Watching ads\n📱 Phone-number subscription offers\n📝 Registration offers\n📲 App installs", "Never pay any money to any platform, website or person while using the bot. All tasks are completely free. Anyone asking for money in the bot's name is a scammer, and users who ask others for money will be banned.", "Withdrawal is available at any balance.", "❌ VPN or proxy of any kind\n❌ Wi-Fi (mobile data is required)\n❌ More than one account per person\n❌ Fake data or unreal numbers\n❌ Cheating or manipulating offers", "Rewards for app installs, registrations and phone subscriptions are credited only after verification, which takes 24 to 72 hours (currently {h}h). If you cancel the subscription, uninstall the app or cancel the registration, your account and its earnings are cancelled immediately.", "Earn 3% of your referrals' earnings for life. A referral counts only after the invited user completes at least one successful offer (subscription/registration/install).", "You can withdraw only after bringing a real user who completes their first successful offer, and after reaching the minimum. Every request is reviewed before payment, and accounts that break the rules may be banned and their earnings cancelled."],
    "es": ["Plataforma para ganar con:\n🎬 Ver anuncios\n📱 Suscripciones con número de teléfono\n📝 Registros\n📲 Instalar apps", "No pagues dinero a ninguna plataforma, sitio o persona. Todas las tareas son gratuitas. Quien pida dinero en nombre del bot es un estafador y será bloqueado.", "El retiro está disponible con cualquier saldo.", "❌ VPN o proxy\n❌ Wi-Fi (usa datos móviles)\n❌ Más de una cuenta por persona\n❌ Datos falsos\n❌ Trampas", "El saldo de instalaciones, registros y suscripciones telefónicas se acredita solo tras verificar (24–72 h, ahora {h} h). Si cancelas la suscripción, borras la app o anulas el registro, tu cuenta y ganancias se cancelan de inmediato.", "Ganas 3% de por vida de lo que ganen tus referidos. Un referido cuenta solo cuando completa al menos una oferta exitosa.", "Solo puedes retirar después de traer a un usuario real que complete su primera oferta exitosa y alcanzar el mínimo. Cada solicitud se revisa antes de pagar."],
    "de": ["Plattform zum Verdienen durch:\n🎬 Werbung ansehen\n📱 Telefon-Abos\n📝 Registrierungen\n📲 App-Installationen", "Zahlen Sie niemals Geld an Plattformen, Websites oder Personen. Alle Aufgaben sind kostenlos. Wer im Namen des Bots Geld verlangt, ist ein Betrüger und wird gesperrt.", "Die Auszahlung ist bei jedem Guthaben möglich.", "❌ VPN oder Proxy\n❌ WLAN (Mobilfunkdaten nutzen)\n❌ Mehrere Konten pro Person\n❌ Falsche Daten\n❌ Betrug", "Belohnungen für Installationen, Registrierungen und Telefon-Abos werden erst nach Prüfung gutgeschrieben (24–72 Std., aktuell {h} Std.). Bei Kündigung, Deinstallation oder Abmeldung wird Ihr Konto sofort gelöscht.", "3% lebenslang auf die Einnahmen Ihrer Empfehlungen. Eine Empfehlung zählt erst nach mindestens einem erfolgreichen Angebot.", "Auszahlung nur, nachdem ein echter Nutzer sein erstes erfolgreiches Angebot abgeschlossen hat und das Minimum erreicht ist. Jeder Antrag wird vorher geprüft."],
    "fr": ["Plateforme pour gagner avec :\n🎬 Pubs\n📱 Abonnements par téléphone\n📝 Inscriptions\n📲 Installations d'apps", "Ne payez jamais d'argent à une plateforme, un site ou une personne. Tout est gratuit. Quiconque demande de l'argent au nom du bot est un escroc et sera banni.", "Le retrait est disponible quel que soit le solde.", "❌ VPN ou proxy\n❌ Wi-Fi (utilisez les données mobiles)\n❌ Plusieurs comptes par personne\n❌ Fausses données\n❌ Triche", "Les gains d'installation, d'inscription et d'abonnement téléphonique sont crédités après vérification (24–72 h, actuellement {h} h). Si vous annulez l'abonnement, désinstallez l'app ou annulez l'inscription, votre compte est supprimé immédiatement.", "3% à vie sur les gains de vos filleuls. Un filleul compte seulement après au moins une offre réussie.", "Retrait possible uniquement après qu'un vrai utilisateur parrainé a terminé sa première offre réussie et que le minimum est atteint. Chaque demande est examinée avant paiement."],
    "ru": ["Платформа для заработка на:\n🎬 Просмотре рекламы\n📱 Подписках по номеру телефона\n📝 Регистрациях\n📲 Установке приложений", "Никому не платите деньги. Все задания бесплатны. Тот, кто просит деньги от имени бота, — мошенник и будет заблокирован.", "Вывод доступен при любом балансе.", "❌ VPN или прокси\n❌ Wi-Fi (используйте мобильный интернет)\n❌ Несколько аккаунтов\n❌ Фейковые данные\n❌ Обман", "Начисления за установки, регистрации и подписки по телефону зачисляются только после проверки (24–72 ч, сейчас {h} ч). Если вы отмените подписку, удалите приложение или отмените регистрацию, аккаунт будет аннулирован сразу.", "3% пожизненно от заработка рефералов. Реферал засчитывается после хотя бы одного успешного задания.", "Вывод возможен только после того, как реальный приглашённый пользователь выполнит первое успешное задание, и при достижении минимума. Каждая заявка проверяется."],
    "pt": ["Plataforma para ganhar com:\n🎬 Anúncios\n📱 Assinaturas por telefone\n📝 Registros\n📲 Instalação de apps", "Não pague dinheiro a nenhuma plataforma, site ou pessoa. Tudo é gratuito. Quem pedir dinheiro em nome do bot é golpista e será banido.", "O saque está disponível com qualquer saldo.", "❌ VPN ou proxy\n❌ Wi-Fi (use dados móveis)\n❌ Contas múltiplas\n❌ Dados falsos\n❌ Trapaças", "Os ganhos de instalações, registros e assinaturas por telefone só são creditados após verificação (24–72 h, atualmente {h} h). Se cancelar a assinatura, desinstalar o app ou cancelar o registro, sua conta será cancelada imediatamente.", "3% vitalício sobre os ganhos dos seus indicados. A indicação só conta após ao menos uma oferta bem-sucedida.", "O saque só é possível depois que um usuário real indicado concluir a primeira oferta bem-sucedida e o mínimo for atingido. Cada pedido é revisado antes do pagamento."],
    "nl": ["Platform om te verdienen met:\n🎬 Advertenties\n📱 Telefoonabonnementen\n📝 Registraties\n📲 App-installaties", "Betaal nooit geld aan een platform, website of persoon. Alles is gratis. Wie namens de bot geld vraagt is een oplichter en wordt geblokkeerd.", "Opnemen is mogelijk bij elk saldo.", "❌ VPN of proxy\n❌ Wi-Fi (gebruik mobiele data)\n❌ Meerdere accounts\n❌ Nepgegevens\n❌ Valsspelen", "Beloningen voor installaties, registraties en telefoonabonnementen worden pas na verificatie bijgeschreven (24–72 uur, nu {h} uur). Bij opzeggen, verwijderen van de app of annuleren van de registratie wordt je account direct geannuleerd.", "3% levenslang van de winst van je referrals. Een referral telt pas na minstens één geslaagde aanbieding.", "Opnemen kan pas nadat een echte genodigde zijn eerste geslaagde aanbieding heeft voltooid en het minimum is bereikt. Elk verzoek wordt eerst beoordeeld."],
    "pl": ["Platforma do zarabiania na:\n🎬 Reklamach\n📱 Subskrypcjach telefonicznych\n📝 Rejestracjach\n📲 Instalacji aplikacji", "Nigdy nie płać żadnej platformie, stronie ani osobie. Wszystko jest darmowe. Kto żąda pieniędzy w imieniu bota, jest oszustem i zostanie zablokowany.", "Wypłata jest dostępna przy każdym saldzie.", "❌ VPN lub proxy\n❌ Wi-Fi (używaj danych mobilnych)\n❌ Wiele kont\n❌ Fałszywe dane\n❌ Oszustwa", "Nagrody za instalacje, rejestracje i subskrypcje telefoniczne są dodawane dopiero po weryfikacji (24–72 godz., obecnie {h} godz.). Anulowanie subskrypcji, usunięcie aplikacji lub rejestracji natychmiast anuluje konto.", "3% dożywotnio od zarobków poleconych. Polecenie liczy się po co najmniej jednej udanej ofercie.", "Wypłata możliwa dopiero po tym, jak prawdziwy zaproszony użytkownik ukończy pierwszą udaną ofertę i osiągniesz minimum. Każdy wniosek jest sprawdzany."]
}

TERMS_TITLE = {"ar": "📜 شروط وأحكام TRX Earn Bot", "en": "📜 TRX Earn Bot Terms & Conditions", "es": "📜 Términos de TRX Earn Bot", "de": "📜 AGB von TRX Earn Bot", "fr": "📜 Conditions de TRX Earn Bot", "ru": "📜 Условия TRX Earn Bot", "pt": "📜 Termos do TRX Earn Bot", "nl": "📜 Voorwaarden van TRX Earn Bot", "pl": "📜 Regulamin TRX Earn Bot"}
AGREE_BTN = {"ar": "أوافق وأفتح التطبيق المصغر 🚀", "en": "I Agree & Open Mini App 🚀", "es": "Aceptar y abrir Mini App 🚀", "de": "Zustimmen & Mini App öffnen 🚀", "fr": "Accepter et ouvrir l'App 🚀", "ru": "Согласен, открыть Mini App 🚀", "pt": "Concordar e abrir Mini App 🚀", "nl": "Akkoord & Mini App openen 🚀", "pl": "Zgadzam się i otwórz 🚀"}
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

_UI_Z = """
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
zb4wBoiBAQwYMHj4V/8PZd5aVA==
"""
UI = json.loads(zlib.decompress(base64.b64decode("".join(_UI_Z.split()))).decode("utf-8"))

_UIX_Z = """
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
"""
for _l, _d in json.loads(zlib.decompress(base64.b64decode("".join(_UIX_Z.split()))).decode("utf-8")).items():
    UI[_l].update(_d)

LANG_NAMES = {"ar": "🇸🇦 العربية", "en": "🇬🇧 English", "es": "🇪🇸 Español", "de": "🇩🇪 Deutsch", "fr": "🇫🇷 Français", "ru": "🇷🇺 Русский", "pt": "🇧🇷 Português", "nl": "🇳🇱 Nederlands", "pl": "🇵🇱 Polski"}

MSG = {
    "ar": {"banned_start": "🚫 تم حظر حسابك.", "reversed": "🚫 تم إيقاف حسابك لأنك ألغيت اشتراكاً أو عرضاً. لفتح الحساب، يجب أن تجلب 5 إحالات مكتملة.", "paid": "✅ تم دفع {amt} TRX إلى محفظتك.\n{note}", "rejected": "❌ تم رفض طلب السحب #{id} وأُعيد الرصيد لحسابك.\n{note}"},
    "en": {"banned_start": "🚫 Your account has been banned.", "reversed": "🚫 Your account was suspended because you cancelled an offer. To unlock it, you must bring 5 completed referrals.", "paid": "✅ {amt} TRX has been sent to your wallet.\n{note}", "rejected": "❌ Withdrawal request #{id} was rejected and the balance was returned to your account.\n{note}"},
    "es": {"banned_start": "🚫 Tu cuenta ha sido bloqueada.", "reversed": "🚫 Tu cuenta fue suspendida porque cancelaste una oferta. Para desbloquearla, debes traer 5 referidos completados.", "paid": "✅ Se enviaron {amt} TRX a tu billetera.\n{note}", "rejected": "❌ La solicitud de retiro #{id} fue rechazada y el saldo volvió a tu cuenta.\n{note}"},
    "de": {"banned_start": "🚫 Dein Konto wurde gesperrt.", "reversed": "🚫 Dein Konto wurde gesperrt, weil du ein Angebot abgebrochen hast. Um es zu entsperren, musst du 5 abgeschlossene Empfehlungen bringen.", "paid": "✅ {amt} TRX wurden an deine Wallet gesendet.\n{note}", "rejected": "❌ Auszahlungsantrag #{id} wurde abgelehnt und das Guthaben wurde deinem Konto gutgeschrieben.\n{note}"},
    "fr": {"banned_start": "🚫 Votre compte a été banni.", "reversed": "🚫 Votre compte a été suspendu car vous avez annulé une offre. Pour le débloquer, vous devez apporter 5 filleuls complétés.", "paid": "✅ {amt} TRX ont été envoyés à votre portefeuille.\n{note}", "rejected": "❌ La demande de retrait #{id} a été refusée et le solde a été restitué à votre compte.\n{note}"},
    "ru": {"banned_start": "🚫 Ваш аккаунт заблокирован.", "reversed": "🚫 Ваш аккаунт заблокирован, потому что вы отменили предложение. Чтобы разблокировать его, вы должны привлечь 5 завершенных рефералов.", "paid": "✅ {amt} TRX отправлены на ваш кошелёк.\n{note}", "rejected": "❌ Заявка на вывод #{id} отклонена, баланс возвращён на ваш аккаунт.\n{note}"},
    "pt": {"banned_start": "🚫 Sua conta foi banida.", "reversed": "🚫 Sua conta foi suspensa porque você cancelou uma oferta. Para desbloquear, você deve trazer 5 indicados concluídos.", "paid": "✅ {amt} TRX foram enviados para sua carteira.\n{note}", "rejected": "❌ O pedido de saque #{id} foi recusado e o saldo voltou para sua conta.\n{note}"},
    "nl": {"banned_start": "🚫 Je account is geblokkeerd.", "reversed": "🚫 Je account is geblokkeerd omdat je een aanbieding hebt geannuleerd. Om het te deblokkeren, moet je 5 voltooide referrals aanbrengen.", "paid": "✅ {amt} TRX is naar je wallet gestuurd.\n{note}", "rejected": "❌ Opnameverzoek #{id} is afgewezen en het saldo is teruggestort op je account.\n{note}"},
    "pl": {"banned_start": "🚫 Twoje konto zostało zablokowane.", "reversed": "🚫 Twoje konto zostało zawieszone, ponieważ anulowałeś ofertę. Aby je odblokować, musisz przyprowadzić 5 ukończonych poleconych.", "paid": "✅ {amt} TRX zostało wysłane do Twojego portfela.\n{note}", "rejected": "❌ Wniosek o wypłatę #{id} został odrzucony, a saldo wróciło na Twoje konto.\n{note}"}
}

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

# ======================================================================
# صفحة التطبيق المصغر (HTML)
# ======================================================================
@server.route("/webapp")
def webapp():
    terms = {l: {"title": TERMS_TITLE[l], "sections": terms_sections(l)} for l in LANGS}
    page = (WEBAPP_HTML
            .replace("__UI__", json.dumps(UI, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__TERMS__", json.dumps(terms, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__LANG_NAMES__", json.dumps(LANG_NAMES, ensure_ascii=False))
            .replace("__AD_ZONE__", MONETAG_ZONE).replace("__OC_SPOT__", OC_SPOT)
            .replace("__AD_SDK__", "".join(
                ('<script src="%s"></script>' % html.escape(OC_SDK_URL, quote=True)) if n == "oc" else
                ('<script src="%s" data-zone="%s" data-sdk="show_%s"></script>' % (html.escape(MONETAG_SDK_URL, quote=True), MONETAG_ZONE, MONETAG_ZONE))
                for n in AD_NETS) if ADS_ENABLED else ""))
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
        referrer = None
        parts = (message.text or "").split()
        if len(parts) > 1 and parts[1].isdigit():
            referrer = int(parts[1])
        
        with tx() as c:
            u = ensure_user(c, uid, username, referrer)
            saved_lang = u["lang"]
            if saved_lang in HEADS:
                lang = saved_lang
            else:
                lang = (message.from_user.language_code or "en")[:2].lower()
                if lang not in HEADS:
                    lang = "en"
                c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
                
        if u["banned"]:
            if u["ban_reason"] == 'offer_reversed':
                msg = f"🚫 حسابك موقوف بسبب إلغاء عرض سابق.\n\nلفتح الحساب مرة أخرى، يجب عليك إحضار 5 إحالات مكتملة (أكملن عرضاً ناجحاً).\n\n🔗 رابط الإحالة الخاص بك:\nhttps://t.me/{bot_username()}?start={uid}"
                bot.reply_to(message, msg)
            else:
                bot.reply_to(message, msg_for(lang, "banned_start"))
            return
            
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            AGREE_BTN[lang], web_app=telebot.types.WebAppInfo(url=f"{RENDER_URL}/webapp")))
        bot.reply_to(message, terms_html(lang), parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"Error in start handler: {e}", flush=True)

def is_admin(m):
    return ADMIN_ID and m.from_user.id == ADMIN_ID

def wd_deadline(created):
    """نص الموعد النهائي لتحويل السحب والوقت المتبقي (48 ساعة افتراضياً)."""
    end = created + WITHDRAW_HOURS * 3600
    left = end - int(time.time())
    when = time.strftime("%Y-%m-%d %H:%M", time.gmtime(end + ADMIN_TZ * 3600))
    if left <= 0:
        return "⏰ انتهت المهلة! (كان الموعد %s)" % when
    return "⏳ المهلة: %d ساعة و%d دقيقة\n📅 آخر موعد للتحويل: %s" % (left // 3600, left % 3600 // 60, when)

@bot.message_handler(commands=["myid"])
def cmd_myid(m):
    bot.reply_to(m, "آيديك: %d" % m.from_user.id)

@bot.message_handler(commands=["withdrawals"])
def cmd_withdrawals(m):
    if not is_admin(m):
        bot.reply_to(m, "هذا الأمر للأدمن فقط. آيديك: %d\nضع هذا الرقم في ADMIN_ID على Render." % m.from_user.id)
        return
    with tx() as c:
        rows = c.execute("SELECT w.*, u.username AS uname FROM withdrawals w LEFT JOIN users u ON u.user_id=w.user_id WHERE w.status='pending' ORDER BY w.id LIMIT 20").fetchall()
    if not rows:
        bot.reply_to(m, "لا توجد طلبات سحب معلقة ✅")
        return
    for r in rows:
        bot.send_message(m.chat.id, "💸 طلب سحب #%d\n👤 %s | 🆔 %d\n💰 %.4f TRX\n📮 عنوان TRX:\n<code>%s</code>\n\n%s\n\n/paid %d  أو  /reject %d" % (
            r["id"], ("@" + html.escape(r["uname"])) if r["uname"] else "-", r["user_id"], r["amount"] / MICRO,
            html.escape(r["address"]), wd_deadline(r["created_at"]), r["id"], r["id"]), parse_mode="HTML", reply_markup=wd_buttons(r["id"]))

def wd_buttons(wid):
    """أزرار تحت رسالة السحب: تم الدفع / إلغاء الطلب."""
    mk = telebot.types.InlineKeyboardMarkup()
    mk.add(telebot.types.InlineKeyboardButton("✅ تم الدفع", callback_data="wd:p:%d" % wid),
           telebot.types.InlineKeyboardButton("❌ إلغاء الطلب", callback_data="wd:r:%d" % wid))
    return mk

def process_withdrawal(wid, paid, note=""):
    """ينفّذ الدفع أو الرفض (مع إرجاع الرصيد) ويُعلم المستخدم. يرجع None إن لم يوجد الطلب."""
    with tx() as c:
        w = c.execute("SELECT * FROM withdrawals WHERE id=? AND status='pending'", (wid,)).fetchone()
        if not w:
            return None
        lang = user_lang(c, w["user_id"])
        c.execute("UPDATE withdrawals SET status=?, note=?, processed_at=? WHERE id=?", ("paid" if paid else "rejected", note, int(time.time()), wid))
        if not paid:
            c.execute("UPDATE users SET balance=balance+? WHERE user_id=? AND banned=0", (w["amount"], w["user_id"]))
    try:
        if paid:
            bot.send_message(w["user_id"], msg_for(lang, "paid", amt=(f"{w['amount'] / MICRO:.4f}".rstrip("0").rstrip(".")), note=note))
        else:
            bot.send_message(w["user_id"], msg_for(lang, "rejected", id=wid, note=note))
    except Exception:
        pass
    return w

@bot.message_handler(commands=["paid", "reject"])
def cmd_process(m):
    if not is_admin(m):
        return
    args = (m.text or "").split()
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(m, "الاستخدام: /paid 12 [رقم العملية]  أو  /reject 12")
        return
    wid, paid = int(args[1]), args[0].startswith("/paid")
    w = process_withdrawal(wid, paid, " ".join(args[2:]))
    if not w:
        bot.reply_to(m, "الطلب غير موجود أو تمت معالجته.")
        return
    bot.reply_to(m, f"تم {'الدفع' if paid else 'الرفض وإرجاع الرصيد'} للطلب #{wid} ✅")

@bot.callback_query_handler(func=lambda call: (call.data or "").startswith("wd:"))
def cb_withdrawal(call):
    if not (ADMIN_ID and call.from_user.id == ADMIN_ID):
        bot.answer_callback_query(call.id, "للأدمن فقط")
        return
    try:
        _, kind, wid = call.data.split(":")
        wid, paid = int(wid), kind == "p"
    except Exception:
        bot.answer_callback_query(call.id, "خطأ")
        return
    w = process_withdrawal(wid, paid)
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass
    if not w:
        bot.answer_callback_query(call.id, "الطلب غير موجود أو تمت معالجته")
        return
    bot.answer_callback_query(call.id, "تم الدفع ✅" if paid else "تم الإلغاء وإرجاع الرصيد ❌")
    bot.send_message(call.message.chat.id, ("✅ تم الدفع للطلب #%d (%.4f TRX) وتم إشعار المستخدم." if paid else "❌ تم إلغاء الطلب #%d وأُرجع %.4f TRX لرصيد المستخدم.") % (wid, w["amount"] / MICRO))

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

@bot.message_handler(commands=["resetads"])
def cmd_resetads(m):
    """للأدمن: /resetads يصفّر مراحل الإعلانات وعدّاداتها لكل المستخدمين، و /resetads 123456 لمستخدم واحد."""
    if not is_admin(m):
        return
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

def _backfill_ref():
    if not REF_ON_AD: return
    try:
        with tx() as c:
            c.execute("UPDATE users SET first_offer_done=1 WHERE first_offer_done=0 AND (user_id IN (SELECT user_id FROM transactions WHERE kind='ad') OR user_id IN (SELECT user_id FROM ad_stage WHERE views>0))")
    except Exception as e:
        print("backfill_ref error:", e, flush=True)
_backfill_ref()

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
