import sqlite3
from datetime import datetime
from contextlib import contextmanager
import threading

DB_NAME = "data.db"

# 🔥 THREAD LOCK (SERVER UCHUN)
lock = threading.Lock()

# ================= CONNECTION =================
def get_conn():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # 🔥 dict ko‘rinish
    return conn

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
            print("DB ERROR:", e)
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

# ================= ROLE =================
def set_role(uid, role):
    with db() as c:
        c.execute(
            "INSERT OR REPLACE INTO users (id, role) VALUES (?,?)",
            (int(uid), role)
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
def add_appeal(data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    with db() as c:
        c.execute("""
        INSERT INTO appeals(user_id,name,phone,address,message,status,created)
        VALUES (?,?,?,?,?,?,?)
        """, (*data, "Yangi", now))

        rid = c.lastrowid
        cid = str(rid)

        c.execute("UPDATE appeals SET cid=? WHERE id=?", (cid, rid))

    return cid

def get_appeal(cid):
    with db() as c:
        c.execute("SELECT * FROM appeals WHERE cid=?", (str(cid),))
        row = c.fetchone()
        return dict(row) if row else None  # 🔥 dict qaytaradi

def update_status(cid, status):
    with db() as c:
        c.execute(
            "UPDATE appeals SET status=? WHERE cid=?",
            (status, str(cid))
        )

# ================= EXTRA =================
def get_all_appeals(limit=50):
    with db() as c:
        c.execute(
            "SELECT * FROM appeals ORDER BY id DESC LIMIT ?",
            (limit,)
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
