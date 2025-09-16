import sqlite3

def init_db():
    conn = sqlite3.connect("bots.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE,
        greeting TEXT DEFAULT 'Hello! Welcome to the channel.'
    )""")
    conn.commit()
    conn.close()

def add_bot(token, greeting="Hello! Welcome to the channel."):
    conn = sqlite3.connect("bots.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO bots (token, greeting) VALUES (?, ?)", (token, greeting))
    conn.commit()
    conn.close()

def update_greeting(bot_id, greeting):
    conn = sqlite3.connect("bots.db")
    c = conn.cursor()
    c.execute("UPDATE bots SET greeting = ? WHERE id = ?", (greeting, bot_id))
    conn.commit()
    conn.close()

def get_bots():
    conn = sqlite3.connect("bots.db")
    c = conn.cursor()
    c.execute("SELECT id, token, greeting FROM bots")
    rows = c.fetchall()
    conn.close()
    return rows
