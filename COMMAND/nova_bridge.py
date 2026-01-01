import time
import os
import sqlite3
import subprocess
import json
import sys
import traceback
from datetime import datetime

# 🏗️ CONFIGURATION
# Updated to point to the centralized NovaHub database
DB_PATH = "c:/AI Fusion Labs/NovaHub-Project/database/nova_memory.db"
INBOX_DIR = "manager_inbox"
OUTBOX_DIR = "engineer_outbox"

# Ensure directories exist
os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs(OUTBOX_DIR, exist_ok=True)

# sys.stdout.reconfigure(encoding='utf-8') # DISABLED FOR USER TERMINAL STABILITY

print(f"[SYSTEM] NOVA BRIDGE ONLINE (SLEDGEHAMMER MODE): Watching {INBOX_DIR}...", flush=True)
print("[INFO] Direct Output Enabled. Watch this terminal for Qwen logs.", flush=True)

def log_task(task_type, content, status):
    """Logs every action to the SQLite Memory."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO TaskHistory (task_type, content, status)
            VALUES (?, ?, ?)
        ''', (task_type, content, status))
        conn.commit()
        conn.close()
        # print(f"[DB] [LOGGED]: {task_type} - {status}") # Reduce noise in terminal
    except Exception as e:
        print(f"[DB ERROR]: {e}")

def execute_script(script_name, args=[]):
    print(f"\n[EXEC] LAUNCHING: {script_name} with args: {args}", flush=True)
    
    # 🛑 VRAM AWARENESS START
    print("[SYSTEM] 5s VRAM COOL-DOWN...", flush=True)
    time.sleep(5)
    # 🛑 VRAM AWARENESS END
    
    try:
        # 🔨 SLEDGEHAMMER FIX: No Pipes, Shell=True, Direct Output
        # We construct the full command string for shell=True usage if needed, 
        # or pass the list. On Windows with shell=True, list is usually fine but 
        # let's be safe and let Python handle the list to string conversion if it wants, 
        # or we just pass the list.
        cmd = ["python", script_name] + args
        
        subprocess.run(
            cmd, 
            shell=True,          # Stability for Windows
            check=True,          # Raise Error on failure
            timeout=300,         # 5 Minute Timeout
            # stdout=None,       # Inherit (Print to Terminal)
            # stderr=None        # Inherit (Print to Terminal)
        )
        
        log_task("SCRIPT_EXECUTION", f"Ran {script_name}", "SUCCESS")
        
        # 🔔 CEO ALERT SYSTEM
        print(f"\n{'='*40}")
        print(f"🚀 MISSION COMPLETE: {script_name}")
        print(f"{'='*40}\n")
        try:
            import winsound
            winsound.Beep(1000, 500) # 1000Hz for 500ms
            time.sleep(0.1)
            winsound.Beep(1000, 500) # Double beep
        except:
            pass
            
        print(f"[SUCCESS] {script_name} COMPLETED.", flush=True) 
        return True
        
    except subprocess.TimeoutExpired as e:
        print(f"\n[CRITICAL] TIMEOUT EXPIRED (300s): {script_name} took too long.")
        log_task("SCRIPT_EXECUTION", f"TIMEOUT: {script_name}", "TIMEOUT")
        return False
        
    except subprocess.CalledProcessError as e:
        # We can't see the error message if we didn't capture it (it went to terminal), 
        # so e.stderr will be None.
        log_task("SCRIPT_EXECUTION", f"Failed {script_name}", "ERROR")
        print(f"\n[ERROR] FAILED: {script_name} (See above for details)")
        return False
        
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED EXECUTION ERROR: {e}")
        return False

# 🔄 MAIN LOOP (GOD MODE)
while True:
    try:
        task_file = os.path.join(INBOX_DIR, "task_queue.json")
        
        if os.path.exists(task_file):
            try:
                with open(task_file, "r", encoding='utf-8') as f:
                    task = json.load(f)
                
                script_to_run = task.get("script")
                args = task.get("args", [])
                
                if script_to_run and os.path.exists(script_to_run):
                    execute_script(script_to_run, args)
                else:
                    print(f"[WARN] Script not found: {script_to_run}")

                # Delete task file
                if os.path.exists(task_file):
                    os.remove(task_file)
                
            except json.JSONDecodeError:
                print("[ERROR] JSON Decode Error - Removing corrupt file")
                if os.path.exists(task_file):
                    os.remove(task_file)
            except Exception as e:
                print(f"[ERROR] Task Processing Error: {e}")
                if os.path.exists(task_file):
                    os.remove(task_file)

        time.sleep(2)

    except KeyboardInterrupt:
        print("\n[SYSTEM] BRIDGE STOPPED BY USER.")
        break
    except Exception as e:
        print(f"\n[CRITICAL] BRIDGE CRASH PREVENTED: {e}")
        traceback.print_exc()
        time.sleep(5)
