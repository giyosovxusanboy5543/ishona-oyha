import sqlite3

def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS appeals(
        id INTEGER PRIMARY KEY,
        cid TEXT,
        user_id INTEGER,
        name TEXT,
        phone TEXT,
        message TEXT,
        status TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        role TEXT
    )""")

    conn.commit()
    conn.close()

def set_role(uid, role):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users VALUES(?,?)",(uid,role))
    conn.commit()
    conn.close()

def get_admins():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE role IN ('admin','super_admin')")
    data = [i[0] for i in c.fetchall()]
    conn.close()
    return data

def add_appeal(data):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("INSERT INTO appeals(user_id,name,phone,message,status) VALUES(?,?,?,?,?)",
              (*data,"Yangi"))
    cid = str(c.lastrowid)
    c.execute("UPDATE appeals SET cid=? WHERE id=?", (cid,c.lastrowid))
    conn.commit()
    conn.close()
    return cid

def get_appeal(cid):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM appeals WHERE cid=?", (cid,))
    data = c.fetchone()
    conn.close()
    return data

def update_status(cid, status):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("UPDATE appeals SET status=? WHERE cid=?", (status,cid))
    conn.commit()
    conn.close()
