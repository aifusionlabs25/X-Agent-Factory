import sqlite3
from pathlib import Path

DB_PATH = Path("growth/db/growth.db")

def migrate():
    print("🚀 Starting G8 Migration...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(lead_tasks)")
    columns = [c[1] for c in cursor.fetchall()]
    
    if "completed_at" not in columns:
        print("   Adding completed_at column...")
        cursor.execute("ALTER TABLE lead_tasks ADD COLUMN completed_at TEXT")
    else:
        print("   completed_at already exists.")
        
    if "completed_by" not in columns:
        print("   Adding completed_by column...")
        cursor.execute("ALTER TABLE lead_tasks ADD COLUMN completed_by TEXT")
    else:
        print("   completed_by already exists.")

    conn.commit()
    conn.close()
    print("✅ Migration Complete.")

if __name__ == "__main__":
    migrate()
