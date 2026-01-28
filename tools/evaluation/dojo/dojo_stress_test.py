"""
DOJO STRESS TESTER
Runs a scenario X times and reports pass/fail/leakage rates.
"""

import sys
import subprocess
import argparse
import time
import json
from pathlib import Path

# Config
BASE_DIR = Path(__file__).parent
FACTORY_ROOT = BASE_DIR.parent.parent.parent

def run_iteration(client, scenario, run_id):
    print(f"\n[ITERATION {run_id}] Running...")
    
    # 1. Run Sim
    cmd_run = ["python", "tools/evaluation/dojo/dojo_runner.py", client, scenario, "--turns", "5"] # 5 turns for escalation check
    try:
        subprocess.run(cmd_run, cwd=FACTORY_ROOT, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Runner crashed: {e}")
        return None

    # 2. Find Log
    log_dir = BASE_DIR / "dojo_logs" / client
    try:
        # Get newest file
        log_files = sorted(log_dir.glob("*.txt"), key=lambda f: f.stat().st_mtime, reverse=True)
        latest_log = log_files[0]
    except IndexError:
        print("[FAIL] No log found")
        return None

    # 3. Score
    cmd_score = ["python", "tools/evaluation/dojo/dojo_scorer.py", str(latest_log), "--rubric", "legal"]
    try:
        subprocess.run(cmd_score, cwd=FACTORY_ROOT, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Scorer crashed: {e}")
        return None

    # 4. Read Score
    score_file = latest_log.with_suffix('.score.json')
    with open(score_file, 'r') as f:
        return json.load(f)

def run_stress_test(client, scenario, count=10):
    print(f"--- STRESS TEST: {client} vs {Path(scenario).name} ({count} runs) ---")
    
    results = []
    
    for i in range(1, count + 1):
        res = run_iteration(client, scenario, i)
        if res:
            results.append(res)
            print(f"[RESULT {i}] Score: {res['score']} | Verdict: {res['verdict']}")
            if res['verdict'] == "FAIL (LEAKAGE)":
                print(f"  !!! LEAKAGE: {res['breakdown'].get('LEAKAGE_DETECTED')} !!!")
        else:
            print(f"[RESULT {i}] ERROR")
            
    # Summary
    total = len(results)
    passed = sum(1 for r in results if r['verdict'] == "PASS")
    leaked = sum(1 for r in results if r['verdict'] == "FAIL (LEAKAGE)")
    avg_score = sum(r['score'] for r in results) / total if total > 0 else 0
    
    print("\n=== SUMMARY ===")
    print(f"Total Runs: {total}")
    print(f"Clean Pass: {passed}")
    print(f"Leakage Fail: {leaked}")
    print(f"Avg Score: {avg_score:.1f}")
    
    if leaked == 0 and passed == total:
        print("\n[SUCCESS] AGENT IS HARDENED.")
    else:
        print("\n[FAIL] AGENT NEEDS WORK.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("client", help="Client slug")
    parser.add_argument("scenario", help="Path to scenario")
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()
    
    run_stress_test(args.client, args.scenario, args.count)
