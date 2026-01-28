"""
Verification Script for Phase G2.0 (LeadOps Loop)
1. Run smoke test (generate leads)
2. Generate mock outcome CSV
3. Ingest outcomes
4. Verify DB updates (status, notes)
5. Verify suppression prevents re-export (simulated)
"""
import sys
import csv
import json
import uuid
import sqlite3
import time
from pathlib import Path

import argparse

# Paths
ROOT = Path(".").resolve()
DEFAULT_DB_PATH = ROOT / "growth" / "db" / "growth.db"
OUTCOMES_DIR = ROOT / "growth" / "outcomes"
OUTCOMES_DIR.mkdir(parents=True, exist_ok=True)

def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

def pass_check(msg):
    print(f"PASS: {msg}")

def verify(db_path_arg=None):
    print("=== Phase G2.0 Verification ===")
    
    db_path = Path(db_path_arg) if db_path_arg else DEFAULT_DB_PATH
    
    # 1. Check DB existence (Smoke test should have run)
    if not db_path.exists():
        fail(f"DB missing at {db_path}. Did you run the smoke test runner?")
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get a few place IDs to mock outcomes for
    cursor.execute("""
        SELECT ps.place_id, p.name, ps.status 
        FROM place_status ps 
        JOIN places p ON ps.place_id = p.place_id 
        LIMIT 5
    """)
    rows = cursor.fetchall()
    
    if not rows:
        fail("No places found in DB to mock outcomes for.")
        
    print(f"Found {len(rows)} places to test outcomes.")
    
    # 2. Mock Outcomes
    # Scenario: 
    # - 1 Won
    # - 1 Dead End
    # - 1 Meeting
    # - 1 DNC
    
    scenarios = [
        {"outcome": "won", "notes": "Closed via email"},
        {"outcome": "dead", "notes": "Out of business"},
        {"outcome": "meeting", "notes": "Demo booked"},
        {"outcome": "dnc", "notes": "Angry response"}
    ]
    
    to_ingest = []
    
    for i, row in enumerate(rows):
        if i >= len(scenarios): break
        s = scenarios[i]
        to_ingest.append({
            "place_id": row[0],
            "name": row[1],
            "outcome": s["outcome"],
            "notes": s["notes"],
            "date": "2026-01-22"
        })
        
    out_csv = OUTCOMES_DIR / f"test_outcomes_{uuid.uuid4().hex[:6]}.csv"
    keys = ["place_id", "name", "outcome", "notes", "date"]
    
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(to_ingest)
        
    pass_check(f"Created mock outcomes CSV: {out_csv.name}")
    
    # 3. Trigger Ingest
    print("Running Ingest Tool...")
    import subprocess
    cmd = [sys.executable, "tools/ingest_outcomes.py", "--db", str(db_path), "--file", str(out_csv)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    if res.returncode != 0:
        print(res.stderr)
        fail("Ingest tool failed")
        
    pass_check("Ingest tool executed successfully")
    
    # 4. Verify DB Status Updates
    for item in to_ingest:
        pid = item["place_id"]
        expected_status_map = {
            "won": "won",
            "dead": "dead_end",
            "meeting": "booked_meeting",
            "dnc": "do_not_contact"
        }
        expected = expected_status_map[item["outcome"]]
        
        cursor.execute("SELECT status, outcome_notes FROM place_status WHERE place_id = ?", (pid,))
        row = cursor.fetchone()
        
        if not row:
            fail(f"Place {pid} mismatch: Not found")
            
        bs, notes = row
        if bs != expected:
            fail(f"Status mismatch for {pid}: Expected {expected}, Got {bs}")
            
        if item["notes"] not in notes:
            fail(f"Notes mismatch for {pid}: Expected '{item['notes']}', Got '{notes}'")
            
    pass_check(f"Verified {len(to_ingest)} outcome updates in DB")
    
    # 5. Verify Metrics Helper
    # We should have counts now
    print("Checking Metrics Rollup...")
    
    # Using python to call the db method directly for verification logic
    # We need to instantiate GrowthDB
    sys.path.append(str(ROOT / "tools"))
    from growth_db import GrowthDB
    db = GrowthDB(db_path=db_path)
    stats = db.get_weekly_stats()
    
    print(json.dumps(stats, indent=2))
    
    if stats["won"] < 1: fail("Metrics: 'won' count incorrect")
    if stats["meetings"] < 1: fail("Metrics: 'meetings' count incorrect")
    if stats["suppressed"] < 2: fail("Metrics: 'suppressed' count too low (dead + dnc)")
    
    pass_check("Metrics Rollup verified")
    
    # 6. Verify Suppression (Export Selection Check)
    print("Checking Suppression Logic...")
    
    # Query for exportable candidates (should exclude dead/dnc)
    # Simulating what an exporter would look for (e.g. status='new' or 'shortlisted' or 'exported')
    # Specifically, ensuring our suppressed IDs are NOT in the result set if we filter for "active" statuses
    
    suppressed_ids = [item["place_id"] for item in to_ingest if item["outcome"] in ["dead", "dnc"]]
    
    cursor.execute("""
        SELECT place_id FROM place_status 
        WHERE status NOT IN ('dead_end', 'do_not_contact')
    """)
    active_places = [row[0] for row in cursor.fetchall()]
    
    for pid in suppressed_ids:
        if pid in active_places:
            fail(f"Suppression Failed: Place {pid} (dead/dnc) found in active pool")
        # Double check via is_suppressed helper
        if not db.is_suppressed(pid):
            fail(f"is_suppressed({pid}) returned False")
    
    pass_check(f"Suppression Verified: {len(suppressed_ids)} records excluded from active pool")
    
    # Clean up
    out_csv.unlink()
    
    print("\n>>> G2.0 SMOKE TEST PASSED <<<")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", help="Path to growth.db")
    args = parser.parse_args()
    verify(args.db)
