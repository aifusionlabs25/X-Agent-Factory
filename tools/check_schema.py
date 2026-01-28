import sqlite3
from pathlib import Path

db_path = Path("growth/db/growth.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

cursor.execute("PRAGMA table_info(place_status);")
columns = cursor.fetchall()
print("place_status Columns:", [c[1] for c in columns])

conn.close()
