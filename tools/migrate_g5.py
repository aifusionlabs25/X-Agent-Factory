"""
Migration Script for G5.0 (Lead Quality & Scoring)
Forces the initialization of the SQLite database schema to ensure new tables 
(place_runs, etc.) are created.
"""
import sys
from pathlib import Path
import logging

# Add tools directory to path
sys.path.append(str(Path(__file__).parent))

from growth_db import GrowthDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

def run_migration():
    logger.info("Starting G5.0 Database Migration...")
    try:
        # Just instantiating GrowthDB triggers _init_schema -> CREATE TABLE IF NOT EXISTS
        db = GrowthDB() 
        logger.info(f"✅ Database initialized at: {db.db_path}")
        
        # Verify schema
        with db._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='place_runs'")
            if cursor.fetchone():
                logger.info("✅ Table 'place_runs' exists.")
            else:
                logger.error("❌ Table 'place_runs' was NOT created.")
                
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='search_runs'")
            if cursor.fetchone():
                logger.info("✅ Table 'search_runs' exists.")
            else:
                logger.error("❌ Table 'search_runs' was NOT created.")
                
    except Exception as e:
        logger.error(f"❌ Migration Failed: {e}", exc_info=True)

if __name__ == "__main__":
    run_migration()
