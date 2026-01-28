"""
Verification Script for Phase G4.0 (LeadOps UI)
Checks if the new Dashboard API endpoints are reachable and return valid data.
"""
import sys
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:3000"

def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

def pass_check(msg):
    print(f"PASS: {msg}")

def verify():
    print("=== Phase G4.0 Verification ===")
    
    # 1. Check Stats API
    try:
        url = f"{BASE_URL}/api/growth/stats"
        print(f"Checking {url}...")
        res = requests.get(url, timeout=5)
        
        if res.status_code != 200:
            print(f"Status: {res.status_code}")
            print(res.text)
            fail("Stats API returned non-200")
            
        data = res.json()
        if not data.get("success"):
            print(data)
            fail("Stats API success=false")
            
        stats = data.get("stats", {})
        if "total_exported" not in stats:
            fail("Stats missing 'total_exported' field")
            
        pass_check(f"Stats API Verified. Exported: {stats.get('total_exported')}")
        
    except Exception as e:
        fail(f"Stats API Exception: {e}")

    # 2. Check Runs API
    try:
        url = f"{BASE_URL}/api/growth/runs"
        print(f"Checking {url}...")
        res = requests.get(url, timeout=5)
        
        if res.status_code != 200:
            print(f"Status: {res.status_code}")
            print(res.text)
            fail("Runs API returned non-200")
            
        data = res.json()
        if not data.get("success"):
            print(data)
            fail("Runs API success=false")
            
        runs = data.get("runs", [])
        pass_check(f"Runs API Verified. Found {len(runs)} runs")
        
    except Exception as e:
        fail(f"Runs API Exception: {e}")
        
    print("\n>>> G4.0 UI API PASSED <<<")
    print("Note: Manual UI verification required for actual button clicks.")

if __name__ == "__main__":
    verify()
