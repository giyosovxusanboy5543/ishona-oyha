import sqlite3
from datetime import datetime
from contextlib import contextmanager

DB_NAME = "data.db"

# ================= CONNECTION =================
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

@contextmanager
def db_cursor():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("DB ERROR:", e)
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
            status TEXT,
            created TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            role TEXT
        )
        """)

# ================= ROLE =================
def set_role(uid, role):
    with db_cursor() as cursor:
        cursor.execute(
            "INSERT OR REPLACE INTO users (id, role) VALUES (?,?)",
            (int(uid), role)
        )

def get_role(uid):
    with db_cursor() as cursor:
        cursor.execute("SELECT role FROM users WHERE id=?", (int(uid),))
        row = cursor.fetchone()
        return row[0] if row else None

def get_admins():
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT id FROM users WHERE role IN ('admin','super_admin')"
        )
        return [row[0] for row in cursor.fetchall()]

# ================= APPEALS =================
def add_appeal(data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    with db_cursor() as cursor:
        cursor.execute("""
        INSERT INTO appeals(user_id,name,phone,address,message,status,created)
        VALUES (?,?,?,?,?,?,?)
        """, (*data, "Yangi", now))

        rid = cursor.lastrowid
        cid = str(rid)  # 🔥 MUHIM

        cursor.execute(
            "UPDATE appeals SET cid=? WHERE id=?",
            (cid, rid)
        )

    return cid

def get_appeal(cid):
    cid = str(cid).strip()

    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM appeals WHERE cid=?", (cid,))
        return cursor.fetchone()

def update_status(cid, status):
    cid = str(cid).strip()

    with db_cursor() as cursor:
        cursor.execute(
            "UPDATE appeals SET status=? WHERE cid=?",
            (status, cid)
        )

# ================= EXTRA =================
def get_all_appeals():
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM appeals ORDER BY id DESC")
        return cursor.fetchall()

def get_stats():
    with db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM appeals")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM appeals WHERE status='Yangi'")
        new = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM appeals WHERE status='Jarayonda'")
        process = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM appeals WHERE status='Rad etildi'")
        rejected = cursor.fetchone()[0]

    return {
        "total": total,
        "new": new,
        "process": process,
        "rejected": rejected
    }