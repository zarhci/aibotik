import sqlite3
import os
import sys

DB_NAME = os.getenv("DB_NAME")
if not DB_NAME:
    print("DB_NAME not set")
    sys.exit(1)

DB_PATH = f"{DB_NAME}.db"

try:
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    conn.close()
    sys.exit(0)
except Exception as e:
    print("DB healthcheck failed:", e)
    sys.exit(1)
