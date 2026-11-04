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
IPQS_KEY = os.environ.get("IPQS_KEY", "")
MICRO = 1_000_000
TRX_USD_PRICE = float(os.environ.get("TRX_USD_PRICE", "0.34")) # سعر التترون مقابل الدولار

bot = telebot.TeleBot(TOKEN, threaded=False)
server = Flask(__name__)

KINDS = ("phone", "app", "site", "ad")

# إعلانات Monetag: مرحلتان (الأولى فيديو 50 مشاهدة، الثانية سريع 100 مشاهدة). كل القيم قابلة للتغيير من متغيرات البيئة
MONETAG_ZONE = "".join(ch for ch in os.environ.get("MONETAG_ZONE", "12130531") if ch.isdigit()) or "12130531"
MONETAG_SDK_URL = os.environ.get("MONETAG_SDK_URL", "https://libtl.com/sdk.js")
OC_SDK_URL = os.environ.get("OC_SDK_URL", "https://js.onclckvd.com/in-stream-ad-admanager/tma.js")   # Onclicka
OC_SPOT = "".join(ch for ch in os.environ.get("OC_SPOT_ID", "6154562") if ch.isalnum()) or "6154562"
ADSGRAM_TOKEN = os.environ.get("ADSGRAM_TOKEN", "").strip()
ADSGRAM_BLOCK = "".join(ch for ch in os.environ.get("ADSGRAM_BLOCK", "57655") if ch.isdigit()) or "57655"
# oc = Onclicka ، mt = Monetag ، ab = AdsGram (إعلان يُرسل لمحادثة البوت؛ لا يعمل إلا مع ADSGRAM_TOKEN) — بالترتيب
AD_NETS = [x for x in dict.fromkeys(t.strip() for t in os.environ.get("AD_NET", "oc,mt,ab").lower().split(",")) if x in ("mt", "oc") or (x == "ab" and ADSGRAM_TOKEN)] or ["oc", "mt"]
AD_STAGES = [{"fmt": n, "views": int(os.environ.get("AD_VIEWS", "10")), "reward": float(os.environ.get("AD_REWARD", "0.0005")), "min": 6 if n == "ab" else 2} for n in AD_NETS]
AD_COOLDOWN = int(os.environ.get("AD_COOLDOWN_SECONDS", "2"))   # الفاصل بين مشاهدة وأخرى
AD_LOCK_HOURS = int(os.environ.get("AD_LOCK_HOURS", "24"))        # قفل كل مرحلة بعد جمع رصيدها

def load_offers():
    try:
        raw = json.loads(os.environ.get("OFFERS_JSON", "[]"))
    except Exception:
        raw = []
    if not isinstance(raw, list):
        return {}
    offers = {}
    for o in raw:
        if not isinstance(o, dict):
            continue
        try:
            reward = float(o.get("reward", 0))
        except (ValueError, TypeError):
            continue
        if (o.get("id") and o.get("kind") in KINDS
                and str(o.get("url", "")).startswith("https://") and reward > 0):
            offers[str(o["id"])] = o
    return offers

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
eNqlXFtzHMd1/isdVdm6hEIiO6xUuUoP4EUydSOLoMhYlSpW727v7mBnp9dzwWrX5SoBJERKZCxbcmJLvsgKI5GgRPECggAhkKrK
Eu+Lt8Wr/kD8E/Kd0z33GVJOHkjs7vScPvf++vSZ+cVTynvqJ+IXT3V1X+HDU3/99IO/iJ/SlwPiKV+1zW+/+VycVG3l+9IN6MKg
qz07/KPb4gR9EwtRI2j6ziB0tEdj5GAQ2CF3xDEvCKXrinn6ERcDJ1T26uVfg3bHCULlC+2JBb6CIUOMV6EZ8+G6OGO+0gUn7LZ8
ObSXtsSZ+Ae+K2x26cp3/3Hvf7Y+wG34Ln4ojkqfucIs/ZitP4pT/A0/95UX0a+v46/47pOPcStTU27TKuaM/YhfG9KlXw5Hvq+8
UJw6+S8CP0mvyVcHymvR5RP463gdsaR8p+00ZayXvuO5jtHe647n9KO+iCWSLkzh/ZIo0si2/PkpFuVPH4lj/YH2Q4npTkauCiAR
qdSPmkQ2sKOPJCp57rkzKc3nnhM/05FoSi+ZScg26dtXstklJsOuEn3LjfRaouHjV7rwAo1xBUQfQP2qha/GD+b+1WO/eO65xDNo
ItKz+PEPRFv7wnXaSrR93RcjHfnJncHTQmEUqAdM5JMvQeQwqc91acrjbYxjYsfadCcxjmtCiiDjYgITtBTxBIYFnO2AmUU2mzqC
moYO3K2hcE9AFlGtOXFKi8hzdbMnnJBHi34UhEZWcbBCxkAcP5n8jPk9NQS9ZlMFQTtyhSZG52ygnCpFighGcOq+eObHP3jWDjrs
sUPPw2pLKp3GXmXzLXSlr4wo0EaPraGsUnW7VpOJwufEfHJdsCoChJU7shaHoUepSBS3lQI19WDEPo6/KTlm6K+f/vZ3doijWnYQ
Pv0drnx0ia542piQrr2hDdVAyCXpuLLhQm6n0w2Fp4c8VUez2KH0Q/HdH1eNLobSZ9InzScbVm/okOPmsK9aDhnKyJSNMPHMj/7p
u3c++ucfdZ+dExmnejFxjIb0eN7hERU0idpRj4iwYimUnzl18vCP/vFZYfKPkK2WD/X8hLOWXOL5F/AX0n74kPXQlV7HsMWfSEHn
eQIa1orHt3KUPD2Pb1ZB9gL9xbCRzXKtQ6FnVPDzSAVhJklghk/eMWOOeW1W38+I+2FXQ7s2FQknSG7x5sQbSrUCCvE4wbBjkf05
vmXeI1lBINNJUvRr+BLJDmc4V0vKbHTtNfPxu3e+YFWclVHI2XcB8pA11NsDx6fYO+EqGSjRdHWgeGpfaZiUEw+C16QJ+tLQofHA
szCUZ/T3s2xgd2WAuMat5jo7fgNC9OI8xine0lgasA5Pn3jjH074+u0RUkaomiFngwhB5YTknsxQBMb6uuFAhS0ZyoSJ1llrHyJ0
zFuSrtMyCjQ/24G6x+M4vK09AzZ74idnPZ0lZTWCX1Lfy/ucaDt+EGsDpjsbrzKxSjKmbihXD3NpPPUXS8GDC5yNLWxpCPoxdYMk
0uFKmXwIso5vuKlJF2cHZrU7q97GSh7E1KULsq0RbLZE+dMOKrMG5WVX9XTtAkfG+5H6+04Ysj6N8zfPglX2NSzLIa9iQ1qOh772
OjCvj5TXkQ6C/ZeERvwyzJld3T8/uz37Yv/92Tr+rRUhD1//fHaD/66VcY+9/9rshthf3X/XfL86uzu7jl+v7p8TuHR7f2V/Vexf
wO/X95dLuKhE4vrsy9k1MHOdPm7Sx/0VurcMmipnvz5bn32Fe86L/eX99/k3XLyIvyuz+xWoygyY3dhfnm0ZEUvoiumuQwvXqvBV
FRcgeBd/L8xuGpJ5zMV33IViLs42BbN2fnYFHJzDp9UsFmNSJPwXILhWjcpw5TaxhrGXoO79cxl8hisb0ORNjiyehi25/34WpcE8
NMQq7wa+rhRAmr3Tjrkyu7n/7v57AnSsVmohG2hButl93IoP12f3aW4wDGuyQ5BUFcAt1TdBILpj/xymPJcxBDmWJbuxfxFkzxl+
ylxeZP+9hznhrokrCxb0fZZ9jW1At9JHzAU/XaVBKcDLxQG4J75IWZj8vGCx3iN0Anlu4pPRFyhfNQThE1fYQzCJyJLZP5fCv9nn
+G0bv35m7r/P/nGPNcCOzHeRSlcpNK7lxmcj7sr+RRp8a385G0CXBUc4JAMHJqRowA2o8yp5zRzpb5lkih2FLwh2rzUS4Gsw9B7o
gMpXZABjzHMio9+DOelyuhTPgLFz9JnUAeHoFnjs/rsY+hXfdOlZy/znNJClNQOTQQL/3SRvLUNODNkihyqkrAroSX5DXpKzg4na
d6HHzSQLsktSHENwDLhN+phtkqddhDJuGYPnjRtnsJvQzsX9C1UOQYqeXcWg/Q/AAGWra0We2bRXYxfPqsOkFqZep8QceMWF9dnX
Ce/FicpA1jiI0QXurEa0sQAXyRwi9lQS9jrH0ZqI80zCkIG4zMXN2ZUyyrVpmjLgMvS5VsS7rK57xmetWjL5KoG8gr32/mwN0NfI
mgTJi8TU1ux2zr3zMJiSxuxrE9Hvcl5+V6RLQw4aM5GvQWKDpEX85NCxuaUCH4PhbQTN+2CjjJFN2CczpwsTftgqYGa6RI52jxSS
3GPXANJPDkDDa8/HbmbSZxk/x8nBXDdrEanCLiGUIeJ1a7aZZHwayDk3zrd/X59kbXSVkTVLSnZaK2Br+BcF37+lxl6llb2EtVn2
61hRrpuRX7GcCDWwtU1LaEzAZkOz6HK24yCNscM1WqXs92ymySJxoyXrSkn6FGyrr1mSZZI8s8TngXgcYciMjBGWBUFzxkkX8SOS
NLO9CTJfEHO0NK1j7NfgZ1UwMmJLp7IygKgG6xl3Ygiwza4Hp6VkdKOM261w7L0Fd6wD8eA174TFkKGcThkjTk1FHJ96GA1doTUu
MchjQEcdpI+XpyuciTnJ3oPMYCrRogmT1Df5q12dLLullQcTX6gF+uDpplkLbaDZIEqRFS+jROm+DYAS4jeqv46FmUitivqYTWA/
Q5YvBYTanF2ZM0n3Iusvt2Yb+M+4uQD/j3lO09GVdU6npSvqnAsRV5+azmQdG1fUntr4gLpDTbVT+kI+ptzpSx/bP+xjcdHRVSXP
Qw59Vb6sxOUnVeiARhUoP031DNGRnrlcqHlO1nw4oS7WPSfb1RD7kKO8JeVBJRlsvSDdlqaqQYQ9WkvF8DdX+8RmTNG1uDzDeiuA
axZCi/7kBjatuhZKQ2Mutv3Y6ZqiJ+zmoQjqxEVRVVUBNbQJQp6IVAvDfaMxQfUOF0XFMT6jrmgnh8ZgE2juBbMNhsC52qds6ULN
k7yEyL8MRRMegqzgRyw5LUmfiWOygdd08Ak/hFGQkC6VPsGLxqVQMskFx1Y9cWfkUeUz43oaXDtQor3Gtc8QZdIIGsdQ5U8+i8ue
YAW1F+kTQ0HD1dhMS9+VB/C1AY0YgQ+mXGWERfEz+ebzRF6klqTlEpUdJ9SBLGPRBSrl91kDKdkyEE00aGpPOlcEPYx5UQ8klSFC
XIkah/FnspfR9OO1m7XFnHjTS00aa0m79BmFn6TQIVnICvEyxVCHXMYwlJGvAkr+92c8uqVry6JdOYotLlpOMNCe06DKvuxqX2Zg
49H+QJGnVtRGiXHlBbKIFxdQbGlyjVSSiQMoKx+FKWRMy6SY4kVhXEQbBVtd5WHiMS/0dStqsm1aKO41DUXc0YjzVRYs5qDhyxF4
x0QVtVPZbzh8pQgMj6RzdPj2lizAwfnJtodyMlcG5eQ2AFRLsy1T9nKAcEG7yPzk1b5JP2U8uKBsthChBjGIGlDGmxNUjXUUKvSR
lyQOiB4DwhH9nk8fxr3LuO9Yy9F9WcB8h6XfIZ8sgbzXKLAD1gLXVCfrsJtD6z7mXIqUywU2ibMMnyxHJVVEPDhDwFSVVE8l+aId
KWt2aJaDxvGaESKCKCGSwni9yCO5BWVrqZN1xnADKq/OCbgJBJ7cQJmUMmoUSKqmgkx/sr6E2mpQDdUyRiY1wphLk89cCt4SSqvw
h/oaq+/0FQzMXvEkj60GaKes6QWtNx4ZVvMK4udWrjo89oZCsdQJOVMX/AIKpxwgMykXWVsMmOXqPFRVZYWHYqVVdgLmaRCvvtVY
y7p/1DIpjG/BEu8YRRZQ1rzb0aQAaEz0Ua8FtoFDwG9c9ntaErSBWC1Vhlh8qhMooJ8izEJWa6uuGyH8vTLSOkXgSnvPzzd0CVzR
ETLjAIAlikSvDLDmo7Y4oxr8IyRktJUM/f7nyvNRMJZdN74tj7HmvUB1gd5+SJmV1K0qzpfnXz5URFk7NcfL8MSe7vcNFYuy5nsh
IpsWBbjn8y8jFciGVZcFWmccvyU6auBPdtph+XQZKSCURgpouhZenXGa3dDB0RVwlnJJpnlvqJwgsU4BWc2nJIFVjkSih7yCIr2M
FXaASvGIMMQbXD8+5oZLKcyEgRHOW14QCrMiazU6WFq6SDUBlJhxDHMwiwOQBHVlnYZmPm01L1ygGS+g9EroQFJse+Ko43myC43i
G1Ti53wuhV/z+IoMSYzgGKnZNaTPWP5xp4AXit5kB0EFboRugRQRJE8U7uReQCJBYjIFzSRe1V6oYRUgMN8PAT/6lDzGBGVC/o0U
hKNnEMMMB+s1QIdcpAP8PX7k6ElmxlM4D4Eq29rtsDrxzYoAQkTGUZNPlVcGZindoP5kusfngMXojHHZKcXHYyS9J16j02CypPK7
0g2LViA1Pd4EdDln8PHkv7puCHrQjIfOBFZzPyesFwubQ2YZ0fiMukc4DGquAGav8qWwGpYdUf4Y2Ur0jH1jz0CEtyc7nYb0n3xi
fQgHcV0PnBRBGcIX1gEIs7KdoJglqRMsthC25gDH5uGHEQa8aBzJeEwehL3sNIxGOTGYFPb8PC97KqnS4Xr+1HrAGvS9Cvg1OY9c
wVeK8OtlcmO+D4qwU5SOsMGtVZnlAcdx46ijSGv50+w0dSBMcXRrZy3iryPk6ogK2acUHmc+E2PIMh1FRBBaR31DI6RjT8p2cMAE
jLFvElc20RR9u4zJFgY+TFM85LZJ1gWE8Mon3U44ZmkaNCJqk18vxFEIuGHSBLEyudduU78FfoLQKgrFZKehfM5Vhyog2pE0lwwj
CImcSpngNIWHBnHsf/gHmuOQImZNykgST80RuPIpXYfMJsctbTqigHn0onCcHIMfkaHNIyW89qbXmey4vGaQB1qzVx2FG3/opF5U
C9ZegrMopEkO/1rvZs+qhmqssMRXYIEOrTQhq9gXpeWwDrNhPWv4MuKFKuM+qd8cYJU7XZ8z1WOycSatA+qFtSAOM2LvgtYU5CwH
/To8K52uU0QV+S2gufR6gEKILzuka2p4Cstg7mg4xHLs0HE62r5UO/VYcipIzL5gnNOAunbFsfl8EzsHxy0iOlQZfBy32x6RPJ7D
Cgqv7tPxPNCjO1kzl2u6BNlgQU3xbOFpYD/UQnzqXDIDg5qWwRMoDsGuEYH8+hKaqiyhAQlJn1f6EGWGjqcqKmmHNQyZ9N89uYXQ
VtKibBMhwLgpn3ExTblZcHfUowYun4sZS9iF1bURQgxoPkw6P+rLaJNrHUKTkMnJdA8+uY5G5BlwaeSJgY6W1NjsHBTVOP3JNWrv
0tgwSrRoOLCym/ahUD/LgOhP1oD5lkAKnSSwSGQra5M1XEkxXupGprQG1Y8JTkz+gmKOsTmJQJ0dRjE6iOkFWVDnRbEfIZCQOmxV
bYkkkHx1TFsmmXom+lWCaMD7L7qkTGFtSYdwNeIUOSCgnZktrUUorHGXHrL8ZM3soP0DZoKWIg0ZsbnAFnOYERn1tTeTr8rnGT1S
LUYanoU/WQNKdFRFkQ0AbnKtz1WoQaKxCkD3UjwxlSHauSIbNB3iprEVEfnSS7x9bBBcjZ6tMbiwlrUlawiaZXVav4i8SmmyNTXF
SuT58+JUtxrCj6rR23zUTGdLS2rksDxDXxNjGQh3mDdcTVVVXJus2eqaKncfTtYQ92DDipiLzXxpLfbDF2P90PLulPoP/cQK0i5z
pn6ZpK/c8WsO1R317AZXVZXVXtctcKaq6mrxgqpiApM1JYqVNaPRmCm5qCPIrXKI7giKvQQeScO+zURlQHcKd1oRA0551NTFKQTB
L465og1ABRiSpI0YxClaw/Npg125pkWxiN3Qk+l32CEf36MIqebES0jvsIT7NJXPMLGPcIRpnnepmj2I0GbnVjcons4mCSk4vo2p
jfN5qGX4BIGaIUdVM1k5yiBtYPoUKSk0KTOKI8gVpj8TnChWSOi4TkCcglYLCQzcBxa11RTYYmuTSh3TxPgYuJbziTq8Nk/eACZa
TyOJAiE/0YGrUdvpglOgyEbxpKjlM0o8yrpFHWaDA3HiZS8q+cuI+uZp7XagKVSzUGRTfWdyza9OTRUIjRc+SUkdhllE+jPVNmYN
aYuWvdp6mw0QW22ztyzpkdFtAaK9SXgT+z1IHzxN6hhQtR0AB6VnsnIgR2pssJkflbHZ9KPpN9Nb0zvTB9Nbex8UIdr0L9ONvfP4
9w7GfLN3qQzUpp9OH07vTr+dbu0tT7entwQ+PhR7K9MN0KV7H04f7J0rAbfplb1lDLqFaR9icnMjZtnCXQ+n93D3A3y+X0ZzxNF0
nWbbWyGu9t7F5w8EsS/Awa3pfSK7t1qB7qafTB/uXSTG9n4z3a7Ed9MP9y6BHUhUBfGmn013QILm3cD/l8UUd2xiNtLObfxd4bvp
7+Uy+CORWbo7xHEWAE7/SPLu/aoaBE5/i3tuY46HrFso55Ylk0xkoeH0P0Fne+/c3nukO0EssXEf7C0Xz1unf4o1ToTIvtvTjQJK
BFtbbIYdNv5l0LlEZO/EOqqFjdMPccc9Hr9hZiEPI9veYp1tEUukx71z4BcWnG5VwMjUGATF6Jsg/ZN3kH/FjGywJ23B+mSX6V3+
esd6IqscQ+/SRxoW+xb5zE4sH9jYsawZJ7zDznshGfqCYNpWDeBhnayxyWJBeexVD5IL7B9J1ExvpVi1GE8sGEXQN7DaBeu9GwSl
rKm3MMmDmLgg58t6HL6a0CFfuAhOV4tzw7opxp3+GeN3mJo1PtSVDzhm6N9Za1usYJ7T3rRl1P5tNuL3zgk2LPR/Dr/SnPGwUjhv
HLCcCozbJs5xzwMS6TbfvGGlg2R02zYoGf+EC8+J6VXQpUi4JFi4zfIwE5SUHx4esNzfJeUaXywYF0MPVthw71KlFsX099M/TH9v
nO5bJsoKoQlNDnsIoWHFZVzdALEH/EOlljfK8LzgGJdNOqaMxpkON5KDltH69NcwwQoLZaItz7nJ2DF+t7l6I7YRKF+msFnGnd9A
jw8pureMgcsOWeN7Vaqq8N25goiG1DLm2IrTJifVZZJ6hRm4TCzlopi4T4Isr+okIO/yooKgze0aKPezy2Y9paArSnDnkIVTjcC5
yzsKrALbeWLEQPUGA2M3oMILJCr5CXu4zUVw+W+tu1XHYmbfQemaqRDbpa0HXZ2usxSQvrj7sPdStH6z90Gi5Kxe8+vAVroj2buA
LUkubbwoSmHHGSgX0Eh5uQ0L1oM7LJ9NDeCTdb8cZ64NY7/tZIG+zFTrugKg1od7qyxwHITlnQwCdjNNXDykuKPJ0gEmeBCvcAl/
hd0Noi1hfGPvvb3fsE1NkrnNieQbmi+325n+DhdYwRzMnDCSFbRi35OuejyaTXXHxmp2RYdd/gRt3zMLQ24pS7ZCFMxMaPogt4DF
UmZTx/1COJS3S9Ob000M3C5smFjAdV7LN8lqpW0TBQHFlFl043y2zSuj4Lu32ZPu164bRhBKONmBxmlA1+RfpKILzPzGdFPYBHWr
tPEiaFKxANWsOnyBwSXJZ5eIrTjRWzBnIzXZk03/DFL2FiMD9zvYKNsmRdiggg72fmVSYCoQAyTObSYJboKKlXiH/Wwra8QtjjcS
m7NL9V4OKWDDhnfRwzPbrMy2LuPo4CQXI7W7O5j5gclSBuclQbF3uRT1FYFevdeLzZWFsmyCe0YfBYAaLwR3KdVl4ixxhNI+0AYR
Gak+VPKRcaAAAvDtogHc3/KQOiiQWZ0sBKjaOE6vmKS4LAxjwgBcin5aMT+IEy5juDSR0LJrtgnp4rxRvb2kkKunQ7fGiP0bm/RL
m06DxZ6n/8xCcpGCwWRD3tZtzxlca3z+durCJm0aAGd2pYOwqtN2cqOi1fYYlNWUk6uTDVXRbTuPDbknw8g3TUmhaQlR/+dmW4GT
5LqTgsPUbOjUNNouyGZ1my1xGKCChb5UNG11K5tt8U1/3+MB1X9+CYdUFX22NW2286YBinoY4/Y+aPOKLuz8FiT1Gn2PHls/02Nr
zPKEowGmbA4GmpPrsBN4DEhdMMZkHRWTkF4jgM7WpFdOUUPimLtsHTZ/2mXrNd1ociPbZZt1ENtoiyMqoNcBdbQGqj+gQq/mRtAu
NX3iHwrQQUL6SV22VNYmxpvxxQiNqzJ1PBwJqLfBlkNXzHlAEFHHVrHRNqhosz1gidNhQCz1wZS1jMT2KMCLZ0KrrU47bRvwCxzO
qVbcDlfXbutk1FWxuchqkyyzJKt6bh23y1V887C/8WzW+WP1nLUINbzIlJkr6B9D85jRGcqo2uHzBJKyTsBCwy1zkpXviq45Gqjv
t1VeNzOjORxAlyK6I9FraA4GdP5kQE2u/m1dt+atBOTQ1vnzQVnbc2s0A0wTi58A7SNOx6G3NAg6z/XBEHrupPFAm7BqMTUSx1Jl
o+28S/2OVQcCR5NJ0O+3pItNHqzBDCdAjNSGz/LCMrKmxTbg5FN1IIAbNXua6a/kyiw5E7o63qbGAi/NGslhAIVhPm/Iv627FnXt
yv5aOgwgI/FhgKSm8ZeoF0xobqWl5jBfPq85Lvv8YMMAfT6VZwELSYJoa8ea1faia84/AZeidX3pn9tqWRHUTctNK4pfT9DiUKNO
WjTnVWPD1Ii20s9ttLqMCQvWrq/yGzMr05hKvaJPcMdq5Leg0j7aEGlTNqTzNu7X1kGe0Edr1xf05zmBNOmj4AdEBEX4rszkVXrl
gOH6MbmmstpPsy2CTeqSw1SGR36PTG2Z/4TivnNeAWm0aanVNS21LeiDpCMrn2KHSlzL4CjP/X+/l8l00SJEkzPuxzbTVvfSnoxP
F3HMoQe1COoxbbTHBzx5FYJ61Vns0amz97gm2tNa+0NJ3Rje935VE1ppMyjqp5GD3k3uJmIfzGKoYzi9aQ8lNcDSy5qkl3mdjKp5
X5MeeDBVLZJCCyBSkU+yUfexcul1TUnDRSWQOm4oApO8okSPXnOijdbQKyi6yrYGka6IQ/ohaa8wX6X00L3K/V80Im6uXdJuqLXT
Uk96b5NtpcWJ4lKmh3OJW2nRdkfdvfRlMfPWoky3BSZ3uAONzsLMkbdpo52H7LiHXteS7bQYjKk3C68z4gtIsND50FmkRj400uIw
MaS74je+oJ3K1b2eAotz4nif5eVHy8zPpp1WK77nYIXIQVY7x1/iST0cMA7jlx/hFpxQykSKmEZVF22iNWqhrX27k6p7vdMRBcix
qCy6Svz+b9K7OKq89FUt2BjhlBDI3aODZ/TmUwOYK2WnlRUph6tiGZJe2cmX1c2yLyvupAWP1bDqqC/GziK0GWFSMmXWERrU/eb0
GvL7ts3Si6yKoOqQs8hddD7ph0TMRGeKqKLIT5stMO7FSt/JYavTGnB80bQYmlzGJ9dJk0Whefb4gHRa1Tp7xlkcOx1V1Tt7fMCm
4Kgg4qW+2Y5VG88cauSKJfzXykEpkxpItTjUNvMUsRRyRhe53i6wJn405vYI13Jzn6KmP04ZEi6TwCnPeoxtkC04bhlVncLdxTdA
VXfFUm8FN0679Jon9Jpia0O9DwZO0VLCiYtzKYUi0BGv61WI6pU0FThB1qKmIzagbsb4ZXsmcJbSJaMOZXWUfRUUZxVqhe0hMim1
ROZMH/P4kdPjtgr12JdCHYcnuPECw7as6axgo1iHqMNb8MsOMhT1wFZ4J3ykGl+9ElufmlQwAVrfjCqM0amljP2oDmCxCzXCnD8k
KcbTJB01vXK0M3eqMs2AiGqHSQ6uRVjxdCCurDcAg3CbRI7PAsYysQCvGmvVE/yXIFlFp6sv+PWFjgrprWfImeh9xlvDfLaw9Tlb
sHJrnlsqNbji7WpNPAgtq54MbwQ9fzRoLsq4UOU0x17dk+HRIsLAdXqyuaiqENeioooVEaNHf/G8JT0wUNPg2jY9o+WXYo4Guytw
2SrYdbzjPlptyUXhCDxZKvHg5WIZdgH4Ra6E+3xP0IXd3mLh2SXperFbFipXx5tj1Yvg4BBwqPxRm5Xx6OMqwAUqGGTFqX+GSe7u
YLaxDOiFY47FWz2r4eLLMWNqgCiv690dFYztDE3n0QXs1rBLcx6tdjzn0cdNJ21KQzuXPx4hgQxlawxXiAC08MjAsDV2kIrw0GlP
755vwinpy4D8hT9multjH6KZ37K6N9WV3Z3RUIeeo8WYrKIbvck6Xjc51Ogqj2mNmt1sj2uEd75hf6nM5sagx90/uA4wWAQnI6mC
xDMffSzcqIF9ZIQ7gnHigY8+PiBODTVs0eNnDcYaLkpEx3JIAyEBPZMyonSkW5R7MemjC/wEkwM6GY2Q7g6mShjlGBevvXkovjbC
QLz/8dGqiJCm8IcFePRxdaMrVgkmo3bPVz+yNBrS/jQbnjHcehMbZtBFvC9ClZP1RQO8Ur/PKR52SDWfUXkS+oTbwD12QdBmi1tX
yc5QTctTiywM/pAwzUKfKz12FNnZmbJcfLTaHFVgrgWCXGTXmlLWIV/2RCwW6ZV192SE9YbsoJWsVLU6gt8wGekvE4lOiq06ujXm
x5JSd+PnxHv0vCi5TKFodWZAXmGWq4D8ikOBE1V9ueotyXeV0dVbfYfMXsZWfIf0RtXIyqG6MKxBpgnGSDZmWJRDVm/trkzWd3fE
ELYPsJ7oOMvAuGWQZXJGk1RF+Rk1j90VFT8WfmbUx8sGPVVqX3XIN7BCxVliRI8hwV9HiX+VUdYrjz4ej3oFnLW7jFoBq78KbC1S
huzIABzOIa/0e+TwaYSDDR3C/f2xgNthagQfGRKxi5ZGYC5ZfkC8mBJ2V/BB2vjnTIvk7ePpE44LP14tojzgOjNC9gGJzCPiZ0a7
K/D9MSUUR0QIv0UCK+TK3MLKIVcJtGBW0qPTAi9Da/nqE08Dt8axj9SBrTfkIsXwkJ1l0RLMOmvNM+GsG7OwsS94zu4OFMF/Y8SV
WbTqQNcJtL6OVcNkas4hFCuZ9SRdQg6IHp60xzst4wy6uyKY9WBcnUWrUNfrkuaBxoU26y/MgNsSr695G2dFeAxH5Gqs2QLyOqx3
/wC+gzH5C3lGKHtz9GDdZB2CJq4H7PXL/wWn8FQ8
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
