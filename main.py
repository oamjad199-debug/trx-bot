import os
import re
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
import zlib, base64
# الواجهة مضغوطة لتبقى ضمن حد اللصق (100 ألف حرف). لا تعدّلها يدوياً.
_WEBAPP_Z = """
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
"""
WEBAPP_HTML = zlib.decompress(base64.b64decode("".join(_WEBAPP_Z.split()))).decode("utf-8")

DB_PATH = os.environ.get("DB_PATH", "bot_database.db")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()   # رابط PostgreSQL الخارجي: يحفظ البيانات بعد كل نشر
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

# إعلانات Monetag: مرحلتان (الأولى فيديو 50 مشاهدة، الثانية سريع 100 مشاهدة). كل القيم قابلة للتغيير من متغيرات البيئة
MONETAG_ZONE = "".join(ch for ch in os.environ.get("MONETAG_ZONE", "12130531") if ch.isdigit()) or "12130531"
MONETAG_SDK_URL = os.environ.get("MONETAG_SDK_URL", "https://libtl.com/sdk.js")
AD_STAGES = [
    {"fmt": "interstitial", "views": int(os.environ.get("AD_STAGE1_VIEWS", "50")), "reward": float(os.environ.get("AD_REWARD_INTERSTITIAL", "0.0005")), "min": 5},
    {"fmt": "pop", "views": int(os.environ.get("AD_STAGE2_VIEWS", "100")), "reward": float(os.environ.get("AD_REWARD_POP", "0.0005")), "min": 2},
]
AD_COOLDOWN = int(os.environ.get("AD_COOLDOWN_SECONDS", "30"))   # الفاصل بين مشاهدة وأخرى
AD_LOCK_HOURS = int(os.environ.get("AD_LOCK_HOURS", "24"))        # القفل بعد إنهاء المرحلتين

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

DB_PG_SRC = r'''"""
طبقة PostgreSQL: تجعل main.py يحفظ كل البيانات (الأرصدة، المستخدمون، الإحالات...) في قاعدة بيانات خارجية
تبقى كما هي بعد كل نشر أو إعادة تشغيل. تُفعَّل فقط عند وضع المتغير DATABASE_URL.
واجهتها تحاكي sqlite3 المستخدمة في main.py، فلا يتغير منطق البوت.
"""
import queue
import re
import threading
from contextlib import contextmanager
from decimal import Decimal

import psycopg2

LOCK_KEY = 73020261  # قفل عام: يجعل المعاملات تنفَّذ واحدة تلو الأخرى (مثل BEGIN IMMEDIATE في SQLite)

_INSERT_IGNORE = re.compile(r"^\s*INSERT\s+OR\s+IGNORE\s+INTO\s", re.I)
_MAX_TWO = re.compile(r"\bMAX\(([^()]*,[^()]*)\)", re.I)
_RETURN_ID = re.compile(r"^\s*INSERT\s+INTO\s+(withdrawals|transactions)\b", re.I)


class Row(tuple):
    """صف يُقرأ بالرقم row[0] وبالاسم row["balance"] مثل sqlite3.Row."""
    def __new__(cls, names, values):
        r = super().__new__(cls, values)
        r._names = list(names)
        return r

    def __getitem__(self, k):
        if isinstance(k, str):
            return tuple.__getitem__(self, self._names.index(k))
        return tuple.__getitem__(self, k)

    def keys(self):
        return list(self._names)


def translate(sql, escape=True):
    """يحوّل لغة SQLite المستخدمة في main.py إلى لغة PostgreSQL."""
    s = sql.strip().rstrip(";")
    if _INSERT_IGNORE.match(s):
        s = _INSERT_IGNORE.sub("INSERT INTO ", s, count=1) + " ON CONFLICT DO NOTHING"
    s = _MAX_TWO.sub(r"GREATEST(\1)", s)
    if escape:
        s = s.replace("%", "%%").replace("?", "%s")
    return s


def translate_ddl(stmt):
    s = stmt.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
    return re.sub(r"\bINTEGER\b", "BIGINT", s)


def _num(v):
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    return v


class Cursor:
    def __init__(self, raw):
        self._c = raw.cursor()
        self.lastrowid = None
        self.rowcount = -1

    def execute(self, sql, params=()):
        args = tuple(params) if params else None
        s = translate(sql, escape=args is not None)
        want_id = bool(_RETURN_ID.match(s)) and "ON CONFLICT" not in s.upper()
        if want_id:
            s += " RETURNING id"
        self._c.execute(s, args)
        self.rowcount = self._c.rowcount
        if want_id:
            self.lastrowid = self._c.fetchone()[0]
        return self

    def _row(self, values):
        names = [d[0] for d in self._c.description]
        return Row(names, [_num(v) for v in values])

    def fetchone(self):
        r = self._c.fetchone()
        return None if r is None else self._row(r)

    def fetchall(self):
        return [self._row(r) for r in self._c.fetchall()]


class Conn:
    def __init__(self, raw):
        self.raw = raw

    def execute(self, sql, params=()):
        return Cursor(self.raw).execute(sql, params)


class Pool:
    """مجموعة اتصالات صغيرة؛ تتخلص من الاتصال الذي أغلقه الخادم بعد خمول طويل."""
    def __init__(self, dsn, size=5):
        self.dsn = dsn
        self.q = queue.LifoQueue()
        self.sem = threading.Semaphore(size)

    def _new(self):
        return psycopg2.connect(
            self.dsn, connect_timeout=10, keepalives=1, keepalives_idle=30,
            keepalives_interval=10, keepalives_count=3, options="-c statement_timeout=30000")

    def get(self):
        self.sem.acquire()
        try:
            while True:
                try:
                    conn = self.q.get_nowait()
                except queue.Empty:
                    return self._new()
                try:
                    if conn.closed:
                        continue
                    cur = conn.cursor()
                    cur.execute("SELECT 1")
                    cur.close()
                    conn.rollback()
                    return conn
                except Exception:
                    try:
                        conn.close()
                    except Exception:
                        pass
        except Exception:
            self.sem.release()
            raise

    def put(self, conn, bad=False):
        try:
            if bad or conn.closed:
                try:
                    conn.close()
                except Exception:
                    pass
            else:
                self.q.put(conn)
        finally:
            self.sem.release()


def make_tx(dsn):
    pool = Pool(dsn)

    @contextmanager
    def tx():
        raw = pool.get()
        bad = False
        try:
            cur = raw.cursor()
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_KEY,))
            cur.close()
            yield Conn(raw)
            raw.commit()
        except Exception:
            try:
                raw.rollback()
            except Exception:
                bad = True
            raise
        finally:
            pool.put(raw, bad)

    return tx


def init_schema(tx, schema):
    with tx() as c:
        for stmt in schema.split(";"):
            if stmt.strip():
                c.execute(translate_ddl(stmt))
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lang TEXT DEFAULT ''")
'''

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
    return jsonify(
        success=True, name=g.user.get("first_name", ""), balance=u["balance"] / MICRO,
        pending=pending / MICRO, active_referrals=refs, ref_link=f"https://t.me/{bot_username()}?start={uid}",
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
    if kind == "ad":
        with tx() as c:
            resp["ads"] = ad_info(ad_get(c, uid, int(time.time())), int(time.time()))
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
        if u["balance"] < MIN_WITHDRAW * MICRO: return jsonify(success=False, code="min_balance")
        if active_referrals(c, uid) < 1: return jsonify(success=False, code="need_referral")
        if c.execute("SELECT 1 FROM withdrawals WHERE user_id=? AND status='pending'", (uid,)).fetchone():
            return jsonify(success=False, code="pending_exists")
        amount = u["balance"]
        c.execute("UPDATE users SET balance=0 WHERE user_id=?", (uid,))
        cur = c.execute("INSERT INTO withdrawals(user_id, amount, address, created_at) VALUES(?,?,?,?)", (uid, amount, u["trx_address"], int(time.time())))
        wid = cur.lastrowid
        address = u["trx_address"]
    if ADMIN_ID:
        try:
            bot.send_message(ADMIN_ID, f"💸 طلب سحب جديد #{wid}\nالمستخدم: {uid}\nالمبلغ: {amount / MICRO:.2f} TRX\nالمحفظة: {address}\n\n/paid {wid}  أو  /reject {wid}")
        except Exception:
            pass
    return jsonify(success=True)

# ======================================================================
# إعلانات Monetag: مراحل مشاهدة، الأرباح تتراكم ثم تُجمع بزر، وبعد آخر مرحلة قفل 24 ساعة
# ======================================================================
def ad_get(conn, uid, now):
    """يرجع صف تقدم المستخدم (وينشئه إن لم يوجد) ويفك القفل تلقائياً بعد انتهاء المدة."""
    r = conn.execute("SELECT * FROM ad_progress WHERE user_id=?", (uid,)).fetchone()
    if not r:
        conn.execute("INSERT INTO ad_progress(user_id) VALUES(?)", (uid,))
        r = conn.execute("SELECT * FROM ad_progress WHERE user_id=?", (uid,)).fetchone()
    if r["locked_until"] and now >= r["locked_until"]:
        conn.execute("UPDATE ad_progress SET stage=0, views=0, earned=0, locked_until=0 WHERE user_id=?", (uid,))
        r = conn.execute("SELECT * FROM ad_progress WHERE user_id=?", (uid,)).fetchone()
    return r

def ad_info(r, now):
    st = AD_STAGES[r["stage"]]
    lock_left = max(0, r["locked_until"] - now) if r["locked_until"] else 0
    wait = max(0, AD_COOLDOWN - (now - r["last_view"])) if r["last_view"] else 0
    return {
        "stages": [{"id": s["fmt"], "target": s["views"]} for s in AD_STAGES],
        "stage": r["stage"], "views": r["views"], "target": st["views"],
        "earned": r["earned"] / MICRO, "ready": bool(r["views"] >= st["views"] and not lock_left),
        "wait": wait, "lock_left": lock_left,
    }

@server.route("/api/ad/start", methods=["POST"])
@auth
def api_ad_start():
    uid = g.user["id"]
    if is_vpn(client_ip()):
        return jsonify(success=False, code="vpn"), 403
    now = int(time.time())
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        r = ad_get(c, uid, now)
        info = ad_info(r, now)
        if info["lock_left"] > 0:
            return jsonify(success=False, code="ad_locked")
        if info["ready"]:
            return jsonify(success=False, code="ad_collect")
        if info["wait"] > 0:
            return jsonify(success=False, code="ad_cooldown", wait=info["wait"])
        fmt = AD_STAGES[r["stage"]]["fmt"]
        token = secrets.token_urlsafe(24)
        c.execute("INSERT INTO ad_sessions(token,user_id,fmt,created_at) VALUES(?,?,?,?)", (token, uid, fmt, now))
        c.execute("DELETE FROM ad_sessions WHERE created_at<?", (now - 86400,))
    return jsonify(success=True, token=token, fmt=fmt)

@server.route("/api/ad/complete", methods=["POST"])
@auth
def api_ad_complete():
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
        r = ad_get(c, uid, now)
        info = ad_info(r, now)
        cfg = AD_STAGES[r["stage"]]
        if s["fmt"] != cfg["fmt"]:
            return jsonify(success=False, code="ad_invalid")
        if now - s["created_at"] < cfg["min"]:
            return jsonify(success=False, code="ad_early")
        if info["lock_left"] > 0:
            return jsonify(success=False, code="ad_locked")
        if info["ready"]:
            return jsonify(success=False, code="ad_collect")
        if info["wait"] > 0:
            return jsonify(success=False, code="ad_cooldown", wait=info["wait"])
        c.execute("UPDATE ad_sessions SET used=1 WHERE token=?", (token,))
        c.execute("UPDATE ad_progress SET views=views+1, earned=earned+?, last_view=? WHERE user_id=?",
                  (int(cfg["reward"] * MICRO), now, uid))
        r2 = ad_get(c, uid, now)
        out = ad_info(r2, now)
    return jsonify(success=True, ads=out)

@server.route("/api/ad/collect", methods=["POST"])
@auth
def api_ad_collect():
    uid = g.user["id"]
    now = int(time.time())
    with tx() as c:
        u = ensure_user(c, uid, g.user.get("username") or "")
        if u["banned"]:
            return jsonify(success=False, code="banned"), 403
        r = ad_get(c, uid, now)
        info = ad_info(r, now)
        if info["lock_left"] > 0:
            return jsonify(success=False, code="ad_locked")
        if not info["ready"]:
            return jsonify(success=False, code="ad_notready")
        amount = r["earned"]
        if amount > 0:
            c.execute(
                "INSERT INTO transactions(txid,user_id,kind,offer_id,amount,status,created_at,release_at) "
                "VALUES(?,?,?,?,?,'pending',?,?)",
                ("adclaim:%d:%s" % (uid, secrets.token_hex(8)), uid, "ad", "monetag:stage%d" % (r["stage"] + 1), amount, now, now))
        if r["stage"] + 1 < len(AD_STAGES):
            c.execute("UPDATE ad_progress SET stage=?, views=0, earned=0 WHERE user_id=?", (r["stage"] + 1, uid))
        else:
            c.execute("UPDATE ad_progress SET stage=0, views=0, earned=0, locked_until=? WHERE user_id=?",
                      (now + AD_LOCK_HOURS * 3600, uid))
        out = ad_info(ad_get(c, uid, now), now)
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
    offer = OFFERS.get(request.args.get("offer_id", ""))
    try:
        uid = int(request.args.get("user_id", ""))
    except ValueError:
        return Response("bad user", 400)
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
    uid = None
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
    try:
        bot.send_message(uid, msg_for(lang, "reversed"))
    except Exception:
        pass
    return Response("OK", 200)

# ======================================================================
# النصوص والترجمات
# ======================================================================
HEADS = {"ar": ["🌍 عن البوت", "⚠️ تنبيه مهم جداً", "💰 حد السحب الأدنى", "🚫 المحظورات", "⏳ التحقق من الأرباح", "👥 نظام الإحالة", "💸 السحب"], "en": ["🌍 About", "⚠️ Important warning", "💰 Minimum withdrawal", "🚫 Prohibited", "⏳ Earnings verification", "👥 Referrals", "💸 Withdrawals"], "es": ["🌍 Sobre el bot", "⚠️ Aviso importante", "💰 Retiro mínimo", "🚫 Prohibido", "⏳ Verificación", "👥 Referidos", "💸 Retiros"], "de": ["🌍 Über den Bot", "⚠️ Wichtige Warnung", "💰 Mindestauszahlung", "🚫 Verboten", "⏳ Verifizierung", "👥 Empfehlungen", "💸 Auszahlungen"], "fr": ["🌍 À propos", "⚠️ Avertissement important", "💰 Retrait minimum", "🚫 Interdit", "⏳ Vérification", "👥 Parrainage", "💸 Retraits"], "ru": ["🌍 О боте", "⚠️ Важное предупреждение", "💰 Минимум для вывода", "🚫 Запрещено", "⏳ Проверка начислений", "👥 Рефералы", "💸 Вывод"], "pt": ["🌍 Sobre o bot", "⚠️ Aviso importante", "💰 Saque mínimo", "🚫 Proibido", "⏳ Verificação", "👥 Indicações", "💸 Saques"], "nl": ["🌍 Over de bot", "⚠️ Belangrijke waarschuwing", "💰 Minimum opname", "🚫 Verboden", "⏳ Verificatie", "👥 Referrals", "💸 Opnames"], "pl": ["🌍 O bocie", "⚠️ Ważne ostrzeżenie", "💰 Minimalna wypłata", "🚫 Zakazy", "⏳ Weryfikacja", "👥 Polecenia", "💸 Wypłaty"]}

BODIES = {
    "ar": ["البوت منصة لتحقيق الربح من:\n🎬 مشاهدة الإعلانات\n📱 عروض الاشتراك برقم الهاتف\n📝 عروض التسجيل\n📲 تثبيت التطبيقات", "لا تدفع أي مبلغ لأي منصة أو موقع أو شخص أثناء استخدام البوت. كل المهام مجانية بالكامل. أي جهة تطلب مالاً باسم البوت فهي احتيال، وسيتم حظر أي مستخدم يطلب أموالاً من غيره.", "الحد الأدنى لسحب الأرباح هو {min} TRX.", "❌ استخدام VPN أو البروكسي\n❌ استخدام الواي فاي (المطلوب بيانات الجوال)\n❌ أكثر من حساب للشخص الواحد\n❌ بيانات وهمية أو أرقام غير حقيقية\n❌ التلاعب بالعروض أو برامج الغش", "لا يُضاف رصيد تثبيت التطبيقات أو التسجيل أو الاشتراك برقم الهاتف إلا بعد التحقق، وتستغرق من 24 إلى 72 ساعة (حالياً {h} ساعة). إذا ألغيت الاشتراك أو حذفت التطبيق أو ألغيت التسجيل فسيُلغى حسابك مباشرة مع أرباحه.", "تحصل على 3% من أرباح كل من تدعوه، مدى الحياة. لا تُحتسب الإحالة إلا بعد أن يشترك المدعو ويُكمل عرضاً ناجحاً واحداً على الأقل (اشتراك/تسجيل/تثبيت).", "لا يمكن السحب إلا بعد أن تُحضر مستخدماً حقيقياً يُكمل أول عرض ناجح له، وبعد بلوغ الحد الأدنى. تراجع الإدارة كل طلب قبل الدفع، ويحق لها حظر أي حساب مخالف وإلغاء أرباحه."],
    "en": ["A platform to earn from:\n🎬 Watching ads\n📱 Phone-number subscription offers\n📝 Registration offers\n📲 App installs", "Never pay any money to any platform, website or person while using the bot. All tasks are completely free. Anyone asking for money in the bot's name is a scammer, and users who ask others for money will be banned.", "The minimum withdrawal is {min} TRX.", "❌ VPN or proxy of any kind\n❌ Wi-Fi (mobile data is required)\n❌ More than one account per person\n❌ Fake data or unreal numbers\n❌ Cheating or manipulating offers", "Rewards for app installs, registrations and phone subscriptions are credited only after verification, which takes 24 to 72 hours (currently {h}h). If you cancel the subscription, uninstall the app or cancel the registration, your account and its earnings are cancelled immediately.", "Earn 3% of your referrals' earnings for life. A referral counts only after the invited user completes at least one successful offer (subscription/registration/install).", "You can withdraw only after bringing a real user who completes their first successful offer, and after reaching the minimum. Every request is reviewed before payment, and accounts that break the rules may be banned and their earnings cancelled."],
    "es": ["Plataforma para ganar con:\n🎬 Ver anuncios\n📱 Suscripciones con número de teléfono\n📝 Registros\n📲 Instalar apps", "No pagues dinero a ninguna plataforma, sitio o persona. Todas las tareas son gratuitas. Quien pida dinero en nombre del bot es un estafador y será bloqueado.", "El retiro mínimo es de {min} TRX.", "❌ VPN o proxy\n❌ Wi-Fi (usa datos móviles)\n❌ Más de una cuenta por persona\n❌ Datos falsos\n❌ Trampas", "El saldo de instalaciones, registros y suscripciones telefónicas se acredita solo tras verificar (24–72 h, ahora {h} h). Si cancelas la suscripción, borras la app o anulas el registro, tu cuenta y ganancias se cancelan de inmediato.", "Ganas 3% de por vida de lo que ganen tus referidos. Un referido cuenta solo cuando completa al menos una oferta exitosa.", "Solo puedes retirar después de traer a un usuario real que complete su primera oferta exitosa y alcanzar el mínimo. Cada solicitud se revisa antes de pagar."],
    "de": ["Plattform zum Verdienen durch:\n🎬 Werbung ansehen\n📱 Telefon-Abos\n📝 Registrierungen\n📲 App-Installationen", "Zahlen Sie niemals Geld an Plattformen, Websites oder Personen. Alle Aufgaben sind kostenlos. Wer im Namen des Bots Geld verlangt, ist ein Betrüger und wird gesperrt.", "Die Mindestauszahlung beträgt {min} TRX.", "❌ VPN oder Proxy\n❌ WLAN (Mobilfunkdaten nutzen)\n❌ Mehrere Konten pro Person\n❌ Falsche Daten\n❌ Betrug", "Belohnungen für Installationen, Registrierungen und Telefon-Abos werden erst nach Prüfung gutgeschrieben (24–72 Std., aktuell {h} Std.). Bei Kündigung, Deinstallation oder Abmeldung wird Ihr Konto sofort gelöscht.", "3% lebenslang auf die Einnahmen Ihrer Empfehlungen. Eine Empfehlung zählt erst nach mindestens einem erfolgreichen Angebot.", "Auszahlung nur, nachdem ein echter Nutzer sein erstes erfolgreiches Angebot abgeschlossen hat und das Minimum erreicht ist. Jeder Antrag wird vorher geprüft."],
    "fr": ["Plateforme pour gagner avec :\n🎬 Pubs\n📱 Abonnements par téléphone\n📝 Inscriptions\n📲 Installations d'apps", "Ne payez jamais d'argent à une plateforme, un site ou une personne. Tout est gratuit. Quiconque demande de l'argent au nom du bot est un escroc et sera banni.", "Le retrait minimum est de {min} TRX.", "❌ VPN ou proxy\n❌ Wi-Fi (utilisez les données mobiles)\n❌ Plusieurs comptes par personne\n❌ Fausses données\n❌ Triche", "Les gains d'installation, d'inscription et d'abonnement téléphonique sont crédités après vérification (24–72 h, actuellement {h} h). Si vous annulez l'abonnement, désinstallez l'app ou annulez l'inscription, votre compte est supprimé immédiatement.", "3% à vie sur les gains de vos filleuls. Un filleul compte seulement après au moins une offre réussie.", "Retrait possible uniquement après qu'un vrai utilisateur parrainé a terminé sa première offre réussie et que le minimum est atteint. Chaque demande est examinée avant paiement."],
    "ru": ["Платформа для заработка на:\n🎬 Просмотре рекламы\n📱 Подписках по номеру телефона\n📝 Регистрациях\n📲 Установке приложений", "Никому не платите деньги. Все задания бесплатны. Тот, кто просит деньги от имени бота, — мошенник и будет заблокирован.", "Минимальная сумма вывода — {min} TRX.", "❌ VPN или прокси\n❌ Wi-Fi (используйте мобильный интернет)\n❌ Несколько аккаунтов\n❌ Фейковые данные\n❌ Обман", "Начисления за установки, регистрации и подписки по телефону зачисляются только после проверки (24–72 ч, сейчас {h} ч). Если вы отмените подписку, удалите приложение или отмените регистрацию, аккаунт будет аннулирован сразу.", "3% пожизненно от заработка рефералов. Реферал засчитывается после хотя бы одного успешного задания.", "Вывод возможен только после того, как реальный приглашённый пользователь выполнит первое успешное задание, и при достижении минимума. Каждая заявка проверяется."],
    "pt": ["Plataforma para ganhar com:\n🎬 Anúncios\n📱 Assinaturas por telefone\n📝 Registros\n📲 Instalação de apps", "Não pague dinheiro a nenhuma plataforma, site ou pessoa. Tudo é gratuito. Quem pedir dinheiro em nome do bot é golpista e será banido.", "O saque mínimo é de {min} TRX.", "❌ VPN ou proxy\n❌ Wi-Fi (use dados móveis)\n❌ Contas múltiplas\n❌ Dados falsos\n❌ Trapaças", "Os ganhos de instalações, registros e assinaturas por telefone só são creditados após verificação (24–72 h, atualmente {h} h). Se cancelar a assinatura, desinstalar o app ou cancelar o registro, sua conta será cancelada imediatamente.", "3% vitalício sobre os ganhos dos seus indicados. A indicação só conta após ao menos uma oferta bem-sucedida.", "O saque só é possível depois que um usuário real indicado concluir a primeira oferta bem-sucedida e o mínimo for atingido. Cada pedido é revisado antes do pagamento."],
    "nl": ["Platform om te verdienen met:\n🎬 Advertenties\n📱 Telefoonabonnementen\n📝 Registraties\n📲 App-installaties", "Betaal nooit geld aan een platform, website of persoon. Alles is gratis. Wie namens de bot geld vraagt is een oplichter en wordt geblokkeerd.", "Minimum opname is {min} TRX.", "❌ VPN of proxy\n❌ Wi-Fi (gebruik mobiele data)\n❌ Meerdere accounts\n❌ Nepgegevens\n❌ Valsspelen", "Beloningen voor installaties, registraties en telefoonabonnementen worden pas na verificatie bijgeschreven (24–72 uur, nu {h} uur). Bij opzeggen, verwijderen van de app of annuleren van de registratie wordt je account direct geannuleerd.", "3% levenslang van de winst van je referrals. Een referral telt pas na minstens één geslaagde aanbieding.", "Opnemen kan pas nadat een echte genodigde zijn eerste geslaagde aanbieding heeft voltooid en het minimum is bereikt. Elk verzoek wordt eerst beoordeeld."],
    "pl": ["Platforma do zarabiania na:\n🎬 Reklamach\n📱 Subskrypcjach telefonicznych\n📝 Rejestracjach\n📲 Instalacji aplikacji", "Nigdy nie płać żadnej platformie, stronie ani osobie. Wszystko jest darmowe. Kto żąda pieniędzy w imieniu bota, jest oszustem i zostanie zablokowany.", "Minimalna wypłata to {min} TRX.", "❌ VPN lub proxy\n❌ Wi-Fi (używaj danych mobilnych)\n❌ Wiele kont\n❌ Fałszywe dane\n❌ Oszustwa", "Nagrody za instalacje, rejestracje i subskrypcje telefoniczne są dodawane dopiero po weryfikacji (24–72 godz., obecnie {h} godz.). Anulowanie subskrypcji, usunięcie aplikacji lub rejestracji natychmiast anuluje konto.", "3% dożywotnio od zarobków poleconych. Polecenie liczy się po co najmniej jednej udanej ofercie.", "Wypłata możliwa dopiero po tym, jak prawdziwy zaproszony użytkownik ukończy pierwszą udaną ofertę i osiągniesz minimum. Każdy wniosek jest sprawdzany."]
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

UI = {
    "en": {"home": "🏠 Home", "ref": "👥 Referrals", "phone": "📱 Phone Subscription", "apps": "📲 Install Apps", "sites": "🌐 Register on Sites", "wallet": "💳 Wallet", "withdraw": "💸 Withdraw", "watch": "▶️ Watch & Earn", "terms": "📜 Terms", "menu": "Menu ⚙️", "welcome": "Welcome", "bal": "Current TRX balance", "pend": "Pending verification", "minline": "Minimum withdrawal: {n} TRX", "faqT": "❓ Important Rules & Instructions", "faqD": "💸 **Withdrawal:** You can withdraw after reaching the minimum and bringing 1 real completed referral.\n👥 **Referrals:** Earn 3% for life from your referrals' earnings.\n🚫 **Cancelling Offers:** If you cancel a subscription or delete an app, your account will be suspended. To unlock it, you must bring 5 completed referrals OR complete a new successful offer.", "refT": "👥 Referral system (3%)", "refCnt": "Active referrals", "refD": "Share your link and earn 3% of your referrals' earnings for life. A referral counts only after they complete one successful offer.", "copy": "Copy referral link 🔗", "copied": "Copied! 📋", "noOffers": "No offers available right now.", "go": "Start ✅", "reward": "Reward", "pendNote": "Credited after verification (24–72h). Cancelling = account ban.", "wDesc": "Enter your TRX (TRC20) wallet address:", "save": "Save 💾", "change": "Change 🔄", "wSaved": "Saved address:", "noAddr": "No address added yet", "wdBtn": "Request withdrawal 🚀", "wdInfo": "Your whole balance is withdrawn. Needs min {n} TRX and one real active referral.", "lang": "🌐 Language", "loading": "Loading…", "c_auth": "Session expired. Please close and reopen the app from the bot.", "c_banned": "Your account has been banned for breaking the terms.", "c_vpn": "VPN/Proxy detected. Turn it off and use mobile data.", "c_bad_address": "Invalid TRX address.", "c_ok_addr": "Address saved 💾", "c_no_address": "Please add your TRX wallet address first.", "c_min_balance": "Your balance is below the minimum withdrawal.", "c_need_referral": "You need one real referral who completed their first successful offer.", "c_pending_exists": "You already have a pending withdrawal.", "c_ok_withdraw": "Withdrawal request submitted 🚀", "c_err": "Something went wrong. Try again."},
    "ar": {"home": "🏠 الرئيسية", "ref": "👥 الإحالة", "phone": "📱 الربح من الاشتراك برقم هاتف", "apps": "📲 الربح من تثبيت تطبيقات", "sites": "🌐 الربح من التسجيل في المواقع", "wallet": "💳 المحفظة", "withdraw": "💸 السحب", "watch": "▶️ الربح من المشاهدة", "terms": "📜 الشروط والأحكام", "menu": "القائمة ⚙️", "welcome": "مرحباً بك", "bal": "رصيد TRX الحالي", "pend": "قيد التحقق", "minline": "الحد الأدنى للسحب: {n} TRX", "faqT": "❓ قواعد وتعليمات هامة", "faqD": "💸 **السحب:** يمكنك السحب بعد وصولك للحد الأدنى وإحضار إحالة حقيقية واحدة مكتملة.\n👥 **الإحالات:** تحصل على 3% مدى الحياة من أرباح إحالاتك.\n🚫 **إلغاء العروض:** في حال قمت بإلغاء اشتراك أو حذف تطبيق، سيتم إيقاف حسابك. لفتح الحساب مرة أخرى، يجب عليك إحضار 5 إحالات مكتملة (أكملن عرضاً ناجحاً) أو إكمال عرض ناجح جديد.", "refT": "👥 نظام الإحالة (3%)", "refCnt": "عدد إحالاتك النشطة", "refD": "شارك رابطك وخذ 3% من أرباح من تدعوه مدى الحياة. لا تُحتسب الإحالة إلا بعد إكمال المدعو عرضاً ناجحاً.", "copy": "نسخ رابط الإحالة 🔗", "copied": "تم النسخ! 📋", "noOffers": "لا توجد عروض متاحة حالياً.", "go": "ابدأ ✅", "reward": "المكافأة", "pendNote": "تُضاف بعد التحقق (24–72 ساعة). الإلغاء = حظر الحساب.", "wDesc": "أدخل عنوان محفظة TRX (TRC20) الخاصة بك:", "save": "حفظ 💾", "change": "تغيير 🔄", "wSaved": "العنوان المحفوظ:", "noAddr": "لم تضف عنواناً بعد", "wdBtn": "طلب السحب 🚀", "wdInfo": "يتم سحب كامل رصيدك. الشرط: {n} TRX كحد أدنى + إحالة حقيقية نشطة.", "lang": "🌐 اللغة", "loading": "جارٍ التحميل…", "c_auth": "انتهت الجلسة. أغلق التطبيق وافتحه من البوت من جديد.", "c_banned": "تم حظر حسابك لمخالفة الشروط.", "c_vpn": "تم اكتشاف VPN/بروكسي. أطفئه واستخدم بيانات الجوال.", "c_bad_address": "عنوان TRX غير صحيح.", "c_ok_addr": "تم حفظ العنوان 💾", "c_no_address": "أضف عنوان محفظة TRX أولاً.", "c_min_balance": "رصيدك أقل من الحد الأدنى للسحب.", "c_need_referral": "يجب أن تُحضر مستخدماً حقيقياً أكمل أول عرض ناجح له.", "c_pending_exists": "لديك طلب سحب قيد المراجعة.", "c_ok_withdraw": "تم تقديم طلب السحب 🚀", "c_err": "حدث خطأ. حاول مرة أخرى."},
    "es": {"home": "🏠 Inicio", "ref": "👥 Referidos", "phone": "📱 Suscripción telefónica", "apps": "📲 Instalar apps", "sites": "🌐 Registrarse en sitios", "wallet": "💳 Billetera", "withdraw": "💸 Retirar", "watch": "▶️ Ver y ganar", "terms": "📜 Términos", "menu": "Menú ⚙️", "welcome": "Bienvenido", "bal": "Saldo actual de TRX", "pend": "Pendiente de verificación", "minline": "Retiro mínimo: {n} TRX", "faqT": "❓ Reglas e instrucciones importantes", "faqD": "💸 **Retiro:** Puedes retirar al alcanzar el mínimo y traer 1 referido real completado.\n👥 **Referidos:** Gana 3% de por vida de las ganancias de tus referidos.\n🚫 **Cancelar ofertas:** Si cancelas una suscripción o eliminas una app, tu cuenta será suspendida. Para desbloquearla, debes traer 5 referidos completados O completar una nueva oferta exitosa.", "refT": "👥 Sistema de referidos (3%)", "refCnt": "Referidos activos", "refD": "Comparte tu enlace y gana el 3% de las ganancias de tus referidos de por vida. Un referido cuenta solo cuando completa una oferta exitosa.", "copy": "Copiar enlace de referido 🔗", "copied": "¡Copiado! 📋", "noOffers": "No hay ofertas disponibles ahora.", "go": "Empezar ✅", "reward": "Recompensa", "pendNote": "Se acredita tras la verificación (24–72 h). Cancelar = bloqueo de la cuenta.", "wDesc": "Introduce tu dirección de billetera TRX (TRC20):", "save": "Guardar 💾", "change": "Cambiar 🔄", "wSaved": "Dirección guardada:", "noAddr": "Aún no has añadido una dirección", "wdBtn": "Solicitar retiro 🚀", "wdInfo": "Se retira todo tu saldo. Requiere un mínimo de {n} TRX y un referido real activo.", "lang": "🌐 Idioma", "loading": "Cargando…", "c_auth": "La sesión expiró. Cierra y vuelve a abrir la app desde el bot.", "c_banned": "Tu cuenta fue bloqueada por incumplir los términos.", "c_vpn": "Se detectó VPN/proxy. Desactívalo y usa datos móviles.", "c_bad_address": "Dirección TRX no válida.", "c_ok_addr": "Dirección guardada 💾", "c_no_address": "Primero añade tu dirección de billetera TRX.", "c_min_balance": "Tu saldo es inferior al retiro mínimo.", "c_need_referral": "Necesitas un referido real que haya completado su primera oferta exitosa.", "c_pending_exists": "Ya tienes un retiro pendiente.", "c_ok_withdraw": "Solicitud de retiro enviada 🚀", "c_err": "Algo salió mal. Inténtalo de nuevo."},
    "de": {"home": "🏠 Startseite", "ref": "👥 Empfehlungen", "phone": "📱 Telefon-Abo", "apps": "📲 Apps installieren", "sites": "🌐 Auf Websites registrieren", "wallet": "💳 Wallet", "withdraw": "💸 Auszahlen", "watch": "▶️ Ansehen & verdienen", "terms": "📜 AGB", "menu": "Menü ⚙️", "welcome": "Willkommen", "bal": "Aktuelles TRX-Guthaben", "pend": "Wird geprüft", "minline": "Mindestauszahlung: {n} TRX", "faqT": "❓ Wichtige Regeln & Anweisungen", "faqD": "💸 **Auszahlung:** Du kannst auszahlen, wenn du das Minimum erreichst und 1 echte abgeschlossene Empfehlung bringst.\n👥 **Empfehlungen:** Verdiene lebenslang 3% an den Einnahmen deiner Empfehlungen.\n🚫 **Angebote abbrechen:** Wenn du ein Abo kündigst oder eine App löschst, wird dein Konto gesperrt. Um es zu entsperren, musst du 5 abgeschlossene Empfehlungen bringen ODER ein neues erfolgreiches Angebot abschließen.", "refT": "👥 Empfehlungssystem (3%)", "refCnt": "Aktive Empfehlungen", "refD": "Teile deinen Link und erhalte lebenslang 3% der Einnahmen deiner Empfehlungen. Eine Empfehlung zählt erst nach einem erfolgreichen Angebot.", "copy": "Empfehlungslink kopieren 🔗", "copied": "Kopiert! 📋", "noOffers": "Derzeit keine Angebote verfügbar.", "go": "Start ✅", "reward": "Belohnung", "pendNote": "Gutschrift nach Prüfung (24–72 Std.). Abbruch = Kontosperre.", "wDesc": "Gib deine TRX-Wallet-Adresse (TRC20) ein:", "save": "Speichern 💾", "change": "Ändern 🔄", "wSaved": "Gespeicherte Adresse:", "noAddr": "Noch keine Adresse hinzugefügt", "wdBtn": "Auszahlung anfordern 🚀", "wdInfo": "Dein gesamtes Guthaben wird ausgezahlt. Erfordert mindestens {n} TRX und eine echte aktive Empfehlung.", "lang": "🌐 Sprache", "loading": "Wird geladen…", "c_auth": "Sitzung abgelaufen. Schließe die App und öffne sie erneut über den Bot.", "c_banned": "Dein Konto wurde wegen Verstoßes gegen die Bedingungen gesperrt.", "c_vpn": "VPN/Proxy erkannt. Schalte es aus und nutze mobile Daten.", "c_bad_address": "Ungültige TRX-Adresse.", "c_ok_addr": "Adresse gespeichert 💾", "c_no_address": "Füge zuerst deine TRX-Wallet-Adresse hinzu.", "c_min_balance": "Dein Guthaben liegt unter der Mindestauszahlung.", "c_need_referral": "Du brauchst eine echte Empfehlung, die ihr erstes erfolgreiches Angebot abgeschlossen hat.", "c_pending_exists": "Du hast bereits eine offene Auszahlung.", "c_ok_withdraw": "Auszahlungsantrag gesendet 🚀", "c_err": "Etwas ist schiefgelaufen. Versuche es erneut."},
    "fr": {"home": "🏠 Accueil", "ref": "👥 Parrainage", "phone": "📱 Abonnement téléphone", "apps": "📲 Installer des apps", "sites": "🌐 S'inscrire sur des sites", "wallet": "💳 Portefeuille", "withdraw": "💸 Retirer", "watch": "▶️ Regarder et gagner", "terms": "📜 Conditions", "menu": "Menu ⚙️", "welcome": "Bienvenue", "bal": "Solde TRX actuel", "pend": "En cours de vérification", "minline": "Retrait minimum : {n} TRX", "faqT": "❓ Règles et instructions importantes", "faqD": "💸 **Retrait:** Vous pouvez retirer après avoir atteint le minimum et apporté 1 vrai filleul complété.\n👥 **Parrainage:** Gagnez 3% à vie sur les gains de vos filleuls.\n🚫 **Annuler des offres:** Si vous annulez un abonnement ou supprimez une app, votre compte sera suspendu. Pour le débloquer, vous devez apporter 5 filleuls complétés OU compléter une nouvelle offre réussie.", "refT": "👥 Système de parrainage (3%)", "refCnt": "Filleuls actifs", "refD": "Partagez votre lien et gagnez 3% des gains de vos filleuls à vie. Un filleul compte seulement après une offre réussie.", "copy": "Copier le lien de parrainage 🔗", "copied": "Copié ! 📋", "noOffers": "Aucune offre disponible pour le moment.", "go": "Commencer ✅", "reward": "Récompense", "pendNote": "Crédité après vérification (24–72 h). Annuler = compte banni.", "wDesc": "Entrez votre adresse de portefeuille TRX (TRC20) :", "save": "Enregistrer 💾", "change": "Modifier 🔄", "wSaved": "Adresse enregistrée :", "noAddr": "Aucune adresse ajoutée", "wdBtn": "Demander le retrait 🚀", "wdInfo": "Tout votre solde est retiré. Il faut au minimum {n} TRX et un vrai filleul actif.", "lang": "🌐 Langue", "loading": "Chargement…", "c_auth": "Session expirée. Fermez l'app et rouvrez-la depuis le bot.", "c_banned": "Votre compte a été banni pour non-respect des conditions.", "c_vpn": "VPN/proxy détecté. Désactivez-le et utilisez les données mobiles.", "c_bad_address": "Adresse TRX invalide.", "c_ok_addr": "Adresse enregistrée 💾", "c_no_address": "Ajoutez d'abord votre adresse de portefeuille TRX.", "c_min_balance": "Votre solde est inférieur au retrait minimum.", "c_need_referral": "Il vous faut un vrai filleul ayant terminé sa première offre réussie.", "c_pending_exists": "Vous avez déjà un retrait en attente.", "c_ok_withdraw": "Demande de retrait envoyée 🚀", "c_err": "Une erreur s'est produite. Réessayez."},
    "ru": {"home": "🏠 Главная", "ref": "👥 Рефералы", "phone": "📱 Подписка по телефону", "apps": "📲 Установка приложений", "sites": "🌐 Регистрация на сайтах", "wallet": "💳 Кошелёк", "withdraw": "💸 Вывод", "watch": "▶️ Смотреть и зарабатывать", "terms": "📜 Условия", "menu": "Меню ⚙️", "welcome": "Добро пожаловать", "bal": "Текущий баланс TRX", "pend": "На проверке", "minline": "Минимальный вывод: {n} TRX", "faqT": "❓ Важные правила и инструкции", "faqD": "💸 **Вывод:** Вы можете вывести средства после достижения минимума и привлечения 1 реального завершенного реферала.\n👥 **Рефералы:** Получайте 3% пожизненно от заработка ваших рефералов.\n🚫 **Отмена предложений:** Если вы отмените подписку или удалите приложение, ваш аккаунт будет заблокирован. Чтобы разблокировать его, вы должны привлечь 5 завершенных рефералов ИЛИ выполнить новое успешное предложение.", "refT": "👥 Реферальная система (3%)", "refCnt": "Активные рефералы", "refD": "Поделитесь ссылкой и получайте 3% от заработка рефералов пожизненно. Реферал засчитывается только после одного успешного задания.", "copy": "Копировать реферальную ссылку 🔗", "copied": "Скопировано! 📋", "noOffers": "Сейчас нет доступных предложений.", "go": "Начать ✅", "reward": "Награда", "pendNote": "Начисляется после проверки (24–72 ч). Отмена = блокировка аккаунта.", "wDesc": "Введите адрес вашего кошелька TRX (TRC20):", "save": "Сохранить 💾", "change": "Изменить 🔄", "wSaved": "Сохранённый адрес:", "noAddr": "Адрес ещё не добавлен", "wdBtn": "Запросить вывод 🚀", "wdInfo": "Выводится весь баланс. Нужно минимум {n} TRX и один реальный активный реферал.", "lang": "🌐 Язык", "loading": "Загрузка…", "c_auth": "Сессия истекла. Закройте приложение и откройте его снова через бота.", "c_banned": "Ваш аккаунт заблокирован за нарушение условий.", "c_vpn": "Обнаружен VPN/прокси. Отключите его и используйте мобильный интернет.", "c_bad_address": "Неверный адрес TRX.", "c_ok_addr": "Адрес сохранён 💾", "c_no_address": "Сначала добавьте адрес кошелька TRX.", "c_min_balance": "Ваш баланс ниже минимального для вывода.", "c_need_referral": "Нужен один реальный реферал, выполнивший первое успешное задание.", "c_pending_exists": "У вас уже есть заявка на вывод в обработке.", "c_ok_withdraw": "Заявка на вывод отправлена 🚀", "c_err": "Что-то пошло не так. Попробуйте ещё раз."},
    "pt": {"home": "🏠 Início", "ref": "👥 Indicações", "phone": "📱 Assinatura por telefone", "apps": "📲 Instalar apps", "sites": "🌐 Registrar em sites", "wallet": "💳 Carteira", "withdraw": "💸 Sacar", "watch": "▶️ Assistir e ganhar", "terms": "📜 Termos", "menu": "Menu ⚙️", "welcome": "Bem-vindo", "bal": "Saldo atual de TRX", "pend": "Aguardando verificação", "minline": "Saque mínimo: {n} TRX", "faqT": "❓ Regras e instruções importantes", "faqD": "💸 **Saque:** Você pode sacar após atingir o mínimo e trazer 1 indicado real concluído.\n👥 **Indicações:** Ganhe 3% para sempre dos ganhos dos seus indicados.\n🚫 **Cancelar ofertas:** Se você cancelar uma assinatura ou excluir um app, sua conta será suspensa. Para desbloquear, você deve trazer 5 indicados concluídos OU concluir uma nova oferta bem-sucedida.", "refT": "👥 Sistema de indicações (3%)", "refCnt": "Indicações ativas", "refD": "Compartilhe seu link e ganhe 3% dos ganhos dos seus indicados para sempre. Uma indicação só conta depois de uma oferta bem-sucedida.", "copy": "Copiar link de indicação 🔗", "copied": "Copiado! 📋", "noOffers": "Nenhuma oferta disponível no momento.", "go": "Começar ✅", "reward": "Recompensa", "pendNote": "Creditado após a verificação (24–72 h). Cancelar = conta banida.", "wDesc": "Digite o endereço da sua carteira TRX (TRC20):", "save": "Salvar 💾", "change": "Alterar 🔄", "wSaved": "Endereço salvo:", "noAddr": "Nenhum endereço adicionado ainda", "wdBtn": "Solicitar saque 🚀", "wdInfo": "Todo o seu saldo é sacado. Exige no mínimo {n} TRX e um indicado real ativo.", "lang": "🌐 Idioma", "loading": "Carregando…", "c_auth": "Sessão expirada. Feche o app e abra-o novamente pelo bot.", "c_banned": "Sua conta foi banida por violar os termos.", "c_vpn": "VPN/proxy detectado. Desative e use dados móveis.", "c_bad_address": "Endereço TRX inválido.", "c_ok_addr": "Endereço salvo 💾", "c_no_address": "Adicione primeiro o endereço da sua carteira TRX.", "c_min_balance": "Seu saldo está abaixo do saque mínimo.", "c_need_referral": "Você precisa de um indicado real que tenha concluído a primeira oferta bem-sucedida.", "c_pending_exists": "Você já tem um saque pendente.", "c_ok_withdraw": "Pedido de saque enviado 🚀", "c_err": "Algo deu errado. Tente novamente."},
    "nl": {"home": "🏠 Home", "ref": "👥 Referrals", "phone": "📱 Telefoonabonnement", "apps": "📲 Apps installeren", "sites": "🌐 Registreren op sites", "wallet": "💳 Wallet", "withdraw": "💸 Opnemen", "watch": "▶️ Kijken en verdienen", "terms": "📜 Voorwaarden", "menu": "Menu ⚙️", "welcome": "Welkom", "bal": "Huidig TRX-saldo", "pend": "In afwachting van verificatie", "minline": "Minimum opname: {n} TRX", "faqT": "❓ Belangrijke regels & instructies", "faqD": "💸 **Opname:** Je kunt opnemen na het bereiken van het minimum en het aanbrengen van 1 echte voltooide referral.\n👥 **Referrals:** Verdien levenslang 3% van de winst van je referrals.\n🚫 **Aanbiedingen annuleren:** Als je een abonnement opzegt of een app verwijdert, wordt je account geblokkeerd. Om het te deblokkeren, moet je 5 voltooide referrals aanbrengen OF een nieuwe succesvolle aanbieding voltooien.", "refT": "👥 Referralsysteem (3%)", "refCnt": "Actieve referrals", "refD": "Deel je link en verdien levenslang 3% van de winst van je referrals. Een referral telt pas na één geslaagde aanbieding.", "copy": "Referrallink kopiëren 🔗", "copied": "Gekopieerd! 📋", "noOffers": "Er zijn nu geen aanbiedingen beschikbaar.", "go": "Start ✅", "reward": "Beloning", "pendNote": "Bijgeschreven na verificatie (24–72 uur). Annuleren = account geblokkeerd.", "wDesc": "Voer je TRX-walletadres (TRC20) in:", "save": "Opslaan 💾", "change": "Wijzigen 🔄", "wSaved": "Opgeslagen adres:", "noAddr": "Nog geen adres toegevoegd", "wdBtn": "Opname aanvragen 🚀", "wdInfo": "Je hele saldo wordt opgenomen. Vereist minimaal {n} TRX en één echte actieve referral.", "lang": "🌐 Taal", "loading": "Laden…", "c_auth": "Sessie verlopen. Sluit de app en open hem opnieuw via de bot.", "c_banned": "Je account is geblokkeerd wegens schending van de voorwaarden.", "c_vpn": "VPN/proxy gedetecteerd. Schakel het uit en gebruik mobiele data.", "c_bad_address": "Ongeldig TRX-adres.", "c_ok_addr": "Adres opgeslagen 💾", "c_no_address": "Voeg eerst je TRX-walletadres toe.", "c_min_balance": "Je saldo is lager dan de minimale opname.", "c_need_referral": "Je hebt één echte referral nodig die zijn eerste geslaagde aanbieding heeft voltooid.", "c_pending_exists": "Je hebt al een openstaande opname.", "c_ok_withdraw": "Opnameverzoek verzonden 🚀", "c_err": "Er ging iets mis. Probeer het opnieuw."},
    "pl": {"home": "🏠 Start", "ref": "👥 Polecenia", "phone": "📱 Subskrypcja telefoniczna", "apps": "📲 Instaluj aplikacje", "sites": "🌐 Rejestracja na stronach", "wallet": "💳 Portfel", "withdraw": "💸 Wypłata", "watch": "▶️ Oglądaj i zarabiaj", "terms": "📜 Regulamin", "menu": "Menu ⚙️", "welcome": "Witaj", "bal": "Aktualne saldo TRX", "pend": "Oczekuje na weryfikację", "minline": "Minimalna wypłata: {n} TRX", "faqT": "❓ Ważne zasady i instrukcje", "faqD": "💸 **Wypłata:** Możesz wypłacić po osiągnięciu minimum i przyprowadzeniu 1 prawdziwego ukończonego poleconego.\n👥 **Polecenia:** Zarabiaj 3% dożywotnio z zarobków swoich poleconych.\n🚫 **Anulowanie ofert:** Jeśli anulujesz subskrypcję lub usuniesz aplikację, Twoje konto zostanie zawieszone. Aby je odblokować, musisz przyprowadzić 5 ukończonych poleconych LUB ukończyć nową udaną ofertę.", "refT": "👥 System poleceń (3%)", "refCnt": "Aktywne polecenia", "refD": "Udostępnij swój link i zarabiaj dożywotnio 3% zarobków poleconych. Polecenie liczy się dopiero po jednej udanej ofercie.", "copy": "Kopiuj link polecający 🔗", "copied": "Skopiowano! 📋", "noOffers": "Brak dostępnych ofert.", "go": "Start ✅", "reward": "Nagroda", "pendNote": "Dodawane po weryfikacji (24–72 godz.). Anulowanie = blokada konta.", "wDesc": "Wpisz adres swojego portfela TRX (TRC20):", "save": "Zapisz 💾", "change": "Zmień 🔄", "wSaved": "Zapisany adres:", "noAddr": "Nie dodano jeszcze adresu", "wdBtn": "Złóż wniosek o wypłatę 🚀", "wdInfo": "Wypłacane jest całe saldo. Wymagane minimum {n} TRX i jeden prawdziwy aktywny polecony.", "lang": "🌐 Język", "loading": "Ładowanie…", "c_auth": "Sesja wygasła. Zamknij aplikację i otwórz ją ponownie przez bota.", "c_banned": "Twoje konto zostało zablokowane za naruszenie regulaminu.", "c_vpn": "Wykryto VPN/proxy. Wyłącz je i użyj danych mobilnych.", "c_bad_address": "Nieprawidłowy adres TRX.", "c_ok_addr": "Adres zapisany 💾", "c_no_address": "Najpierw dodaj adres portfela TRX.", "c_min_balance": "Twoje saldo jest niższe niż minimalna wypłata.", "c_need_referral": "Potrzebujesz jednego prawdziwego poleconego, który ukończył pierwszą udaną ofertę.", "c_pending_exists": "Masz już oczekującą wypłatę.", "c_ok_withdraw": "Wniosek o wypłatę wysłany 🚀", "c_err": "Coś poszło nie tak. Spróbuj ponownie."}
}

AD_UI = {
    "en": {"adInterT": "Rewarded video ad", "adPopT": "Quick rewarded ad", "adWatch": "Watch ad", "adWait": "Next ad in {s}s", "adStepOf": "Stage {a} of {b}", "adProgress": "{v} / {t} views", "adEarned": "Accumulated earnings: {r} TRX", "adDoneHint": "Stage complete! Collect your balance to continue.", "adCollect": "Collect your balance", "adLockedT": "All stages completed", "adLockedD": "You can watch ads again in:", "c_ok_collect": "Added to your balance: +{r} TRX 🎉", "c_ad_cooldown": "Please wait a little before the next ad.", "c_ad_early": "The ad wasn't completed, so it was not counted.", "c_ad_invalid": "The ad session expired. Please try again.", "c_ad_fail": "The ad could not be shown right now. Try again later.", "c_ad_sdk": "Ads are not available right now. Reload the app and try again.", "c_ad_locked": "Ads are locked until the timer ends.", "c_ad_collect": "Collect your balance first to continue.", "c_ad_notready": "This stage is not complete yet."},
    "ar": {"adInterT": "إعلان فيديو بمكافأة", "adPopT": "إعلان سريع بمكافأة", "adWatch": "شاهد الإعلان", "adWait": "الإعلان التالي بعد {s} ث", "adStepOf": "المرحلة {a} من {b}", "adProgress": "{v} / {t} مشاهدة", "adEarned": "الأرباح المتراكمة: {r} TRX", "adDoneHint": "اكتملت المرحلة! اجمع رصيدك للمتابعة.", "adCollect": "اجمع رصيدك", "adLockedT": "أنهيت جميع المراحل", "adLockedD": "ستتمكن من المشاهدة مجدداً خلال:", "c_ok_collect": "تمت إضافة {r} TRX إلى رصيدك 🎉", "c_ad_cooldown": "انتظر قليلاً قبل الإعلان التالي.", "c_ad_early": "لم يكتمل الإعلان، لذلك لم تُحسب المشاهدة.", "c_ad_invalid": "انتهت جلسة الإعلان. حاول مرة أخرى.", "c_ad_fail": "تعذّر عرض الإعلان الآن. حاول لاحقاً.", "c_ad_sdk": "الإعلانات غير متاحة حالياً. أعد فتح التطبيق وحاول مجدداً.", "c_ad_locked": "الإعلانات مقفلة حتى ينتهي العداد.", "c_ad_collect": "اجمع رصيدك أولاً للمتابعة.", "c_ad_notready": "المرحلة لم تكتمل بعد."},
    "es": {"adInterT": "Anuncio en vídeo con recompensa", "adPopT": "Anuncio rápido con recompensa", "adWatch": "Ver anuncio", "adWait": "Próximo anuncio en {s} s", "adStepOf": "Etapa {a} de {b}", "adProgress": "{v} / {t} vistas", "adEarned": "Ganancias acumuladas: {r} TRX", "adDoneHint": "¡Etapa completada! Recoge tu saldo para continuar.", "adCollect": "Recoger saldo", "adLockedT": "Completaste todas las etapas", "adLockedD": "Podrás ver anuncios de nuevo en:", "c_ok_collect": "Añadido a tu saldo: +{r} TRX 🎉", "c_ad_cooldown": "Espera un poco antes del siguiente anuncio.", "c_ad_early": "El anuncio no se completó, por lo que no se contó.", "c_ad_invalid": "La sesión del anuncio expiró. Inténtalo de nuevo.", "c_ad_fail": "No se pudo mostrar el anuncio ahora. Inténtalo más tarde.", "c_ad_sdk": "Los anuncios no están disponibles ahora. Recarga la app e inténtalo de nuevo.", "c_ad_locked": "Los anuncios están bloqueados hasta que termine el temporizador.", "c_ad_collect": "Recoge tu saldo primero para continuar.", "c_ad_notready": "Esta etapa aún no está completa."},
    "de": {"adInterT": "Video-Werbung mit Belohnung", "adPopT": "Kurzwerbung mit Belohnung", "adWatch": "Werbung ansehen", "adWait": "Nächste Werbung in {s} s", "adStepOf": "Stufe {a} von {b}", "adProgress": "{v} / {t} Aufrufe", "adEarned": "Gesammelte Einnahmen: {r} TRX", "adDoneHint": "Stufe abgeschlossen! Hole dir dein Guthaben, um fortzufahren.", "adCollect": "Guthaben einsammeln", "adLockedT": "Alle Stufen abgeschlossen", "adLockedD": "Du kannst wieder Werbung ansehen in:", "c_ok_collect": "Deinem Guthaben gutgeschrieben: +{r} TRX 🎉", "c_ad_cooldown": "Bitte warte kurz bis zur nächsten Werbung.", "c_ad_early": "Die Werbung wurde nicht abgeschlossen und deshalb nicht gezählt.", "c_ad_invalid": "Die Werbesitzung ist abgelaufen. Bitte versuche es erneut.", "c_ad_fail": "Die Werbung konnte gerade nicht angezeigt werden. Versuche es später erneut.", "c_ad_sdk": "Werbung ist derzeit nicht verfügbar. Lade die App neu und versuche es erneut.", "c_ad_locked": "Werbung ist gesperrt, bis der Timer abläuft.", "c_ad_collect": "Hole zuerst dein Guthaben, um fortzufahren.", "c_ad_notready": "Diese Stufe ist noch nicht abgeschlossen."},
    "fr": {"adInterT": "Vidéo publicitaire récompensée", "adPopT": "Pub rapide récompensée", "adWatch": "Regarder la pub", "adWait": "Prochaine pub dans {s} s", "adStepOf": "Étape {a} sur {b}", "adProgress": "{v} / {t} vues", "adEarned": "Gains accumulés : {r} TRX", "adDoneHint": "Étape terminée ! Récupérez votre solde pour continuer.", "adCollect": "Récupérer mon solde", "adLockedT": "Toutes les étapes sont terminées", "adLockedD": "Vous pourrez revoir des pubs dans :", "c_ok_collect": "Ajouté à votre solde : +{r} TRX 🎉", "c_ad_cooldown": "Patientez un peu avant la prochaine pub.", "c_ad_early": "La pub n'a pas été terminée, elle n'est donc pas comptée.", "c_ad_invalid": "La session publicitaire a expiré. Réessayez.", "c_ad_fail": "La pub n'a pas pu s'afficher pour le moment. Réessayez plus tard.", "c_ad_sdk": "Les pubs ne sont pas disponibles pour le moment. Rechargez l'app et réessayez.", "c_ad_locked": "Les pubs sont verrouillées jusqu'à la fin du minuteur.", "c_ad_collect": "Récupérez d'abord votre solde pour continuer.", "c_ad_notready": "Cette étape n'est pas encore terminée."},
    "ru": {"adInterT": "Видеореклама с наградой", "adPopT": "Быстрая реклама с наградой", "adWatch": "Смотреть рекламу", "adWait": "Следующая реклама через {s} с", "adStepOf": "Этап {a} из {b}", "adProgress": "{v} / {t} просмотров", "adEarned": "Накопленный заработок: {r} TRX", "adDoneHint": "Этап завершён! Заберите баланс, чтобы продолжить.", "adCollect": "Забрать баланс", "adLockedT": "Все этапы пройдены", "adLockedD": "Снова смотреть рекламу можно через:", "c_ok_collect": "Добавлено на баланс: +{r} TRX 🎉", "c_ad_cooldown": "Подождите немного перед следующей рекламой.", "c_ad_early": "Реклама не была досмотрена, поэтому просмотр не засчитан.", "c_ad_invalid": "Сессия рекламы истекла. Попробуйте ещё раз.", "c_ad_fail": "Не удалось показать рекламу. Попробуйте позже.", "c_ad_sdk": "Реклама сейчас недоступна. Перезапустите приложение и попробуйте снова.", "c_ad_locked": "Реклама заблокирована до конца таймера.", "c_ad_collect": "Сначала заберите баланс, чтобы продолжить.", "c_ad_notready": "Этот этап ещё не завершён."},
    "pt": {"adInterT": "Anúncio em vídeo com recompensa", "adPopT": "Anúncio rápido com recompensa", "adWatch": "Assistir anúncio", "adWait": "Próximo anúncio em {s} s", "adStepOf": "Etapa {a} de {b}", "adProgress": "{v} / {t} visualizações", "adEarned": "Ganhos acumulados: {r} TRX", "adDoneHint": "Etapa concluída! Colete seu saldo para continuar.", "adCollect": "Coletar saldo", "adLockedT": "Todas as etapas concluídas", "adLockedD": "Você poderá assistir anúncios novamente em:", "c_ok_collect": "Adicionado ao seu saldo: +{r} TRX 🎉", "c_ad_cooldown": "Aguarde um pouco antes do próximo anúncio.", "c_ad_early": "O anúncio não foi concluído, então não foi contado.", "c_ad_invalid": "A sessão do anúncio expirou. Tente novamente.", "c_ad_fail": "Não foi possível exibir o anúncio agora. Tente mais tarde.", "c_ad_sdk": "Os anúncios não estão disponíveis agora. Recarregue o app e tente novamente.", "c_ad_locked": "Os anúncios estão bloqueados até o fim do cronômetro.", "c_ad_collect": "Colete seu saldo primeiro para continuar.", "c_ad_notready": "Esta etapa ainda não foi concluída."},
    "nl": {"adInterT": "Videoadvertentie met beloning", "adPopT": "Snelle advertentie met beloning", "adWatch": "Advertentie bekijken", "adWait": "Volgende advertentie over {s} s", "adStepOf": "Fase {a} van {b}", "adProgress": "{v} / {t} weergaven", "adEarned": "Opgebouwde winst: {r} TRX", "adDoneHint": "Fase voltooid! Haal je saldo op om door te gaan.", "adCollect": "Saldo ophalen", "adLockedT": "Alle fases voltooid", "adLockedD": "Je kunt weer advertenties bekijken over:", "c_ok_collect": "Toegevoegd aan je saldo: +{r} TRX 🎉", "c_ad_cooldown": "Wacht even voor de volgende advertentie.", "c_ad_early": "De advertentie is niet voltooid en telt dus niet mee.", "c_ad_invalid": "De advertentiesessie is verlopen. Probeer het opnieuw.", "c_ad_fail": "De advertentie kon nu niet worden getoond. Probeer het later opnieuw.", "c_ad_sdk": "Advertenties zijn nu niet beschikbaar. Laad de app opnieuw en probeer het nog eens.", "c_ad_locked": "Advertenties zijn vergrendeld tot de timer afloopt.", "c_ad_collect": "Haal eerst je saldo op om door te gaan.", "c_ad_notready": "Deze fase is nog niet voltooid."},
    "pl": {"adInterT": "Reklama wideo z nagrodą", "adPopT": "Szybka reklama z nagrodą", "adWatch": "Obejrzyj reklamę", "adWait": "Następna reklama za {s} s", "adStepOf": "Etap {a} z {b}", "adProgress": "{v} / {t} wyświetleń", "adEarned": "Zgromadzone zarobki: {r} TRX", "adDoneHint": "Etap ukończony! Odbierz saldo, aby kontynuować.", "adCollect": "Odbierz saldo", "adLockedT": "Wszystkie etapy ukończone", "adLockedD": "Reklamy będzie można obejrzeć ponownie za:", "c_ok_collect": "Dodano do salda: +{r} TRX 🎉", "c_ad_cooldown": "Poczekaj chwilę przed kolejną reklamą.", "c_ad_early": "Reklama nie została ukończona, więc nie została zaliczona.", "c_ad_invalid": "Sesja reklamy wygasła. Spróbuj ponownie.", "c_ad_fail": "Nie udało się teraz wyświetlić reklamy. Spróbuj później.", "c_ad_sdk": "Reklamy są obecnie niedostępne. Odśwież aplikację i spróbuj ponownie.", "c_ad_locked": "Reklamy są zablokowane do końca odliczania.", "c_ad_collect": "Najpierw odbierz saldo, aby kontynuować.", "c_ad_notready": "Ten etap nie został jeszcze ukończony."},
}
for _l, _d in AD_UI.items():
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
            .replace("__AD_ZONE__", MONETAG_ZONE)
            .replace("__AD_SDK__", '<script src="%s" data-zone="%s" data-sdk="show_%s"></script>' % (html.escape(MONETAG_SDK_URL, quote=True), MONETAG_ZONE, MONETAG_ZONE)))
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

@bot.message_handler(commands=["withdrawals"])
def cmd_withdrawals(m):
    if not is_admin(m):
        return
    with tx() as c:
        rows = c.execute("SELECT * FROM withdrawals WHERE status='pending' ORDER BY id LIMIT 20").fetchall()
    if not rows:
        bot.reply_to(m, "لا توجد طلبات سحب معلقة ✅")
        return
    bot.reply_to(m, "\n\n".join(f"#{r['id']} | user {r['user_id']} | {r['amount'] / MICRO:.2f} TRX\n{r['address']}" for r in rows))

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
        lang = user_lang(c, w["user_id"])
        c.execute("UPDATE withdrawals SET status=?, note=?, processed_at=? WHERE id=?", ("paid" if paid else "rejected", note, int(time.time()), wid))
        if not paid:
            c.execute("UPDATE users SET balance=balance+? WHERE user_id=? AND banned=0", (w["amount"], w["user_id"]))
    bot.reply_to(m, f"تم {'الدفع' if paid else 'الرفض وإرجاع الرصيد'} للطلب #{wid} ✅")
    try:
        if paid:
            bot.send_message(w["user_id"], msg_for(lang, "paid", amt=f"{w['amount'] / MICRO:.2f}", note=note))
        else:
            bot.send_message(w["user_id"], msg_for(lang, "rejected", id=wid, note=note))
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
