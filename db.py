import sqlite3
from datetime import datetime
from contextlib import contextmanager
import threading
import time

DB_NAME = "data.db"

lock = threading.Lock()

# ================= CONNECTION =================
def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # 🔥 PERFORMANCE (MUHIM)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA foreign_keys=ON;")

    return conn


# ================= SAFE EXECUTE =================
def safe_execute(cursor, query, params=(), retries=3):
    for i in range(retries):
        try:
            cursor.execute(query, params)
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                time.sleep(0.2)
            else:
                raise
    raise Exception("DB LOCK ERROR")


@contextmanager
def db_cursor():
    with lock:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("❌ DB ERROR:", e)
            raise
        finally:
            conn.close()


# ================= INIT =================
def init_db():
    with db_cursor() as cursor:
        cursor.execute("""
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

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            role TEXT
        )
        """)

        # 🔥 INDEX (TEZLIK)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cid ON appeals(cid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON appeals(status)")


# ================= ROLE =================
def set_role(uid, role):
    with db_cursor() as cursor:
        safe_execute(cursor,
            "INSERT OR REPLACE INTO users (id, role) VALUES (?,?)",
            (int(uid), role)
        )


def delete_admin(uid):
    with db_cursor() as cursor:
        safe_execute(cursor,
            "DELETE FROM users WHERE id=? AND role='admin'",
            (int(uid),)
        )


def get_role(uid):
    with db_cursor() as cursor:
        cursor.execute("SELECT role FROM users WHERE id=?", (int(uid),))
        row = cursor.fetchone()
        return row["role"] if row else None


def is_admin(uid):
    role = get_role(uid)
    return role in ["admin", "super_admin"]


def get_admins():
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT id FROM users WHERE role IN ('admin','super_admin')"
        )
        return [row["id"] for row in cursor.fetchall()]


# ================= APPEALS =================
def add_appeal(data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    with db_cursor() as cursor:
        safe_execute(cursor, """
        INSERT INTO appeals(user_id,name,phone,address,message,status,created)
        VALUES (?,?,?,?,?,?,?)
        """, (*data, "Yangi", now))

        rid = cursor.lastrowid
        cid = str(rid)

        safe_execute(cursor,
            "UPDATE appeals SET cid=? WHERE id=?",
            (cid, rid)
        )

    return cid


def get_appeal(cid):
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM appeals WHERE cid=?", (str(cid),))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_status(cid, status):
    with db_cursor() as cursor:
        safe_execute(cursor,
            "UPDATE appeals SET status=? WHERE cid=?",
            (status, str(cid))
        )


# ================= EXTRA =================
def get_all_appeals(limit=50):
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM appeals ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]


def get_stats():
    with db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as c FROM appeals")
        total = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM appeals WHERE status='Yangi'")
        new = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM appeals WHERE status='Jarayonda'")
        process = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM appeals WHERE status='Rad etildi'")
        rejected = cursor.fetchone()["c"]

    return {
        "total": total,
        "new": new,
        "process": process,
        "rejected": rejected
    }
