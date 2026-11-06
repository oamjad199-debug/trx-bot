"""
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
