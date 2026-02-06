import sqlite3
import os

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Check if table exists to migrate or create
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            pin TEXT NOT NULL,
            face_encoding BLOB,
            gmail_email TEXT,
            gmail_password TEXT
        )
    ''')
    
    # Simple migration hack for existing table
    try:
        c.execute("ALTER TABLE users ADD COLUMN gmail_email TEXT")
        c.execute("ALTER TABLE users ADD COLUMN gmail_password TEXT")
    except sqlite3.OperationalError:
        pass # Columns likely exist
        
    conn.commit()
    conn.close()

def add_user(name, email, pin, face_encoding, gmail_email=None, gmail_password=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO users (name, email, pin, face_encoding, gmail_email, gmail_password) VALUES (?, ?, ?, ?, ?, ?)",
              (name, email, pin, face_encoding, gmail_email, gmail_password))
    conn.commit()
    conn.close()

def update_user_credentials(email, gmail_email, gmail_password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET gmail_email=?, gmail_password=? WHERE email=?", (gmail_email, gmail_password, email))
    conn.commit()
    conn.close()

def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    return user

def get_all_users_encodings():
    """
    Returns a list of (email, face_encoding) for all users.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT email, face_encoding FROM users WHERE face_encoding IS NOT NULL")
    users = c.fetchall()
    conn.close()
    return users
