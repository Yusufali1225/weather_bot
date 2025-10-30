import os
import psycopg2
from psycopg2.extras import RealDictCursor

# 🔹 Render DATABASE_URL dan ulanish
def connect():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    else:
        # Lokal ishga tushirish uchun eski config usuli
        from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
        return psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

def create_tables():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT UNIQUE,
        username TEXT,
        first_name TEXT,
        language VARCHAR(5),
        subscribed BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_messages (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT,
        message_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def add_or_update_user(chat_id, username, first_name, language=None, subscribed=None):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO users (chat_id, username, first_name, language, subscribed)
    VALUES (%s,%s,%s,%s,%s)
    ON CONFLICT (chat_id) DO UPDATE
      SET username = EXCLUDED.username,
          first_name = EXCLUDED.first_name,
          language = COALESCE(EXCLUDED.language, users.language),
          subscribed = COALESCE(EXCLUDED.subscribed, users.subscribed)
    """, (chat_id, username, first_name, language, subscribed))
    conn.commit()
    cur.close()
    conn.close()

def set_subscription(chat_id, subscribed: bool):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET subscribed = %s WHERE chat_id = %s", (subscribed, chat_id))
    conn.commit()
    cur.close()
    conn.close()

def get_user(chat_id):
    conn = connect()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE chat_id = %s", (chat_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def all_users():
    conn = connect()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT chat_id, username, first_name, language, subscribed FROM users ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def save_user_message(chat_id, text):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO user_messages (chat_id, message_text) VALUES (%s, %s)", (chat_id, text))
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_tables()
    conn = connect()
    cur = conn.cursor()
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(5);")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS subscribed BOOLEAN DEFAULT FALSE;")
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Jadval yangilandi!")
