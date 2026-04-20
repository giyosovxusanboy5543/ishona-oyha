import sqlite3
from datetime import datetime
from contextlib import contextmanager
import threading
import time

DB_NAME = "data.db"
lock = threading.Lock()

# ================= CONNECTION =================
def get_conn():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    return conn


# ================= SAFE EXECUTE =================
def safe_execute(cur, query, params=(), retry=5):
    for _ in range(retry):
        try:
            cur.execute(query, params)
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                time.sleep(0.1)
            else:
                raise
    raise Exception("DB LOCK ERROR")


@contextmanager
def db():
    with lock:
        conn = get_conn()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("❌ DB ERROR:", e)
            raise
        finally:
            conn.close()


# ================= INIT =================
def init_db():
    with db() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS appeals(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cid TEXT UNIQUE,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            address TEXT,
            message TEXT,
            status TEXT DEFAULT 'Yangi',
            created TEXT
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            role TEXT
        )
        """)

        c.execute("CREATE INDEX IF NOT EXISTS idx_cid ON appeals(cid)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_user ON appeals(user_id)")


# ================= ROLE =================
def set_role(uid, role):
    with db() as c:
        safe_execute(c,
            "INSERT OR REPLACE INTO users (id, role) VALUES (?,?)",
            (int(uid), role)
        )


def delete_admin(uid):
    with db() as c:
        safe_execute(c,
            "DELETE FROM users WHERE id=? AND role='admin'",
            (int(uid),)
        )


def get_admins():
    with db() as c:
        c.execute("SELECT id FROM users WHERE role IN ('admin','super_admin')")
        return [row["id"] for row in c.fetchall()]


def is_admin(uid):
    with db() as c:
        c.execute("SELECT role FROM users WHERE id=?", (int(uid),))
        row = c.fetchone()
        return row and row["role"] in ["admin", "super_admin"]


# ================= APPEALS =================
def add_appeal(data, custom_cid=None):
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    with db() as c:
        # 🔥 OLDIN BO‘SH CID INSERT
        safe_execute(c, """
        INSERT INTO appeals(user_id,name,phone,address,message,status,created,cid)
        VALUES (?,?,?,?,?,?,?,?)
        """, (*data, "Yangi", now, ""))

        rid = c.lastrowid

        # 🔥 CID TO‘G‘RI BERILADI
        cid = str(custom_cid).strip() if custom_cid else str(rid)

        safe_execute(c,
            "UPDATE appeals SET cid=? WHERE id=?",
            (cid, rid)
        )

    return cid


def get_appeal(cid):
    if not cid:
        return None

    cid = str(cid).strip()

    with db() as c:
        c.execute("SELECT * FROM appeals WHERE cid=?", (cid,))
        row = c.fetchone()
        return dict(row) if row else None


def update_status(cid, status):
    with db() as c:
        safe_execute(c,
            "UPDATE appeals SET status=? WHERE cid=?",
            (status, str(cid).strip())
        )


# ================= EXTRA =================
def get_all_appeals(limit=50):
    with db() as c:
        c.execute(
            "SELECT * FROM appeals ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in c.fetchall()]


def get_user_appeals(user_id):
    with db() as c:
        c.execute(
            "SELECT * FROM appeals WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        )
        return [dict(row) for row in c.fetchall()]


def get_stats():
    with db() as c:
        c.execute("SELECT COUNT(*) as c FROM appeals")
        total = c.fetchone()["c"]

        c.execute("SELECT COUNT(*) as c FROM appeals WHERE status='Yangi'")
        new = c.fetchone()["c"]

        c.execute("SELECT COUNT(*) as c FROM appeals WHERE status='Jarayonda'")
        process = c.fetchone()["c"]

        c.execute("SELECT COUNT(*) as c FROM appeals WHERE status='Rad etildi'")
        rejected = c.fetchone()["c"]

    return {
        "total": total,
        "new": new,
        "process": process,
        "rejected": rejected
    }
