import sqlite3
import hashlib
import secrets
from pathlib import Path
from datetime import date

DB_PATH = Path(__file__).resolve().parent / "data" / "finshield.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            monthly_budget REAL DEFAULT 30000,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tx_type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            tx_date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS fraud_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            risk_score INTEGER,
            risk_level TEXT,
            message_preview TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000)
    return digest.hex(), salt


def register_user(name, email, password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    password_hash, salt = hash_password(password)
    try:
        with get_db() as conn:
            cur = conn.execute("INSERT INTO users(name,email,password_hash,salt) VALUES(?,?,?,?)",
                               (name.strip(), email.strip().lower(), password_hash, salt))
            user_id = cur.lastrowid
        seed_demo_transactions(user_id)
        return True, user_id
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."


def authenticate(email, password):
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    if not user:
        return None
    expected, _ = hash_password(password, user["salt"])
    if secrets.compare_digest(expected, user["password_hash"]):
        return dict(user)
    return None


def seed_demo_transactions(user_id):
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM transactions WHERE user_id=?", (user_id,)).fetchone()[0]
        if count:
            return
        year_month = date.today().strftime("%Y-%m")
        data = [
            ("income", "Others", 60000, "Monthly simulated salary", f"{year_month}-01"),
            ("expense", "Food", 1850, "Groceries and café", f"{year_month}-04"),
            ("expense", "Bills", 4200, "Utilities and mobile", f"{year_month}-06"),
            ("expense", "Travel", 2600, "Metro and fuel", f"{year_month}-08"),
            ("expense", "Shopping", 6500, "Online shopping", f"{year_month}-11"),
            ("expense", "Entertainment", 1700, "Subscriptions", f"{year_month}-13"),
            ("expense", "Education", 3000, "Course payment", f"{year_month}-15"),
            ("expense", "Medical", 1200, "Pharmacy", f"{year_month}-17"),
        ]
        conn.executemany("INSERT INTO transactions(user_id,tx_type,category,amount,description,tx_date) VALUES(?,?,?,?,?,?)",
                         [(user_id, *row) for row in data])


def update_budget(user_id, amount):
    with get_db() as conn:
        conn.execute("UPDATE users SET monthly_budget=? WHERE id=?", (amount, user_id))


def get_user(user_id):
    with get_db() as conn:
        return dict(conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone())


def add_transaction(user_id, tx_type, category, amount, description, tx_date):
    with get_db() as conn:
        conn.execute("INSERT INTO transactions(user_id,tx_type,category,amount,description,tx_date) VALUES(?,?,?,?,?,?)",
                     (user_id, tx_type, category, amount, description, tx_date))


def get_transactions(user_id):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY tx_date DESC, id DESC", (user_id,)).fetchall()
        return [dict(row) for row in rows]


def delete_transaction(tx_id, user_id):
    with get_db() as conn:
        conn.execute("DELETE FROM transactions WHERE id=? AND user_id=?", (tx_id, user_id))


def add_fraud_alert(user_id, score, level, preview):
    with get_db() as conn:
        conn.execute("INSERT INTO fraud_alerts(user_id,risk_score,risk_level,message_preview) VALUES(?,?,?,?)",
                     (user_id, score, level, preview[:180]))


def get_fraud_alerts(user_id):
    with get_db() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM fraud_alerts WHERE user_id=? ORDER BY id DESC LIMIT 20", (user_id,)).fetchall()]


def save_chat(user_id, role, content):
    with get_db() as conn:
        conn.execute("INSERT INTO chat_history(user_id,role,content) VALUES(?,?,?)", (user_id, role, content))


def get_chat_history(user_id, limit=20):
    with get_db() as conn:
        rows = conn.execute("SELECT role,content FROM chat_history WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
        return [dict(r) for r in reversed(rows)]

init_db()
