"""
Growth Database - SQLite Persistence Layer (Phase G1.9)
Handles deduplication, pipeline state, suppression, and caching.

Schema based on Nova SPEC:
- places: Master candidate table (deduped by place_id)
- place_status: Pipeline tracking (new -> shortlisted -> exported)
- search_runs: Audit log for monthly runs
- search_queries: Query-level granularity
- cache: Response caching (TTL)
"""
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "growth" / "db" / "growth.db"

class GrowthDB:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        
        self._init_schema()
        
    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        
    def _init_schema(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # 1. Places (Master Dedupe)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS places (
                place_id TEXT PRIMARY KEY,
                name TEXT,
                formatted_address TEXT,
                city TEXT,
                state TEXT,
                zip TEXT,
                lat REAL,
                lng REAL,
                types_json TEXT,
                website TEXT,
                phone TEXT,
                rating REAL,
                user_ratings_total INTEGER,
                business_status TEXT,
                source TEXT,
                first_seen_at TEXT,
                last_seen_at TEXT,
                last_enriched_at TEXT
            )
            """)
            
            # 2. Place Status (Pipeline)
            # G2.0: Added Outcome States
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS place_status (
                place_id TEXT PRIMARY KEY,
                status TEXT, -- new, shortlisted, exported, contacted, booked_meeting, won, dead_end, do_not_contact
                status_reason TEXT,
                outcome_notes TEXT,
                outcome_source TEXT,
                owner TEXT,
                last_contacted_at TEXT,
                updated_at TEXT,
                FOREIGN KEY(place_id) REFERENCES places(place_id)
            )
            """)
            
            # 3. Search Runs (Audit)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_runs (
                run_id TEXT PRIMARY KEY,
                started_at TEXT,
                ended_at TEXT,
                coverage_pack TEXT,
                config_json TEXT,
                vertical_pack_id TEXT, -- Traceability
                total_candidates INTEGER DEFAULT 0,
                total_enriched INTEGER DEFAULT 0,
                total_exported INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                cost_estimate_usd REAL DEFAULT 0.0 -- Cost Telemetry
            )
            """)
            
            # 4. Search Queries (Granular Log)
            # Nova Spec: Added pack traceability
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_queries (
                query_id TEXT PRIMARY KEY,
                run_id TEXT,
                region_tag TEXT,
                text_query TEXT,
                max_results INTEGER,
                result_count INTEGER,
                status TEXT,
                error TEXT,
                created_at TEXT,
                coverage_pack_id TEXT,
                vertical_pack_id TEXT,
                template_id TEXT,
                trade_id TEXT
            )
            """)
            
            # 5. Cache (TTL)
            # Nova Spec: Key must include endpoint + field_mask
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                cache_key TEXT PRIMARY KEY,
                payload_json TEXT,
                created_at TEXT,
                expires_at TEXT,
                endpoint TEXT,
                field_mask TEXT
            )
            """)
            
            # 6. Run Attribution (G5.0)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS place_runs (
                place_id TEXT,
                run_id TEXT,
                created_at TEXT,
                PRIMARY KEY (place_id, run_id),
                FOREIGN KEY(place_id) REFERENCES places(place_id),
                FOREIGN KEY(run_id) REFERENCES search_runs(run_id)
            )
            """)

            # 7. Lead Tasks (G7.0)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                place_id TEXT,
                run_id TEXT,
                due_at TEXT,
                task_type TEXT, 
                status TEXT, 
                priority TEXT,
                notes TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY(place_id) REFERENCES places(place_id)
            )
            """)

            # 8. Lead Playbooks (G7.0)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_playbooks (
                place_id TEXT PRIMARY KEY,
                recommendation_json TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """)
            
            conn.commit()

    # ==========================
    # Places & Status
    # ==========================
    
    def upsert_place(self, place: Dict, source: str = "PLACES_API", run_id: str = None) -> bool:
        """Upsert a place record. Returns True if new to DB."""
        now = datetime.now().isoformat()
        place_id = place.get("id") or place.get("place_id")
        
        if not place_id:
            logger.warning("Attempted to upsert place without ID")
            return False
            
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Check existence
            cursor.execute("SELECT first_seen_at FROM places WHERE place_id = ?", (place_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update last_seen
                cursor.execute("""
                UPDATE places SET 
                    last_seen_at = ?,
                    source = ?
                WHERE place_id = ?
                """, (now, source, place_id))
                return False
            else:
                # Insert new
                types_json = json.dumps(place.get("types", []))
                loc = place.get("location", {})
                
                cursor.execute("""
                INSERT INTO places (
                    place_id, name, formatted_address, 
                    lat, lng, types_json, 
                    website, phone, rating, user_ratings_total,
                    business_status, source, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    place_id, place.get("displayName", {}).get("text", place.get("name")), 
                    place.get("formattedAddress", place.get("address")),
                    loc.get("latitude"), loc.get("longitude"), types_json,
                    place.get("websiteUri", place.get("website")), 
                    place.get("nationalPhoneNumber", place.get("phone")),
                    place.get("rating"), place.get("userRatingCount"),
                    place.get("businessStatus"), source, now, now
                ))
                
                # Init status
                cursor.execute("""
                INSERT INTO place_status (place_id, status, updated_at)
                VALUES (?, 'new', ?)
                """, (place_id, now))
                
                # Log run attribution
                if run_id:
                    cursor.execute("""
                    INSERT OR IGNORE INTO place_runs (place_id, run_id, created_at)
                    VALUES (?, ?, ?)
                    """, (place_id, run_id, now))
                    
                return True
                
            # If exists, still log run attribution if new for this run
            if run_id:
                cursor.execute("""
                INSERT OR IGNORE INTO place_runs (place_id, run_id, created_at)
                VALUES (?, ?, ?)
                """, (place_id, run_id, now))
                
            return False

    def get_run_metrics(self, run_id: str) -> Dict:
        """Get metrics for a specific run."""
        stats = {"leads": 0, "wins": 0, "cost": 0.0}
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Leads count
            cursor.execute("SELECT count(*) FROM place_runs WHERE run_id = ?", (run_id,))
            stats["leads"] = cursor.fetchone()[0]
            
            # Wins count (joined)
            cursor.execute("""
                SELECT count(*) 
                FROM place_runs pr
                JOIN place_status ps ON pr.place_id = ps.place_id
                WHERE pr.run_id = ? AND ps.status = 'won'
            """, (run_id,))
            stats["wins"] = cursor.fetchone()[0]
            
            # Cost
            cursor.execute("SELECT cost_estimate_usd FROM search_runs WHERE run_id = ?", (run_id,))
            res = cursor.fetchone()
            if res and res[0]:
                stats["cost"] = res[0]
                
        return stats

    def is_suppressed(self, place_id: str) -> bool:
        """Check if place is in suppress list (dead_end, do_not_contact)."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM place_status WHERE place_id = ?", (place_id,))
            row = cursor.fetchone()
            if row and row[0] in ['dead_end', 'do_not_contact']:
                return True
        return False
        
    def update_outcome(self, place_id: str, outcome: str, notes: str = None, source: str = "manual"):
        """
        Update prospect outcome state (G2.0).
        Valid outcomes: new, exported, contacted, booked_meeting, won, dead_end, do_not_contact
        """
        now = datetime.now().isoformat()
        
        # Normalize outcome to status
        status_map = {
            "dnc": "do_not_contact",
            "suppressed": "do_not_contact",
            "dead": "dead_end",
            "meeting": "booked_meeting",
            "loss": "dead_end"
        }
        final_status = status_map.get(outcome.lower(), outcome.lower())
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute("SELECT status FROM place_status WHERE place_id = ?", (place_id,))
            row = cursor.fetchone()
            
            if row:
                cursor.execute("""
                UPDATE place_status 
                SET status = ?, outcome_notes = ?, outcome_source = ?, updated_at = ?
                WHERE place_id = ?
                """, (final_status, notes, source, now, place_id))
            else:
                # Create stub if missing
                cursor.execute("""
                INSERT INTO place_status (place_id, status, outcome_notes, outcome_source, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """, (place_id, final_status, notes, source, now))
                
            conn.commit()
            
        # Log Activity
        self.log_activity(place_id, "status_change", None, final_status, notes)

    def log_activity(self, place_id: str, action: str, old: str = None, new: str = None, notes: str = None):
        """Log activity to valid audit trail."""
        try:
            with self._get_conn() as conn:
                conn.execute("""
                INSERT INTO place_activity_log (place_id, action, old_value, new_value, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (place_id, action, old, new, notes, datetime.now().isoformat()))
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            
    def get_weekly_stats(self) -> Dict:
        """G2.0 Metrics Rollup"""
        stats = {
            "total_exported": 0,
            "total_contacted": 0,
            "won": 0,
            "meetings": 0,
            "suppressed": 0
        }
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Exported (approximation based on status or logs - using status for now)
            cursor.execute("SELECT count(*) FROM place_status WHERE status IN ('exported', 'contacted', 'booked_meeting', 'won', 'dead_end', 'do_not_contact')")
            res = cursor.fetchone()
            stats["total_exported"] = res[0] if res else 0
            
            # Funnel
            cursor.execute("SELECT status, count(*) FROM place_status GROUP BY status")
            rows = cursor.fetchall()
            for status, count in rows:
                if status in ['contacted', 'booked_meeting', 'won', 'dead_end', 'do_not_contact']:
                    stats["total_contacted"] += count
                if status == 'won':
                    stats["won"] += count
                if status == 'booked_meeting':
                    stats["meetings"] += count
                if status in ['dead_end', 'do_not_contact']:
                    stats["suppressed"] += count
                    
        return stats

    # ==========================
    # Runs & Queries
    # ==========================
    
    def log_run_start(self, run_dict: Dict):
        """Log run start with full metadata."""
        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO search_runs (
                run_id, started_at, coverage_pack, vertical_pack_id, config_json
            ) VALUES (?, ?, ?, ?, ?)
            """, (
                run_dict["run_id"], 
                datetime.now().isoformat(), 
                run_dict["coverage_pack"], 
                run_dict.get("vertical_pack_id"),
                json.dumps(run_dict.get("config", {}))
            ))
            
    def log_run_end(self, run_id: str, stats: Dict):
        """Log run end with stats and cost."""
        with self._get_conn() as conn:
            conn.execute("""
            UPDATE search_runs 
            SET ended_at = ?, total_candidates = ?, total_enriched = ?, total_exported = ?, cost_estimate_usd = ?
            WHERE run_id = ?
            """, (
                datetime.now().isoformat(),
                stats.get("candidates", 0), stats.get("enriched", 0), stats.get("exported", 0),
                stats.get("cost_usd", 0.0),
                run_id
            ))
            
    def log_query(self, query: Dict, result_count: int, error: str = None):
        status = "failed" if error else "completed"
        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO search_queries (
                query_id, run_id, region_tag, text_query, 
                max_results, result_count, status, error, created_at,
                coverage_pack_id, vertical_pack_id, template_id, trade_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query.get("query_id"), query.get("run_id"), query.get("region_tag"),
                query.get("text"), query.get("max_results"), result_count,
                status, error, datetime.now().isoformat(),
                query.get("coverage_pack_id"), query.get("vertical_pack_id"),
                query.get("template_id"), query.get("trade_id")
            ))

    # ==========================
    # Cache
    # ==========================
    
    def get_cache(self, key: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT payload_json, expires_at FROM cache WHERE cache_key = ?", (key,))
            row = cursor.fetchone()
            
            if row:
                payload, expires_at = row
                if datetime.now().isoformat() < expires_at:
                    return json.loads(payload)
                else:
                    # Expired
                    cursor.execute("DELETE FROM cache WHERE cache_key = ?", (key,))
        return None
        
    def set_cache(self, key: str, payload: Any, ttl_hours: int = 24, extras: Dict = None):
        expires = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
        extras = extras or {}
        with self._get_conn() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO cache (
                cache_key, payload_json, created_at, expires_at, endpoint, field_mask
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                key, json.dumps(payload), datetime.now().isoformat(), expires,
                extras.get("endpoint"), extras.get("field_mask")
            ))

    # ==========================
    # G7.0 Tasks & Playbooks
    # ==========================

    def create_task(self, place_id: str, due_at: str, notes: str, run_id: str = None, priority: str = "normal", task_type: str = "follow_up", source: str = "manual") -> int:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO lead_tasks (place_id, run_id, due_at, task_type, status, priority, notes, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?)
            """, (place_id, run_id, due_at, task_type, priority, notes, source, datetime.now().isoformat(), datetime.now().isoformat()))
            task_id = cursor.lastrowid
            
            # Log it
            self.log_activity(place_id, "task_created", None, str(task_id), f"{task_type} due {due_at}: {notes}")
            return task_id

    def update_task_status(self, task_id: int, status: str, user: str = "user"):
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            if status == 'done':
                cursor.execute("""
                    UPDATE lead_tasks 
                    SET status = ?, completed_at = ?, completed_by = ?, updated_at = ? 
                    WHERE task_id = ?
                """, (status, now, user, now, task_id))
            else:
                # Clear completion if re-opened
                cursor.execute("""
                    UPDATE lead_tasks 
                    SET status = ?, completed_at = NULL, completed_by = NULL, updated_at = ? 
                    WHERE task_id = ?
                """, (status, now, task_id))
            
            # Get place_id for logging
            cursor.execute("SELECT place_id FROM lead_tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if row:
                self.log_activity(row[0], "task_update", None, status, f"Task {task_id} marked {status}")

    def get_pending_tasks(self) -> List[Dict]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
            SELECT t.*, p.name as place_name, p.phone, p.website, ps.status as lead_status, ps.score 
            FROM lead_tasks t
            LEFT JOIN places p ON t.place_id = p.place_id
            LEFT JOIN place_status ps ON t.place_id = ps.place_id
            WHERE t.status != 'done'
            ORDER BY t.due_at ASC, t.priority DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def auto_create_tasks(self, run_id: str = None):
        """
        Scans leads and auto-creates tasks based on G9 rules.
        Idempotent: Checks if similar task exists to avoid duplicates.
        """
        from tools.suggestion_engine import SuggestionEngine
        engine = SuggestionEngine()
        
        # 1. Fetch leads
        leads = self.get_run_leads(run_id) if run_id else [] 
        
        created_count = 0
        
        for lead in leads:
            place_id = lead['place_id']
            # Get existing tasks
            existing_tasks = self.get_lead_tasks(place_id)
            
            suggestions = engine.generate_suggestions(lead, existing_tasks)
            
            for sugg in suggestions:
                if sugg['confidence'] == 'high' and sugg['action'] == 'call':
                    # Check duplication
                    if not any(t['task_type'] == 'call' and t['status'] != 'done' for t in existing_tasks):
                        # Create it
                        due_at = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0).isoformat()
                        self.create_task(
                            place_id=place_id,
                            due_at=due_at,
                            notes=f"Auto: {sugg['label']}",
                            task_type='call',
                            priority='high',
                            source='auto'
                        )
                        created_count += 1
                        
        return created_count
        
    def get_run_leads(self, run_id: str) -> List[Dict]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
            SELECT p.*, ps.score, ps.status, ps.updated_at
            FROM place_runs pr
            JOIN places p ON pr.place_id = p.place_id
            JOIN place_status ps ON pr.place_id = ps.place_id
            WHERE pr.run_id = ?
            """, (run_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_lead_tasks(self, place_id: str) -> List[Dict]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lead_tasks WHERE place_id = ?", (place_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_completed_tasks(self, limit: int = 10) -> List[Dict]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
            SELECT t.*, p.name as place_name, p.phone, p.website, ps.status as lead_status, ps.score 
            FROM lead_tasks t
            LEFT JOIN places p ON t.place_id = p.place_id
            LEFT JOIN place_status ps ON t.place_id = ps.place_id
            WHERE t.status = 'done'
            ORDER BY t.completed_at DESC
            LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def save_playbook(self, place_id: str, recommendation: Dict):
        with self._get_conn() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO lead_playbooks (place_id, recommendation_json, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """, (place_id, json.dumps(recommendation), datetime.now().isoformat(), datetime.now().isoformat()))

    def get_playbook(self, place_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT recommendation_json FROM lead_playbooks WHERE place_id = ?", (place_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None

if __name__ == "__main__":
    # Test DB init
    db = GrowthDB()
    print(f"DB initialized at {db.db_path}")
