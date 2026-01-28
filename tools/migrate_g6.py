"""
Migration Script for G6.0 (UX Leverage)
Adds place_activity_log table for tracking status changes and notes.
"""
import sys
from pathlib import Path
import logging

# Add tools directory to path
sys.path.append(str(Path(__file__).parent))

from growth_db import GrowthDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration_g6")

def run_migration():
    logger.info("Starting G6.0 Database Migration...")
    try:
        db = GrowthDB()
        logger.info(f"✅ Database initialized at: {db.db_path}")
        
        with db._get_conn() as conn:
            cursor = conn.cursor()
            
            # Create place_activity_log
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS place_activity_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                place_id TEXT,
                action TEXT, -- 'status_change', 'note_added'
                old_value TEXT,
                new_value TEXT,
                notes TEXT,
                created_at TEXT,
                FOREIGN KEY(place_id) REFERENCES places(place_id)
            )
            """)
            
            # Verify
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='place_activity_log'")
            if cursor.fetchone():
                logger.info("✅ Table 'place_activity_log' exists.")
            else:
                logger.error("❌ Table 'place_activity_log' was NOT created.")
                
    except Exception as e:
        logger.error(f"❌ Migration Failed: {e}", exc_info=True)

if __name__ == "__main__":
    run_migration()
