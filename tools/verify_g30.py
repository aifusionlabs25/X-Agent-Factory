"""
Verification Script for Phase G3.0 (Local Growth Engine)
1. Run Orchestrator (executes smoke_test_g30)
2. Verify Outbound Artifacts (CSV, MD)
3. Verify Batch Ingestion (Inbox -> Processed)
4. Verify Reporting (Weekly Report)
"""
import sys
import shutil
import csv
import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime

# Paths
ROOT = Path(".").resolve()
DB_PATH = ROOT / "growth" / "db" / "growth.db"
RUN_QUEUE = ROOT / "growth" / "runs" / "run_queue.yaml"
OUTCOMES_DIR = ROOT / "growth" / "outcomes"
INBOX_DIR = OUTCOMES_DIR / "inbox"
PROCESSED_DIR = OUTCOMES_DIR / "processed"
REPORTS_DIR = OUTCOMES_DIR / "reports"
REPORT_OUT = ROOT / "growth" / "reports" / "weekly.md"

def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

def pass_check(msg):
    print(f"PASS: {msg}")

def run_cmd(args):
    res = subprocess.run([sys.executable] + args, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Command failed: {' '.join(args)}")
        print(res.stderr)
        fail("Subprocess execution failed")
    return res

def verify():
    print("=== Phase G3.0 Verification ===")
    
    # Clean prev runs
    for p in ROOT.glob("growth/exports/run_*"):
        try:
            shutil.rmtree(p)
        except Exception: pass
        
    if DB_PATH.exists():
        DB_PATH.unlink()
        
    # 1. Run Orchestrator
    print("Running Orchestrator...")
    run_cmd(["tools/run_orchestrator.py", "--queue", str(RUN_QUEUE)])
    pass_check("Orchestrator finished successfully")
    
    # Find artifact dir
    exports = list((ROOT / "growth" / "exports").glob("run_*"))
    if not exports: fail("No run exports found")
    latest_run = sorted(exports, key=lambda x: x.stat().st_mtime)[-1]
    
    # 2. Verify Outbound Artifacts
    if not (latest_run / "outbound_import.csv").exists():
        fail("outbound_import.csv missing")
    if not (latest_run / "campaign_notes.md").exists():
        fail("campaign_notes.md missing")
        
    # Check CSV Content
    with open(latest_run / "outbound_import.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        row = next(reader, None)
        if not row: fail("outbound_import.csv empty")
        if "Variables" not in row: fail("Missing 'Variables' column in outbound CSV")
        
    pass_check(f"Outbound artifacts verified in {latest_run.name}")
    
    # 3. Verify Batch Ingest
    print("Testing Batch Ingest...")
    
    # Setup folders
    for d in [INBOX_DIR, PROCESSED_DIR, REPORTS_DIR]:
        if d.exists(): shutil.rmtree(d)
        d.mkdir(parents=True)
        
    # Create dummy outcome CSV
    with open(INBOX_DIR / "test_batch.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["outcome", "place_id", "website"])
        writer.writeheader()
        # We need a real place_id or domain match to count
        # Let's get one from the export
        with open(latest_run / "leads.csv", 'r', encoding='utf-8') as leads_f:
             leads = list(csv.DictReader(leads_f))
             target = leads[0]
             
        writer.writerow({
            "outcome": "won",
            "place_id": target.get("place_id"), # Match via ID
            "website": ""
        })
        
    run_cmd(["tools/ingest_outcomes.py", "--db", str(DB_PATH), "--batch"])
    
    # Check Inbox Empty
    if list(INBOX_DIR.glob("*.csv")): fail("Inbox not empty after batch")
    # Check Processed
    if not list(PROCESSED_DIR.glob("*.csv")): fail("File not moved to processed")
    # Check Report
    if not list(REPORTS_DIR.glob("*.json")): fail("Batch report missing")
    
    pass_check("Batch ingestion & archiving verified")
    
    # 4. Verify Reporting
    print("Generating Weekly Report...")
    run_cmd(["tools/generate_report.py", "--db", str(DB_PATH), "--out", str(REPORT_OUT)])
    
    if not REPORT_OUT.exists(): fail("Report file missing")
    
    with open(REPORT_OUT, 'r', encoding='utf-8') as f:
        content = f.read()
        if "Pipeline Summary" not in content: fail("Report content malformed")
        
    pass_check("Weekly report generated successfully")
    
    print("\n>>> G3.0 COMPLETE <<<")

if __name__ == "__main__":
    verify()
