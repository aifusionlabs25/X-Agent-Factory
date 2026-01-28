"""
Verify G7.0 - Operator Excellence
1. Verify Note Parser logic.
2. Verify Playbook Engine logic.
3. Verify Task API (Create, Get, Update).
4. Verify Lead Scorer Confidence.
"""
import sys
import requests
import json
import traceback
from pathlib import Path
from datetime import datetime
import time

# Add current dir to path
sys.path.append(str(Path(__file__).parent))

try:
    from note_parser import parse_followup
    from playbook_engine import generate_playbook
    from lead_scorer import get_scorer
    from growth_db import GrowthDB
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

BASE_URL = "http://localhost:3000"

def verify_logic():
    print("\n🧠 Verifying Logic Engines...")
    success = True
    
    try:
        # 1. Note Parser
        note = "Call John tomorrow"
        due, typ = parse_followup(note)
        if due and typ == "call":
            print(f"✅ Note Parser: '{note}' -> {due} ({typ})")
        else:
            print(f"❌ Note Parser Failed: {due}, {typ}")
            success = False
            
        # 2. Playbook
        lead = {"score": 9, "phone": "123", "status": "new"}
        pb = generate_playbook(lead)
        if pb['action'] == "Call Now" and pb['priority'] == "High":
             print(f"✅ Playbook Engine: Score 9 + Phone -> {pb['action']}")
        else:
             print(f"❌ Playbook Failed: {pb}")
             success = False
             
        # 3. Scorer Confidence
        print("   Testing Scorer...")
        scorer = get_scorer()
        print(f"   Scorer instance: {scorer}")
        prospect = {"website": "x", "phone": "y", "name": "z"}
        print(f"   Scoring prospect: {prospect}")
        res = scorer.score_prospect(prospect)
        print(f"   Result: {res}")
        
        if res.get('confidence') == "high":
            print(f"✅ Scorer Confidence: 3 fields -> High")
        else:
            print(f"❌ Scorer Confidence Failed: {res}")
            success = False
            
    except Exception as e:
        print(f"❌ Logic Verification Crashed: {e}")
        traceback.print_exc()
        success = False
        
    return success

def verify_api_tasks():
    print("\n🔌 Verifying Task API...")
    place_id = "g7_test_place"
    
    try:
        # Create Task
        print("   Creating Task...")
        url = f"{BASE_URL}/api/growth/tasks"
        payload = {
            "placeId": place_id,
            "dueAt": datetime.now().isoformat(),
            "notes": "Verify G7 Task",
            "priority": "high"
        }
        res = requests.post(url, json=payload, timeout=5)
        
        if res.status_code != 200:
            print(f"❌ API Error Status: {res.status_code} - {res.text}")
            return False
            
        data = res.json()
        
        if not data.get('success'):
            print(f"❌ Create Task Failed: {data}")
            return False
            
        task_id = data.get('taskId')
        print(f"✅ Task Created: ID {task_id}")
        
        # Get Tasks
        print("   Fetching Tasks...")
        res = requests.get(url, timeout=5)
        data = res.json()
        tasks = data.get('tasks', [])
        filter_task = [t for t in tasks if t['task_id'] == task_id]
        my_task = filter_task[0] if filter_task else None
        
        if my_task:
            print(f"✅ Task Found in List: {my_task['notes']}")
        else:
            print(f"❌ Task NOT found in list. Listing first 3: {tasks[:3]}")
            return False
            
        # Update Task
        print("   Marking Done...")
        res = requests.put(url, json={"taskId": task_id, "status": "done"}, timeout=5)
        if res.json().get('success'):
            print("✅ Task Marked Done")
        else:
             print("❌ Update Task Failed")
             return False
             
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False
        
    return True

    return True

def seed_test_data():
    print("\n🌱 Seeding Test Data...")
    db = GrowthDB()
    place = {
        "id": "g7_test_place",
        "name": "G7 Test Place",
        "formattedAddress": "123 Test St",
        "website": "example.com",
        "phone": "555-1234"
    }
    db.upsert_place(place, source="TEST")
    print("   ✅ Test Place Inserted")

if __name__ == "__main__":
    seed_test_data()
    
    logic_ok = verify_logic()
    print(f"Logic OK: {logic_ok}")
    
    api_ok = verify_api_tasks()
    print(f"API OK: {api_ok}")
    
    if logic_ok and api_ok:
        print("\n✅ PASSED: G7.0 Operator Excellence Verified.")
        sys.exit(0)
    else:
        print("\n❌ FAILED: G7.0 Verification Errors.")
        sys.exit(1)
