import requests
import sqlite3
from pathlib import Path
import sys

BASE_URL = "http://localhost:3000/api/growth"
DB_PATH = Path("growth/db/growth.db")

def verify_db_schema():
    print("🔍 Checking Schema...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(lead_tasks)")
    cols = [c[1] for c in cursor.fetchall()]
    conn.close()
    
    if "completed_at" in cols and "completed_by" in cols:
        print("   ✅ Columns completed_at/by exist.")
        return True
    print("   ❌ Missing columns.")
    return False

def verify_persistence():
    print("🔄 Testing Persistence...")
    
    # 1. Create Task
    res = requests.post(f"{BASE_URL}/tasks", json={
        "placeId": "g7_test_place",
        "notes": "Persistence Test Task",
        "dueAt": "2025-01-01T10:00:00",
        "priority": "normal"
    })
    if not res.ok:
        print("   ❌ Failed to create task")
        return False
    task_id = res.json()['taskId']
    print(f"   ✅ Created Task ID {task_id}")
    
    # 2. Complete Task
    res = requests.put(f"{BASE_URL}/tasks", json={
        "taskId": task_id,
        "status": "done"
    })
    if not res.ok:
        print("   ❌ Failed to complete task")
        return False
    print("   ✅ Marked Done")
    
    # 3. Check DB for timestamps
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT completed_at, completed_by FROM lead_tasks WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0] and row[1]:
        print(f"   ✅ DB Verified: completed_at={row[0]}, by={row[1]}")
    else:
        print(f"   ❌ DB Verification Failed: {row}")
        return False
        
    # 4. Check API List
    res = requests.get(f"{BASE_URL}/tasks?status=done&limit=5")
    tasks = res.json().get('tasks', [])
    found = any(t['task_id'] == task_id for t in tasks)
    if found:
        print("   ✅ Found in 'Recently Completed' API response")
        return True
    else:
        print("   ❌ Not found in API response")
        return False

if __name__ == "__main__":
    if verify_db_schema() and verify_persistence():
        print("\n✅ PASSED: G8.0 Task Persistence.")
        sys.exit(0)
    else:
        print("\n❌ FAILED: G8.0 Verification.")
        sys.exit(1)
