"""
Verify G6.0 - UX Leverage & Activity Logging
1. Seeds a test run and lead in the DB.
2. Calls the Runs/Leads API to fetch the lead.
3. Calls the Status API to update the lead.
4. Verifies the database state (Activity Log present).
"""
import sys
import sqlite3
import requests
import json
from pathlib import Path
from datetime import datetime
import time

# Add current dir to path
sys.path.append(str(Path(__file__).parent))
from growth_db import GrowthDB

BASE_URL = "http://localhost:3000"

def seed_data(run_id, place_id):
    print(f"🌱 Seeding Run {run_id} and Place {place_id}...")
    db = GrowthDB()
    now = datetime.now().isoformat()
    
    with db._get_conn() as conn:
        cursor = conn.cursor()
        # Seed Run
        cursor.execute("INSERT OR REPLACE INTO search_runs (run_id, started_at, total_exported) VALUES (?, ?, ?)", 
                      (run_id, now, 1))
        # Seed Place
        cursor.execute("INSERT OR REPLACE INTO places (place_id, name, formatted_address) VALUES (?, ?, ?)", 
                      (place_id, "G6 Verify Corp", "123 Verification Lane"))
        # Seed Attribution
        cursor.execute("INSERT OR REPLACE INTO place_runs (place_id, run_id, created_at) VALUES (?, ?, ?)", 
                      (place_id, run_id, now))
        # Seed Status (New)
        cursor.execute("INSERT OR REPLACE INTO place_status (place_id, status, updated_at) VALUES (?, ?, ?)", 
                      (place_id, "new", now))
        conn.commit()

def verify_api_get(run_id):
    print(f"\n🔍 Verifying GET {BASE_URL}/api/growth/runs/{run_id}/leads ...")
    try:
        url = f"{BASE_URL}/api/growth/runs/{run_id}/leads"
        res = requests.get(url, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            if data.get("success") and len(data.get("leads", [])) > 0:
                print("✅ API returned leads successfully.")
                print(f"   Found: {data['leads'][0]['name']}")
                return True
            else:
                print(f"❌ API success but no leads or success=false: {data}")
        else:
            print(f"❌ API Failed: {res.status_code} - {res.text}")
            
    except Exception as e:
        print(f"❌ Request Error: {e}")
        print("   (Is the dashboard server running on localhost:3000?)")
    return False

def verify_api_post(place_id):
    print(f"\n📝 Verifying POST {BASE_URL}/api/growth/leads/{place_id}/status ...")
    try:
        url = f"{BASE_URL}/api/growth/leads/{place_id}/status"
        payload = {"status": "won", "notes": "Verified by G6 script"}
        res = requests.post(url, json=payload, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            if data.get("success"):
                print("✅ API status update successful.")
                return True
            else:
                print(f"❌ API success=false: {data}")
        else:
            print(f"❌ API Failed: {res.status_code} - {res.text}")
            
    except Exception as e:
        print(f"❌ Request Error: {e}")
    return False

def verify_db_state(place_id):
    print(f"\n🗄️ Verifying Database State...")
    db = GrowthDB()
    with db._get_conn() as conn:
        cursor = conn.cursor()
        
        # Check Status
        cursor.execute("SELECT status, outcome_notes FROM place_status WHERE place_id = ?", (place_id,))
        row = cursor.fetchone()
        if row and row[0] == "won" and row[1] == "Verified by G6 script":
            print("✅ DB place_status updated correctly.")
        else:
            print(f"❌ DB place_status mismatch: {row}")

        # Check Activity Log
        try:
            cursor.execute("SELECT action, new_value, notes FROM place_activity_log WHERE place_id = ? ORDER BY log_id DESC LIMIT 1", (place_id,))
            log = cursor.fetchone()
            if log:
                print(f"✅ Activity Log found: {log}")
                if log[0] == "status_change" and log[1] == "won":
                    print("✅ Log entry content correct.")
                else:
                    print("❌ Log entry content incorrect.")
            else:
                print("❌ No activity log entry found.")
        except Exception as e:
            print(f"❌ Failed to query activity log: {e}")

def main():
    run_id = "g6_verify_run"
    place_id = "g6_place_001"
    
    seed_data(run_id, place_id)
    
    if verify_api_get(run_id):
        if verify_api_post(place_id):
             verify_db_state(place_id)
        else:
            print("Skipping DB check due to POST failure.")
    else:
        print("Skipping remaining checks due to GET failure.")

if __name__ == "__main__":
    main()
