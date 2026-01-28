import sqlite3
from pathlib import Path

DB_PATH = Path("growth/db/growth.db")

def migrate():
    print("🚀 Starting G9 Migration...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(lead_tasks)")
    columns = [c[1] for c in cursor.fetchall()]
    
    if "source" not in columns:
        print("   Adding source column...")
        cursor.execute("ALTER TABLE lead_tasks ADD COLUMN source TEXT DEFAULT 'manual'")
    else:
        print("   source already exists.")
        
    conn.commit()
    conn.close()
    print("✅ Migration Complete.")

if __name__ == "__main__":
    migrate()
