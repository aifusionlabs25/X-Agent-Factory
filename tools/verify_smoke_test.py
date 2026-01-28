"""
Verification Script for Smoke Test G1.9
"""
import sys
import json
import sqlite3
from pathlib import Path

# Paths
EXPORTS_DIR = Path("growth/exports")
DB_PATH = Path("growth/db/growth.db")

def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

def pass_check(msg):
    print(f"PASS: {msg}")

def verify():
    print("=== Smoke Test Verification ===")
    
    # 1. Find Latest Export
    if not EXPORTS_DIR.exists():
        fail(f"Export directory missing: {EXPORTS_DIR.absolute()}")
        
    print(f"Checking exports in: {EXPORTS_DIR.absolute()}")
    items = list(EXPORTS_DIR.iterdir())
    run_dirs = [d for d in items if d.is_dir() and d.name.startswith("run_")]
    print(f"Found {len(run_dirs)} run directories.")
    
    if not run_dirs:
        fail("No run export directories found.")
        
    # 1. Hardening: Sort by mtime (latest first)
    latest_run = sorted(run_dirs, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    print(f"Inspecting Latest Run: {latest_run.name}")
    
    # 2. Check Artifacts
    csv_file = latest_run / "leads.csv"
    jsonl_file = latest_run / "leads.jsonl"
    
    if not csv_file.exists() or csv_file.stat().st_size == 0:
        fail("leads.csv missing or empty")
    pass_check("leads.csv created and non-empty")
        
    if not jsonl_file.exists() or jsonl_file.stat().st_size == 0:
        fail("leads.jsonl missing or empty")
    pass_check("leads.jsonl created and non-empty")
    
    summary_file = latest_run / "run_summary.json"
    if not summary_file.exists():
        # Fallback check
        if (latest_run / "summary.json").exists():
            pass_check("Found summary.json (legacy)")
            summary_file = latest_run / "summary.json"
        else:
            fail("run_summary.json missing")
        
    with open(summary_file, 'r') as f:
        summary = json.load(f)
        
        # 3. Hardening: Strict Summary Validation
        required_keys = ["run_id", "candidates", "enriched", "total_queries"]
        missing = [k for k in required_keys if k not in summary]
        if missing:
            fail(f"Summary missing required fields: {missing}")
            
    pass_check(f"Summary Valid (Candidates: {summary['candidates']}, Enriched: {summary['enriched']})")
    
    # 4. Check SQLite (Decoupled Lookup)
    if not DB_PATH.exists():
        fail("DB missing")
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Read run_id from summary for DB lookup
    target_run_id = summary.get("run_id")
    print(f"Verifying DB for Run ID: {target_run_id}")
    
    cursor.execute("SELECT run_id FROM search_runs WHERE run_id = ?", (target_run_id,))
    if not cursor.fetchone():
        fail(f"Run ID {target_run_id} not found in search_runs table")
    pass_check("Run logged in DB")
    
    # Check Queries
    cursor.execute("SELECT count(*) FROM search_queries WHERE run_id = ?", (target_run_id,))
    q_count = cursor.fetchone()[0]
    if q_count == 0:
        fail("No queries logged for this run")
    pass_check(f"Queries logged: {q_count}")
    
    conn.close()
    print("\n>>> SMOKE TEST PASSED <<<")

if __name__ == "__main__":
    verify()
