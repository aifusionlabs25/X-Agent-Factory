"""
Migration Script for G7.0 (Operator Excellence)
Adds lead_tasks and lead_playbooks tables.
"""
import sys
from pathlib import Path
import logging

# Add tools directory to path
sys.path.append(str(Path(__file__).parent))

from growth_db import GrowthDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration_g7")

def run_migration():
    logger.info("Starting G7.0 Database Migration...")
    try:
        db = GrowthDB()
        logger.info(f"✅ Database initialized at: {db.db_path}")
        
        with db._get_conn() as conn:
            cursor = conn.cursor()
            
            # Create lead_tasks
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                place_id TEXT,
                run_id TEXT,
                due_at TEXT,
                task_type TEXT, -- 'follow_up', 'outreach', 'admin'
                status TEXT, -- 'pending', 'done', 'snoozed'
                priority TEXT, -- 'high', 'normal'
                notes TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY(place_id) REFERENCES places(place_id)
            )
            """)
            
            # Create lead_playbooks
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_playbooks (
                place_id TEXT PRIMARY KEY,
                recommendation_json TEXT, -- { "action": "Call", "reason": "...", "script": "..." }
                created_at TEXT,
                updated_at TEXT
            )
            """)
            
            # Verify
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lead_tasks'")
            if cursor.fetchone():
                logger.info("✅ Table 'lead_tasks' exists.")
            else:
                logger.error("❌ Table 'lead_tasks' was NOT created.")
                
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lead_playbooks'")
            if cursor.fetchone():
                logger.info("✅ Table 'lead_playbooks' exists.")
            else:
                logger.error("❌ Table 'lead_playbooks' was NOT created.")

    except Exception as e:
        logger.error(f"❌ Migration Failed: {e}", exc_info=True)

if __name__ == "__main__":
    run_migration()
