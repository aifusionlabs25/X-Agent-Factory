"""
Verify G5.0 - Lead Quality & Scoring (Robust with Data Seeding)
1. Test Lead Scorer logic.
2. Seed DB with a test run and test leads.
3. Test Run Metrics SQL query (wins count).
"""
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add tools directory to path
sys.path.append(str(Path(__file__).parent))

try:
    from lead_scorer import get_scorer
    from growth_db import GrowthDB
    print("✅ Successfully imported modules")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    sys.exit(1)

def test_scorer():
    print("\n--- Testing Lead Scorer ---")
    scorer = get_scorer()
    
    p1 = {
        "website": "https://example.com",
        "domain_quality": "good",
        "gbp_data": {"phone": "123", "rating": 4.8, "userRatingCount": 100},
        "tags": ["plumber"]
    }
    s1 = scorer.score_prospect(p1)
    if s1['score'] > 7:
        print("✅ High quality prospect scored correctly")
    else:
        print(f"❌ High quality prospect score unexpected: {s1['score']}")

def test_db_metrics():
    print("\n--- Testing DB Metrics Query (With Seeding) ---")
    db = GrowthDB()
    
    # 1. Seed Data
    run_id = "verify_g5_run_001"
    now = datetime.now().isoformat()
    
    with db._get_conn() as conn:
        cursor = conn.cursor()
        
        # Create Run
        cursor.execute("INSERT OR REPLACE INTO search_runs (run_id, started_at, total_exported, cost_estimate_usd) VALUES (?, ?, ?, ?)", 
                      (run_id, now, 10, 1.25))
        
        # Create Places & Attribution
        # Place A: Won
        place_a = "place_verify_A"
        cursor.execute("INSERT OR REPLACE INTO places (place_id, name) VALUES (?, ?)", (place_a, "Place A"))
        cursor.execute("INSERT OR REPLACE INTO place_status (place_id, status) VALUES (?, ?)", (place_a, "won"))
        cursor.execute("INSERT OR REPLACE INTO place_runs (place_id, run_id) VALUES (?, ?)", (place_a, run_id))
        
        # Place B: Contacted (Not Won)
        place_b = "place_verify_B"
        cursor.execute("INSERT OR REPLACE INTO places (place_id, name) VALUES (?, ?)", (place_b, "Place B"))
        cursor.execute("INSERT OR REPLACE INTO place_status (place_id, status) VALUES (?, ?)", (place_b, "contacted"))
        cursor.execute("INSERT OR REPLACE INTO place_runs (place_id, run_id) VALUES (?, ?)", (place_b, run_id))
        
        conn.commit()
        print(f"✅ Seeded Run {run_id} with 1 Win and 1 Contacted")

    # 2. Test API Query
    with db._get_conn() as conn:
        cursor = conn.cursor()
        
        # Check if place_runs exists (Simulate API check)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='place_runs'")
        has_table = cursor.fetchone()
        
        if not has_table:
            print("❌ place_runs table MISSING in sqlite_master!")
            return

        query = """
            SELECT 
                sr.run_id,
                (SELECT COUNT(*) 
                 FROM place_runs pr 
                 JOIN place_status ps ON pr.place_id = ps.place_id 
                 WHERE pr.run_id = sr.run_id AND ps.status = 'won') as wins_count,
                 total_exported
            FROM search_runs sr
            WHERE sr.run_id = ?
        """
        try:
            cursor.execute(query, (run_id,))
            row = cursor.fetchone()
            if row:
                print(f"  Run: {row[0]} | Wins: {row[1]} | Exported: {row[2]}")
                if row[1] == 1:
                    print("✅ Correct wins count (1)")
                else:
                    print(f"❌ Incorrect wins count: {row[1]} (Expected 1)")
            else:
                print("❌ Run not found in query")
        except Exception as e:
            print(f"❌ Query Failed: {e}")

if __name__ == "__main__":
    test_scorer()
    test_db_metrics()
